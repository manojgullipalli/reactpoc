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

    // Prepare placeholders for customer IDs
    $placeholders = implode(',', array_fill(0, count($cust_id), '?'));

    // Execute the query to fetch the month trend using the monthTrendSr function
    $result = monthTrendSr($conn, $cust_id, $placeholders);

    if ($result === false || empty($result)) {
        echo json_encode(['success' => false, 'message' => 'No data found or query failed']);
    } else {
        echo json_encode(['success' => true, 'data' => $result]);
    }
} else {
    echo json_encode(['success' => false, 'message' => 'Customer ID not provided or invalid']);
}

$conn->close();

function monthTrendSr($conn, $cust_ids, $placeholders)
{
    // Prepare SQL query for service requests month trend
    $cust_validation = "";
    if (!empty($cust_ids)) {
        $cust_validation = " AND sr_cust_id IN ($placeholders)";
    }

    $subquery_c = "
        SELECT DAY(DATE(UTC_DATE() + INTERVAL 1 DAY) - INTERVAL NUM DAY) AS DAY_3
        FROM number 
        WHERE NUM <= 10
    ";

    $sql = "
        SELECT DAY_3 AS Day, IFNULL(OPEN_COUNT, 0) AS OPEN_COUNT, IFNULL(CLOSED_COUNT, 0) AS CLOSED_COUNT 
        FROM ($subquery_c) c 
        LEFT JOIN (
            SELECT DAY(sr_created_date) AS DAY_1, COUNT(*) AS OPEN_COUNT 
            FROM osi_service_requests SR 
            WHERE sr_status NOT IN ('7', '8') 
                AND DATE(SR.sr_created_date) BETWEEN DATE_SUB(UTC_DATE(), INTERVAL 10 DAY) AND UTC_DATE()
                $cust_validation
            GROUP BY DAY_1
            ORDER BY sr_created_date DESC
        ) a ON c.DAY_3 = a.DAY_1 
        LEFT JOIN (
            SELECT DAY(SR1.sr_closed_date) AS DAY_2, COUNT(*) AS CLOSED_COUNT 
            FROM osi_service_requests SR1 
            WHERE sr_status IN ('7', '8') 
                AND ((DATE(SR1.sr_closed_date) BETWEEN DATE_SUB(UTC_DATE(), INTERVAL 10 DAY) AND UTC_DATE()) 
                OR (DATE(SR1.sr_resolved_date) BETWEEN DATE_SUB(UTC_DATE(), INTERVAL 10 DAY) AND UTC_DATE()))
                $cust_validation
            GROUP BY DAY_2
            ORDER BY sr_closed_date DESC
        ) b ON c.DAY_3 = b.DAY_2
    ";

    // Log the final query for debugging
    error_log('Month Trend Service Request Query: ' . $sql);

    $stmt = $conn->prepare($sql);
    if ($stmt === false) {
        die(json_encode(['success' => false, 'message' => 'Month trend statement preparation failed: ' . $conn->error]));
    }

    // Bind parameters if necessary
    if (!empty($cust_ids)) {
        $types = str_repeat('i', count($cust_ids));
        $stmt->bind_param($types, ...$cust_ids);
    }

    $stmt->execute();
    $result = $stmt->get_result()->fetch_all(MYSQLI_ASSOC);

    // Log the query result for debugging
    error_log('Month Trend Service Request Result: ' . print_r($result, true));

    $stmt->close();

    return $result;
}
?>
