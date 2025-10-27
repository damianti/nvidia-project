import { NextRequest, NextResponse } from 'next/server'

const  API_GATEWAY_EXTERNAL_URL = process.env.API_GATEWAY_EXTERNAL_URL || 'http://localhost:8080'

// Helper function to get auth token from cookies
function getAuthToken(request: NextRequest): string | null {
  return request.cookies.get('auth-token')?.value || null
}

// POST /api/images/[id]/containers - Create containers for a specific image
export async function POST(
  request: NextRequest,
  { params }: { params: Promise <{ id: string } >}
) {
  try {
    const token = getAuthToken(request)
    const {id} = await params
    if (!token) {
      return NextResponse.json(
        { error: 'Authentication required' },
        { status: 401 }
      )
    }

    const body = await request.json()
    const imageId = id

    // Forward request to Orchestrator
    const response = await fetch(`${API_GATEWAY_EXTERNAL_URL}/api/images/${imageId}/containers`, {
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
        { error: data.detail || 'Failed to create containers' },
        { status: response.status }
      )
    }

    return NextResponse.json(data, { status: 201 })

  } catch (error) {
    console.error('Create containers API error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}




