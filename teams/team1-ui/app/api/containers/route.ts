import { NextRequest, NextResponse } from 'next/server'

const  API_GATEWAY_EXTERNAL_URL = process.env.API_GATEWAY_EXTERNAL_URL || 'http://localhost:8080'


// Helper function to get auth token from cookies
function getAuthToken(request: NextRequest): string | null {
  return request.cookies.get('auth-token')?.value || null
}

// GET /api/containers - Get all containers
export async function GET(request: NextRequest) {
  try {
    const token = getAuthToken(request)
    
    if (!token) {
      return NextResponse.json(
        { error: 'Authentication required' },
        { status: 401 }
      )
    }

    const response = await fetch(`${API_GATEWAY_EXTERNAL_URL}/api/containers`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    })

    const data = await response.json()

    if (!response.ok) {
      return NextResponse.json(
        { error: data.detail || 'Failed to fetch containers' },
        { status: response.status }
      )
    }

    return NextResponse.json(data)

  } catch (error) {
    console.error('Get containers API error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

// POST /api/containers - Create new container
export async function POST(request: NextRequest) {
  try {
    const token = getAuthToken(request)
    
    if (!token) {
      return NextResponse.json(
        { error: 'Authentication required' },
        { status: 401 }
      )
    }

    const body = await request.json()

    const response = await fetch(`${API_GATEWAY_EXTERNAL_URL}/api/containers`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })

    const data = await response.json()

    if (!response.ok) {
      return NextResponse.json(
        { error: data.detail || 'Failed to create container' },
        { status: response.status }
      )
    }

    return NextResponse.json(data, { status: 201 })

  } catch (error) {
    console.error('Create container API error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
} 