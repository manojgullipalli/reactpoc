import React, { useState, useEffect, useContext } from 'react';
import ReactEcharts from 'echarts-for-react';
import axios from 'axios';
import { UserContext } from '../UserContext'; 

const ActiveRequestsByType = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { user } = useContext(UserContext);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.post('http://localhost/myproject2/backend/getActiveRequestsByType.php', {
          cust_id: user.customer_ids  
        });

        if (response.data.success) {
          const resultData = response.data.data;

          const chartData = [
            { value: resultData.Incident, name: 'Incident' },
            { value: resultData.ServiceRequest, name: 'Service Request' }
          ];

          setData(chartData);
        } else {
          setError(response.data.message || 'Failed to fetch data');
        }
      } catch (err) {
        setError('Error fetching data');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [user]);

  const total = data.reduce((sum, item) => sum + item.value, 0);

  const option = {
    title: {
      text: 'Active Requests By Type',
      left: 'left',
      padding: 15,
      textStyle: {
        fontSize: 12,
      },
    },
    legend: {
      orient: 'vertical',
      left: 'right',
      padding: 30,
      textStyle: {
        fontSize: 10,
        lineHeight: 2,
      },
      icon: 'circle',
      formatter: function (name) {
        const item = data.find((d) => d.name === name);
        const percent = ((item.value / total) * 100).toFixed(2);
        return `${name}: ${percent}%`;
      },
    },
    series: [
      {
        name: 'Requests',
        type: 'pie',
        radius: '30%',
        center: ['25%', '30%'],
        data: data,
        tooltip: {
          trigger: 'item',
          formatter: '{a} <br/>{b}: {c} ({d}%)',
        },
        emphasis: {
          itemStyle: {},
        },
        label: {
          show: false,
        },
      },
    ],
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return <ReactEcharts option={option} />;
};

export default ActiveRequestsByType;
