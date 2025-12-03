// Types for billing operations
export interface UsageRecord {
  id: number
  container_id: string
  start_time: string
  end_time: string | null
  duration_minutes: number | null
  cost: number | null
  status: string
}

export interface BillingSummary {
  image_id: number
  total_containers: number
  total_minutes: number
  total_cost: number
  active_containers: number
  last_activity: string | null
}

export interface BillingDetail {
  image_id: number
  summary: BillingSummary
  containers: UsageRecord[]
}

// Billing service class
class BillingService {
  private baseUrl = '/api/billing'

  // Helper to get headers
  private getHeaders(): HeadersInit {
    return {
      'Content-Type': 'application/json',
    }
  }

  // Get billing summaries for all images
  async getAllBillingSummaries(): Promise<BillingSummary[]> {
    try {
      const response = await fetch(`${this.baseUrl}/images`, {
        method: 'GET',
        headers: this.getHeaders(),
        credentials: 'include',
      })

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Authentication required')
        }
        const error = await response.json()
        throw new Error(error.detail || error.error || 'Failed to fetch billing summaries')
      }

      return await response.json()
    } catch (error) {
      console.error('Error fetching billing summaries:', error)
      throw error
    }
  }

  // Get detailed billing for a specific image
  async getImageBilling(imageId: number): Promise<BillingDetail> {
    try {
      const response = await fetch(`${this.baseUrl}/images/${imageId}`, {
        method: 'GET',
        headers: this.getHeaders(),
        credentials: 'include',
      })

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Authentication required')
        }
        if (response.status === 404) {
          throw new Error('Billing information not found for this image')
        }
        const error = await response.json()
        throw new Error(error.detail || error.error || 'Failed to fetch billing detail')
      }

      return await response.json()
    } catch (error) {
      console.error('Error fetching billing detail:', error)
      throw error
    }
  }
}

// Export singleton instance
export const billingService = new BillingService()


