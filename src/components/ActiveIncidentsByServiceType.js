import React, { useState, useEffect, useContext } from 'react';
import ReactEcharts from 'echarts-for-react';
import axios from 'axios';
import { UserContext } from '../UserContext';

const ActiveIncidentsByServiceType = () => {
    const [data, setData] = useState([]);
    const { user } = useContext(UserContext);
    const [total, setTotal] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                //console.log(user.customer_ids);
                const response = await axios.post('http://localhost/myproject2/backend/getActiveIncidentsByServiceType.php', { cust_id: user.customer_ids });
                const data = response.data.data;
                //console.log(data);
                
                if (data && Array.isArray(data) && data.length > 0) {
                    const chartData = data.map(item => ({
                        value: parseInt(item.count, 10),
                        name: item.st_id // Assuming `st_id` is the service type name/ID
                    }));

                    const percentTotal = chartData.reduce((sum, item) => sum + item.value, 0);
                    setTotal(percentTotal);
                    setData(chartData);
                } else {
                    console.error('Fetched data is invalid or empty:', data);
                }
            } catch (error) {
                console.error('Error fetching the data', error);
            }
        };

        fetchData();
    }, [user]);

    const option = {
        title: {
            text: 'Active Incidents By Service Type',
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
            },
            formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        xAxis: {
            type: 'category',
            data: data.map(item => item.name),
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
                data: data.map(item => item.value),
                itemStyle: {
                    color: '#73C9E5'
                },
                label: {
                    show: true,
                    position: 'top',
                    fontSize: 12,
                    formatter: function (params) {
                        const percent = ((params.value / total) * 100).toFixed(2);
                        return `${percent}%`;
                    }
                }
            }
        ]
    };

    return (
        total && data.length > 0 ? (
            <ReactEcharts style={{height:'225px',paddingLeft:'30px'}} option={option} />
        ) : (
            <div>Loading or no data available...</div>
        )
    );
};

export default ActiveIncidentsByServiceType;
