import React from 'react';
import { Link } from 'react-router-dom';
import { BiSolidGrid } from 'react-icons/bi';
import { BiFile } from 'react-icons/bi';
import { BiRightIndent } from 'react-icons/bi';
import { BiLaptop } from 'react-icons/bi';
import { BiSolidBriefcase } from "react-icons/bi";
import { BiBookmark } from "react-icons/bi";
import { BiSolidUser } from "react-icons/bi";
import { BiSolidPieChartAlt2 } from "react-icons/bi";
import { BiSolidCog } from "react-icons/bi";

const Sidebar = () => {
    return (
        <div className="sidebar" style={{width:'250px'}}>
            <ul style={{width:'100%'}}>
                <li><Link to="/myproject/dashboard"><BiSolidGrid /> Dashboard</Link></li>
                <li><Link to="/myproject/tickets-summary"><BiFile /> Tickets Summary</Link></li>
                <li><Link to="/myproject/hosts-summary"><BiFile /> Hosts Summary</Link></li>
                <li><Link to="/myproject/tickets"><BiRightIndent /> Tickets</Link></li>
                <li><Link to="/myproject/service-requests"><BiFile /> Service Requests</Link></li>
                <li><Link to="/myproject/help-desk"><BiFile /> Help Desk</Link></li>
                <li><Link to="/myproject/knowledge-base"><BiFile /> Knowledge Base</Link></li>
                <li><Link to="/myproject/monitoring"><BiLaptop /> Monitoring</Link></li>
                <li><Link to="/myproject/customers"><BiSolidBriefcase /> Customers</Link></li>
                <li><Link to="/myproject/catalogue"><BiBookmark /> Catalogue</Link></li>
                <li><Link to="/myproject/user-management"><BiSolidUser /> User Management</Link></li>
                <li><Link to="/myproject/reports"><BiSolidPieChartAlt2 /> Reports</Link></li>
                <li><Link to="/myproject/settings"><BiSolidCog /> Settings</Link></li>
            </ul>
        </div>
    );
};

export default Sidebar;
