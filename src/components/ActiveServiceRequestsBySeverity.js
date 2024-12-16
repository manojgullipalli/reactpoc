import React, { useState, useEffect, useContext } from 'react';
import ReactEcharts from 'echarts-for-react';
import axios from 'axios';
import { UserContext } from '../UserContext';

const ActiveServiceRequestsBySeverity = () => {
    const [chartData, setChartData] = useState([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const { user } = useContext(UserContext);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await axios.post('http://localhost/myproject2/backend/getActiveServiceRequestsBySeverity.php', { cust_id: user.customer_ids });

                const data = response.data.data;
                const formattedData = data.map(item => ({
                    value: item.sr_count,
                    name: item.ts_name
                }));

                const percentTotal = formattedData.reduce((sum, item) => sum + item.value, 0);
                setTotal(percentTotal);

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
            text: 'Active Service Requests By Severity',
            left: 'left',
            padding: 15,
            textStyle: {
                fontSize: 14
            }
        },
        legend: {
            orient: 'vertical',
            left: 'right',
            padding: 30,
            textStyle: {
                fontSize: 10,
                lineHeight: 2
            },
            icon: 'circle',
            formatter: function (name) {
                const item = chartData.find(d => d.name === name);
                const percent = ((item.value / total) * 100).toFixed(2);
                return `${name}: ${percent}%`;
            }
        },
        series: [
            {
                name: 'Severity',
                type: 'pie',
                radius: '30%',
                center: ['25%', '30%'],
                data: chartData,
                tooltip: {
                    trigger: 'item',
                    formatter: '{a} <br/>{b}: {c} ({d}%)'
                },
                emphasis: {
                    itemStyle: {
                   
                    }
                },
                label: {
                    show: false
                }
            }
        ]
    };

    if (loading) return <div>Loading...</div>;
    if (error) return <div>{error}</div>;

    return (
        <ReactEcharts option={option} />
    );
};

export default ActiveServiceRequestsBySeverity;
