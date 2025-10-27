import { NextRequest, NextResponse } from 'next/server'

const  API_GATEWAY_EXTERNAL_URL = process.env.API_GATEWAY_EXTERNAL_URL || 'http://localhost:8080'


// Helper function to get auth token from cookies
function getAuthToken(request: NextRequest): string | null {
  return request.cookies.get('auth-token')?.value || null
}

// POST /api/containers/[id]/start - Start container
export async function POST(
  request: NextRequest,
  { params }: { params: Promise <{ id: string } >}
) {
  try {
    const token = getAuthToken(request)
    const {id} = await params;
    if (!token) {
      return NextResponse.json(
        { error: 'Authentication required' },
        { status: 401 }
      )
    }

    const response = await fetch(`${API_GATEWAY_EXTERNAL_URL}/api/containers/${id}/start`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    })

    const data = await response.json()

    if (!response.ok) {
      return NextResponse.json(
        { error: data.detail || 'Failed to start container' },
        { status: response.status }
      )
    }

    return NextResponse.json(data)

  } catch (error) {
    console.error('Start container API error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
} 