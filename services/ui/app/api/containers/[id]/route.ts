import { NextRequest, NextResponse } from 'next/server'
import { config } from '@/utils/config'

// GET /api/containers/[id] - Get specific container
export async function GET(
  request: NextRequest,
  { params }: { params: Promise <{ id: string }> }
) {
  try {
    const { id } = await params
    const cookieHeader = request.headers.get('cookie') || ''

    const response = await fetch(`${config.apiGatewayUrl}/api/containers/${id}`, {
      headers: {
        'Cookie': cookieHeader,
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

    const responseToClient = NextResponse.json(data)
    response.headers.forEach((value, key) => {
      if (key.toLowerCase() === 'set-cookie') {
        responseToClient.headers.append('Set-Cookie', value)
      }
    })

    return responseToClient

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
    const { id } = await params
    const cookieHeader = request.headers.get('cookie') || ''
    const body = await request.json()

    const response = await fetch(`${config.apiGatewayUrl}/api/containers/${id}`, {
      method: 'PUT',
      headers: {
        'Cookie': cookieHeader,
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

    const responseToClient = NextResponse.json(data)
    response.headers.forEach((value, key) => {
      if (key.toLowerCase() === 'set-cookie') {
        responseToClient.headers.append('Set-Cookie', value)
      }
    })

    return responseToClient

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
    const { id } = await params
    const cookieHeader = request.headers.get('cookie') || ''

    const response = await fetch(`${config.apiGatewayUrl}/api/containers/${id}`, {
      method: 'DELETE',
      headers: {
        'Cookie': cookieHeader,
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

    const responseToClient = NextResponse.json(
      { message: 'Container deleted successfully' },
      { status: 200 }
    )
    response.headers.forEach((value, key) => {
      if (key.toLowerCase() === 'set-cookie') {
        responseToClient.headers.append('Set-Cookie', value)
      }
    })

    return responseToClient

  } catch (error) {
    console.error('Delete container API error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
} 