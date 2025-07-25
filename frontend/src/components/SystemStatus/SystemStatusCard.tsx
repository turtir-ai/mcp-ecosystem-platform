import React from "react";
import {
  Card,
  CardContent,
  CardHeader,
  Typography,
  Box,
  Button,
  CircularProgress,
  Chip,
  Grid,
} from "@mui/material";
import RefreshIcon from "@mui/icons-material/Refresh";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import ErrorIcon from "@mui/icons-material/Error";
import WarningIcon from "@mui/icons-material/Warning";

export interface SystemStatusCardProps {
  onRefresh?: () => void | Promise<void>;
  loading?: boolean;
}

export const SystemStatusCard: React.FC<SystemStatusCardProps> = ({
  onRefresh,
  loading = false,
}) => {
  const handleRefresh = async () => {
    if (onRefresh && !loading) {
      await onRefresh();
    }
  };

  // Mock system status data - in real implementation this would come from props or hooks
  const systemStatus = {
    overall: "healthy",
    services: [
      { name: "Backend API", status: "healthy", uptime: "99.9%" },
      { name: "MCP Servers", status: "warning", uptime: "98.5%" },
      { name: "Database", status: "healthy", uptime: "100%" },
      { name: "File System", status: "healthy", uptime: "99.8%" },
    ],
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "healthy":
        return <CheckCircleIcon color="success" />;
      case "warning":
        return <WarningIcon color="warning" />;
      case "error":
        return <ErrorIcon color="error" />;
      default:
        return <CheckCircleIcon color="disabled" />;
    }
  };

  const getStatusColor = (
    status: string
  ): "success" | "warning" | "error" | "default" => {
    switch (status) {
      case "healthy":
        return "success";
      case "warning":
        return "warning";
      case "error":
        return "error";
      default:
        return "default";
    }
  };

  return (
    <Card>
      <CardHeader
        title="System Status"
        action={
          <Button
            variant="outlined"
            size="small"
            startIcon={
              loading ? <CircularProgress size={16} /> : <RefreshIcon />
            }
            onClick={handleRefresh}
            disabled={loading}
          >
            {loading ? "Refreshing..." : "Refresh"}
          </Button>
        }
      />
      <CardContent>
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Overall Status
          </Typography>
          <Chip
            icon={getStatusIcon(systemStatus.overall)}
            label={systemStatus.overall.toUpperCase()}
            color={getStatusColor(systemStatus.overall)}
            variant="outlined"
          />
        </Box>

        <Typography variant="h6" gutterBottom>
          Service Status
        </Typography>
        <Grid container spacing={2}>
          {systemStatus.services.map((service, index) => (
            <Grid item xs={12} sm={6} key={index}>
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  p: 2,
                  border: "1px solid",
                  borderColor: "divider",
                  borderRadius: 1,
                  bgcolor: "background.paper",
                }}
              >
                <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                  {getStatusIcon(service.status)}
                  <Typography variant="body2" fontWeight="medium">
                    {service.name}
                  </Typography>
                </Box>
                <Typography variant="caption" color="text.secondary">
                  {service.uptime}
                </Typography>
              </Box>
            </Grid>
          ))}
        </Grid>
      </CardContent>
    </Card>
  );
};

export default SystemStatusCard;
