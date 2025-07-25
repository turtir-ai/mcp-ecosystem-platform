/**
 * MCP Status Table Component
 */
import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Tooltip,
  Typography
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import { MCPServerStatus } from '../../services/api';

interface MCPStatusTableProps {
  servers?: MCPServerStatus[];
  onServerClick?: (serverName: string) => void;
  onRefresh?: () => void;
  loading?: boolean;
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'healthy':
      return 'success';
    case 'degraded':
      return 'warning';
    case 'unhealthy':
      return 'error';
    case 'offline':
      return 'default';
    default:
      return 'default';
  }
};

const MCPStatusTable: React.FC<MCPStatusTableProps> = ({
  servers = [],
  onServerClick,
  onRefresh,
  loading = false
}) => {
  return (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Server Name</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Response Time</TableCell>
            <TableCell>Last Check</TableCell>
            <TableCell align="right">
              <Tooltip title="Refresh">
                <IconButton onClick={onRefresh} disabled={loading}>
                  <RefreshIcon />
                </IconButton>
              </Tooltip>
            </TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {servers.length === 0 ? (
            <TableRow>
              <TableCell colSpan={5} align="center">
                <Typography variant="body2" color="textSecondary">
                  No MCP servers found
                </Typography>
              </TableCell>
            </TableRow>
          ) : (
            servers.map((server) => (
              <TableRow key={server.name} hover>
                <TableCell>{server.name}</TableCell>
                <TableCell>
                  <Chip
                    label={server.status}
                    color={getStatusColor(server.status) as any}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  {server.response_time_ms ? `${server.response_time_ms.toFixed(0)}ms` : 'N/A'}
                </TableCell>
                <TableCell>
                  {server.last_check ? new Date(server.last_check).toLocaleTimeString() : 'N/A'}
                </TableCell>
                <TableCell align="right">
                  <Tooltip title="View Details">
                    <IconButton
                      onClick={() => onServerClick?.(server.name)}
                      size="small"
                    >
                      <InfoIcon />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default MCPStatusTable;