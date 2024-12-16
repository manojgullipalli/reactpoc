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

    $result = activeTickets($conn, $cust_id, $placeholders);

    echo json_encode(['success' => true, 'data' => $result]);
} else {
    echo json_encode(['success' => false, 'message' => 'Customer ID not provided or invalid']);
}

$conn->close();

function activeTickets($conn, $cust_ids, $placeholders)
{
    $sel_options = [
        "SUM(CASE WHEN tkt_status = 'O' THEN 1 ELSE 0 END) AS Open",
        "SUM(CASE WHEN tkt_status = 'A' THEN 1 ELSE 0 END) AS Acknowledged",
        "SUM(CASE WHEN tkt_status = 'W' THEN 1 ELSE 0 END) AS Inprogress",
        "SUM(CASE WHEN tkt_status = 'CH' THEN 1 ELSE 0 END) AS Hold"
    ];

    $query = "SELECT " . implode(", ", $sel_options) . " 
              FROM osi_tickets 
              WHERE tkt_status NOT IN ('N', 'C', 'S') AND tkt_cust_id IN ($placeholders)";

    $stmt = $conn->prepare($query);

    if ($stmt === false) {
        die(json_encode(['success' => false, 'message' => 'Statement preparation failed: ' . $conn->error]));
    }

    // Bind parameters
    $types = str_repeat('i', count($cust_ids)); // assuming cust_id is integer
    $stmt->bind_param($types, ...$cust_ids);

    $stmt->execute();
    $result = $stmt->get_result()->fetch_assoc();

    $stmt->close();

    return $result;
}
?>
