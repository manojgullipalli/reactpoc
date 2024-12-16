import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { UserContext } from './UserContext';
import './Header.css';

const Header = () => {
    const navigate = useNavigate();
    const { user, setUser } = useContext(UserContext);
    const [currentTime, setCurrentTime] = useState(new Date());

    useEffect(() => {
        const timer = setInterval(() => {
            setCurrentTime(new Date());
        }, 1000);

        return () => clearInterval(timer);
    }, []);

    const handleLogout = () => {
        localStorage.removeItem('authToken');  
        localStorage.removeItem('user'); 
        setUser(null);
        navigate('/myproject/');
    };

    const formattedTime = currentTime.toLocaleString();

    return (
        <header className="header" >
            <div className="header-content">
                <div className="logo">
                    <img src="https://occ.osidigital.com/images/logo.png" alt="OSI Digital" style={{ width: '200px' }} />
                </div>
                <div className="current-time">
                    {formattedTime} IST
                </div>
                <div className="current-name">{user && <span>Welcome {user.fullName}!</span>}</div>
                <div className="user-actions">
                    <button onClick={handleLogout}>Logout</button>
                </div>
            </div>
        </header>
    );
};

export default Header;
