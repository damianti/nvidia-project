import { rest } from 'msw'

// Mock data
export const mockImages = [
  {
    id: 1,
    name: 'test-image',
    tag: 'latest',
    app_hostname: 'test.example.com',
    status: 'ready',
    created_at: '2024-01-01T00:00:00Z',
    min_instances: 1,
    max_instances: 3,
    cpu_limit: '0.5',
    memory_limit: '512m',
    container_port: 8080,
  },
  {
    id: 2,
    name: 'another-image',
    tag: 'v1.0',
    app_hostname: 'another.example.com',
    status: 'building',
    created_at: '2024-01-02T00:00:00Z',
    min_instances: 2,
    max_instances: 5,
    cpu_limit: '1.0',
    memory_limit: '1g',
    container_port: 3000,
  },
]

export const mockContainers = [
  {
    id: 1,
    container_id: 'container-123',
    name: 'test-container',
    port: 8080,
    status: 'running',
    cpu_usage: '0.5',
    memory_usage: '256m',
    created_at: '2024-01-01T00:00:00Z',
    image_id: 1,
    image: mockImages[0],
  },
]

export const mockBillingSummaries = [
  {
    image_id: 1,
    total_containers: 5,
    total_minutes: 1200,
    total_cost: 10.5,
    active_containers: 2,
    last_activity: '2024-01-01T12:00:00Z',
  },
]

// MSW handlers
export const handlers = [
  // Images API
  rest.get('*/api/images', (req, res, ctx) => {
    return res(ctx.json(mockImages))
  }),

  // Este handler debe ir ANTES de /api/images/:id (los específicos primero)
  rest.get('/api/images/with-containers', (req, res, ctx) => {
    return res(
      ctx.json(
        mockImages.map(img => ({
          ...img,
          containers: mockContainers.filter(c => c.image_id === img.id),
        }))
      )
    )
  }),

  rest.get('*/api/images/:id', (req, res, ctx) => {
    const image = mockImages.find(img => img.id === Number(req.params.id))
    if (!image) {
      return res(
        ctx.status(404),
        ctx.json({ detail: 'Image not found' })
      )
    }
    return res(ctx.json(image))
  }),

  rest.post('/api/images', (req, res, ctx) => {
    // MSW v1 doesn't parse FormData automatically, so we create a mock response
    const newImage = {
      id: mockImages.length + 1,
      name: 'new-image',
      tag: 'v1.0',
      app_hostname: 'new.example.com',
      status: 'building',
      created_at: new Date().toISOString(),
      min_instances: 1,
      max_instances: 3,
      cpu_limit: '0.5',
      memory_limit: '512m',
      container_port: 8080,
    }
    return res(ctx.status(201), ctx.json(newImage))
  }),

  rest.delete('/api/images/:id', (req, res, ctx) => {
    const imageId = Number(req.params.id)
    const image = mockImages.find(img => img.id === imageId)
    if (!image) {
      return res(
        ctx.status(404),
        ctx.json({ detail: 'Image not found' })
      )
    }
    return res(ctx.json({ message: 'Image deleted successfully' }))
  }),

  rest.get('/api/images/:id/build-logs', (req, res, ctx) => {
    const imageId = Number(req.params.id)
    const image = mockImages.find(img => img.id === imageId)
    if (!image) {
      return res(
        ctx.status(404),
        ctx.json({ detail: 'Image not found' })
      )
    }
    return res(ctx.json({ build_logs: 'Build logs here...' }))
  }),

  // Containers API
  rest.get('/api/containers', (req, res, ctx) => {
    return res(ctx.json(mockContainers))
  }),

  rest.post('/api/containers/:imageId', async (req, res, ctx) => {
    const body = await req.json()
    const newContainers = Array.from({ length: body.count || 1 }, (_, i) => ({
      id: mockContainers.length + i + 1,
      container_id: `container-${Date.now()}-${i}`,
      name: body.name || `container-${i}`,
      port: 8080,
      status: 'running',
      cpu_usage: '0.0',
      memory_usage: '0m',
      created_at: new Date().toISOString(),
      image_id: Number(req.params.imageId),
      image: mockImages.find(img => img.id === Number(req.params.imageId))!,
    }))
    return res(ctx.status(201), ctx.json(newContainers))
  }),

  rest.post('/api/containers/:id/start', (req, res, ctx) => {
    const container = mockContainers.find(c => c.id === Number(req.params.id))
    if (!container) {
      return res(
        ctx.status(404),
        ctx.json({ detail: 'Container not found' })
      )
    }
    return res(ctx.json({ ...container, status: 'running' }))
  }),

  rest.post('/api/containers/:id/stop', (req, res, ctx) => {
    const container = mockContainers.find(c => c.id === Number(req.params.id))
    if (!container) {
      return res(
        ctx.status(404),
        ctx.json({ detail: 'Container not found' })
      )
    }
    return res(ctx.json({ ...container, status: 'stopped' }))
  }),

  rest.delete('/api/containers/:id', (req, res, ctx) => {
    const container = mockContainers.find(c => c.id === Number(req.params.id))
    if (!container) {
      return res(
        ctx.status(404),
        ctx.json({ detail: 'Container not found' })
      )
    }
    return res(ctx.json({ message: 'Container deleted successfully' }))
  }),

  // Billing API
  rest.get('/api/billing/images', (req, res, ctx) => {
    return res(ctx.json(mockBillingSummaries))
  }),

  rest.get('/api/billing/images/:id', (req, res, ctx) => {
    const summary = mockBillingSummaries.find(
      s => s.image_id === Number(req.params.id)
    )
    if (!summary) {
      return res(
        ctx.status(404),
        ctx.json({ detail: 'Billing information not found' })
      )
    }
    return res(
      ctx.json({
        image_id: summary.image_id,
        summary,
        containers: [],
      })
    )
  }),

  // Auth API
  rest.get('/api/auth/me', (req, res, ctx) => {
    return res(
      ctx.json({
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
      })
    )
  }),

  rest.post('/api/auth/login', async (req, res, ctx) => {
    const body = await req.json()
    if (body.email === 'test@example.com' && body.password === 'password') {
      return res(
        ctx.json({
          user: {
            id: 1,
            username: 'testuser',
            email: 'test@example.com',
          },
        })
      )
    }
    return res(
      ctx.status(401),
      ctx.json({ detail: 'Invalid credentials' })
    )
  }),

  rest.post('/api/auth/logout', (req, res, ctx) => {
    return res(ctx.json({ message: 'Logged out successfully' }))
  }),
]
