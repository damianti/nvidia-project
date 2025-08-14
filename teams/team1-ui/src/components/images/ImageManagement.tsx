import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Slider,
  Card,
  CardContent,
  LinearProgress,
  Collapse,
} from '@mui/material';

import {
  PlayArrow,
  Stop,
  Delete,
  Settings,
  ExpandMore,
  ExpandLess,
  TrendingUp,
  Memory,
  Speed,
  AttachMoney,
} from '@mui/icons-material';
import { DockerImage } from '../../types';

// Mock data for image management
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

const ImageManagement: React.FC = () => {
  const [images, setImages] = useState<DockerImage[]>(mockImages);
  const [expandedImage, setExpandedImage] = useState<string | null>(null);
  const [scalingDialog, setScalingDialog] = useState<{ open: boolean; image: DockerImage | null }>({
    open: false,
    image: null,
  });
  const [newReplicas, setNewReplicas] = useState(1);

  const handleExpandImage = (imageId: string) => {
    setExpandedImage(expandedImage === imageId ? null : imageId);
  };

  const handleStartImage = (imageId: string) => {
    setImages(prev =>
      prev.map(img =>
        img.id === imageId
          ? { ...img, status: 'active' as const, instances: [...img.instances, {
              id: Date.now().toString(),
              imageId,
              status: 'running',
              port: 3000 + Math.floor(Math.random() * 1000),
              cpu: 25,
              memory: 512,
              createdAt: new Date().toISOString(),
              lastHealthCheck: new Date().toISOString(),
            }]}
          : img
      )
    );
  };

  const handleStopImage = (imageId: string) => {
    setImages(prev =>
      prev.map(img =>
        img.id === imageId
          ? { ...img, status: 'inactive' as const, instances: [] }
          : img
      )
    );
  };

  const handleDeleteImage = (imageId: string) => {
    setImages(prev => prev.filter(img => img.id !== imageId));
  };

  const handleOpenScaling = (image: DockerImage) => {
    setScalingDialog({ open: true, image });
    setNewReplicas(image.instances.length);
  };

  const handleCloseScaling = () => {
    setScalingDialog({ open: false, image: null });
  };

  const handleApplyScaling = () => {
    if (scalingDialog.image) {
      const image = scalingDialog.image;
      const currentInstances = image.instances.length;
      const instancesToAdd = newReplicas - currentInstances;

      let newInstances = [...image.instances];
      
      if (instancesToAdd > 0) {
        // Add instances
        for (let i = 0; i < instancesToAdd; i++) {
          newInstances.push({
            id: Date.now().toString() + i,
            imageId: image.id,
            status: 'running',
            port: 3000 + Math.floor(Math.random() * 1000),
            cpu: 25,
            memory: 512,
            createdAt: new Date().toISOString(),
            lastHealthCheck: new Date().toISOString(),
          });
        }
      } else if (instancesToAdd < 0) {
        // Remove instances
        newInstances = newInstances.slice(0, newReplicas);
      }

      setImages(prev =>
        prev.map(img =>
          img.id === image.id
            ? { ...img, instances: newInstances }
            : img
        )
      );
    }
    handleCloseScaling();
  };

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

  const getInstanceStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'success';
      case 'stopped':
        return 'default';
      case 'starting':
        return 'warning';
      case 'stopping':
        return 'warning';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Image Management
      </Typography>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Image</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Instances</TableCell>
              <TableCell>Requests/sec</TableCell>
              <TableCell>Cost</TableCell>
              <TableCell>Actions</TableCell>
              <TableCell></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {images.map((image) => (
              <React.Fragment key={image.id}>
                <TableRow>
                  <TableCell>
                    <Box>
                      <Typography variant="subtitle2">
                        {image.name}:{image.tag}
                      </Typography>
                      <Typography variant="caption" color="textSecondary">
                        {image.size} • Created {new Date(image.createdAt).toLocaleDateString()}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={image.status}
                      color={getStatusColor(image.status) as any}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {image.instances.length} running
                    </Typography>
                  </TableCell>
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
                  <TableCell>
                    <Typography variant="body2">
                      ${image.cost.toFixed(2)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      {image.status === 'inactive' ? (
                        <IconButton
                          size="small"
                          color="success"
                          onClick={() => handleStartImage(image.id)}
                        >
                          <PlayArrow />
                        </IconButton>
                      ) : (
                        <IconButton
                          size="small"
                          color="warning"
                          onClick={() => handleStopImage(image.id)}
                        >
                          <Stop />
                        </IconButton>
                      )}
                      <IconButton
                        size="small"
                        color="primary"
                        onClick={() => handleOpenScaling(image)}
                      >
                        <Settings />
                      </IconButton>
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => handleDeleteImage(image.id)}
                      >
                        <Delete />
                      </IconButton>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <IconButton
                      size="small"
                      onClick={() => handleExpandImage(image.id)}
                    >
                      {expandedImage === image.id ? <ExpandLess /> : <ExpandMore />}
                    </IconButton>
                  </TableCell>
                </TableRow>
                
                {/* Expanded row with detailed metrics */}
                <TableRow>
                  <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={7}>
                    <Collapse in={expandedImage === image.id} timeout="auto" unmountOnExit>
                      <Box sx={{ margin: 1 }}>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                          {/* Metrics Cards */}
                          <Box sx={{ flex: '1 1 400px', minWidth: 400 }}>
                            <Typography variant="h6" gutterBottom>
                              Performance Metrics
                            </Typography>
                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                              <Box sx={{ flex: '1 1 150px', minWidth: 150 }}>
                                <Card>
                                  <CardContent>
                                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                      <TrendingUp color="primary" sx={{ mr: 1 }} />
                                      <Box>
                                        <Typography variant="h6">
                                          {image.metrics.requestsPerSecond}
                                        </Typography>
                                        <Typography variant="caption">
                                          Requests/sec
                                        </Typography>
                                      </Box>
                                    </Box>
                                  </CardContent>
                                </Card>
                              </Box>
                              <Box sx={{ flex: '1 1 150px', minWidth: 150 }}>
                                <Card>
                                  <CardContent>
                                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                      <Speed color="info" sx={{ mr: 1 }} />
                                      <Box>
                                        <Typography variant="h6">
                                          {image.metrics.averageResponseTime}ms
                                        </Typography>
                                        <Typography variant="caption">
                                          Avg Response
                                        </Typography>
                                      </Box>
                                    </Box>
                                  </CardContent>
                                </Card>
                              </Box>
                              <Box sx={{ flex: '1 1 150px', minWidth: 150 }}>
                                <Card>
                                  <CardContent>
                                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                      <Memory color="warning" sx={{ mr: 1 }} />
                                      <Box>
                                        <Typography variant="h6">
                                          {image.metrics.cpuUsage}%
                                        </Typography>
                                        <Typography variant="caption">
                                          CPU Usage
                                        </Typography>
                                      </Box>
                                    </Box>
                                  </CardContent>
                                </Card>
                              </Box>
                              <Box sx={{ flex: '1 1 150px', minWidth: 150 }}>
                                <Card>
                                  <CardContent>
                                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                      <AttachMoney color="success" sx={{ mr: 1 }} />
                                      <Box>
                                        <Typography variant="h6">
                                          ${image.cost.toFixed(2)}
                                        </Typography>
                                        <Typography variant="caption">
                                          Total Cost
                                        </Typography>
                                      </Box>
                                    </Box>
                                  </CardContent>
                                </Card>
                              </Box>
                            </Box>
                          </Box>

                          {/* Instances Table */}
                          <Box sx={{ flex: '1 1 400px', minWidth: 400 }}>
                            <Typography variant="h6" gutterBottom>
                              Running Instances
                            </Typography>
                            <Table size="small">
                              <TableHead>
                                <TableRow>
                                  <TableCell>Port</TableCell>
                                  <TableCell>Status</TableCell>
                                  <TableCell>CPU</TableCell>
                                  <TableCell>Memory</TableCell>
                                </TableRow>
                              </TableHead>
                              <TableBody>
                                {image.instances.map((instance) => (
                                  <TableRow key={instance.id}>
                                    <TableCell>{instance.port}</TableCell>
                                    <TableCell>
                                      <Chip
                                        label={instance.status}
                                        color={getInstanceStatusColor(instance.status) as any}
                                        size="small"
                                      />
                                    </TableCell>
                                    <TableCell>{instance.cpu}%</TableCell>
                                    <TableCell>{instance.memory}MB</TableCell>
                                  </TableRow>
                                ))}
                              </TableBody>
                            </Table>
                          </Box>
                        </Box>
                      </Box>
                    </Collapse>
                  </TableCell>
                </TableRow>
              </React.Fragment>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Scaling Dialog */}
      <Dialog open={scalingDialog.open} onClose={handleCloseScaling}>
        <DialogTitle>Scale Instances</DialogTitle>
        <DialogContent>
          {scalingDialog.image && (
            <Box sx={{ pt: 1 }}>
              <Typography gutterBottom>
                Current instances: {scalingDialog.image.instances.length}
              </Typography>
              <Typography gutterBottom>
                New number of instances: {newReplicas}
              </Typography>
              <Slider
                value={newReplicas}
                onChange={(_, value) => setNewReplicas(value as number)}
                min={0}
                max={10}
                step={1}
                marks
                valueLabelDisplay="auto"
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseScaling}>Cancel</Button>
          <Button onClick={handleApplyScaling} variant="contained">
            Apply Scaling
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ImageManagement; 