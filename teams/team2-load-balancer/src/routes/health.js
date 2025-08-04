const express = require('express');
const loadBalancer = require('../services/loadBalancer');

const router = express.Router();

// Basic health check
router.get('/', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'load-balancer',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    version: '1.0.0'
  });
});

// Detailed health check with service status
router.get('/detailed', (req, res) => {
  try {
    const servicesStatus = loadBalancer.getAllServicesStatus();
    const healthyServices = Object.values(servicesStatus).filter(service => 
      service.healthyInstances > 0
    ).length;
    const totalServices = Object.keys(servicesStatus).length;

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
        ),
        totalRequests: Object.values(servicesStatus).reduce((sum, service) => 
          sum + service.totalRequests, 0
        ),
        activeRequests: Object.values(servicesStatus).reduce((sum, service) => 
          sum + service.activeRequests, 0
        )
      },
      services: servicesStatus
    });
  } catch (error) {
    res.status(500).json({
      status: 'unhealthy',
      service: 'load-balancer',
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Health check for specific service
router.get('/service/:serviceType', (req, res) => {
  try {
    const { serviceType } = req.params;
    const status = loadBalancer.getServiceStatus(serviceType);
    
    if (!status) {
      return res.status(404).json({
        status: 'not_found',
        service: serviceType,
        error: `Service ${serviceType} not found`
      });
    }

    res.json({
      status: status.healthyInstances > 0 ? 'healthy' : 'unhealthy',
      service: serviceType,
      timestamp: new Date().toISOString(),
      data: status
    });
  } catch (error) {
    res.status(500).json({
      status: 'error',
      service: req.params.serviceType,
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Force health check
router.post('/check', async (req, res) => {
  try {
    await loadBalancer.performHealthCheck();
    res.json({
      status: 'success',
      message: 'Health check performed successfully',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(500).json({
      status: 'error',
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

module.exports = router; 