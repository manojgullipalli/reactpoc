from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from dateutil import parser
from requests.auth import HTTPBasicAuth
from datetime import timezone
import pymysql
import logging as lg
import configparser as cp
import datetime
import hmac
import hashlib
import json
import os
import requests
import re

# Version and logging configuration
PGM_VERSION = "1.0.0"
cfg = cp.ConfigParser()
cfg.read('/osiocc/occv2/site/occ.osidigital.com/jira/import_jira_tickets_to_occ.ini')

FORMAT = '%(asctime)s %(levelname)s: %(message)s'
logpath = cfg['Logs']['Filepath']
logfile = "import_jira_tickets_to_occ-" + datetime.datetime.now().strftime("%Y-%m-%d") + ".log"
loglevel = cfg['Logs']['Level']
level = getattr(lg, loglevel.upper(), lg.INFO)

lg.basicConfig(format=FORMAT, filename=os.path.join(logpath, logfile), level=level)
lg.info('==================================================')
lg.info('Program starting. Version ' + PGM_VERSION)

# Database connection
server = cfg['OCC']['Server']
database = cfg['OCC']['Database']
username = cfg['OCC']['Username']
password = cfg['OCC']['Password']
try:
    db_occ = pymysql.connect(host=server, user=username, password=password, database=database)
    lg.info('Successfully connected to OCC database.')
except Exception as inst:
    lg.critical('Unable to connect to OCC database.')
    lg.critical(inst)
    raise HTTPException(status_code=500, detail="Unable to connect to OCC database")

