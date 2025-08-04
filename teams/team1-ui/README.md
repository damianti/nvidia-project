# Team 1 - UI Service

## 🎯 Mission
Create a modern, responsive user interface for the NVIDIA Cloud Platform that allows users to:
- Authenticate and manage their account
- Upload and configure Docker images
- Monitor and control running instances
- View performance metrics and costs
- Scale applications dynamically

## 🚀 Quick Start

### Prerequisites
- Node.js (v16+)
- npm or yarn
- Docker and Docker Compose

### Development Setup
```bash
# Install dependencies
npm install

# Start development server
npm start

# The UI will be available at http://localhost:3000
```

### Docker Setup
```bash
# Build and run with Docker Compose (includes mock services)
npm run docker:compose

# Or build and run standalone
npm run docker:build
npm run docker:run
```

## 🏗️ Architecture

### Frontend Stack
- **React 19** with TypeScript
- **Material-UI (MUI)** for components and theming
- **React Router** for navigation
- **React Dropzone** for file uploads
- **Axios** for API communication

### Key Components
- **Authentication**: Login/Signup with JWT
- **Dashboard**: Overview metrics and recent images
- **Image Upload**: Drag-and-drop Docker image upload with resource configuration
- **Image Management**: View, start, stop, and scale images
- **Layout**: Responsive navigation with sidebar

### Mock Data
The application includes comprehensive mock data for development:
- Sample Docker images with metrics
- Instance management simulation
- Cost tracking
- Performance metrics

## 📁 Project Structure
```
src/
├── components/
│   ├── auth/           # Authentication components
│   ├── dashboard/      # Dashboard and metrics
│   ├── images/         # Image management
│   └── layout/         # Navigation and layout
├── contexts/           # React contexts (Auth)
├── types/              # TypeScript interfaces
└── services/           # API services (future)
```

## 🔧 Configuration

### Environment Variables
- `REACT_APP_API_BASE_URL`: Base URL for API calls
- `REACT_APP_MOCK_MODE`: Enable mock mode for development

### Docker Configuration
- **Dockerfile**: Multi-stage build with nginx
- **nginx.conf**: Production server configuration
- **docker-compose.yml**: Development environment with mock services

## 🎨 UI Features

### Authentication
- Modern login/signup forms
- JWT token management
- Persistent sessions
- User profile management

### Dashboard
- Real-time metrics overview
- Performance indicators
- Cost tracking
- Recent activity

### Image Management
- Drag-and-drop file upload
- Resource configuration sliders
- Instance scaling controls
- Detailed metrics view
- Status indicators

### Responsive Design
- Mobile-friendly interface
- Adaptive navigation
- Touch-friendly controls
- Cross-browser compatibility

## 🔌 API Integration Points

### Current (Mock)
- Image CRUD operations
- Instance management
- Metrics retrieval
- Cost calculations

### Future Integration
- Team 2: Load Balancer API
- Team 3: Orchestrator API
- Team 6: Billing API
- Team 7: Client Workload API

## 🧪 Testing

### Development Testing
```bash
# Run tests
npm test

# Run tests with coverage
npm test -- --coverage
```

### Manual Testing
1. **Authentication Flow**: Test login/signup
2. **Image Upload**: Test file upload with different sizes
3. **Instance Management**: Test start/stop/scaling
4. **Responsive Design**: Test on different screen sizes

## 🚀 Deployment

### Development
```bash
npm run dev
```

### Production
```bash
# Build and deploy
npm run prod

# Or with Docker Compose
docker-compose -f docker-compose.prod.yml up -d
```

## 📊 Performance

### Optimization Features
- Code splitting with React.lazy()
- Material-UI tree shaking
- Optimized bundle size
- Gzip compression
- Static asset caching

### Monitoring
- Health check endpoint: `/health`
- Performance metrics
- Error tracking
- User analytics

## 🔒 Security

### Implemented
- JWT authentication
- Secure headers
- Input validation
- XSS protection
- CSRF protection

### Best Practices
- Environment variable management
- Secure file upload validation
- API rate limiting (future)
- Audit logging (future)

## 🤝 Team Collaboration

### Day 1 Tasks
- [x] Set up React application structure
- [x] Implement authentication UI
- [x] Create dashboard with mock data
- [x] Build image upload interface
- [x] Develop image management features

### Day 2 Tasks
- [ ] Meet with other teams for API contracts
- [ ] Replace mock data with real API calls
- [ ] Test integration points
- [ ] Implement error handling

### Day 3 Tasks
- [ ] Final integration testing
- [ ] Performance optimization
- [ ] Prepare presentation demo
- [ ] Create final docker-compose.yml with other teams

## 📞 Support

### Team Communication
- **Daily Standups**: 9:00 AM
- **Integration Meetings**: 2:00 PM
- **API Contract Reviews**: As needed

### Documentation
- API specifications in `/docs/api-specifications.md`
- Architecture overview in `/docs/architecture.md`
- Collaboration guide in `/docs/collaboration-guide.md`

## 🎯 Success Criteria
- [ ] Modern, responsive UI
- [ ] Complete authentication flow
- [ ] Image upload and management
- [ ] Instance scaling controls
- [ ] Real-time metrics display
- [ ] Integration with other teams' APIs
- [ ] Production-ready deployment
- [ ] Comprehensive testing coverage

---

**Team 1 - UI Service** | NVIDIA ScaleUp Hackathon 2025 