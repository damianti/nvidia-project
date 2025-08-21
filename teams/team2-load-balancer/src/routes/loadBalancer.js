const express = require('express');
const loadBalancer = require('../services/loadBalancer');

const router = express.Router();

// Get all services status
router.get('/services', (req, res) => {
  try {
    const status = loadBalancer.getAllServicesStatus();
    res.json({
      success: true,
      data: status,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Get specific service status
router.get('/services/:serviceType', (req, res) => {
  try {
    const { serviceType } = req.params;
    const status = loadBalancer.getServiceStatus(serviceType);
    
    if (!status) {
      return res.status(404).json({
        success: false,
        error: `Service ${serviceType} not found`
      });
    }

    res.json({
      success: true,
      data: status,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Route requests to UI service
router.get('/ui', async (req, res) => {
  try {
    const result = await loadBalancer.routeRequest('ui', '/', req.method, req.body);
    
    if (result.success) {
      res.status(result.status).json(result.data);
    } else {
      res.status(result.status).json({
        error: result.error,
        serviceType: result.serviceType,
        instance: result.instance
      });
    }
  } catch (error) {
    res.status(503).json({
      error: 'Service unavailable',
      message: error.message
    });
  }
});

// Route requests to Orchestrator service
router.get('/orchestrator', async (req, res) => {
  try {
    const result = await loadBalancer.routeRequest('orchestrator', '/', req.method, req.body);
    
    if (result.success) {
      res.status(result.status).json(result.data);
    } else {
      res.status(result.status).json({
        error: result.error,
        serviceType: result.serviceType,
        instance: result.instance
      });
    }
  } catch (error) {
    res.status(503).json({
      error: 'Service unavailable',
      message: error.message
    });
  }
});

// Route requests to Billing service
router.get('/billing', async (req, res) => {
  try {
    const result = await loadBalancer.routeRequest('billing', '/', req.method, req.body);
    
    if (result.success) {
      res.status(result.status).json(result.data);
    } else {
      res.status(result.status).json({
        error: result.error,
        serviceType: result.serviceType,
        instance: result.instance
      });
    }
  } catch (error) {
    res.status(503).json({
      error: 'Service unavailable',
      message: error.message
    });
  }
});

// Route requests to Workload service
router.get('/workload', async (req, res) => {
  try {
    const result = await loadBalancer.routeRequest('workload', '/', req.method, req.body);
    
    if (result.success) {
      res.status(result.status).json(result.data);
    } else {
      res.status(result.status).json({
        error: result.error,
        serviceType: result.serviceType,
        instance: result.instance
      });
    }
  } catch (error) {
    res.status(503).json({
      error: 'Service unavailable',
      message: error.message
    });
  }
});

// Mock endpoints for development (when other services aren't ready)
router.get('/mock/images', (req, res) => {
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

router.get('/mock/metrics', (req, res) => {
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

// Add new service endpoint
router.post('/services', (req, res) => {
  try {
    const { serviceType, instances } = req.body;
    
    if (!serviceType || !instances) {
      return res.status(400).json({
        success: false,
        error: 'serviceType and instances are required'
      });
    }

    loadBalancer.addService(serviceType, instances);
    
    res.json({
      success: true,
      message: `Service ${serviceType} added successfully`,
      data: loadBalancer.getServiceStatus(serviceType)
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

module.exports = router; 