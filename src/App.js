import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom'; 
import PrivateRoute from './PrivateRoute'; 
import { UserProvider } from './UserContext';
import Login from './Login';
import Sidebar from './Sidebar';
import Dashboard from './Dashboard';
import TicketsSummary from './TicketsSummary';
import HostsSummary from './HostsSummary';
import Tickets from './Tickets';
import ServiceRequests from './ServiceRequests';
import HelpDesk from './HelpDesk';
import KnowledgeBase from './KnowledgeBase';
import Monitoring from './Monitoring';
import Customers from './Customers';
import Catalogue from './Catalogue';
import UserManagement from './UserManagement';
import Reports from './Reports';
import Settings from './Settings';
import Header from './Header'; 
import Footer from './Footer'; 
import './App.css';

function App() {
    return (
        <UserProvider>
        <Router>
            <div className="App">
                <Routes>
                    <Route path="/myproject/" element={<Login />} />
                    <Route path="/myproject/" element={<Layout />}>
                        <Route path="dashboard" element={<PrivateRoute element={Dashboard} />} />  
                        <Route path="tickets-summary" element={<PrivateRoute element={TicketsSummary} />} />
                        <Route path="hosts-summary" element={<PrivateRoute element={HostsSummary} />} />
                        <Route path="tickets" element={<PrivateRoute element={Tickets} />} />
                        <Route path="service-requests" element={<PrivateRoute element={ServiceRequests} />} />
                        <Route path="help-desk" element={<PrivateRoute element={HelpDesk} />} />
                        <Route path="knowledge-base" element={<PrivateRoute element={KnowledgeBase} />} />
                        <Route path="monitoring" element={<PrivateRoute element={Monitoring} />} />
                        <Route path="customers" element={<PrivateRoute element={Customers} />} />
                        <Route path="catalogue" element={<PrivateRoute element={Catalogue} />} />
                        <Route path="user-management" element={<PrivateRoute element={UserManagement} />} />
                        <Route path="reports" element={<PrivateRoute element={Reports} />} />
                        <Route path="settings" element={<PrivateRoute element={Settings} />} />
                    </Route>
                </Routes>
            </div>
        </Router>
        </UserProvider>
    );
}

const Layout = () => {
    return (
        <div className="" style={{backgroundColor:'#d3d3d3',width:'100%',display:'flex',flexDirection:'column'}}>
            <Header />  
            <div style={{display:'flex'}}>
            <div style={{width:'250px'}}>

            <Sidebar />
            </div>
            <div className="" style={{ width: 'calc(100% - 250px)',marginLeft:'15px',marginTop:'15px' }}>
                <Routes>
                <Route path="dashboard" element={<PrivateRoute element={Dashboard} />} />  
                <Route path="tickets-summary" element={<PrivateRoute element={TicketsSummary} />} />
                <Route path="hosts-summary" element={<PrivateRoute element={HostsSummary} />} />
                <Route path="tickets" element={<PrivateRoute element={Tickets} />} />
                <Route path="service-requests" element={<PrivateRoute element={ServiceRequests} />} />
                <Route path="help-desk" element={<PrivateRoute element={HelpDesk} />} />
                <Route path="knowledge-base" element={<PrivateRoute element={KnowledgeBase} />} />
                <Route path="monitoring" element={<PrivateRoute element={Monitoring} />} />
                <Route path="customers" element={<PrivateRoute element={Customers} />} />
                <Route path="catalogue" element={<PrivateRoute element={Catalogue}/>} />
                <Route path="user-management" element={<PrivateRoute element={UserManagement}/>} />
                <Route path="reports" element={<PrivateRoute element={Reports} />} />
                <Route path="settings" element={<PrivateRoute element={Settings} />} />
                </Routes>
                </div>
                </div>
            <Footer />  
        </div>
    );
};

export default App;
