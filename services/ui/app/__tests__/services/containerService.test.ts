/**
 * Unit tests for containerService.
 * Tests API client methods with mocked fetch responses.
 */
import { containerService } from '@/services/containerService'
import { server } from '../mocks/server'
import { rest } from 'msw'

describe('ContainerService', () => {
  describe('getContainers', () => {
    it('should fetch all containers successfully', async () => {
      // Arrange & Act
      const containers = await containerService.getContainers()

      // Assert
      expect(containers).toHaveLength(1)
      expect(containers[0]).toMatchObject({
        id: 1,
        container_id: 'container-123',
        name: 'test-container',
        status: 'running',
      })
    })

    it('should handle 401 authentication error', async () => {
      // Arrange
      server.use(
        rest.get('/api/containers', (req, res, ctx) => {
          return res(
            ctx.status(401),
            ctx.json({ detail: 'Authentication required' })
          )
        })
      )

      // Act & Assert
      await expect(containerService.getContainers()).rejects.toThrow(
        'Authentication required'
      )
    })

    it('should handle server error (500)', async () => {
      // Arrange
      server.use(
        rest.get('/api/containers', (req, res, ctx) => {
          return res(
            ctx.status(500),
            ctx.json({ error: 'Internal server error' })
          )
        })
      )

      // Act & Assert
      await expect(containerService.getContainers()).rejects.toThrow(
        'Failed to fetch containers'
      )
    })
  })

  describe('getImagesWithContainers', () => {
    it('should fetch images with containers successfully', async () => {
      // Arrange & Act
      const imagesWithContainers = await containerService.getImagesWithContainers()

      // Assert
      expect(imagesWithContainers).toHaveLength(2)
      expect(imagesWithContainers[0]).toHaveProperty('containers')
      expect(Array.isArray(imagesWithContainers[0].containers)).toBe(true)
    })

    it('should handle 401 authentication error', async () => {
      // Arrange
      server.use(
        rest.get('/api/images/with-containers', (req, res, ctx) => {
          return res(
            ctx.status(401),
            ctx.json({ detail: 'Authentication required' })
          )
        })
      )

      // Act & Assert
      await expect(
        containerService.getImagesWithContainers()
      ).rejects.toThrow('Authentication required')
    })
  })

  describe('createContainer', () => {
    it('should create a single container successfully', async () => {
      // Arrange
      const imageId = 1
      const containerName = 'new-container'
      const count = 1

      // Act
      const containers = await containerService.createContainer(
        imageId,
        containerName,
        count
      )

      // Assert
      expect(containers).toHaveLength(1)
      expect(containers[0]).toMatchObject({
        name: containerName,
        image_id: imageId,
        status: 'running',
      })
    })

    it('should create multiple containers when count > 1', async () => {
      // Arrange
      const imageId = 1
      const count = 3

      // Act
      const containers = await containerService.createContainer(
        imageId,
        undefined,
        count
      )

      // Assert
      expect(containers).toHaveLength(3)
      containers.forEach(container => {
        expect(container.image_id).toBe(imageId)
      })
    })

    it('should handle 401 authentication error', async () => {
      // Arrange
      server.use(
        rest.post('/api/containers/:imageId', (req, res, ctx) => {
          return res(
            ctx.status(401),
            ctx.json({ detail: 'Authentication required' })
          )
        })
      )

      // Act & Assert
      await expect(
        containerService.createContainer(1, 'test', 1)
      ).rejects.toThrow('Authentication required')
    })

    it('should handle server error with non-JSON response', async () => {
      // Arrange
      server.use(
        rest.post('/api/containers/:imageId', (req, res, ctx) => {
          return res(
            ctx.status(500),
            ctx.text('Internal Server Error')
          )
        })
      )

      // Act & Assert
      await expect(
        containerService.createContainer(1, 'test', 1)
      ).rejects.toThrow('HTTP 500')
    })
  })

  describe('startContainer', () => {
    it('should start a container successfully', async () => {
      // Arrange & Act
      const container = await containerService.startContainer(1)

      // Assert
      expect(container).toMatchObject({
        id: 1,
        status: 'running',
      })
    })

    it('should handle 404 when container not found', async () => {
      // Arrange
      server.use(
        rest.post('/api/containers/:id/start', (req, res, ctx) => {
          return res(
            ctx.status(404),
            ctx.json({ detail: 'Container not found' })
          )
        })
      )

      // Act & Assert
      await expect(containerService.startContainer(999)).rejects.toThrow(
        'Container not found'
      )
    })

    it('should handle 401 authentication error', async () => {
      // Arrange
      server.use(
        rest.post('/api/containers/:id/start', (req, res, ctx) => {
          return res(
            ctx.status(401),
            ctx.json({ detail: 'Authentication required' })
          )
        })
      )

      // Act & Assert
      await expect(containerService.startContainer(1)).rejects.toThrow(
        'Authentication required'
      )
    })
  })

  describe('stopContainer', () => {
    it('should stop a container successfully', async () => {
      // Arrange & Act
      const container = await containerService.stopContainer(1)

      // Assert
      expect(container).toMatchObject({
        id: 1,
        status: 'stopped',
      })
    })

    it('should handle 404 when container not found', async () => {
      // Arrange
      server.use(
        rest.post('/api/containers/:id/stop', (req, res, ctx) => {
          return res(
            ctx.status(404),
            ctx.json({ detail: 'Container not found' })
          )
        })
      )

      // Act & Assert
      await expect(containerService.stopContainer(999)).rejects.toThrow(
        'Container not found'
      )
    })
  })

  describe('deleteContainer', () => {
    it('should delete a container successfully', async () => {
      // Arrange & Act
      const result = await containerService.deleteContainer(1)

      // Assert
      expect(result).toMatchObject({
        message: 'Container deleted successfully',
      })
    })

    it('should handle 404 when container not found', async () => {
      // Arrange
      server.use(
        rest.delete('/api/containers/:id', (req, res, ctx) => {
          return res(
            ctx.status(404),
            ctx.json({ detail: 'Container not found' })
          )
        })
      )

      // Act & Assert
      await expect(containerService.deleteContainer(999)).rejects.toThrow(
        'Container not found'
      )
    })

    it('should handle 401 authentication error', async () => {
      // Arrange
      server.use(
        rest.delete('/api/containers/:id', (req, res, ctx) => {
          return res(
            ctx.status(401),
            ctx.json({ detail: 'Authentication required' })
          )
        })
      )

      // Act & Assert
      await expect(containerService.deleteContainer(1)).rejects.toThrow(
        'Authentication required'
      )
    })
  })
})
