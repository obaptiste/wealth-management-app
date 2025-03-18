// components/PortfolioChart.tsx
import { Box } from '@chakra-ui/react';
import { useColorModeValue } from '@chakra-ui/color-mode';
import { 
  ResponsiveContainer, 
  PieChart, 
  Pie, 
  Cell, 
  Tooltip, 
  Legend 
} from 'recharts';
import { AssetWithPerformance } from '../types/assets';

interface PortfolioChartProps {
  assets: AssetWithPerformance[];
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

const PortfolioChart: React.FC<PortfolioChartProps> = ({ assets }) => {
  const data = assets.map(asset => ({
    name: asset.symbol,
    value: asset.current_value,
  }));

  const bgColor = useColorModeValue('white', 'gray.800');

  return (
    <Box 
      bg={bgColor} 
      p={4} 
      borderRadius="lg" 
      boxShadow="sm" 
      height="400px"
    >
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={100}
            fill="#8884d8"
            dataKey="value"
            nameKey="name"
            label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip 
            formatter={(value: number) => [`$${value.toFixed(2)}`, 'Value']}
          />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </Box>
  );
};

export default PortfolioChart;