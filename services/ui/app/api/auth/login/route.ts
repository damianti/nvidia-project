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
    const nextResponse = NextResponse.json(
      { user: data.user },
      { status: 200 }
    )
    const setCookieHeader = response.headers.get('set-cookie');
    if (setCookieHeader){
      nextResponse.headers.set('Set-Cookie', setCookieHeader)
    }
    return nextResponse;

  } catch (error) {
    console.error('Login API error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
} 