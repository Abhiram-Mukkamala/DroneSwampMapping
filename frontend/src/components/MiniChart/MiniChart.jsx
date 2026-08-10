import React, { useState, useEffect } from 'react';
import { LineChart, Line, ResponsiveContainer } from 'recharts';

const MiniChart = ({ color = "#38bdf8" }) => {
  const [data, setData] = useState([]);

  useEffect(() => {
    // Generate initial dummy data
    const initialData = Array.from({ length: 20 }, (_, i) => ({
      name: i,
      value: 50 + Math.random() * 50
    }));
    setData(initialData);

    const interval = setInterval(() => {
      setData(prevData => {
        const newData = [...prevData.slice(1)];
        newData.push({
          name: prevData[prevData.length - 1].name + 1,
          value: 50 + Math.random() * 50
        });
        return newData;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ width: '100%', height: '100%' }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
          <Line 
            type="monotone" 
            dataKey="value" 
            stroke={color} 
            strokeWidth={2} 
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default MiniChart;
