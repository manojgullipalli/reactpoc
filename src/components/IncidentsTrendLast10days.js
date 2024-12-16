import ReactEcharts from 'echarts-for-react';
import React, { useState, useEffect, useContext} from 'react';
import axios from 'axios';
import { UserContext } from '../UserContext';

const IncidentsTrendLast10days = () => {
    const [chartData, setChartData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const { user } = useContext(UserContext);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await axios.post('http://localhost/myproject2/backend/getIncidentsTrendLast10days.php', { cust_id: [] });
                const data = response.data.data;
                console.log(data)
                if (data && Array.isArray(data)) {
                    // Prepare data for the line chart
                    const days = data.map(item => item.Day);
                    const openCounts = data.map(item => item.OPEN_COUNT);
                    const closedCounts = data.map(item => item.CLOSED_COUNT);

                    setChartData({ days, openCounts, closedCounts });
                } else {
                    console.error('Fetched data is invalid or empty:', data);
                }
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
            text: 'Incidents Trend Last 10 Days',
            left: 'left',
            padding: 15,
            textStyle: {
                fontSize: 14
            }
        },
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'cross'
            }
        },
        legend: {
            data: ['Open Incidents', 'Closed Incidents'],
            left: 'right',
            padding: 30,
            textStyle: {
                fontSize: 10,
                lineHeight: 2
            }
        },
        xAxis: {
            type: 'category',
            data: chartData.days,
            axisLabel: {
                fontSize: 12
            }
        },
        yAxis: {
            type: 'value',
            axisLabel: {
                fontSize: 12
            }
        },
        series: [
            {
                name: 'Open Incidents',
                type: 'line',
                data: chartData.openCounts,
                smooth: true,
                itemStyle: {
                    color: '#73C9E5'
                },
                lineStyle: {
                    width: 2
                },
                symbol: 'circle',
                symbolSize: 8
            },
            {
                name: 'Closed Incidents',
                type: 'line',
                data: chartData.closedCounts,
                smooth: true,
                itemStyle: {
                    color: '#FF6F61'
                },
                lineStyle: {
                    width: 2
                },
                symbol: 'circle',
                symbolSize: 8
            }
        ]
    };

    if (loading) return <div>Loading...</div>;
    if (error) return <div>{error}</div>;

    return (
        <ReactEcharts option={option} style={{height:'225px',paddingLeft:'30px'}} />
    );
};

export default IncidentsTrendLast10days;
