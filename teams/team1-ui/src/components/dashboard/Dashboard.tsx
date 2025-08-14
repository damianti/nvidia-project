import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  LinearProgress,
} from '@mui/material';

import {
  Storage,
  Speed,
  AttachMoney,
  Warning,
  CheckCircle,
  Error,
} from '@mui/icons-material';
import { DockerImage } from '../../types';

// Mock data for dashboard
const mockImages: DockerImage[] = [
  {
    id: '1',
    name: 'nginx',
    tag: 'latest',
    size: '133MB',
    createdAt: '2024-01-15T10:30:00Z',
    status: 'active',
    instances: [
      { id: '1', imageId: '1', status: 'running', port: 8080, cpu: 25, memory: 512, createdAt: '2024-01-15T10:30:00Z', lastHealthCheck: '2024-01-15T12:00:00Z' },
      { id: '2', imageId: '1', status: 'running', port: 8081, cpu: 30, memory: 512, createdAt: '2024-01-15T10:30:00Z', lastHealthCheck: '2024-01-15T12:00:00Z' },
    ],
    metrics: {
      requestsPerSecond: 150,
      averageResponseTime: 45,
      totalRequests: 125000,
      errorRate: 0.5,
      cpuUsage: 55,
      memoryUsage: 70,
    },
    cost: 12.50,
  },
  {
    id: '2',
    name: 'nodejs-app',
    tag: 'v1.2.0',
    size: '245MB',
    createdAt: '2024-01-14T15:20:00Z',
    status: 'active',
    instances: [
      { id: '3', imageId: '2', status: 'running', port: 3000, cpu: 40, memory: 1024, createdAt: '2024-01-14T15:20:00Z', lastHealthCheck: '2024-01-15T12:00:00Z' },
    ],
    metrics: {
      requestsPerSecond: 80,
      averageResponseTime: 120,
      totalRequests: 45000,
      errorRate: 1.2,
      cpuUsage: 40,
      memoryUsage: 60,
    },
    cost: 8.75,
  },
  {
    id: '3',
    name: 'python-api',
    tag: 'dev',
    size: '189MB',
    createdAt: '2024-01-13T09:15:00Z',
    status: 'inactive',
    instances: [],
    metrics: {
      requestsPerSecond: 0,
      averageResponseTime: 0,
      totalRequests: 0,
      errorRate: 0,
      cpuUsage: 0,
      memoryUsage: 0,
    },
    cost: 0,
  },
];

const Dashboard: React.FC = () => {
  const totalImages = mockImages.length;
  const activeImages = mockImages.filter(img => img.status === 'active').length;
  const totalInstances = mockImages.reduce((sum, img) => sum + img.instances.length, 0);
  const totalCost = mockImages.reduce((sum, img) => sum + img.cost, 0);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'inactive':
        return 'default';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle fontSize="small" />;
      case 'inactive':
        return <Warning fontSize="small" />;
      case 'error':
        return <Error fontSize="small" />;
      default:
        return <Warning fontSize="small" />;
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      
      {/* Overview Cards */}
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3, mb: 4 }}>
        <Box sx={{ flex: '1 1 250px', minWidth: 250 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Storage color="primary" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Total Images
                  </Typography>
                  <Typography variant="h4">
                    {totalImages}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Box>
        
        <Box sx={{ flex: '1 1 250px', minWidth: 250 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <CheckCircle color="success" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Active Images
                  </Typography>
                  <Typography variant="h4">
                    {activeImages}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Box>
        
        <Box sx={{ flex: '1 1 250px', minWidth: 250 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Speed color="info" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Running Instances
                  </Typography>
                  <Typography variant="h4">
                    {totalInstances}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Box>
        
        <Box sx={{ flex: '1 1 250px', minWidth: 250 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <AttachMoney color="warning" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Total Cost
                  </Typography>
                  <Typography variant="h4">
                    ${totalCost.toFixed(2)}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Box>
      </Box>

      {/* Recent Images Table */}
      <Paper sx={{ width: '100%', overflow: 'hidden' }}>
        <Box sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Recent Images
          </Typography>
        </Box>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Image Name</TableCell>
                <TableCell>Tag</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Instances</TableCell>
                <TableCell>Requests/sec</TableCell>
                <TableCell>Cost</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {mockImages.map((image) => (
                <TableRow key={image.id}>
                  <TableCell>
                    <Typography variant="subtitle2">
                      {image.name}
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      {image.size}
                    </Typography>
                  </TableCell>
                  <TableCell>{image.tag}</TableCell>
                  <TableCell>
                    <Chip
                      icon={getStatusIcon(image.status)}
                      label={image.status}
                      color={getStatusColor(image.status) as any}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{image.instances.length}</TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Typography variant="body2" sx={{ mr: 1 }}>
                        {image.metrics.requestsPerSecond}
                      </Typography>
                      <LinearProgress
                        variant="determinate"
                        value={Math.min((image.metrics.requestsPerSecond / 200) * 100, 100)}
                        sx={{ width: 50, height: 6 }}
                      />
                    </Box>
                  </TableCell>
                  <TableCell>${image.cost.toFixed(2)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Box>
  );
};

export default Dashboard; 