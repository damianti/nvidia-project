const http = require('http');
const url = require('url');

const PORT = process.env.PORT || 8080;

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

// Helper function to send JSON response
function sendJsonResponse(res, statusCode, data) {
  res.writeHead(statusCode, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify(data, null, 2));
}

// Create HTTP server
const server = http.createServer((req, res) => {
  const parsedUrl = url.parse(req.url, true);
  const path = parsedUrl.pathname;
  const method = req.method;

  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  // Handle OPTIONS requests
  if (method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }

  // Route handling
  if (method === 'GET') {
    switch (path) {
      case '/':
        sendJsonResponse(res, 200, {
          message: 'NVIDIA Cloud Platform - Load Balancer API Gateway',
          version: '1.0.0',
          status: 'running',
          endpoints: {
            health: '/health',
            api: '/api',
            services: '/api/services'
          }
        });
        break;

      case '/health':
        sendJsonResponse(res, 200, {
          status: 'healthy',
          service: 'load-balancer',
          timestamp: new Date().toISOString(),
          uptime: process.uptime(),
          version: '1.0.0'
        });
        break;

      case '/health/detailed':
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

        sendJsonResponse(res, 200, {
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
        break;

      case '/api/services':
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

        sendJsonResponse(res, 200, {
          success: true,
          data: status,
          timestamp: new Date().toISOString()
        });
        break;

      case '/api/ui':
        try {
          const instance = getNextInstance('ui');
          sendJsonResponse(res, 200, {
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
          sendJsonResponse(res, 503, {
            error: 'Service unavailable',
            message: error.message
          });
        }
        break;

      case '/api/orchestrator':
        try {
          const instance = getNextInstance('orchestrator');
          sendJsonResponse(res, 200, {
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
          sendJsonResponse(res, 503, {
            error: 'Service unavailable',
            message: error.message
          });
        }
        break;

      case '/api/billing':
        try {
          const instance = getNextInstance('billing');
          sendJsonResponse(res, 200, {
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
          sendJsonResponse(res, 503, {
            error: 'Service unavailable',
            message: error.message
          });
        }
        break;

      case '/api/workload':
        try {
          const instance = getNextInstance('workload');
          sendJsonResponse(res, 200, {
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
          sendJsonResponse(res, 503, {
            error: 'Service unavailable',
            message: error.message
          });
        }
        break;

      case '/api/mock/images':
        sendJsonResponse(res, 200, {
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
        break;

      case '/api/mock/metrics':
        sendJsonResponse(res, 200, {
          success: true,
          data: {
            totalImages: 3,
            activeImages: 2,
            totalInstances: 3,
            totalCost: 21.25,
            totalRequests: 170000
          }
        });
        break;

      default:
        sendJsonResponse(res, 404, {
          error: 'Endpoint not found',
          path: path
        });
        break;
    }
  } else {
    sendJsonResponse(res, 405, {
      error: 'Method not allowed',
      method: method
    });
  }
});

server.listen(PORT, () => {
  console.log(`🚀 Load Balancer running on port ${PORT}`);
  console.log(`📊 Health check: http://localhost:${PORT}/health`);
  console.log(`🔗 API Gateway: http://localhost:${PORT}/api`);
});

module.exports = server; 