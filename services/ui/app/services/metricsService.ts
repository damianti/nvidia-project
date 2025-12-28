export interface MetricsByDimension {
  requests: number
  errors: number
  avg_latency_ms: number
}

export interface GlobalMetrics {
  total_requests: number
  total_errors: number
  avg_latency_ms: number
  status_codes: Record<string, number>
  by_user?: Record<string, MetricsByDimension>
  by_app_hostname?: Record<string, MetricsByDimension>
  by_container?: Record<string, MetricsByDimension>
}

class MetricsService {
  private baseUrl = '/api/metrics'

  private getHeaders(): HeadersInit {
    return {
      'Content-Type': 'application/json'
    }
  }
  async getGlobalMetrics(): Promise<GlobalMetrics> {
    try {
      const response = await fetch(`${this.baseUrl}`, {
        method: 'GET',
        headers: this.getHeaders(),
        credentials: 'include',
      })
      if (!response.ok){
        if (response.status == 401) {
          throw new Error ('Authentication required')
        }
        const error = await response.json()
        throw new Error(error.detail || error.error || 'Failed to fetch metrics') 
      }
      return await response.json()
    } catch(error){
      console.error('Error fetching global metrics:', error)
      throw error
    }
  }

  async getMetricsByHostname(appHostname: string): Promise<GlobalMetrics>{
    try {
      const response = await fetch(`${this.baseUrl}?app_hostname=${encodeURIComponent(appHostname)}`, {
        method: 'GET',
        headers: this.getHeaders(),
        credentials: 'include',
      })

      if (!response.ok){
        if (response.status == 401){
          throw new Error ('Authentication required')
        }
        const error = await response.json()
        throw new Error(error.detail || error.error || 'Failed to fetch metrics') 
      }
      return await response.json()
    } catch (error){
      console.error('Error fetching metrics by app_hostname:', error)
      throw error
    }
  }
  // Get metrics for the authenticated user (user_id is extracted from token automatically)
  async getMetricsByUserId(userId: number): Promise<GlobalMetrics>{
    try {
      // Note: user_id is extracted automatically from the JWT token by the API Gateway
      // The userId parameter is kept for API compatibility but not sent as query parameter
      const response = await fetch(`${this.baseUrl}`, {
        method: 'GET',
        headers: this.getHeaders(),
        credentials: 'include',
      })

      if (!response.ok){
        if (response.status == 401){
          throw new Error ('Authentication required')
        }
        if (response.status == 403){
          throw new Error ('Access denied')
        }
        const error = await response.json()
        throw new Error(error.detail || error.error || 'Failed to fetch metrics') 
      }
      return await response.json()
    } catch (error){
      console.error('Error fetching metrics by user_id:', error)
      throw error
    }
  }
}

export const metricsService = new MetricsService()