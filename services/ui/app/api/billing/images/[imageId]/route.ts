import { NextRequest, NextResponse } from 'next/server'
import { config } from '@/utils/config'

// Helper function to get user_id from cookies via /auth/me
async function getUserId(cookieHeader: string): Promise<number | null> {
  try {
    const response = await fetch(`${config.apiGatewayUrl}/auth/me`, {
      headers: {
        'Cookie': cookieHeader,
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      return null
    }

    const userData = await response.json()
    return userData.id || null
  } catch (error) {
    console.error('Error getting user_id:', error)
    return null
  }
}

// GET /api/billing/images/[imageId] - Get detailed billing for a specific image
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ imageId: string }> }
) {
  try {
    const cookieHeader = request.headers.get('cookie') || ''

    // Get user_id from cookies
    const userId = await getUserId(cookieHeader)
    if (!userId) {
      return NextResponse.json(
        { error: 'Failed to get user information' },
        { status: 401 }
      )
    }

    const { imageId } = await params
    const imageIdNum = parseInt(imageId, 10)
    
    if (isNaN(imageIdNum)) {
      return NextResponse.json(
        { error: 'Invalid image ID' },
        { status: 400 }
      )
    }

    // Call billing service directly (not through API Gateway)
    const billingServiceUrl = process.env.BILLING_SERVICE_URL || 'http://billing:3007'
    const response = await fetch(`${billingServiceUrl}/images/${imageIdNum}`, {
      headers: {
        'X-User-Id': userId.toString(),
        'Content-Type': 'application/json',
      },
    })

    const data = await response.json()

    if (!response.ok) {
      return NextResponse.json(
        { error: data.detail || 'Failed to fetch billing detail' },
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
    console.error('Get billing detail API error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}


