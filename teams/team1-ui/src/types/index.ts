export interface User {
  id: string;
  email: string;
  name: string;
}

export interface DockerImage {
  id: string;
  name: string;
  tag: string;
  size: string;
  createdAt: string;
  status: 'active' | 'inactive' | 'error';
  instances: Instance[];
  metrics: ImageMetrics;
  cost: number;
}

export interface Instance {
  id: string;
  imageId: string;
  status: 'running' | 'stopped' | 'starting' | 'stopping' | 'error';
  port: number;
  cpu: number;
  memory: number;
  createdAt: string;
  lastHealthCheck: string;
}

export interface ImageMetrics {
  requestsPerSecond: number;
  averageResponseTime: number;
  totalRequests: number;
  errorRate: number;
  cpuUsage: number;
  memoryUsage: number;
}

export interface ResourceConfig {
  cpu: number;
  memory: number;
  storage: number;
  replicas: number;
}

export interface UploadProgress {
  percentage: number;
  status: 'uploading' | 'processing' | 'complete' | 'error';
  message: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
} 