/**
 * Real-time System Metrics Chart Component
 * Shows CPU, Memory, and Disk usage over time
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Typography,
  ToggleButton,
  ToggleButtonGroup,
  Tooltip
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';
import { ResourceUsage } from '../../types/health';

interface MetricDataPoint {
  timestamp: string;
  cpu_percent: number;
  memory_percent: number;
  disk_usage_percent: number;
}

interface SystemMetricsChartProps {
  currentMetrics?: ResourceUsage;
  height?: number;
}

const SystemMetricsChart: React.FC<SystemMetricsChartProps> = ({
  currentMetrics,
  height = 300
}) => {
  const [metricsHistory, setMetricsHistory] = useState<MetricDataPoint[]>([]);
  const [timeRange, setTimeRange] = useState<'5m' | '15m' | '1h' | '6h'>('15m');
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>(['cpu_percent', 'memory_percent']);

  // Add current metrics to history
  useEffect(() => {
    if (currentMetrics) {
      const newDataPoint: MetricDataPoint = {
        timestamp: new Date().toLocaleTimeString(),
        cpu_percent: currentMetrics.cpu_percent,
        memory_percent: currentMetrics.memory_percent,
        disk_usage_percent: currentMetrics.disk_usage_percent
      };

      setMetricsHistory(prev => {
        const updated = [...prev, newDataPoint];
        
        // Keep only data points within time range
        const maxPoints = getMaxDataPoints(timeRange);
        return updated.slice(-maxPoints);
      });
    }
  }, [currentMetrics, timeRange]);

  const getMaxDataPoints = (range: string): number => {
    switch (range) {
      case '5m': return 10;   // 30s intervals
      case '15m': return 30;  // 30s intervals
      case '1h': return 60;   // 1min intervals
      case '6h': return 72;   // 5min intervals
      default: return 30;
    }
  };

  const handleTimeRangeChange = (
    event: React.MouseEvent<HTMLElement>,
    newTimeRange: string | null,
  ) => {
    if (newTimeRange !== null) {
      setTimeRange(newTimeRange as '5m' | '15m' | '1h' | '6h');
    }
  };

  const handleMetricToggle = (
    event: React.MouseEvent<HTMLElement>,
    newMetrics: string[],
  ) => {
    if (newMetrics.length > 0) {
      setSelectedMetrics(newMetrics);
    }
  };

  const getLineColor = (metric: string): string => {
    switch (metric) {
      case 'cpu_percent': return '#2196f3';
      case 'memory_percent': return '#ff9800';
      case 'disk_usage_percent': return '#4caf50';
      default: return '#9e9e9e';
    }
  };

  const getMetricLabel = (metric: string): string => {
    switch (metric) {
      case 'cpu_percent': return 'CPU %';
      case 'memory_percent': return 'Memory %';
      case 'disk_usage_percent': return 'Disk %';
      default: return metric;
    }
  };

  const formatTooltipValue = (value: number, name: string): [string, string] => {
    return [`${value.toFixed(1)}%`, getMetricLabel(name)];
  };

  if (metricsHistory.length === 0) {
    return (
      <Card>
        <CardHeader title="System Metrics" />
        <CardContent>
          <Box display="flex" alignItems="center" justifyContent="center" height={height}>
            <Typography variant="body2" color="textSecondary">
              Collecting metrics data...
            </Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader
        title="System Metrics"
        action={
          <Box display="flex" gap={2}>
            <ToggleButtonGroup
              value={selectedMetrics}
              onChange={handleMetricToggle}
              size="small"
            >
              <ToggleButton value="cpu_percent">
                <Tooltip title="CPU Usage">
                  <span>CPU</span>
                </Tooltip>
              </ToggleButton>
              <ToggleButton value="memory_percent">
                <Tooltip title="Memory Usage">
                  <span>RAM</span>
                </Tooltip>
              </ToggleButton>
              <ToggleButton value="disk_usage_percent">
                <Tooltip title="Disk Usage">
                  <span>Disk</span>
                </Tooltip>
              </ToggleButton>
            </ToggleButtonGroup>
            
            <ToggleButtonGroup
              value={timeRange}
              exclusive
              onChange={handleTimeRangeChange}
              size="small"
            >
              <ToggleButton value="5m">5m</ToggleButton>
              <ToggleButton value="15m">15m</ToggleButton>
              <ToggleButton value="1h">1h</ToggleButton>
              <ToggleButton value="6h">6h</ToggleButton>
            </ToggleButtonGroup>
          </Box>
        }
      />
      
      <CardContent>
        <ResponsiveContainer width="100%" height={height}>
          <LineChart data={metricsHistory}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="timestamp" 
              tick={{ fontSize: 12 }}
              interval="preserveStartEnd"
            />
            <YAxis 
              domain={[0, 100]}
              tick={{ fontSize: 12 }}
              label={{ value: 'Usage %', angle: -90, position: 'insideLeft' }}
            />
            <RechartsTooltip 
              formatter={formatTooltipValue}
              labelStyle={{ color: '#666' }}
            />
            <Legend />
            
            {selectedMetrics.includes('cpu_percent') && (
              <Line
                type="monotone"
                dataKey="cpu_percent"
                stroke={getLineColor('cpu_percent')}
                strokeWidth={2}
                dot={false}
                name="CPU %"
              />
            )}
            
            {selectedMetrics.includes('memory_percent') && (
              <Line
                type="monotone"
                dataKey="memory_percent"
                stroke={getLineColor('memory_percent')}
                strokeWidth={2}
                dot={false}
                name="Memory %"
              />
            )}
            
            {selectedMetrics.includes('disk_usage_percent') && (
              <Line
                type="monotone"
                dataKey="disk_usage_percent"
                stroke={getLineColor('disk_usage_percent')}
                strokeWidth={2}
                dot={false}
                name="Disk %"
              />
            )}
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};

export default SystemMetricsChart;