const axios = require('axios');

class LoadBalancer {
  constructor() {
    this.services = new Map();
    this.currentIndex = 0;
    this.healthCheckInterval = 30000; // 30 seconds
    this.initializeMockServices();
    this.startHealthChecks();
  }

  // Initialize mock services for development
  initializeMockServices() {
    // Mock UI Service
    this.addService('ui', [
      { id: 'ui-1', url: 'http://localhost:3000', port: 3000, healthy: true, load: 0 },
      { id: 'ui-2', url: 'http://localhost:3001', port: 3001, healthy: false, load: 0 }
    ]);

    // Mock Orchestrator Service
    this.addService('orchestrator', [
      { id: 'orch-1', url: 'http://localhost:8081', port: 8081, healthy: true, load: 0 },
      { id: 'orch-2', url: 'http://localhost:8082', port: 8082, healthy: true, load: 0 }
    ]);

    // Mock Billing Service
    this.addService('billing', [
      { id: 'billing-1', url: 'http://localhost:8083', port: 8083, healthy: true, load: 0 }
    ]);

    // Mock Client Workload Service
    this.addService('workload', [
      { id: 'workload-1', url: 'http://localhost:8084', port: 8084, healthy: true, load: 0 }
    ]);
  }

  // Add a new service type
  addService(serviceType, instances) {
    this.services.set(serviceType, {
      instances: instances,
      lastCheck: Date.now(),
      totalRequests: 0,
      activeRequests: 0
    });
  }

  // Get next healthy instance using round-robin
  getNextInstance(serviceType) {
    const service = this.services.get(serviceType);
    if (!service) {
      throw new Error(`Service ${serviceType} not found`);
    }

    const healthyInstances = service.instances.filter(instance => instance.healthy);
    if (healthyInstances.length === 0) {
      throw new Error(`No healthy instances available for ${serviceType}`);
    }

    // Simple round-robin
    const instance = healthyInstances[this.currentIndex % healthyInstances.length];
    this.currentIndex = (this.currentIndex + 1) % healthyInstances.length;
    
    return instance;
  }

  // Route request to appropriate service
  async routeRequest(serviceType, path, method = 'GET', data = null) {
    const instance = this.getNextInstance(serviceType);
    const service = this.services.get(serviceType);
    
    // Update metrics
    service.totalRequests++;
    service.activeRequests++;
    instance.load++;

    try {
      const url = `${instance.url}${path}`;
      const config = {
        method: method.toLowerCase(),
        url: url,
        timeout: 5000,
        headers: {
          'Content-Type': 'application/json'
        }
      };

      if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
        config.data = data;
      }

      const response = await axios(config);
      
      // Update metrics
      service.activeRequests--;
      instance.load--;

      return {
        success: true,
        data: response.data,
        status: response.status,
        instance: instance.id,
        serviceType: serviceType
      };

    } catch (error) {
      // Update metrics
      service.activeRequests--;
      instance.load--;

      // Mark instance as unhealthy if it's a connection error
      if (error.code === 'ECONNREFUSED' || error.code === 'ENOTFOUND') {
        instance.healthy = false;
      }

      return {
        success: false,
        error: error.message,
        status: error.response?.status || 500,
        instance: instance.id,
        serviceType: serviceType
      };
    }
  }

  // Health check for all services
  async performHealthCheck() {
    console.log('🔍 Performing health check...');
    
    for (const [serviceType, service] of this.services) {
      for (const instance of service.instances) {
        try {
          const response = await axios.get(`${instance.url}/health`, {
            timeout: 3000
          });
          
          instance.healthy = response.status === 200;
          console.log(`✅ ${serviceType} (${instance.id}): ${instance.healthy ? 'HEALTHY' : 'UNHEALTHY'}`);
          
        } catch (error) {
          instance.healthy = false;
          console.log(`❌ ${serviceType} (${instance.id}): UNHEALTHY - ${error.message}`);
        }
      }
      service.lastCheck = Date.now();
    }
  }

  // Start periodic health checks
  startHealthChecks() {
    setInterval(() => {
      this.performHealthCheck();
    }, this.healthCheckInterval);
  }

  // Get service status
  getServiceStatus(serviceType) {
    const service = this.services.get(serviceType);
    if (!service) {
      return null;
    }

    const healthyInstances = service.instances.filter(instance => instance.healthy);
    
    return {
      serviceType: serviceType,
      totalInstances: service.instances.length,
      healthyInstances: healthyInstances.length,
      totalRequests: service.totalRequests,
      activeRequests: service.activeRequests,
      lastHealthCheck: service.lastCheck,
      instances: service.instances.map(instance => ({
        id: instance.id,
        url: instance.url,
        healthy: instance.healthy,
        load: instance.load
      }))
    };
  }

  // Get all services status
  getAllServicesStatus() {
    const status = {};
    for (const [serviceType] of this.services) {
      status[serviceType] = this.getServiceStatus(serviceType);
    }
    return status;
  }
}

module.exports = new LoadBalancer(); 