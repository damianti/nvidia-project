import { NextRequest, NextResponse } from 'next/server'
import { config } from '@/utils/config'

// Helper function to get auth token from cookies
function getAuthToken(request: NextRequest): string | null {
  return request.cookies.get('auth-token')?.value || null
}

// Helper function to get user_id from token via /auth/me
async function getUserId(token: string): Promise<number | null> {
  try {
    const response = await fetch(`${config.apiGatewayUrl}/auth/me`, {
      headers: {
        'Authorization': `Bearer ${token}`,
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

// GET /api/billing/images - Get billing summaries for all images
export async function GET(request: NextRequest) {
  try {
    const token = getAuthToken(request)
    
    if (!token) {
      return NextResponse.json(
        { error: 'Authentication required' },
        { status: 401 }
      )
    }

    // Get user_id from token
    const userId = await getUserId(token)
    if (!userId) {
      return NextResponse.json(
        { error: 'Failed to get user information' },
        { status: 401 }
      )
    }

    // Call billing service directly (not through API Gateway)
    const billingServiceUrl = process.env.BILLING_SERVICE_URL || 'http://billing:3007'
    const response = await fetch(`${billingServiceUrl}/images`, {
      headers: {
        'X-User-Id': userId.toString(),
        'Content-Type': 'application/json',
      },
    })

    const data = await response.json()

    if (!response.ok) {
      return NextResponse.json(
        { error: data.detail || 'Failed to fetch billing summaries' },
        { status: response.status }
      )
    }

    return NextResponse.json(data)

  } catch (error) {
    console.error('Get billing summaries API error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}


