import React, { useState, useEffect, useContext } from 'react';
import ReactEcharts from 'echarts-for-react';
import axios from 'axios';
import { UserContext } from '../UserContext';

const ActiveIncidentsByPriority = () => {
    const [chartData, setChartData] = useState([]);
    const { user } = useContext(UserContext);
    const [total,setTotal] =useState();
    useEffect(() => {
        const fetchData = async () => {
            try {
              const response = await axios.post('http://localhost/myproject2/backend/getActiveIncidentsByPriority.php', { cust_id: user.customer_ids });
                const data = response.data.data; 
               // console.log(data);
                const percentTotal=Object.values(data)?.reduce((sum, item) => sum + parseInt(item), 0)
                    setTotal(percentTotal)
                setChartData([
                    { value: data.High, name: 'High' },
                    { value: data.Medium, name: 'Medium' },
                    { value: data.Low, name: 'Low' }
                ]);
            } catch (error) {
                console.error('Error fetching data:', error);
            }
        };

        fetchData();
    }, [user]);

    //const total = chartData.reduce((sum, item) => sum + item.value, 0);

    const option = {
        title: {
            text: 'Active Incidents By Priority',
            left: 'left',
            padding: 15,
            textStyle: {
                fontSize: 12
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
                name: 'Priority',
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

    return (
      total && <ReactEcharts option={option} />
    );
};

export default ActiveIncidentsByPriority;
