const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const loadBalancerRoutes = require('./routes/loadBalancer');
const healthRoutes = require('./routes/health');

const app = express();
const PORT = process.env.PORT || 8080;

// Middleware
app.use(helmet());
app.use(cors());
app.use(morgan('combined'));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Routes
app.use('/api', loadBalancerRoutes);
app.use('/health', healthRoutes);

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