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

if (isset($data['username']) && isset($data['password'])) {
    $username = $data['username'];
    $password = $data['password'];

    $stmt = $conn->prepare('SELECT u_password, u_fname, u_id FROM osi_users WHERE u_username = ?');
    $stmt->bind_param('s', $username);
    $stmt->execute();
    $result = $stmt->get_result();

    if ($result->num_rows > 0) {
        $row = $result->fetch_assoc();
        if (password_verify($password, $row['u_password'])) {
            $user_id = $row['u_id'];
            
            // Fetch customer IDs associated with the user
            $customer_ids = getUserCustomers($conn, $user_id);
            
            echo json_encode([
                'success' => true,
                'message' => 'Login successful',
                'u_fname' => $row['u_fname'],
                'u_id' => $user_id,
                'customer_ids' => $customer_ids
            ]);
        } else {
            echo json_encode(['success' => false, 'message' => 'Invalid username or password']);
        }
    } else {
        echo json_encode(['success' => false, 'message' => 'Invalid username or password']);
    }

    $stmt->close();
} else {
    echo json_encode(['success' => false, 'message' => 'Please provide username and password']);
}

$conn->close();

function getUserCustomers($conn, $user_id)
{
    $query = "SELECT cust_id FROM osi_customers
              WHERE cust_active = '1'";

    $stmt = $conn->prepare($query);

    $stmt->execute();
    $result = $stmt->get_result();
    
    $customer_ids = [];
    while ($row = $result->fetch_assoc()) {
        $customer_ids[] = $row['cust_id'];
    }

    $stmt->close();

    return $customer_ids;
}
?>
