import React, { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import './TicketsSummary.css';
import { UserContext } from './UserContext';

const TicketsSummary = () => {
    const [selectedOption, setSelectedOption] = useState('Incidents');
    const [ticketData, setTicketData] = useState([]);
    const [loading, setLoading] = useState(true);
    const { user } = useContext(UserContext);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                const response = await axios.post('http://localhost/myproject2/backend/getIncidentSummary.php', { cust_id: user.customer_ids });

                if (response.data.success) {
                    setTicketData(response.data.data);
                } else {
                    console.error('Failed to fetch data:', response.data.message);
                }
            } catch (error) {
                console.error('Error fetching data:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [selectedOption, user]);

    const handleOptionChange = (e) => {
        setSelectedOption(e.target.value);
    };

    return (
        <div className="ticket-summary">
            <div className="ticket-summary-header">
                <h2>Tickets Summary (Public : Private)</h2>
                <div className="controls">
                    <div className="radio-buttons">
                        <label>
                            <input
                                type="radio"
                                value="Incidents"
                                checked={selectedOption === 'Incidents'}
                                onChange={handleOptionChange}
                            />
                            Incidents
                        </label>
                        <label>
                            <input
                                type="radio"
                                value="ServiceRequests"
                                checked={selectedOption === 'ServiceRequests'}
                                onChange={handleOptionChange}
                            />
                            Service Requests
                        </label>
                        <label>
                            <input
                                type="radio"
                                value="HelpDesk"
                                checked={selectedOption === 'HelpDesk'}
                                onChange={handleOptionChange}
                            />
                            Help Desk
                        </label>
                    </div>
                </div>
            </div>
            {loading ? (
                <p>Loading...</p>
            ) : (
                <table>
                    <thead>
                        <tr>
                            <th>Customer</th>
                            <th>Open</th>
                            <th>Acknowledged</th>
                            <th>Work In Progress</th>
                            <th>Customer Hold</th>
                            <th>Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        {ticketData.map((ticket, index) => (
                            <tr key={index}>
                                <td>{ticket.cust_name}</td>
                                <td>{ticket.public_open} : {ticket.private_open}</td>
                                <td>{ticket.public_acknowledged} : {ticket.private_acknowledged}</td>
                                <td>{ticket.public_workin_progress} : {ticket.private_workin_progress}</td>
                                <td>{ticket.public_customer_hold} : {ticket.private_customer_hold}</td>
                                <td>{ticket.public_total} : {ticket.private_total}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
        </div>
    );
};

export default TicketsSummary;
