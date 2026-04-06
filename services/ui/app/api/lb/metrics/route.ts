import { NextRequest, NextResponse } from 'next/server'
import { config } from '@/utils/config'

// GET /api/lb/metrics - Proxy load-balancer metrics to API Gateway
export async function GET(request: NextRequest) {
  try {
    const cookieHeader = request.headers.get('cookie') || ''

    const response = await fetch(`${config.apiGatewayUrl}/api/lb/metrics`, {
      headers: {
        'Cookie': cookieHeader,
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: errorData.detail || errorData.error || 'Failed to fetch LB metrics' },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Error proxying LB metrics request:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
