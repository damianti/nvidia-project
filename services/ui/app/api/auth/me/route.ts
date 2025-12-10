import { NextRequest, NextResponse } from 'next/server'
import { config } from '@/utils/config'

// GET /api/auth/me - Get current user info
export async function GET(request: NextRequest) {
  try {
    const cookieHeader = request.headers.get('cookie') || ''

    // Forward request to API Gateway with cookies
    const response = await fetch(`${config.apiGatewayUrl}/auth/me`, {
      headers: {
        'Cookie': cookieHeader,
        'Content-Type': 'application/json',
      },
    })

    const data = await response.json()

    if (!response.ok) {
      return NextResponse.json(
        { error: data.detail || 'Invalid token' },
        { status: response.status }
      )
    }

    const responseToClient = NextResponse.json(data)
    // Copy Set-Cookie headers from backend if any
    response.headers.forEach((value, key) => {
      if (key.toLowerCase() === 'set-cookie') {
        responseToClient.headers.append('Set-Cookie', value)
      }
    })

    return responseToClient

  } catch (error) {
    console.error('Auth me API error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
} 