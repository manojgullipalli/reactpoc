import React, { useContext } from 'react';
import { Navigate } from 'react-router-dom';
import { UserContext } from './UserContext';

const PrivateRoute = ({ element: Component, ...rest }) => {
    const { user } = useContext(UserContext);

    return user ? <Component {...rest} /> : <Navigate to="/myproject/" />;
};

export default PrivateRoute;
