import React, { useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { UserContext } from './UserContext';

function Login() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [message, setMessage] = useState('');
    const navigate = useNavigate();
    const { setUser } = useContext(UserContext);

    const handleLogin = async (e) => {
        e.preventDefault();
        console.log("Username:", username);
        console.log("Password:", password);
        try {
            const response = await axios.post('http://localhost/myproject2/backend/login.php', { username, password });
            if (response.data.success) {
                const user = { username, fullName: response.data.u_fname, userId: response.data.u_id, customer_ids: response.data.customer_ids };
                setUser(user);
                localStorage.setItem('user', JSON.stringify(user)); // Save user to local storage
                navigate('/myproject/dashboard');
            } else {
                setMessage(response.data.message);
            }
        } catch (error) {
            console.error('There was an error logging in!', error);
        }
    };

    return (
        <div className="login-container">
            <div>
                <img src="https://occ.osidigital.com/images/logo.png" alt="OSI Digital" style={{width: "200px"}} />
            </div>
            <h2 className="text-center">OSI Control Center</h2>
            <div className="login-box-body">
                <form onSubmit={handleLogin}>
                    <p className="login-box-msg">Sign in to start your session</p>
                    <div>
                        <input
                            type="text"
                            value={username}
                            placeholder='User Name'
                            className='form-control'
                            onChange={(e) => setUsername(e.target.value)}
                            required
                        />
                    </div>
                    <div>
                        <input
                            type="password"
                            value={password}
                            placeholder='Password'
                            className='form-control'
                            onChange={(e) => setPassword(e.target.value)}
                            required
                        />
                    </div>
                    <button type="submit">Sign In</button>
                </form>
            </div>
            {message && <p>{message}</p>}
        </div>
    );
}

export default Login;
