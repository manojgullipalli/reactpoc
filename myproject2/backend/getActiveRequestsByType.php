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

    $result = activeTicketsByType($conn, $cust_id, $placeholders);

    echo json_encode(['success' => true, 'data' => $result]);
} else {
    echo json_encode(['success' => false, 'message' => 'Customer ID not provided or invalid']);
}

$conn->close();

function activeTicketsByType($conn, $cust_ids, $placeholders)
{
    // Query for incidents
    $incidentQuery = "
        SELECT COUNT(tkt_id) AS Incident
        FROM osi_tickets
        WHERE tkt_status NOT IN ('N', 'S', 'C')
        AND tkt_cust_id IN ($placeholders)
    ";

    $stmt = $conn->prepare($incidentQuery);
    if ($stmt === false) {
        die(json_encode(['success' => false, 'message' => 'Incident statement preparation failed: ' . $conn->error]));
    }

    // Bind parameters
    $types = str_repeat('i', count($cust_ids)); // assuming cust_id is integer
    $stmt->bind_param($types, ...$cust_ids);

    $stmt->execute();
    $incidentResult = $stmt->get_result()->fetch_assoc();
    $stmt->close();

    // Query for service requests
    $serviceRequestQuery = "
        SELECT COUNT(sr_id) AS ServiceRequest
        FROM osi_service_requests
        WHERE sr_status NOT IN (4, 7, 8, 9)
        AND sr_cust_id IN ($placeholders)
    ";

    $stmt = $conn->prepare($serviceRequestQuery);
    if ($stmt === false) {
        die(json_encode(['success' => false, 'message' => 'Service request statement preparation failed: ' . $conn->error]));
    }

    // Bind parameters
    $stmt->bind_param($types, ...$cust_ids);

    $stmt->execute();
    $serviceRequestResult = $stmt->get_result()->fetch_assoc();
    $stmt->close();

    return array_merge($incidentResult, $serviceRequestResult);
}
?>
