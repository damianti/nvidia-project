/**
 * Unit tests for billingService.
 * Tests API client methods with mocked fetch responses.
 */
import { billingService } from '@/services/billingService'
import { server } from './mocks/server'
import { rest } from 'msw'

describe('BillingService', () => {
  describe('getAllBillingSummaries', () => {
    it('should fetch all billing summaries successfully', async () => {
      // Arrange & Act
      const summaries = await billingService.getAllBillingSummaries()

      // Assert
      expect(summaries).toHaveLength(1)
      expect(summaries[0]).toMatchObject({
        image_id: 1,
        total_containers: 5,
        total_minutes: 1200,
        total_cost: 10.5,
        active_containers: 2,
      })
    })

    it('should handle 401 authentication error', async () => {
      // Arrange
      server.use(
        rest.get('/api/billing/images', (req, res, ctx) => {
          return res(
            ctx.status(401),
            ctx.json({ detail: 'Authentication required' })
          )
        })
      )

      // Act & Assert
      await expect(
        billingService.getAllBillingSummaries()
      ).rejects.toThrow('Authentication required')
    })

    it('should handle server error (500)', async () => {
      // Arrange
      server.use(
        rest.get('/api/billing/images', (req, res, ctx) => {
          return res(
            ctx.status(500),
            ctx.json({ error: 'Internal server error' })
          )
        })
      )

      // Act & Assert
      await expect(
        billingService.getAllBillingSummaries()
      ).rejects.toThrow('Internal server error')
    })

    it('should handle network error', async () => {
      // Arrange
      server.use(
        rest.get('/api/billing/images', (_req, res) => {
          return res.networkError("Network error")
        })
      )

      // Act & Assert
      await expect(billingService.getAllBillingSummaries()).rejects.toThrow()
    })
  })

  describe('getImageBilling', () => {
    it('should fetch billing detail for a specific image', async () => {
      // Arrange & Act
      const detail = await billingService.getImageBilling(1)

      // Assert
      expect(detail).toMatchObject({
        image_id: 1,
        summary: expect.objectContaining({
          total_containers: 5,
          total_cost: 10.5,
        }),
        containers: expect.any(Array),
      })
    })

    it('should handle 404 when billing info not found', async () => {
      // Arrange & Act
      await expect(billingService.getImageBilling(999)).rejects.toThrow(
        'Billing information not found for this image'
      )
    })

    it('should handle 401 authentication error', async () => {
      // Arrange
      server.use(
        rest.get('/api/billing/images/:id', (req, res, ctx) => {
          return res(
            ctx.status(401),
            ctx.json({ detail: 'Authentication required' })
          )
        })
      )

      // Act & Assert
      await expect(billingService.getImageBilling(1)).rejects.toThrow(
        'Authentication required'
      )
    })

    it('should handle server error (500)', async () => {
      // Arrange
      server.use(
        rest.get('/api/billing/images/:id', (req, res, ctx) => {
          return res(
            ctx.status(500),
            ctx.json({ error: 'Internal server error' })
          )
        })
      )

      // Act & Assert
      await expect(billingService.getImageBilling(1)).rejects.toThrow(
        'Internal server error'
      )
    })
  })
})

