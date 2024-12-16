import React, { useState, useEffect, useContext } from 'react';
import ReactEcharts from 'echarts-for-react';
import axios from 'axios';
import { UserContext } from '../UserContext';

const ActiveIncidentsByAge = () => {
    const [chartData, setChartData] = useState([]);
    const { user } = useContext(UserContext);
    const [total,setTotal] =useState();
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await axios.post('http://localhost/myproject2/backend/getActiveIncidentsByAge.php', { cust_id: user.customer_ids });
                const data = response.data.data;
                const percentTotal=Object.values(data)?.reduce((sum, item) => sum + parseInt(item), 0)
                    setTotal(percentTotal)
                const formattedData = [
                    { name: '1-2 Days', value: data.One },
                    { name: '3-5 Days', value: data.Two },
                    { name: '6-12 Days', value: data.Three },
                    { name: '13-22 Days', value: data.Four },
                    { name: 'More than 22 Days', value: data.Five }
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
            text: 'Active Incidents By Age',
            left: 'left',
            padding: 15,
            textStyle: {
                fontSize: 14
            }
        },
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'shadow'
            }
        },
        xAxis: {
            type: 'category',
            data: chartData.map(item => item.name),
            axisLabel: {
                fontSize: 12
            }
        },
        yAxis: {
            type: 'value',
            axisLabel: {
                fontSize: 12
            },
        },
        series: [
            {
                name: 'Incidents',
                type: 'bar',
                data: chartData.map(item => item.value),
                itemStyle: {
                    color: '#73C9E5'
                },
                label: {
                    show: true,
                    position: 'top',
                    fontSize: 12
                }
            }
        ]
    };

    if (loading) return <div>Loading...</div>;
    if (error) return <div>{error}</div>;

    return (
        total && <ReactEcharts style={{height:'225px',paddingLeft:'10px'}} option={option} />
    );
};

export default ActiveIncidentsByAge;
