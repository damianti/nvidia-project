import React, { useState, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  LinearProgress,
  Alert,
  Slider,
  FormControlLabel,
  Switch,
} from '@mui/material';

import { CloudUpload, Upload } from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { ResourceConfig, UploadProgress } from '../../types';

const ImageUpload: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState<UploadProgress>({
    percentage: 0,
    status: 'uploading',
    message: '',
  });
  const [imageName, setImageName] = useState('');
  const [imageTag, setImageTag] = useState('latest');
  const [resourceConfig, setResourceConfig] = useState<ResourceConfig>({
    cpu: 1,
    memory: 512,
    storage: 10,
    replicas: 1,
  });
  const [autoScale, setAutoScale] = useState(false);
  const [error, setError] = useState('');

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      if (file.type === 'application/octet-stream' || file.name.endsWith('.tar')) {
        setSelectedFile(file);
        setError('');
        // Auto-generate image name from filename
        const fileName = file.name.replace('.tar', '').replace('.tar.gz', '');
        setImageName(fileName);
      } else {
        setError('Please select a valid Docker image file (.tar)');
      }
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/octet-stream': ['.tar'],
    },
    multiple: false,
  });

  const handleUpload = async () => {
    if (!selectedFile || !imageName) {
      setError('Please select a file and provide an image name');
      return;
    }

    setUploadProgress({
      percentage: 0,
      status: 'uploading',
      message: 'Starting upload...',
    });

    // Simulate upload progress
    const simulateUpload = () => {
      let progress = 0;
      const interval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress >= 100) {
          progress = 100;
          setUploadProgress({
            percentage: 100,
            status: 'complete',
            message: 'Upload completed successfully!',
          });
          clearInterval(interval);
          // Reset form after successful upload
          setTimeout(() => {
            setSelectedFile(null);
            setImageName('');
            setImageTag('latest');
            setResourceConfig({
              cpu: 1,
              memory: 512,
              storage: 10,
              replicas: 1,
            });
            setUploadProgress({
              percentage: 0,
              status: 'uploading',
              message: '',
            });
          }, 2000);
        } else {
          setUploadProgress({
            percentage: Math.round(progress),
            status: 'uploading',
            message: `Uploading... ${Math.round(progress)}%`,
          });
        }
      }, 500);
    };

    simulateUpload();
  };

  const handleCpuChange = (event: Event, newValue: number | number[]) => {
    setResourceConfig(prev => ({ ...prev, cpu: newValue as number }));
  };

  const handleMemoryChange = (event: Event, newValue: number | number[]) => {
    setResourceConfig(prev => ({ ...prev, memory: newValue as number }));
  };

  const handleStorageChange = (event: Event, newValue: number | number[]) => {
    setResourceConfig(prev => ({ ...prev, storage: newValue as number }));
  };

  const handleReplicasChange = (event: Event, newValue: number | number[]) => {
    setResourceConfig(prev => ({ ...prev, replicas: newValue as number }));
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Upload Docker Image
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
        {/* File Upload Section */}
        <Box sx={{ flex: '1 1 400px', minWidth: 400 }}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Select Docker Image
            </Typography>
            
            <Box
              {...getRootProps()}
              sx={{
                border: '2px dashed #ccc',
                borderRadius: 2,
                p: 4,
                textAlign: 'center',
                cursor: 'pointer',
                backgroundColor: isDragActive ? '#f0f8ff' : '#fafafa',
                '&:hover': {
                  backgroundColor: '#f0f8ff',
                },
              }}
            >
              <input {...getInputProps()} />
              <CloudUpload sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
              {isDragActive ? (
                <Typography>Drop the Docker image file here...</Typography>
              ) : (
                <Typography>
                  Drag and drop a Docker image file here, or click to select
                </Typography>
              )}
            </Box>

            {selectedFile && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Selected File:
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
                </Typography>
              </Box>
            )}

            {uploadProgress.status !== 'uploading' && uploadProgress.percentage > 0 && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" gutterBottom>
                  {uploadProgress.message}
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={uploadProgress.percentage}
                  sx={{ height: 8, borderRadius: 4 }}
                />
              </Box>
            )}
          </Paper>
        </Box>

        {/* Configuration Section */}
        <Box sx={{ flex: '1 1 400px', minWidth: 400 }}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Image Configuration
            </Typography>

            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
              <Box sx={{ flex: '1 1 200px', minWidth: 200 }}>
                <TextField
                  fullWidth
                  label="Image Name"
                  value={imageName}
                  onChange={(e) => setImageName(e.target.value)}
                  margin="normal"
                />
              </Box>
              <Box sx={{ flex: '1 1 200px', minWidth: 200 }}>
                <TextField
                  fullWidth
                  label="Tag"
                  value={imageTag}
                  onChange={(e) => setImageTag(e.target.value)}
                  margin="normal"
                />
              </Box>
            </Box>

            <Typography variant="h6" sx={{ mt: 3, mb: 2 }}>
              Resource Configuration
            </Typography>

            <Box sx={{ mb: 2 }}>
              <Typography gutterBottom>CPU Cores: {resourceConfig.cpu}</Typography>
              <Slider
                value={resourceConfig.cpu}
                onChange={handleCpuChange}
                min={0.5}
                max={8}
                step={0.5}
                marks
                valueLabelDisplay="auto"
              />
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography gutterBottom>Memory (MB): {resourceConfig.memory}</Typography>
              <Slider
                value={resourceConfig.memory}
                onChange={handleMemoryChange}
                min={256}
                max={4096}
                step={256}
                marks
                valueLabelDisplay="auto"
              />
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography gutterBottom>Storage (GB): {resourceConfig.storage}</Typography>
              <Slider
                value={resourceConfig.storage}
                onChange={handleStorageChange}
                min={1}
                max={100}
                step={1}
                marks
                valueLabelDisplay="auto"
              />
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography gutterBottom>Replicas: {resourceConfig.replicas}</Typography>
              <Slider
                value={resourceConfig.replicas}
                onChange={handleReplicasChange}
                min={1}
                max={10}
                step={1}
                marks
                valueLabelDisplay="auto"
              />
            </Box>

            <FormControlLabel
              control={
                <Switch
                  checked={autoScale}
                  onChange={(e) => setAutoScale(e.target.checked)}
                />
              }
              label="Enable Auto-scaling"
            />

            <Box sx={{ mt: 3 }}>
              <Button
                variant="contained"
                startIcon={<Upload />}
                onClick={handleUpload}
                disabled={!selectedFile || !imageName || uploadProgress.status === 'uploading'}
                fullWidth
                size="large"
              >
                Upload Image
              </Button>
            </Box>
          </Paper>
        </Box>
      </Box>
    </Box>
  );
};

export default ImageUpload; 