def remove_html_tags(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def add_jira_comment(issue_key, comment, jira_url, jira_user_email, jira_user_token):
    
    clean_comment = remove_html_tags(comment)
    
    payload =  json.dumps( {
      "body": {
        "content": [
          {
            "content": [
              {
                "text": clean_comment,
                "type": "text"
              }
            ],
            "type": "paragraph"
          }
        ],
        "type": "doc",
        "version": 1
      }
    })

    auth = HTTPBasicAuth(jira_user_email, jira_user_token)
    api_url = f"{jira_url}issue/{issue_key}/comment"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    response = requests.request(
       "POST",
       url=api_url,
       data=payload,
       headers=headers,
       auth=auth
    )

    if response.status_code == 201:

        response_json = response.json()
        comment_id = response_json.get('id')
        comment_created_time = response_json.get('created')
        comment_created_time_obj = parser.isoparse(comment_created_time)
        comment_created_time_utc = comment_created_time_obj.astimezone(timezone.utc)
        created_createddate = comment_created_time_utc.strftime("%Y-%m-%d %H:%M:%S")
        comment_updated_time = response_json.get('updated')
        comment_updated_time_obj = parser.isoparse(comment_updated_time)
        comment_updated_time_utc = comment_updated_time_obj.astimezone(timezone.utc)
        created_updateddate = comment_updated_time_utc.strftime("%Y-%m-%d %H:%M:%S")

        lg.info(f"Comment added successfully to Jira Ticket {issue_key}")
        
        insert_sql = """
                        INSERT INTO osi_jira_ticket_comment_ids (
                            jtc_jira_ticket_id, jtc_jira_comment_id, jtc_status, jtc_created_time, jtc_updated_time
                        ) VALUES (%s, %s, %s, %s, %s)
                    """
                    
        try:
            with db_occ.cursor() as cursor:
                cursor.execute(insert_sql, (
                    issue_key, comment_id, 'New Comment', created_createddate, created_updateddate ))
                db_occ.commit()
                lg.info("Successfully inserted Jira ticket comment into the OCC database.")

                return JSONResponse(content={"status": "success"}, status_code=200)
                
        except pymysql.MySQLError as e:
            lg.error(f"Error inserting Jira ticket comment into the OCC database: {e}")
            db_occ.rollback()  # Rollback in case of error
    
        lg.info('==================================================')
    else:
        lg.error(f"Failed to add comment. Status code: {response.status_code}. Response: {response.text}")

def get_user_details_by_email(email):
    try:
        with db_occ.cursor(pymysql.cursors.DictCursor) as cursor:
            # SQL query
            sql = """
            SELECT *
            FROM `osi_user_contact_methods`
            JOIN `osi_users` ON u_id = ucm_u_id
            JOIN `osi_user_entity_mapping` ON u_id = user_id
            WHERE FIND_IN_SET(%s, ucm_contact)
              AND ucm_type = 'Email'
              AND u_active = 1
            """
            # Execute the SQL query
            cursor.execute(sql, (email,))
            user_details = cursor.fetchone()

            # If user details are found
            if user_details:
                arr_custUserDet = {}

                if user_details.get('type_name') == 'customer':
                    arr_custUserDet['user_id'] = user_details['ucm_u_id']
                    arr_custUserDet['user_name'] = (
                        f"{user_details.get('u_fname', '')} "
                        f"{user_details.get('u_mname', '')} "
                        f"{user_details.get('u_lname', '')}".strip()
                    )
                    # Fetch customer details by user ID
                    cust_details = get_customer_details_by_user_id(user_details['ucm_u_id'])
                    if cust_details:
                        arr_custUserDet['cust_id'] = cust_details.get('ref_entity_id')
                        arr_custUserDet['cust_code'] = cust_details.get('cust_code')
                else:
                    arr_custUserDet['user_id'] = user_details['u_id']
                    arr_custUserDet['user_name'] = (
                        f"{user_details.get('u_fname', '')} "
                        f"{user_details.get('u_lname', '')}".strip()
                    )

                return arr_custUserDet
            else:
                return None

    except Exception as e:
        lg.info(f"Error fetching user details: {e}")
        return None


def get_customer_details_by_user_id(user_id):
    try:
        with db_occ.cursor(pymysql.cursors.DictCursor) as cursor:
            # Fetch customer details by user ID using the given query
            sql = """
            SELECT ref_entity_id, cust_code 
            FROM osi_user_entity_mapping 
            JOIN osi_customers ON ref_entity_id = cust_id
            WHERE type_name = 'customer'
              AND user_id = %s
              AND cust_active = 1
            """
            cursor.execute(sql, (user_id,))
            cust_details = cursor.fetchone()
            return cust_details

    except Exception as e:
        lg.info(f"Error fetching customer details: {e}")
        return None

def download_attachment(save_path, attachment_image_url, jira_user_email, jira_user_token, file_path_total, filename, fileid, file_as_created_id, file_created_date, file_as_sr_id, file_as_tkt_type):
    try:
        attachment_response = requests.get(attachment_image_url, auth=(jira_user_email, jira_user_token))
        if attachment_response.status_code == 200:
            file_path = os.path.join(save_path, filename)
            with open(file_path, 'wb') as f:
                f.write(attachment_response.content)
            lg.info(f"Attachment {filename} downloaded successfully.")
            
            with db_occ.cursor() as cursor:
                sql = "SELECT count(*) FROM osi_files WHERE file_associatedto_jiraid=%s"
                cursor.execute(sql, (fileid))
                jira_file_id = cursor.fetchone()                         
                
                if jira_file_id[0] > 0:
                    lg.info("Image Already Inserted, Stop Insert into OCC")
                else:
                    # Insert attachment 
                    with db_occ.cursor() as cursor:
                        query = """
                            INSERT INTO osi_files (file_associatedto_id, file_associatedto_jiraid, file_associatedto_type, file_name, file_path, file_as_created_id, file_created_date)
                            VALUES (%s, %s, %s, %s, %s, %s, %s);
                        """
                        values = (file_as_sr_id, fileid, file_as_tkt_type, filename, file_path_total, file_as_created_id, file_created_date)
                        cursor.execute(query, values)
                        db_occ.commit()
                        lg.info(f"Attachment metadata for {filename} inserted into the database.")
        else:
            lg.error(f"Failed to download attachment. Status code: {attachment_response.status_code}")
    except Exception as e:
        lg.error(f"Error handling attachment: {e}")

def getAttachmentsfromjira(attachments,mapped_sr_id,occ_create_user_id,jira_user_email,jira_user_token):
    
    for attachment in attachments:
                                        
        attachment_image_url = attachment['content']  # Get the attachment content URL
        filename = attachment['filename']  # Get the attachment filename
        fileid = attachment['id']  # Get the attachment fileid
        size = attachment['size']  # Get the attachment size
        
        lg.info(f"Processing attachment: {filename}, Size: {size}")
        
        # Define the directory where you want to save the attachments
        save_path = "/osiocc/occv2/site/occ.osidigital.com/uploads/jira_images"
        
        file_path_total = 'uploads/jira_images/'+filename 
        file_as_sr_id = mapped_sr_id
        file_as_tkt_type = 'SR'
        file_as_created_id = occ_create_user_id
        file_utc_time = datetime.datetime.now().astimezone(datetime.timezone.utc)

        file_created_date = file_utc_time.strftime("%Y-%m-%d %H:%M:%S") 
        
        # Save Files
        download_attachment(save_path, attachment_image_url, jira_user_email, jira_user_token, file_path_total, filename, fileid, file_as_created_id, file_created_date, file_as_sr_id, file_as_tkt_type)


def get_comment_attachments(jira_url, ticket_key, jira_user_email, jira_user_token):
    issue_url = f"{jira_url}issue/{ticket_key}"
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.get(issue_url, auth=(jira_user_email, jira_user_token), headers=headers)
    
    if response.status_code == 200:
        issue_data = response.json()

        if 'attachment' in issue_data['fields']:
            return issue_data['fields']['attachment']
        else:
            lg.info("No attachments found in the issue.")
            return None
    else:
        lg.info(f"Failed to retrieve issue details. Status Code: {response.status_code}")
        return None

def log_jira_ticket(db_occ, jira_tkt, occ_tkt, jira_username, jira_email, jira_tkt_status, jira_tkt_comments):
    try:
        # Define the SQL query for inserting the log
        insert_log_sql = """
            INSERT INTO osi_jira_ticket_log (
                jira_tkt, occ_tkt, jira_username, jira_eamil, jira_tkt_status, jira_tkt_comments, jira_log_time
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        # Get the current time for logging
        jira_utc_time = datetime.datetime.now().astimezone(datetime.timezone.utc)
        jira_log_time = jira_utc_time.strftime('%Y-%m-%d %H:%M:%S')

        # Execute the SQL query
        with db_occ.cursor() as cursor:
            cursor.execute(insert_log_sql, (jira_tkt, occ_tkt, jira_username, jira_email, jira_tkt_status, jira_tkt_comments, jira_log_time))
            db_occ.commit()
            lg.info("Log data inserted successfully.")
    
    except Exception as e:
        lg.info(f"Error inserting log: {e}")
        db_occ.rollback()

def last_updated_time_occ_ticket(db_occ, ticket_key):
    try:
    
         # Get the current time for logging
        occ_utc_time = datetime.datetime.now().astimezone(datetime.timezone.utc)
        last_updated_time_occ = occ_utc_time.strftime('%Y-%m-%d %H:%M:%S')

        # Define the SQL query for inserting the log
        update_last_time_sql = """
            UPDATE osi_service_requests SET sr_updated_date = %s WHERE sr_jira_tkt_id = %s
        """

        # Execute the SQL query
        with db_occ.cursor() as cursor:
            cursor.execute(update_last_time_sql, (last_updated_time_occ, ticket_key))
            db_occ.commit()
            lg.info(f"Successfully Updated Last Updated Time to OCC Ticket")
    
    except Exception as e:
        lg.info(f"Error inserting log: {e}")
        db_occ.rollback()

app = FastAPI()

@app.post("/import_jira_tickets")
async def import_jira_tickets(request: Request):
    input_data = await request.body()
    signature_header = request.headers.get('x-hub-signature')

    if signature_header:
        try:
            algo, received_hash = signature_header.split('=', 1)
        except ValueError:
            lg.error("Invalid signature header format.")
            raise HTTPException(status_code=400, detail="Invalid signature header format")

        try:
            with db_occ.cursor() as cursor:
                sql = "SELECT ji_secrate_key,ji_cust_id,ji_api_url,ji_u_email,ji_u_tocken FROM osi_jira_config LIMIT 1"
                cursor.execute(sql)
                result = cursor.fetchone()
                if result:
                    secret_key = result[0]
                    cust_id = result[1]
                    jira_url = result[2]
                    jira_user_email = result[3]
                    jira_user_token = result[4]
                    lg.info('Successfully fetched the secret key from the database.')
                else:
                    lg.error('Secret key not found in the database.')
                    raise HTTPException(status_code=401, detail="Secret key not found in the database")
        except Exception as e:
            lg.error(f'Error fetching secret key from database: {str(e)}')
            raise HTTPException(status_code=500, detail=f"Error fetching secret key from database: {str(e)}")

        computed_hash = hmac.new(
            key=secret_key.encode(),
            msg=input_data,
            digestmod=hashlib.sha256 if algo == 'sha256' else hashlib.sha1
        ).hexdigest()

        lg.info(f"Computed Hash: {computed_hash}")
        lg.info(f"Received Signature: {received_hash}")

        if hmac.compare_digest(computed_hash, received_hash):
            lg.info("Signature validation succeeded.")
            try:
                data = json.loads(input_data)
            except json.JSONDecodeError as e:
                lg.error(f"Error decoding JSON: {str(e)}")
                raise HTTPException(status_code=400, detail="Invalid JSON format")
            lg.info(f"Data: {data}")
            # Ticket Insertion Block
            if 'comment' not in data and 'issue' in data:
                issue = data['issue']
                ticket_id = issue.get('id')
                ticket_key = issue.get('key')
                summary = issue['fields']['summary']
                description_exist = issue['fields']['description'] 
                created = issue['fields']['created']
                jira_created_date_obj = parser.isoparse(created)
                jira_created_utc = jira_created_date_obj.astimezone(timezone.utc)
                jira_created_formatted = jira_created_utc.strftime("%Y-%m-%d %H:%M:%S")
                created_date_utc_time = datetime.datetime.now().astimezone(datetime.timezone.utc)
                created_formatted = created_date_utc_time.strftime("%Y-%m-%d %H:%M:%S") 
                updated = issue['fields']['updated']
                jira_updated_date_obj = parser.isoparse(updated)
                jira_updated_utc = jira_updated_date_obj.astimezone(timezone.utc)
                jira_updated_formatted = jira_updated_utc.strftime("%Y-%m-%d %H:%M:%S")
                updated_date_utc_time = datetime.datetime.now().astimezone(datetime.timezone.utc)
                updated_formatted = updated_date_utc_time.strftime("%Y-%m-%d %H:%M:%S") 
                project = issue['fields']['project']['name']
                project_id = issue['fields']['project']['id']
                priority = issue['fields']['priority']['name']
                priority_id = issue['fields']['priority']['id']
                status = issue['fields']['status']['name']
                status_id = issue['fields']['status']['id']
                creator = issue['fields']['creator']['displayName']
                updateuser = data['user']['displayName']
                updateuseremail = data['user'].get('emailAddress')
                creatoremail = issue['fields']['creator'].get('emailAddress')
                attachments = issue['fields'].get('attachment', [])
                changelog_field = data['changelog']['items'][0]['fieldId']
                
                if creatoremail:
                    #Function: Get Create User Details 
                    create_user_data = get_user_details_by_email(creatoremail)
                    
                    if create_user_data:
                        lg.info(f"Create User Details: {create_user_data}")
                        occ_create_user_id = create_user_data['user_id']
                        description = f"""{description_exist}"""
                    else:
                        lg.info(f"No user found.")
                        occ_create_user_id = '7116'
                        description = f"""
                            Jira Ticket Created By: {creator} <br>
                            {description_exist}
                        """
                else:
                    occ_create_user_id = '7116'
                    description = f"""
                            Jira Ticket Created By: {creator} <br>
                            {description_exist}
                        """
                    
                try:
                    #Query 1: Map priority
                    with db_occ.cursor() as cursor:
                        sql = "SELECT srp_level FROM osi_jira_priority_mapping WHERE jira_priority_code=%s AND cust_id=%s"
                        cursor.execute(sql, (priority_id, cust_id))
                        priority_mapping = cursor.fetchone()
                        if priority_mapping:
                            mapped_priority = priority_mapping[0]
                            if mapped_priority == 17:
                                mapped_severity = 15
                            elif mapped_priority == 22:
                                mapped_severity = 16
                            elif mapped_priority == 23:
                                mapped_severity = 17
                            lg.info(f"Mapped Priority: {mapped_priority}")
                        else:
                            lg.error(f"No mapping found for Jira priority: {priority_id}")
                          
                    # Query 2: Map status
                    with db_occ.cursor() as cursor:
                        sql = "SELECT srs_id,srs_name,jira_status_code FROM osi_jira_status_mapping WHERE jira_to_occ_status=%s AND cust_id=%s"
                        cursor.execute(sql, (status_id, cust_id))
                        status_mapping = cursor.fetchone()
                        if status_mapping:
                            mapped_status = status_mapping[0]
                            mapped_srs_name = status_mapping[1]
                            mapped_jira_status_code = status_mapping[2]
                            lg.info(f"Mapped Status: {mapped_status}")
                        else:
                            lg.error(f"No mapping found for Jira status: {status_id}")
                             
                    # Query 3: Map project
                    with db_occ.cursor() as cursor:
                        sql = "SELECT p_id FROM osi_jira_project_mapping WHERE jira_project_code=%s AND cust_id=%s"
                        cursor.execute(sql, (project_id, cust_id))
                        project_mapping = cursor.fetchone()
                        if project_mapping:
                            mapped_project = project_mapping[0]
                            lg.info(f"Mapped Project: {mapped_project}")
                        else:
                            lg.error(f"No mapping found for Jira project: {project_id}")
                             
                    # Query 4: Fetch cust_code
                    with db_occ.cursor() as cursor:
                        sql = """
                            SELECT cust_code 
                            FROM osi_customers
                            LEFT JOIN osi_users ON u_id = cust_prim_analyst_id
                            WHERE cust_id = %s
                        """
                        cursor.execute(sql, (cust_id,))
                        cust_code_result = cursor.fetchone()
                        if cust_code_result:
                            cust_code = cust_code_result[0]
                            lg.info(f"Fetched Cust Code: {cust_code}")
                        else:
                            lg.error("No cust_code found.")     
     
                    # Query 5: Fetch external ID
                    with db_occ.cursor() as cursor:
                        sql = """
                            SELECT sr_external_id 
                            FROM osi_service_requests 
                            WHERE sr_id = (
                                SELECT MAX(sr_id) 
                                FROM osi_service_requests 
                                WHERE sr_cust_id = %s 
                                AND (sr_isHelpDeskReq IN (0, 1))
                            )
                            LIMIT 1;
                        """
                        cursor.execute(sql, (cust_id,))
                        external_id_result = cursor.fetchone()
                        if external_id_result:
                            external_id = external_id_result[0]
                            lg.info(f"Fetched External ID: {external_id}")
                            
                            # Generate new external ID
                            tkt_hd_type = 'SR'
                            arr_ext = external_id.split('-', 10)
                            new_sr_external_id = f"{cust_code}-{tkt_hd_type}-{str(int(arr_ext[-1]) + 1).zfill(6)}"
                            lg.info(f"New External ID: {new_sr_external_id}")
                        else:
                            lg.error("No external ID found.")
                     
                    
                    with db_occ.cursor() as cursor:
                        sql = "SELECT count(*) FROM osi_jira_ticket_comment_ids WHERE jtc_jira_ticket_id=%s"
                        cursor.execute(sql, (ticket_key))
                        jira_tkt_id = cursor.fetchone()
                    
                        if ((jira_tkt_id[0] > 0) or (jira_tkt_id[0] > 0 and data['webhookEvent']=='jira:issue_updated')):
                            lg.info("Ticket Already Inserted, Stop Insert into OCC")
                            with db_occ.cursor() as cursor:
                                sql = "SELECT sr_id,sr_external_id FROM osi_service_requests WHERE sr_jira_tkt_id=%s"
                                cursor.execute(sql, (ticket_key))
                                sr_id_mapping = cursor.fetchone()
                                if sr_id_mapping:
                                    mapped_sr_id = sr_id_mapping[0]
                                    mapped_sr_external_id = sr_id_mapping[1]
                                    lg.info(f"Mapped 1 sr_id: {mapped_sr_id}")
                                else:
                                    lg.error(f"1.No sr_id found for Jira Ticket: {ticket_key}")
                                    
                            if data['issue_event_type_name']=='issue_generic': 
                                
                                with db_occ.cursor() as cursor:
                                    sql = "SELECT count(*) FROM osi_jira_ticket_comment_ids WHERE jtc_jira_ticket_id=%s AND jtc_status=%s AND jtc_ticket_status=%s"
                                    cursor.execute(sql, (ticket_key, 'occ_status_updated',mapped_jira_status_code))
                                    jira_tkt_cmt_id = cursor.fetchone()
                                
                                    if jira_tkt_cmt_id[0] > 0:
                                        lg.info("Status Already Added, Stop Insert into OCC")
                                        return JSONResponse(content={"status": "success"}, status_code=200)
                                    else:
                                
                                        update_sql = """
                                            UPDATE osi_service_requests
                                            SET sr_status = %s
                                            WHERE sr_jira_tkt_id = %s
                                        """

                                        try:
                                            with db_occ.cursor() as cursor:
                                                cursor.execute(update_sql, (mapped_status, ticket_key))
                                                db_occ.commit()
                                                lg.info(f"Updated status to {mapped_status} for Jira Ticket ID: {ticket_key}")
                                                
                                            last_updated_time_occ_ticket(db_occ, ticket_key)    
                                            
                                        except pymysql.MySQLError as e:
                                            lg.error(f"Error Updating Jira ticket status into the OCC database: {e}")
                                            db_occ.rollback()  # Rollback in case of error
                                        try:
                                            comment = f"""Successfully Updated the OCC ticket Status for Ticket Id: {mapped_sr_external_id}"""

                                            add_jira_comment(ticket_key, comment, jira_url, jira_user_email, jira_user_token)

                                        except Exception as e:
                                            lg.error(f"An error occurred: {str(e)}")

                                status_update_desc = f"""Request status changed to {mapped_srs_name} by {updateuser}"""
                                
                                insert_sql = """
                                    INSERT INTO osi_sr_details (
                                        sd_jira_ticket_id, sd_sr_id, sd_work_note, sd_public, sd_as_created_id, sd_created_date, sd_updated_date, sd_note_type
                                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                                """

                                try:
                                    with db_occ.cursor() as cursor:
                                        cursor.execute(insert_sql, (
                                            ticket_key, mapped_sr_id, status_update_desc, 'Y', occ_create_user_id, created_formatted, updated_formatted, 'W'
                                        ))
                                        db_occ.commit()
                                        lg.info("Successfully updated Jira Ticket Status into the OCC database.")
                                    last_updated_time_occ_ticket(db_occ, ticket_key)      
                                except pymysql.MySQLError as e:
                                    lg.error(f"Error inserting Jira ticket comment into the OCC database: {e}")
                                    db_occ.rollback()  # Rollback in case of error
                                
                            else:

                                if changelog_field == 'attachment':

                                    getAttachmentsfromjira(attachments,mapped_sr_id,occ_create_user_id,jira_user_email,jira_user_token)

                                elif changelog_field == 'description':

                                    getAttachmentsfromjira(attachments,mapped_sr_id,occ_create_user_id,jira_user_email,jira_user_token)
                            
                                    description_update = f"""
                                        Jira Ticket Description Updated By: {updateuser} <br>
                                        {description_exist}
                                    """
                                    insert_sql = """
                                        INSERT INTO osi_sr_details (
                                            sd_jira_ticket_id, sd_sr_id, sd_work_note, sd_public, sd_as_created_id, sd_created_date, sd_updated_date, sd_note_type
                                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                                    """

                                    try:
                                        with db_occ.cursor() as cursor:
                                            cursor.execute(insert_sql, (
                                                ticket_key, mapped_sr_id, description_update, 'Y', occ_create_user_id, created_formatted, updated_formatted, 'W'
                                            ))
                                            db_occ.commit()
                                            
                                            lg.info("Successfully inserted Jira Ticket Description into the OCC database.")
                                        last_updated_time_occ_ticket(db_occ, ticket_key)    
                                    except pymysql.MySQLError as e:
                                        lg.error(f"Error inserting Jira ticket comment into the OCC database: {e}")
                                        db_occ.rollback()  # Rollback in case of error
                                    try:
                                        comment = f"""Successfully OCC ticket Description Updated for Ticket Id: {mapped_sr_external_id}"""

                                        add_jira_comment(ticket_key, comment, jira_url, jira_user_email, jira_user_token)    
                                        
                                    except Exception as e:
                                        lg.error(f"An error occurred: {str(e)}")
                                    
                            return JSONResponse(content={"status": "success"}, status_code=200)
                        else:
                            # Insert extracted data into the osi_service_requests table
                            insert_sql = """
                                INSERT INTO osi_service_requests (
                                    sr_external_id, sr_jira_tkt_id, sr_cust_id, sr_title, sr_desc, sr_scat_id, sr_dev_id, sr_app_id, sr_p_id, sr_created_by, sr_created_for, sr_request_mode, sr_status, sr_ts_id, sr_priority_id, sr_event_count, sr_first_event_date, sr_disp_status, sr_location, sr_product_type, sr_created_date, sr_updated_date
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """

                            try:
                                with db_occ.cursor() as cursor:
                                    cursor.execute(insert_sql, (
                                        new_sr_external_id, ticket_key, cust_id, summary, description, '0', '0', '0', mapped_project, occ_create_user_id, occ_create_user_id, 'Jira', mapped_status, mapped_severity, mapped_priority, '1', created_formatted, '1', None, 'Project', created_formatted, created_formatted
                                    ))
                                    
                                    last_sr_id = cursor.lastrowid
                                    db_occ.commit()
                                    lg.info("Successfully inserted Jira ticket into the OCC database.")

                                    try:
                                        comment = f"""Successfully OCC ticket Created with Ticket Id: {new_sr_external_id}"""

                                        add_jira_comment(ticket_key, comment, jira_url, jira_user_email, jira_user_token)    
                                        
                                    except Exception as e:
                                        lg.error(f"An error occurred: {str(e)}")

                                    getAttachmentsfromjira(attachments,last_sr_id,occ_create_user_id,jira_user_email,jira_user_token)
                                    
                                    log_jira_ticket(db_occ, ticket_key, last_sr_id, creator, creatoremail, 'Success', '')
                                    
                                    return JSONResponse(content={"status": "success"}, status_code=200)
                                    
                            except pymysql.MySQLError as e:
                                lg.error(f"Error inserting Jira ticket data into the database: {e}")
                                log_jira_ticket(db_occ, ticket_key, '', creator, creatoremail, 'Fail', e)
                                db_occ.rollback()  # Rollback in case of error
                    
                    lg.info('==================================================')
                except Exception as e:
                    lg.error(f"Error executing database queries: {str(e)}")
                    lg.info(f"Extracted Info:\nJira Info: {issue}")
                    raise HTTPException(status_code=500, detail=f"Database query error: {str(e)}")        
                else:
                    lg.info("No issue data found.")

            if data.get("webhookEvent") in ["comment_created", "comment_updated", "comment_deleted"]:
                
                comment = data['comment']
                issue = data['issue']
                ticket_key = issue.get('key')
                comment_id = comment.get('id')
                comment_text_exist = comment.get('body')
                comment_by = comment['updateAuthor']['displayName']
                comment_emailAddress = comment['updateAuthor'].get('emailAddress')
                comment_created_date = comment['created']
                jira_comment_created_date_obj = parser.isoparse(comment_created_date)
                jira_comment_created_utc = jira_comment_created_date_obj.astimezone(timezone.utc)
                jira_comment_created_formatted = jira_comment_created_utc.strftime("%Y-%m-%d %H:%M:%S")
                comment_created_utc = datetime.datetime.now().astimezone(datetime.timezone.utc)
                comment_created_formatted = comment_created_utc.strftime("%Y-%m-%d %H:%M:%S") 
                comment_updated_date = comment['updated']
                jira_comment_updated_date_obj = parser.isoparse(comment_updated_date)
                jira_comment_updated_utc = jira_comment_updated_date_obj.astimezone(timezone.utc)
                jira_comment_updated_formatted = jira_comment_updated_utc.strftime("%Y-%m-%d %H:%M:%S")
                comment_updated_utc = datetime.datetime.now().astimezone(datetime.timezone.utc)
                comment_updated_formatted = comment_updated_utc.strftime("%Y-%m-%d %H:%M:%S") 
                
                if comment_emailAddress:
                    comment_user_data = get_user_details_by_email(comment_emailAddress)

                    if comment_user_data:
                        lg.info(f"Comment User Details: {comment_user_data}")
                        occ_comment_user_id = comment_user_data['user_id']
                        comment_text = f"""{comment_text_exist}"""
                    else:
                        lg.info(f"No user found.")
                        occ_comment_user_id = '7116'
                        comment_text = f"""
                            Commented By: {comment_by} <br>
                            {comment_text_exist}
                        """
                else:
                    occ_comment_user_id = '7116'
                    comment_text = f"""
                        Commented By: {comment_by} <br>
                        {comment_text_exist}
                    """
                    
                with db_occ.cursor() as cursor:
                    sql = "SELECT count(*) FROM osi_jira_ticket_comment_ids WHERE jtc_jira_ticket_id=%s AND jtc_jira_comment_id=%s"
                    cursor.execute(sql, (ticket_key, comment_id))
                    jira_tkt_cmt_id = cursor.fetchone()
                
                    if jira_tkt_cmt_id[0] > 0:
                        lg.info("Comment Already Added, Stop Insert into OCC")
                        return JSONResponse(content={"status": "success"}, status_code=200)
                    else:
                        try:
                            # Query 1: Get Sr_id
                            with db_occ.cursor() as cursor:
                                sql = "SELECT sr_id,sr_external_id FROM osi_service_requests WHERE sr_jira_tkt_id=%s AND sr_cust_id=%s"
                                cursor.execute(sql, (ticket_key, cust_id))
                                sr_id_mapping = cursor.fetchone()
                                if sr_id_mapping:
                                    mapped_sr_id = sr_id_mapping[0]
                                    mapped_sr_external_id = sr_id_mapping[1]
                                    lg.info(f"Mapped sr_id: {mapped_sr_id}")
                                else:
                                    lg.error(f"2.No sr_id found for Jira Ticket: {ticket_key}")
                                    
                            # Insert extracted data into the osi_sr_details table
                            insert_sql = """
                                INSERT INTO osi_sr_details (
                                    sd_jira_comment_id, sd_sr_id, sd_work_note, sd_public, sd_as_created_id, sd_created_date, sd_updated_date, sd_note_type
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            """

                            try:
                                with db_occ.cursor() as cursor:
                                    cursor.execute(insert_sql, (
                                        comment_id, mapped_sr_id, comment_text, 'Y', occ_comment_user_id, comment_created_formatted, comment_updated_formatted, 'W'
                                    ))
                                    db_occ.commit()
                                    last_updated_time_occ_ticket(db_occ, ticket_key)
                                    lg.info("Inserted Jira Ticket Comment into the OCC database.")
                                    
                                    if(data['webhookEvent']=='comment_updated'):
                                        comment = f"""OCC ticket Comment Updated for Ticket Id: {mapped_sr_external_id}"""
                                        add_jira_comment(ticket_key, comment, jira_url, jira_user_email, jira_user_token)
                                        attachments = get_comment_attachments(jira_url, ticket_key, jira_user_email, jira_user_token)
                                        getAttachmentsfromjira(attachments,mapped_sr_id,occ_comment_user_id,jira_user_email,jira_user_token)
                                        last_updated_time_occ_ticket(db_occ, ticket_key)
                                        return JSONResponse(content={"status": "success"}, status_code=201)
                                    else:
                                        # Add a comment to the Jira issue
                                        comment = f"""OCC ticket Commented for Ticket Id: {mapped_sr_external_id}"""
                                        add_jira_comment(ticket_key, comment, jira_url, jira_user_email, jira_user_token)
                                        attachments = get_comment_attachments(jira_url, ticket_key, jira_user_email, jira_user_token)
                                        getAttachmentsfromjira(attachments,mapped_sr_id,occ_comment_user_id,jira_user_email,jira_user_token)
                                        last_updated_time_occ_ticket(db_occ, ticket_key)
                                        return JSONResponse(content={"status": "success"}, status_code=201)
                                    
                            except pymysql.MySQLError as e:
                                lg.error(f"Error inserting Jira ticket comment into the OCC database: {e}")
                                db_occ.rollback()  # Rollback in case of error

                            lg.info('==================================================')
                        
                        except Exception as e:
                            lg.error(f"Error executing database queries: {str(e)}")
                            lg.info(f"Extracted Info:\nJira Comment Info: {comment}")
                            raise HTTPException(status_code=500, detail=f"Database query error: {str(e)}")    
            else:
                lg.info("No issue data found.")   
        else:
            lg.error("Signature validation failed.")
            raise HTTPException(status_code=403, detail="Signature validation failed")
    else:
        lg.error("No signature header found.")
        raise HTTPException(status_code=400, detail="No signature header found")
    
    return JSONResponse(content={"status": "success"}, status_code=200)

@app.post("/create_sr_occ_jira")
async def create_sr_occ_jira(request: Request):
    try:
        data = await request.json()     
        sr_title = data.get('sr_title')
        sr_desc = data.get('sr_desc') 
        project = data.get('project')
        occ_id = data.get('external_id')
        occ_sr_id = data.get('occ_sr_id')
        user_name = data.get('user_name') 
        jira_url = data.get('jira_url')   
        jira_user_email = data.get('jira_user_email')   
        jira_user_token = data.get('jira_user_token')   
        
        url = f'{jira_url}issue'
        auth = HTTPBasicAuth(jira_user_email, jira_user_token)
    
        headers = {
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                  }

        desc_text = f"""OCC Ticket Created By: {user_name} | OCC Ticket ID: {occ_id}\n{sr_desc}""" 
        
        issue_data = {
                        "fields": {
                            "project": {
                                "key": project  
                            },
                            "summary": sr_title, 
                            "description": {
                                "type": "doc",
                                "version": 1,
                                "content": [
                                    {
                                        "type": "paragraph",
                                        "content": [
                                            {
                                                "type": "text",
                                                "text": desc_text  
                                            }
                                        ]
                                    }
                                ]
                            },
                            "issuetype": {
                                "name": "Task"  
                            }
                        }
                    }
        
        payload = json.dumps(issue_data)

        response = requests.request(
                                    "POST",
                                    url,
                                    data=payload,
                                    headers=headers,
                                    auth=auth
                                    )

        response_json = response.json()
        jira_tkt_number = response_json.get('key')
        jira_tkt_created_time = datetime.datetime.now()
        jira_tkt_updated_time = datetime.datetime.now()
        
        lg.info(f"OCC to Jira Ticket Created Successfully to issue {jira_tkt_number}")
        
        update_jira_id_tosr_sql = """
            UPDATE osi_service_requests SET sr_jira_tkt_id = %s WHERE sr_id = %s
        """

        # Execute the SQL query
        with db_occ.cursor() as cursor:
            cursor.execute(update_jira_id_tosr_sql, (occ_sr_id, jira_tkt_number))
            db_occ.commit()
            lg.info(f"Successfully Updated OCC Ticket with Jira Ticket ID")
        
        insert_sql = """
                        INSERT INTO osi_jira_ticket_comment_ids (
                            jtc_jira_ticket_id, jtc_status, jtc_created_time, jtc_updated_time
                        ) VALUES (%s, %s, %s, %s)
                    """
                    
        try:
            with db_occ.cursor() as cursor:
                cursor.execute(insert_sql, (
                    jira_tkt_number, 'OCC to Jira New Ticket', jira_tkt_created_time, jira_tkt_updated_time ))
                db_occ.commit()
                lg.info("Successfully inserted Jira ticket data into the database.")

                return {"key": jira_tkt_number}
                
        except pymysql.MySQLError as e:
            lg.error(f"Error inserting Jira ticket data into the database: {e}")
            db_occ.rollback()  # Rollback in case of error
    
        lg.info('==================================================')
        
    except json.JSONDecodeError:
        return {"error": "Response is not in JSON format."}
    except Exception as e:
        lg.info("Exception occurred:", e)
        return {"error": str(e)} 

@app.post("/update_occ_jira")
async def update_occ_jira(request: Request):

    try:
        data = await request.json()     
        issue_key = data.get('tkt_id')
        status_id = data.get('status') 
        jira_url = data.get('jira_url')   
        jira_user_email = data.get('jira_user_email')   
        jira_user_token = data.get('jira_user_token')   
        
        url = f'{jira_url}issue/{issue_key}/transitions'
        auth = HTTPBasicAuth(jira_user_email, jira_user_token)
        
        headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"  
        }

        payload = json.dumps( {
                "transition": {
                    "id": status_id
                }
                } )

        response = requests.request(
        "POST",
        url,
        data=payload,
        headers=headers,
        auth=auth
        )
        
        lg.info({"Update OCC to Jira Status:":response})
        
        insert_sql = """
                        INSERT INTO osi_jira_ticket_comment_ids (
                            jtc_jira_ticket_id, jtc_status, jtc_ticket_status
                        ) VALUES (%s, %s, %s)
                    """
                    
        try:
            with db_occ.cursor() as cursor:
                cursor.execute(insert_sql, (
                    issue_key, 'occ_status_updated', status_id))
                db_occ.commit()
                lg.info("Successfully inserted OCC ticket status into the database.")
                
        except pymysql.MySQLError as e:
            lg.error(f"Error inserting OCC ticket status into the database: {e}")
            db_occ.rollback()  # Rollback in case of error
        
    except Exception as e:
        lg.error({"update_status_error":e})

@app.post("/comment_occ_jira")
async def comment_occ_jira(request: Request):
    try:
        data = await request.json()     
        issue_key = data.get('tkt_id')
        worknote = data.get('worknote')
        user_name = data.get('user_name') 
        jira_url = data.get('jira_url')   
        jira_user_email = data.get('jira_user_email')   
        jira_user_token = data.get('jira_user_token')  
        
        comment_text = f"""Commented By OCC User: {user_name}\n{worknote}"""
        
        add_jira_comment(issue_key, comment_text, jira_url, jira_user_email, jira_user_token)

    except Exception as e:
        lg.error({"comment_error":e}) 

@app.post("/attachment_occ_jira")
async def attachment_occ_jira(request: Request):
    
    data = await request.json()
    issue_key = data.get('tkt_id')
    att_path = data.get('att_path')
    jira_url = data.get('jira_url')   
    jira_user_email = data.get('jira_user_email')   
    jira_user_token = data.get('jira_user_token')
    url = f'{jira_url}issue/{issue_key}/attachments'
    auth = HTTPBasicAuth(jira_user_email, jira_user_token)  

    headers = {
        "Accept": "application/json",
        "X-Atlassian-Token": "no-check"
    }

    file_path = att_path
    
    with open(file_path, 'rb') as file:
          files = {'file': (file_path, file, "application-type")}
          response = requests.post(
          url,
          headers=headers,
          auth=auth,
          files=files
    )
    
    if response.status_code == 200:
        attachment_data = response.json()
        attachment_id = attachment_data[0]['id']  
        attachment_name = attachment_data[0]['filename'] 

        lg.info({"OCC to JIRA attachment": response.json()})
    else:
        lg.error({"attachment_upload_error": response.text})
        raise HTTPException(status_code=response.status_code, detail=response.text)