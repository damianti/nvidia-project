const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');

const app = express();
const PORT = process.env.PORT || 8080;

// Middleware
app.use(helmet());
app.use(cors());
app.use(morgan('combined'));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Mock services data
const mockServices = {
  ui: [
    { id: 'ui-1', url: 'http://localhost:3000', port: 3000, healthy: true, load: 0 },
    { id: 'ui-2', url: 'http://localhost:3001', port: 3001, healthy: false, load: 0 }
  ],
  orchestrator: [
    { id: 'orch-1', url: 'http://localhost:8081', port: 8081, healthy: true, load: 0 },
    { id: 'orch-2', url: 'http://localhost:8082', port: 8082, healthy: true, load: 0 }
  ],
  billing: [
    { id: 'billing-1', url: 'http://localhost:8083', port: 8083, healthy: true, load: 0 }
  ],
  workload: [
    { id: 'workload-1', url: 'http://localhost:8084', port: 8084, healthy: true, load: 0 }
  ]
};

let currentIndex = 0;

// Get next healthy instance using round-robin
function getNextInstance(serviceType) {
  const instances = mockServices[serviceType];
  if (!instances) {
    throw new Error(`Service ${serviceType} not found`);
  }

  const healthyInstances = instances.filter(instance => instance.healthy);
  if (healthyInstances.length === 0) {
    throw new Error(`No healthy instances available for ${serviceType}`);
  }

  const instance = healthyInstances[currentIndex % healthyInstances.length];
  currentIndex = (currentIndex + 1) % healthyInstances.length;
  
  return instance;
}

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    message: 'NVIDIA Cloud Platform - Load Balancer API Gateway',
    version: '1.0.0',
    status: 'running',
    endpoints: {
      health: '/health',
      api: '/api',
      services: '/api/services'
    }
  });
});

// Health check
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'load-balancer',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    version: '1.0.0'
  });
});

// Detailed health check
app.get('/health/detailed', (req, res) => {
  const servicesStatus = {};
  let totalServices = 0;
  let healthyServices = 0;

  for (const [serviceType, instances] of Object.entries(mockServices)) {
    const healthyInstances = instances.filter(instance => instance.healthy);
    servicesStatus[serviceType] = {
      serviceType: serviceType,
      totalInstances: instances.length,
      healthyInstances: healthyInstances.length,
      totalRequests: 0,
      activeRequests: 0,
      lastHealthCheck: Date.now(),
      instances: instances.map(instance => ({
        id: instance.id,
        url: instance.url,
        healthy: instance.healthy,
        load: instance.load
      }))
    };
    
    totalServices++;
    if (healthyInstances.length > 0) {
      healthyServices++;
    }
  }

  res.json({
    status: healthyServices === totalServices ? 'healthy' : 'degraded',
    service: 'load-balancer',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    version: '1.0.0',
    metrics: {
      totalServices: totalServices,
      healthyServices: healthyServices,
      totalInstances: Object.values(servicesStatus).reduce((sum, service) => 
        sum + service.totalInstances, 0
      ),
      healthyInstances: Object.values(servicesStatus).reduce((sum, service) => 
        sum + service.healthyInstances, 0
      )
    },
    services: servicesStatus
  });
});

// Get all services status
app.get('/api/services', (req, res) => {
  const status = {};
  
  for (const [serviceType, instances] of Object.entries(mockServices)) {
    const healthyInstances = instances.filter(instance => instance.healthy);
    status[serviceType] = {
      serviceType: serviceType,
      totalInstances: instances.length,
      healthyInstances: healthyInstances.length,
      totalRequests: 0,
      activeRequests: 0,
      lastHealthCheck: Date.now(),
      instances: instances.map(instance => ({
        id: instance.id,
        url: instance.url,
        healthy: instance.healthy,
        load: instance.load
      }))
    };
  }

  res.json({
    success: true,
    data: status,
    timestamp: new Date().toISOString()
  });
});

// Get specific service status
app.get('/api/services/:serviceType', (req, res) => {
  const { serviceType } = req.params;
  const instances = mockServices[serviceType];
  
  if (!instances) {
    return res.status(404).json({
      success: false,
      error: `Service ${serviceType} not found`
    });
  }

  const healthyInstances = instances.filter(instance => instance.healthy);
  const status = {
    serviceType: serviceType,
    totalInstances: instances.length,
    healthyInstances: healthyInstances.length,
    totalRequests: 0,
    activeRequests: 0,
    lastHealthCheck: Date.now(),
    instances: instances.map(instance => ({
      id: instance.id,
      url: instance.url,
      healthy: instance.healthy,
      load: instance.load
    }))
  };

  res.json({
    success: true,
    data: status,
    timestamp: new Date().toISOString()
  });
});

// Route requests to services
app.get('/api/ui', (req, res) => {
  try {
    const instance = getNextInstance('ui');
    res.json({
      success: true,
      data: {
        message: 'UI Service',
        status: 'running',
        instance: instance.id,
        url: instance.url
      },
      instance: instance.id,
      serviceType: 'ui'
    });
  } catch (error) {
    res.status(503).json({
      error: 'Service unavailable',
      message: error.message
    });
  }
});

app.get('/api/orchestrator', (req, res) => {
  try {
    const instance = getNextInstance('orchestrator');
    res.json({
      success: true,
      data: {
        message: 'Orchestrator Service',
        status: 'running',
        instance: instance.id,
        url: instance.url
      },
      instance: instance.id,
      serviceType: 'orchestrator'
    });
  } catch (error) {
    res.status(503).json({
      error: 'Service unavailable',
      message: error.message
    });
  }
});

app.get('/api/billing', (req, res) => {
  try {
    const instance = getNextInstance('billing');
    res.json({
      success: true,
      data: {
        message: 'Billing Service',
        status: 'running',
        instance: instance.id,
        url: instance.url
      },
      instance: instance.id,
      serviceType: 'billing'
    });
  } catch (error) {
    res.status(503).json({
      error: 'Service unavailable',
      message: error.message
    });
  }
});

app.get('/api/workload', (req, res) => {
  try {
    const instance = getNextInstance('workload');
    res.json({
      success: true,
      data: {
        message: 'Workload Service',
        status: 'running',
        instance: instance.id,
        url: instance.url
      },
      instance: instance.id,
      serviceType: 'workload'
    });
  } catch (error) {
    res.status(503).json({
      error: 'Service unavailable',
      message: error.message
    });
  }
});

// Mock endpoints for development
app.get('/api/mock/images', (req, res) => {
  res.json({
    success: true,
    data: [
      {
        id: '1',
        name: 'nginx',
        tag: 'latest',
        status: 'active',
        instances: 2,
        requestsPerSecond: 150,
        cost: 12.50
      },
      {
        id: '2',
        name: 'nodejs-app',
        tag: 'v1.2.0',
        status: 'active',
        instances: 1,
        requestsPerSecond: 80,
        cost: 8.75
      }
    ]
  });
});

app.get('/api/mock/metrics', (req, res) => {
  res.json({
    success: true,
    data: {
      totalImages: 3,
      activeImages: 2,
      totalInstances: 3,
      totalCost: 21.25,
      totalRequests: 170000
    }
  });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({
    error: 'Something went wrong!',
    message: err.message
  });
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    error: 'Endpoint not found',
    path: req.originalUrl
  });
});

app.listen(PORT, () => {
  console.log(`🚀 Load Balancer running on port ${PORT}`);
  console.log(`📊 Health check: http://localhost:${PORT}/health`);
  console.log(`🔗 API Gateway: http://localhost:${PORT}/api`);
});

module.exports = app; 