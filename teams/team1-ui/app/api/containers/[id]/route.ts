import { NextRequest, NextResponse } from 'next/server'

const  API_GATEWAY_EXTERNAL_URL = process.env.API_GATEWAY_EXTERNAL_URL || 'http://localhost:8080'

// Helper function to get auth token from cookies
function getAuthToken(request: NextRequest): string | null {
  return request.cookies.get('auth-token')?.value || null
}

// GET /api/containers/[id] - Get specific container
export async function GET(
  request: NextRequest,
  { params }: { params: Promise <{ id: string }> }
) {
  try {
    const { id } = await params;
    const token = getAuthToken(request)
    
    if (!token) {
      return NextResponse.json(
        { error: 'Authentication required' },
        { status: 401 }
      )
    }

    const response = await fetch(`${API_GATEWAY_EXTERNAL_URL}/api/containers/${id}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    })

    const data = await response.json()

    if (!response.ok) {
      return NextResponse.json(
        { error: data.detail || 'Container not found' },
        { status: response.status }
      )
    }

    return NextResponse.json(data)

  } catch (error) {
    console.error('Get container API error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

// PUT /api/containers/[id] - Update container
export async function PUT(
  request: NextRequest,
  { params }: { params: Promise <{ id: string } >}
) {
  try {
    const token = getAuthToken(request)
    const { id } = await params;
    if (!token) {
      return NextResponse.json(
        { error: 'Authentication required' },
        { status: 401 }
      )
    }

    const body = await request.json()

    const response = await fetch(`${API_GATEWAY_EXTERNAL_URL}/api/containers/${id}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })

    const data = await response.json()

    if (!response.ok) {
      return NextResponse.json(
        { error: data.detail || 'Failed to update container' },
        { status: response.status }
      )
    }

    return NextResponse.json(data)

  } catch (error) {
    console.error('Update container API error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

// DELETE /api/containers/[id] - Delete container
export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise <{ id: string }> }
) {
  try {
    const token = getAuthToken(request)
    const { id } = await params;
    if (!token) {
      return NextResponse.json(
        { error: 'Authentication required' },
        { status: 401 }
      )
    }

    const response = await fetch(`${API_GATEWAY_EXTERNAL_URL}/api/containers/${id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      const data = await response.json()
      return NextResponse.json(
        { error: data.detail || 'Failed to delete container' },
        { status: response.status }
      )
    }

    return NextResponse.json(
      { message: 'Container deleted successfully' },
      { status: 200 }
    )

  } catch (error) {
    console.error('Delete container API error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
} 