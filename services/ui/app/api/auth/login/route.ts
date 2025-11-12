import { NextRequest, NextResponse } from 'next/server'
import { config } from '@/utils/config'

const  API_GATEWAY_EXTERNAL_URL = config.apiGatewayUrl

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { email, password } = body

    // Validate input
    if (!email || !password) {
      return NextResponse.json(
        { error: 'Email and password are required' },
        { status: 400 }
      )
    }

    // Forward request to API Gateway
    const response = await fetch(`${API_GATEWAY_EXTERNAL_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    })

    const data = await response.json()

    if (!response.ok) {
      return NextResponse.json(
        { error: data.detail || 'Login failed' },
        { status: response.status }
      )
    }

    // Set JWT token in cookies
    const responseWithCookie = NextResponse.json(
      { message: 'Login successful', user: data.user },
      { status: 200 }
    )

    responseWithCookie.cookies.set('auth-token', data.access_token, {
      httpOnly: true,
      secure: false, // Allow HTTP for development
      sameSite: 'lax',
      path: '/',
      maxAge: 60 * 60 * 24 * 7, // 7 days
    })

    return responseWithCookie

  } catch (error) {
    console.error('Login API error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
} 