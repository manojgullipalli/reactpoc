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

    $result = openSrByAge($conn, $cust_id, $placeholders);

    echo json_encode(['success' => true, 'data' => $result]);
} else {
    echo json_encode(['success' => false, 'message' => 'Customer ID not provided or invalid']);
}

$conn->close();

function openSrByAge($conn, $cust_ids, $placeholders)
{
    // Query for open service requests by age
    $ageQuery = "
        SELECT 
            SUM(CASE WHEN sr_created_date BETWEEN DATE_SUB(UTC_TIMESTAMP(), INTERVAL 2 DAY) AND UTC_TIMESTAMP() THEN 1 ELSE 0 END) AS One,
            SUM(CASE WHEN sr_created_date BETWEEN DATE_SUB(UTC_TIMESTAMP(), INTERVAL 5 DAY) AND DATE_SUB(UTC_TIMESTAMP(), INTERVAL 2 DAY) THEN 1 ELSE 0 END) AS Two,
            SUM(CASE WHEN sr_created_date BETWEEN DATE_SUB(UTC_TIMESTAMP(), INTERVAL 12 DAY) AND DATE_SUB(UTC_TIMESTAMP(), INTERVAL 5 DAY) THEN 1 ELSE 0 END) AS Three,
            SUM(CASE WHEN sr_created_date BETWEEN DATE_SUB(UTC_TIMESTAMP(), INTERVAL 22 DAY) AND DATE_SUB(UTC_TIMESTAMP(), INTERVAL 12 DAY) THEN 1 ELSE 0 END) AS Four,
            SUM(CASE WHEN sr_created_date < DATE_SUB(UTC_TIMESTAMP(), INTERVAL 30 DAY) THEN 1 ELSE 0 END) AS Five
        FROM osi_service_requests
        WHERE sr_status NOT IN ('7', '8', '9')
    ";

    if (count($cust_ids) == 1) {
        $ageQuery .= " AND sr_cust_id = ?";
    } else {
        $ageQuery .= " AND sr_cust_id IN ($placeholders)";
    }

    $stmt = $conn->prepare($ageQuery);
    if ($stmt === false) {
        die(json_encode(['success' => false, 'message' => 'Service requests by age statement preparation failed: ' . $conn->error]));
    }

    // Bind parameters
    if (count($cust_ids) == 1) {
        $stmt->bind_param('i', $cust_ids[0]);
    } else {
        $types = str_repeat('i', count($cust_ids)); // assuming cust_id is integer
        $stmt->bind_param($types, ...$cust_ids);
    }

    $stmt->execute();
    $ageResult = $stmt->get_result()->fetch_assoc();
    $stmt->close();

    return $ageResult;
}
?>
