/**
 * Unit tests for imageService.
 * Tests API client methods with mocked fetch responses.
 */
import { imageService } from '@/services/imageService'
import { server } from '../mocks/server'
import { rest } from 'msw'

describe('ImageService', () => {
  describe('getImages', () => {
    it('should fetch all images successfully', async () => {
      // Arrange & Act
      const images = await imageService.getImages()

      // Assert
      expect(images).toHaveLength(2)
      expect(images[0]).toMatchObject({
        id: 1,
        name: 'test-image',
        tag: 'latest',
        app_hostname: 'test.example.com',
        status: 'ready',
      })
    })

    it('should handle 401 authentication error', async () => {
      // Arrange
      server.use(
        rest.get('/api/images', (req, res, ctx) => {
          return res(
            ctx.status(401),
            ctx.json({ detail: 'Authentication required' })
          )
        })
      )

      // Act & Assert
      await expect(imageService.getImages()).rejects.toThrow(
        'Authentication required'
      )
    })

    it('should handle server error (500)', async () => {
      // Arrange
      server.use(
        rest.get('/api/images', (req, res, ctx) => {
          return res(
            ctx.status(500),
            ctx.json({ error: 'Internal server error' })
          )
        })
      )

      // Act & Assert
      await expect(imageService.getImages()).rejects.toThrow(
        'Failed to fetch images'
      )
    })

    it('should handle network error', async () => {
      // Arrange
      server.use(
        rest.get('/api/images', (_req, res) => {
          return res.networkError('Network error')
        })
      )

      // Act & Assert
      await expect(imageService.getImages()).rejects.toThrow()
    })
  })

  describe('getImage', () => {
    it('should fetch a single image by id', async () => {
      // Arrange & Act
      const image = await imageService.getImage(1)

      // Assert
      expect(image).toMatchObject({
        id: 1,
        name: 'test-image',
        tag: 'latest',
      })
    })

    it('should handle 404 when image not found', async () => {
      // Arrange & Act
      await expect(imageService.getImage(999)).rejects.toThrow(
        'Image not found'
      )
    })

    it('should handle 401 authentication error', async () => {
      // Arrange
      server.use(
        rest.get('/api/images/:id', (req, res, ctx) => {
          return res(
            ctx.status(401),
            ctx.json({ detail: 'Authentication required' })
          )
        })
      )

      // Act & Assert
      await expect(imageService.getImage(1)).rejects.toThrow(
        'Authentication required'
      )
    })
  })

  describe('getBuildLogs', () => {
    it('should fetch build logs successfully', async () => {
      // Arrange & Act
      const logs = await imageService.getBuildLogs(1)

      // Assert
      expect(logs).toBe('Build logs here...')
    })

    it('should handle 404 when image not found', async () => {
      // Arrange & Act
      await expect(imageService.getBuildLogs(999)).rejects.toThrow(
        'Image not found'
      )
    })

    it('should return empty string when build_logs is missing', async () => {
      // Arrange
      server.use(
        rest.get('/api/images/:id/build-logs', (req, res, ctx) => {
          return res(ctx.json({}))
        })
      )

      // Act
      const logs = await imageService.getBuildLogs(1)

      // Assert
      expect(logs).toBe('')
    })
  })

  describe('createImage', () => {
    it('should create a new image with FormData', async () => {
      // Arrange
      const file = new File(['test content'], 'test.zip', {
        type: 'application/zip',
      })
      const imageData = {
        name: 'new-image',
        tag: 'v1.0',
        app_hostname: 'new.example.com',
        container_port: 3000,
        min_instances: 1,
        max_instances: 3,
        cpu_limit: '0.5',
        memory_limit: '512m',
        user_id: 1,
        file,
      }

      // Act
      const createdImage = await imageService.createImage(imageData)

      // Assert
      expect(createdImage).toMatchObject({
        id: expect.any(Number),
        name: 'new-image',
        tag: 'v1.0',
        app_hostname: 'new.example.com',
        status: 'building',
      })
    })

    it('should handle 401 authentication error', async () => {
      // Arrange
      server.use(
        rest.post('/api/images', (req, res, ctx) => {
          return res(
            ctx.status(401),
            ctx.json({ detail: 'Authentication required' })
          )
        })
      )

      const file = new File(['test'], 'test.zip', { type: 'application/zip' })
      const imageData = {
        name: 'new-image',
        tag: 'v1.0',
        app_hostname: 'new.example.com',
        container_port: 8080,
        min_instances: 1,
        max_instances: 3,
        cpu_limit: '0.5',
        memory_limit: '512m',
        user_id: 1,
        file,
      }

      // Act & Assert
      await expect(imageService.createImage(imageData)).rejects.toThrow(
        'Authentication required'
      )
    })

    it('should handle server error (500)', async () => {
      // Arrange
      server.use(
        rest.post('/api/images', (req, res, ctx) => {
          return res(
            ctx.status(500),
            ctx.json({ error: 'Build failed' })
          )
        })
      )

      const file = new File(['test'], 'test.zip', { type: 'application/zip' })
      const imageData = {
        name: 'new-image',
        tag: 'v1.0',
        app_hostname: 'new.example.com',
        container_port: 8080,
        min_instances: 1,
        max_instances: 3,
        cpu_limit: '0.5',
        memory_limit: '512m',
        user_id: 1,
        file,
      }

      // Act & Assert
      await expect(imageService.createImage(imageData)).rejects.toThrow(
        'Failed to create image'
      )
    })
  })

  describe('updateImage', () => {
    it('should update an existing image', async () => {
      // Arrange
      server.use(
        rest.put('/api/images/:id', async (req, res, ctx) => {
          const body = await req.json()
          return res(
            ctx.json({
              id: Number(req.params.id),
              ...body,
              status: 'ready',
              created_at: '2024-01-01T00:00:00Z',
            })
          )
        })
      )

      const updateData = {
        name: 'updated-image',
        tag: 'v2.0',
      }

      // Act
      const updatedImage = await imageService.updateImage(1, updateData)

      // Assert
      expect(updatedImage).toMatchObject({
        id: 1,
        name: 'updated-image',
        tag: 'v2.0',
      })
    })

    it('should handle 404 when image not found', async () => {
      // Arrange
      server.use(
        rest.put('/api/images/:id', (req, res, ctx) => {
          return res(
            ctx.status(404),
            ctx.json({ detail: 'Image not found' })
          )
        })
      )

      // Act & Assert
      await expect(
        imageService.updateImage(999, { name: 'updated' })
      ).rejects.toThrow('Image not found')
    })
  })

  describe('deleteImage', () => {
    it('should delete an image successfully', async () => {
      // Arrange & Act
      await expect(imageService.deleteImage(1)).resolves.not.toThrow()
    })

    it('should handle 404 when image not found', async () => {
      // Arrange
      server.use(
        rest.delete('/api/images/:id', (req, res, ctx) => {
          return res(
            ctx.status(404),
            ctx.json({ detail: 'Image not found' })
          )
        })
      )

      // Act & Assert
      await expect(imageService.deleteImage(999)).rejects.toThrow(
        'Image not found'
      )
    })

    it('should handle 401 authentication error', async () => {
      // Arrange
      server.use(
        rest.delete('/api/images/:id', (req, res, ctx) => {
          return res(
            ctx.status(401),
            ctx.json({ detail: 'Authentication required' })
          )
        })
      )

      // Act & Assert
      await expect(imageService.deleteImage(1)).rejects.toThrow(
        'Authentication required'
      )
    })
  })
})
