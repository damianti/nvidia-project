import { NextRequest, NextResponse } from 'next/server'
import { config } from '@/utils/config'

// GET /api/images - Get all images
export async function GET(request: NextRequest) {
  try {
    const cookieHeader = request.headers.get('cookie') || '';

    const response = await fetch(`${config.apiGatewayUrl}/api/images`, {
      headers: {
        'Cookie': cookieHeader,
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    })

    const data = await response.json()

    if (!response.ok) {
      return NextResponse.json(
        { error: data.detail || 'Failed to fetch images' },
        { status: response.status }
      )
    }
    
    const responseToClient = NextResponse.json(data)
    response.headers.forEach((value, key) => {
      if (key.toLowerCase() === 'set-cookie'){
        responseToClient.headers.append("Set-Cookie", value)
      }
    })
    return responseToClient
    
  } catch (error) {
    console.error('Get images API error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

// POST /api/images - Create new image
export async function POST(request: NextRequest) {
  try {
    const cookieHeader = request.headers.get('cookie') || '';

    const body = await request.json()

    const response = await fetch(`${config.apiGatewayUrl}/api/images`, {
      method: 'POST',
      headers: {
        'Cookie': cookieHeader,
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify(body),
    })

    const data = await response.json()

    if (!response.ok) {
      return NextResponse.json(
        { error: data.detail || 'Failed to create image' },
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
    console.error('Create image API error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
} 