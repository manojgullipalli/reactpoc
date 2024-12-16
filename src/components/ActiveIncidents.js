import React, { useState, useEffect, useContext } from 'react';
import ReactEcharts from 'echarts-for-react';
import axios from 'axios';
import { UserContext } from '../UserContext';

const ActiveIncidents = () => {
    const [data, setData] = useState([]);
    const { user } = useContext(UserContext);
    const [total,setTotal] =useState();
    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await axios.post('http://localhost/myproject2/backend/getActiveTickets.php', { cust_id: user.customer_ids });
                if (response.data.success) {
                    const responseData = response.data.data;
                    // console.log(Object.values(responseData),"22222222")
                    const percentTotal=Object.values(responseData)?.reduce((sum, item) => sum + parseInt(item), 0)
                    setTotal(percentTotal)
                    setData([
                        { value: responseData.Open, name: 'Open' },
                        { value: responseData.Acknowledged, name: 'Acknowledged' },
                        { value: responseData.Inprogress, name: 'Inprogress' },
                        { value: responseData.Hold, name: 'Hold' },
                    ]);
                } else {
                    console.error('Failed to fetch data', response.data.message);
                }
            } catch (error) {
                console.error('There was an error fetching the data!', error);
            }
        };

        fetchData();
    }, [user.userId]);
    
    const option = {
        title: {
            text: 'Active Incidents',
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
              const item = data?.find(d => d.name === name);
              const percent = item ? ((parseInt(item.value) / total) * 100).toFixed(2) : '0.00';
              return `${name}: ${percent}%`;
            }
        },
        series: [
            {
                name: 'Access From',
                type: 'pie',
                radius: '30%',
                center: ['25%', '30%'],
                data: data,
                tooltip: {
                    trigger: 'item',
                    formatter: '{a} <br/>{b}: {c} ({d}%)'
                },
                emphasis: {
                    itemStyle: {}
                },
                label: {
                    show: false
                }
            }
        ]
    };

    return (
        data && total && <ReactEcharts option={option} />
    );
};

export default ActiveIncidents;
