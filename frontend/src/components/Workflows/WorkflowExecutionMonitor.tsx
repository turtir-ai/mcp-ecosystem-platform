/**
 * Workflow Execution Monitor Component
 */
import React, { useEffect, useState } from "react";
import {
  Alert,
  Box,
  Card,
  CardContent,
  CardHeader,
  Chip,
  LinearProgress,
  List,
  ListItem,
  Typography,
} from "@mui/material";
import {
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  PlayArrow as PlayArrowIcon,
  Schedule as ScheduleIcon,
} from "@mui/icons-material";

interface WorkflowStep {
  id: string;
  name: string;
  status: "pending" | "running" | "completed" | "failed";
  startTime?: string;
  duration?: number;
  progress?: number;
  error?: string;
}

interface WorkflowExecutionMonitorProps {
  executionId?: string;
  executions?: any[];
  onComplete?: () => void;
  onError?: (error: string) => void;
  onCancelExecution?: (executionId: string) => Promise<void>;
  onRefresh?: () => Promise<void>;
}

const WorkflowExecutionMonitor: React.FC<WorkflowExecutionMonitorProps> = ({
  executionId,
  executions,
  onComplete,
  onError,
  onCancelExecution,
  onRefresh,
}) => {
  const [steps, setSteps] = useState<WorkflowStep[]>([]);
  const [overallStatus, setOverallStatus] = useState<
    "running" | "completed" | "failed"
  >("running");

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircleIcon color="success" />;
      case "failed":
        return <ErrorIcon color="error" />;
      case "running":
        return <PlayArrowIcon color="primary" />;
      default:
        return <ScheduleIcon color="disabled" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "success";
      case "failed":
        return "error";
      case "running":
        return "primary";
      default:
        return "default";
    }
  };

  const formatDuration = (duration: number) => {
    const seconds = Math.floor(duration / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;

    if (minutes > 0) {
      return `${minutes}m ${remainingSeconds}s`;
    }
    return `${remainingSeconds}s`;
  };

  useEffect(() => {
    // Mock data for demonstration
    const mockSteps: WorkflowStep[] = [
      {
        id: "1",
        name: "Initialize Workflow",
        status: "completed",
        startTime: new Date().toISOString(),
        duration: 1500,
      },
      {
        id: "2",
        name: "Process Data",
        status: "running",
        startTime: new Date().toISOString(),
        progress: 65,
      },
      {
        id: "3",
        name: "Generate Report",
        status: "pending",
      },
    ];

    setSteps(mockSteps);
  }, [executionId]);

  return (
    <Card>
      <CardHeader
        title="Workflow Execution"
        subheader={`Execution ID: ${executionId}`}
        action={
          <Chip
            label={overallStatus}
            color={getStatusColor(overallStatus) as any}
            variant="outlined"
          />
        }
      />
      <CardContent>
        <List>
          {steps.map((step, index) => (
            <ListItem
              key={step.id}
              sx={{ flexDirection: "column", alignItems: "flex-start" }}
            >
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  width: "100%",
                  mb: 1,
                }}
              >
                <Box sx={{ mr: 2 }}>{getStatusIcon(step.status)}</Box>
                <Box sx={{ flexGrow: 1 }}>
                  <Typography variant="h6" component="span">
                    {step.name}
                  </Typography>
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{ ml: 2 }}
                  >
                    {step.startTime &&
                      new Date(step.startTime).toLocaleTimeString()}
                  </Typography>
                </Box>
              </Box>
              <Box sx={{ width: "100%", ml: 4 }}>
                <Typography variant="body2" color="text.secondary">
                  Status: {step.status}
                  {step.duration &&
                    ` • Duration: ${formatDuration(step.duration)}`}
                </Typography>
                {step.error && (
                  <Alert severity="error" sx={{ mt: 1 }}>
                    {step.error}
                  </Alert>
                )}
                {step.progress !== undefined && step.status === "running" && (
                  <Box sx={{ mt: 1 }}>
                    <LinearProgress
                      variant="determinate"
                      value={step.progress}
                    />
                    <Typography variant="caption" color="text.secondary">
                      {step.progress}% complete
                    </Typography>
                  </Box>
                )}
              </Box>
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
};

export default WorkflowExecutionMonitor;
