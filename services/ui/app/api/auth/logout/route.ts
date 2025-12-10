import { NextRequest, NextResponse } from 'next/server'
import { config } from '@/utils/config'

export async function POST(request: NextRequest) {
  try {
    const cookieHeader = request.headers.get('cookie') || ''

    // Forward logout request to backend (which will delete the cookie)
    const response = await fetch(`${config.apiGatewayUrl}/auth/logout`, {
      method: 'POST',
      headers: {
        'Cookie': cookieHeader,
        'Content-Type': 'application/json',
      },
    })

    const data = await response.json()

    const nextResponse = NextResponse.json(
      { message: data.message || 'Logout successful' },
      { status: response.ok ? 200 : response.status }
    )

    // Copy Set-Cookie header from backend (which deletes the cookie)
    const setCookieHeader = response.headers.get('set-cookie')
    if (setCookieHeader) {
      nextResponse.headers.set('Set-Cookie', setCookieHeader)
    }

    return nextResponse

  } catch (error) {
    console.error('Logout API error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
} 