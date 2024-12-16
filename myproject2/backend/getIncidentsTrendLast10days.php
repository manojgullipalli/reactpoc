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

    // Execute the query to fetch the month trend
    $result = monthTrend($conn, $cust_id, $placeholders);

    if ($result === false || empty($result)) {
        echo json_encode(['success' => false, 'message' => 'No data found or query failed']);
    } else {
        echo json_encode(['success' => true, 'data' => $result]);
    }
} else {
    echo json_encode(['success' => false, 'message' => 'Customer ID not provided or invalid']);
}

$conn->close();

function monthTrend($conn, $cust_ids, $placeholders)
{
    // Prepare SQL query
    $cust_validation = "";
    if (!empty($cust_ids)) {
        $cust_validation = " AND tkt_cust_id IN ($placeholders)";
    }

    $sql = "
        SELECT Day_3 AS Day, NUM, IFNULL(OPEN_COUNT, 0) OPEN_COUNT, IFNULL(CLOSED_COUNT, 0) CLOSED_COUNT
        FROM (SELECT DAY(DATE(UTC_DATE() + INTERVAL 1 DAY) - INTERVAL NUM DAY) AS DAY_3, NUM
              FROM number WHERE NUM <= 10) c
        LEFT JOIN (
            SELECT DAY(tkt_created_date) DAY_1, COUNT(*) OPEN_COUNT
            FROM osi_tickets TKT
            WHERE tkt_status NOT IN ('C', 'S') 
            AND DATE(TKT.tkt_created_date) BETWEEN DATE_SUB(UTC_DATE(), INTERVAL 10 DAY) AND UTC_DATE()
            $cust_validation
            GROUP BY DAY_1
            ORDER BY tkt_created_date DESC
        ) a ON c.DAY_3 = a.DAY_1
        LEFT JOIN (
            SELECT DAY(TKT1.tkt_closed_date) DAY_2, COUNT(*) CLOSED_COUNT
            FROM osi_tickets TKT1
            WHERE tkt_status IN ('C', 'S') 
            AND ((DATE(TKT1.tkt_closed_date) BETWEEN DATE_SUB(UTC_DATE(), INTERVAL 10 DAY) AND UTC_DATE())
            OR (DATE(TKT1.tkt_resolved_date) BETWEEN DATE_SUB(UTC_DATE(), INTERVAL 10 DAY) AND UTC_DATE()))
            $cust_validation
            GROUP BY DAY_2
            ORDER BY tkt_closed_date DESC
        ) b ON c.DAY_3 = b.DAY_2
    ";

    // Log the final query for debugging
    error_log('Month Trend Query: ' . $sql);

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
    error_log('Month Trend Result: ' . print_r($result, true));

    $stmt->close();

    return $result;
}
?>
