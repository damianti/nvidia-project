import { NextRequest, NextResponse } from 'next/server'
import { config } from '@/utils/config'

// POST /api/images/[id]/containers - Create containers for a specific image
export async function POST(
  request: NextRequest,
  { params }: { params: Promise <{ id: string } >}
) {
  try {
    const { id } = await params
    const cookieHeader = request.headers.get('cookie') || ''
    const body = await request.json()

    // Forward request to api gateway
    const response = await fetch(`${config.apiGatewayUrl}/api/containers/${id}/create`, {
      method: 'POST',
      headers: {
        'Cookie': cookieHeader,
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

    const responseToClient = NextResponse.json(data, { status: 201 })
    response.headers.forEach((value, key) => {
      if (key.toLowerCase() === 'set-cookie') {
        responseToClient.headers.append('Set-Cookie', value)
      }
    })

    return responseToClient

  } catch (error) {
    console.error('Create containers API error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}




