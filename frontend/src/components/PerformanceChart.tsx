// components/PerformanceChart.tsx
import React, { useEffect, useRef } from 'react';
import { Box } from '@chakra-ui/react';
import { useColorModeValue } from '@chakra-ui/color-mode';
import * as d3 from 'd3';

interface DataPoint {
  date: string;
  value: number;
}

interface PerformanceChartProps {
  data: DataPoint[];
  width?: number;
  height?: number;
}

const PerformanceChart: React.FC<PerformanceChartProps> = ({ 
  data,
  width = 600,
  height = 300
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const chartColor = useColorModeValue('#3182CE', '#63B3ED');
  const textColor = useColorModeValue('#1A202C', '#E2E8F0');

  useEffect(() => {
    if (!data.length || !svgRef.current) return;

    // Clear previous chart
    d3.select(svgRef.current).selectAll('*').remove();

    const svg = d3.select(svgRef.current);
    
    const margin = { top: 20, right: 30, bottom: 30, left: 60 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;
    
    // Create scales
    const parseDate = d3.timeParse('%Y-%m-%d');
    const xScale = d3.scaleTime()
      .domain(d3.extent(data, d => parseDate(d.date) as Date) as [Date, Date])
      .range([0, innerWidth]);
    
    const yScale = d3.scaleLinear()
      .domain([0, d3.max(data, d => d.value) as number])
      .range([innerHeight, 0])
      .nice();
    
    // Create group element for the chart
    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);
    
    // Add axes
    g.append('g')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(d3.axisBottom(xScale))
      .attr('color', textColor);
    
    g.append('g')
      .call(d3.axisLeft(yScale).tickFormat(d => `$${d}`))
      .attr('color', textColor);
    
    // Create the line generator
    const line = d3.line<DataPoint>()
      .x(d => xScale(parseDate(d.date) as Date))
      .y(d => yScale(d.value))
      .curve(d3.curveMonotoneX);
    
    // Add the line path
    g.append('path')
      .datum(data)
      .attr('fill', 'none')
      .attr('stroke', chartColor)
      .attr('stroke-width', 2)
      .attr('d', line);
      
    // Add tooltips (simple circle points)
    g.selectAll('.dot')
      .data(data)
      .enter().append('circle')
      .attr('class', 'dot')
      .attr('cx', d => xScale(parseDate(d.date) as Date))
      .attr('cy', d => yScale(d.value))
      .attr('r', 4)
      .attr('fill', chartColor)
      .append('title')
      .text(d => `${d.date}: $${d.value.toFixed(2)}`);
      
  }, [data, width, height, chartColor, textColor]);

  return (
    <Box borderRadius="lg" p={4} boxShadow="sm">
      <svg ref={svgRef} width={width} height={height} />
    </Box>
  );
};

export default PerformanceChart;