import { NextRequest, NextResponse } from 'next/server'
import { config } from '@/utils/config'

// GET /api/metrics - Proxy metrics request to API Gateway
export async function GET(request: NextRequest) {
  try {
    const cookieHeader = request.headers.get('cookie') || ''
    
    // Get query parameters from request
    const searchParams = request.nextUrl.searchParams
    const queryString = searchParams.toString()
    const url = queryString 
      ? `${config.apiGatewayUrl}/api/metrics?${queryString}`
      : `${config.apiGatewayUrl}/api/metrics`

    const response = await fetch(url, {
      headers: {
        'Cookie': cookieHeader,
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: errorData.detail || errorData.error || 'Failed to fetch metrics' },
        { status: response.status }
      )
    }

    const data = await response.json()
    const responseToClient = NextResponse.json(data)
    
    // Copy Set-Cookie headers from backend if any
    response.headers.forEach((value, key) => {
      if (key.toLowerCase() === 'set-cookie') {
        responseToClient.headers.append('Set-Cookie', value)
      }
    })

    return responseToClient
  } catch (error) {
    console.error('Error proxying metrics request:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}