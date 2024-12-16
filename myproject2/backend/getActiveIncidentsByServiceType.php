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

// Capture the input data
$data = json_decode(file_get_contents('php://input'), true);

if (isset($data['cust_id']) && is_array($data['cust_id'])) {
    $cust_id = $data['cust_id'];

    // Log input data for debugging
    error_log('Input cust_id: ' . print_r($cust_id, true));

    $placeholders = implode(',', array_fill(0, count($cust_id), '?'));

    $result = openTicketsByServiceType($conn, $cust_id, $placeholders);

    if ($result === false || empty($result)) {
        echo json_encode(['success' => false, 'message' => 'No data found or query failed']);
    } else {
        echo json_encode(['success' => true, 'data' => $result]);
    }
} else {
    echo json_encode(['success' => false, 'message' => 'Customer ID not provided or invalid']);
}

$conn->close();

function openTicketsByServiceType($conn, $cust_ids, $placeholders)
{
    // Query for open tickets by service type
    $serviceTypeQuery = "
        SELECT 
            *,
            COUNT(tkt_id) AS count
        FROM osi_tickets
        LEFT JOIN osi_customers ON cust_id = tkt_cust_id
        LEFT JOIN osi_service_catalog ON scat_id = tkt_scat_id
        LEFT JOIN osi_events ON event_id = scat_event_id
        LEFT JOIN osi_service_type ON st_id = event_st_id
        WHERE tkt_status NOT IN ('N', 'S', 'C')
        AND event_st_id != ''
    ";

    if (count($cust_ids) == 1) {
        $serviceTypeQuery .= " AND tkt_cust_id = ?";
    } else {
        $serviceTypeQuery .= " AND tkt_cust_id IN ($placeholders)";
    }

    $serviceTypeQuery .= " GROUP BY st_id";

    // Log the final query for debugging
    error_log('Service Type Query: ' . $serviceTypeQuery);

    $stmt = $conn->prepare($serviceTypeQuery);
    if ($stmt === false) {
        die(json_encode(['success' => false, 'message' => 'Tickets by service type statement preparation failed: ' . $conn->error]));
    }

    // Bind parameters
    if (count($cust_ids) == 1) {
        $stmt->bind_param('i', $cust_ids[0]);
    } else {
        $types = str_repeat('i', count($cust_ids)); 
        $stmt->bind_param($types, ...$cust_ids);
    }

    $stmt->execute();
    $serviceTypeResult = $stmt->get_result()->fetch_all(MYSQLI_ASSOC);

    // Log the query result for debugging
    error_log('Service Type Result: ' . print_r($serviceTypeResult, true));

    $stmt->close();

    return $serviceTypeResult;
}
?>
