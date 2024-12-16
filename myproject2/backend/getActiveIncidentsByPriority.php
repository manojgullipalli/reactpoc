<?php
header('Access-Control-Allow-Origin: *');
header('Content-Type: application/json');
header('Access-Control-Allow-Methods: POST');
header('Access-Control-Allow-Headers: Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With');

$host = 'localhost';
$db = 'occ_2';
$user = 'root';
$pass = '';

$conn = new mysqli($host, $user, $pass, $db);

if ($conn->connect_error) {
    die(json_encode(['success' => false, 'message' => 'Database connection failed: ' . $conn->connect_error]));
}

$data = json_decode(file_get_contents('php://input'), true);

if (isset($data['cust_id']) && is_array($data['cust_id'])) {
    $cust_id = $data['cust_id'];

    // Create placeholders for the prepared statement
    $placeholders = implode(',', array_fill(0, count($cust_id), '?'));

    $result = activeTicketsByPriority($conn, $cust_id, $placeholders);

    echo json_encode(['success' => true, 'data' => $result]);
} else {
    echo json_encode(['success' => false, 'message' => 'Customer ID not provided or invalid']);
}

$conn->close();

function activeTicketsByPriority($conn, $cust_ids, $placeholders)
{
    // Query for tickets by priority
    $priorityQuery = "
        SELECT 
            SUM(CASE WHEN tkt_priority_id = 'High' THEN 1 ELSE 0 END) AS High,
            SUM(CASE WHEN tkt_priority_id = 'Medium' THEN 1 ELSE 0 END) AS Medium,
            SUM(CASE WHEN tkt_priority_id = 'Low' OR tkt_priority_id = '' THEN 1 ELSE 0 END) AS Low
        FROM osi_tickets
        WHERE tkt_status NOT IN ('N', 'S', 'C')
        AND tkt_cust_id IN ($placeholders)
    ";

    $stmt = $conn->prepare($priorityQuery);
    if ($stmt === false) {
        die(json_encode(['success' => false, 'message' => 'Priority statement preparation failed: ' . $conn->error]));
    }

    // Bind parameters
    $types = str_repeat('i', count($cust_ids)); // assuming cust_id is integer
    $stmt->bind_param($types, ...$cust_ids);

    $stmt->execute();
    $priorityResult = $stmt->get_result()->fetch_assoc();
    $stmt->close();

    return $priorityResult;
}
?>
