import { NextRequest, NextResponse } from 'next/server'
import { config } from '@/utils/config'

// GET /api/images/with-containers - Get all images with their containers
export async function GET(request: NextRequest) {
  try {
    const cookieHeader = request.headers.get('cookie') || ''

    const response = await fetch(`${config.apiGatewayUrl}/api/images/with-containers`, {
      headers: {
        'Cookie': cookieHeader,
        'Content-Type': 'application/json',
      },
    })

    const data = await response.json()

    if (!response.ok) {
      return NextResponse.json(
        { error: data.detail || 'Failed to fetch images with containers' },
        { status: response.status }
      )
    }

    const responseToClient = NextResponse.json(data)
    response.headers.forEach((value, key) => {
      if (key.toLowerCase() === 'set-cookie') {
        responseToClient.headers.append('Set-Cookie', value)
      }
    })

    return responseToClient

  } catch (error) {
    console.error('Get images with containers API error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

