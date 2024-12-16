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

    $result = activeSrBySeverity($conn, $cust_id, $placeholders);

    echo json_encode(['success' => true, 'data' => $result]);
} else {
    echo json_encode(['success' => false, 'message' => 'Customer ID not provided or invalid']);
}

$conn->close();

function activeSrBySeverity($conn, $cust_ids, $placeholders)
{
    // Query for service requests by severity
    $severityQuery = "
        SELECT 
            COUNT(*) AS sr_count,
            ts_name
        FROM osi_service_requests
        LEFT JOIN osi_severities ON ts_id = sr_ts_id
        WHERE sr_status NOT IN ('7', '8', '9')
        AND sr_ts_id <> ''
        AND sr_ts_id <> '0'
    ";

    if (count($cust_ids) == 1) {
        $severityQuery .= " AND sr_cust_id = ?";
    } else {
        $severityQuery .= " AND sr_cust_id IN ($placeholders)";
    }

    $severityQuery .= " GROUP BY ts_id";

    $stmt = $conn->prepare($severityQuery);
    if ($stmt === false) {
        die(json_encode(['success' => false, 'message' => 'Severity statement preparation failed: ' . $conn->error]));
    }

    // Bind parameters
    if (count($cust_ids) == 1) {
        $stmt->bind_param('i', $cust_ids[0]);
    } else {
        $types = str_repeat('i', count($cust_ids)); // assuming cust_id is integer
        $stmt->bind_param($types, ...$cust_ids);
    }

    $stmt->execute();
    $severityResult = $stmt->get_result()->fetch_all(MYSQLI_ASSOC);
    $stmt->close();

    return $severityResult;
}
?>
