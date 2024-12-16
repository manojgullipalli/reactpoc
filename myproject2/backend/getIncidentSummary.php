<?php
header('Access-Control-Allow-Origin: *');
header('Content-Type: application/json');
header('Access-Control-Allow-Methods: POST');
header('Access-Control-Allow-Headers: Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With');

// Database connection details
$host = 'localhost';
$db = 'occ_2';
$user = 'root';
$pass = '';

// Create the connection
$conn = new mysqli($host, $user, $pass, $db);

// Check the connection
if ($conn->connect_error) {
    die(json_encode(['success' => false, 'message' => 'Database connection failed: ' . $conn->connect_error]));
}

// Get the input data
$data = json_decode(file_get_contents('php://input'), true);

if (isset($data['cust_id']) && is_array($data['cust_id'])) {
    $cust_id = $data['cust_id'];

    // Create placeholders for the prepared statement
    $placeholders = implode(',', array_fill(0, count($cust_id), '?'));

    // Fetch the incident summary
    $result = getIncidentSummary($conn, $cust_id, $placeholders);

    // Output the result as JSON
    echo json_encode(['success' => true, 'data' => $result]);
} else {
    echo json_encode(['success' => false, 'message' => 'Customer ID not provided or invalid']);
}

// Close the connection
$conn->close();

/**
 * Fetches the incident summary based on customer IDs.
 *
 * @param mysqli $conn Database connection
 * @param array $cust_ids Array of customer IDs
 * @param string $placeholders Placeholders for the SQL query
 * @return array The incident summary data
 */
function getIncidentSummary($conn, $cust_ids, $placeholders)
{
    $query = "
        SELECT 
            c.cust_name,
            t.tkt_cust_id,
            COUNT(IF((t.tkt_status IN ('O', 'A', 'W', 'CH')) AND (t.tkt_disp_status = '1'), 1, NULL)) AS public_total,
            COUNT(IF(t.tkt_disp_status = '0', 1, NULL)) AS private_total,
            COUNT(IF(t.tkt_status = 'O' AND t.tkt_disp_status = '1', 1, NULL)) AS public_open,
            COUNT(IF(t.tkt_status = 'O' AND t.tkt_disp_status = '0', 1, NULL)) AS private_open,
            COUNT(IF(t.tkt_status = 'A' AND t.tkt_disp_status = '1', 1, NULL)) AS public_acknowledged,
            COUNT(IF(t.tkt_status = 'A' AND t.tkt_disp_status = '0', 1, NULL)) AS private_acknowledged,
            COUNT(IF(t.tkt_status = 'W' AND t.tkt_disp_status = '1', 1, NULL)) AS public_workin_progress,
            COUNT(IF(t.tkt_status = 'W' AND t.tkt_disp_status = '0', 1, NULL)) AS private_workin_progress,
            COUNT(IF(t.tkt_status = 'CH' AND t.tkt_disp_status = '1', 1, NULL)) AS public_customer_hold,
            COUNT(IF(t.tkt_status = 'CH' AND t.tkt_disp_status = '0', 1, NULL)) AS private_customer_hold
        FROM 
            osi_tickets t
        LEFT JOIN 
            osi_customers c ON c.cust_id = t.tkt_cust_id
        WHERE 
            t.tkt_status <> 'C'
            AND t.tkt_type <> 'SR'
            AND t.tkt_parent_tkt_id IS NULL
            AND t.tkt_cust_id IN ($placeholders)
        GROUP BY 
            t.tkt_cust_id
        ORDER BY 
            public_open DESC,
            public_acknowledged DESC,
            public_workin_progress DESC";

    $stmt = $conn->prepare($query);

    if ($stmt === false) {
        die(json_encode(['success' => false, 'message' => 'Statement preparation failed: ' . $conn->error]));
    }

    // Bind parameters
    $types = str_repeat('i', count($cust_ids)); // assuming cust_id is integer
    $stmt->bind_param($types, ...$cust_ids);

    // Execute and fetch the result
    $stmt->execute();
    $result = $stmt->get_result()->fetch_all(MYSQLI_ASSOC);

    $stmt->close();

    return $result;
}
