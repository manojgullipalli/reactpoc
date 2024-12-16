import React, { useState, useEffect, useContext } from 'react';
import ReactEcharts from 'echarts-for-react';
import axios from 'axios';
import { UserContext } from '../UserContext';

const ActiveServiceRequestsByAge = () => {
    const [chartData, setChartData] = useState([]);
    const { user } = useContext(UserContext);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await axios.post('http://localhost/myproject2/backend/getActiveServiceRequestsByAge.php', { cust_id: user.customer_ids });
                const data = response.data.data;

                const formattedData = [
                    { value: data.One, name: '0-2 days' },
                    { value: data.Two, name: '3-5 days' },
                    { value: data.Three, name: '6-12 days' },
                    { value: data.Four, name: '13-22 days' },
                    { value: data.Five, name: '23+ days' }
                ];

                setChartData(formattedData);
            } catch (err) {
                setError('Error fetching data');
                console.error('Error fetching data:', err);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [user]);

    const option = {
        title: {
            text: 'Active Service Requests By Age',
            left: 'left',
            padding: 15,
            textStyle: {
                fontSize: 14
            }
        },
        xAxis: {
            type: 'category',
            data: chartData.map(item => item.name),
            axisLabel: {
                fontSize: 10
            }
        },
        yAxis: {
            type: 'value',
            axisLabel: {
                fontSize: 10
            }
        },
        series: [
            {
                data: chartData.map(item => item.value),
                type: 'bar',
                barWidth: '50%',
                itemStyle: {
                    color: '#7cb5ec'
                }
            }
        ],
        tooltip: {
            trigger: 'axis',
            formatter: '{b}: {c}'
        }
    };

    if (loading) return <div>Loading...</div>;
    if (error) return <div>{error}</div>;

    return <ReactEcharts style={{height:'225px',paddingLeft:'30px'}} option={option} />;
};

export default ActiveServiceRequestsByAge;
