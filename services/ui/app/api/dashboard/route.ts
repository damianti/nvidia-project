import { NextRequest, NextResponse } from 'next/server'
import { config } from '@/utils/config'

// GET /api/dashboard - Get dashboard statistics
export async function GET(request: NextRequest) {
  try {
    const cookieHeader = request.headers.get('cookie') || ''

    // Fetch images and containers in parallel
    const [imagesResponse, containersResponse] = await Promise.all([
      fetch(`${config.apiGatewayUrl}/api/images`, {
        headers: {
          'Cookie': cookieHeader,
          'Content-Type': 'application/json',
        },
      }),
      fetch(`${config.apiGatewayUrl}/api/containers`, {
        headers: {
          'Cookie': cookieHeader,
          'Content-Type': 'application/json',
        },
      })
    ])

    const images = await imagesResponse.json()
    const containers = await containersResponse.json()

    if (!imagesResponse.ok || !containersResponse.ok) {
      return NextResponse.json(
        { error: 'Failed to fetch dashboard data' },
        { status: 500 }
      )
    }

    // Calculate statistics
    const totalImages = images.length
    const totalContainers = containers.length
    const runningContainers = containers.filter((c: any) => c.status === 'running').length

    // Generate recent activity (mock for now)
    const recentActivity = [
      {
        id: '1',
        type: 'container' as const,
        action: 'Started nginx:latest',
        timestamp: '2 minutes ago'
      },
      {
        id: '2',
        type: 'image' as const,
        action: 'Pulled python:3.9',
        timestamp: '5 minutes ago'
      },
      {
        id: '3',
        type: 'container' as const,
        action: 'Stopped redis:alpine',
        timestamp: '10 minutes ago'
      }
    ]

    const dashboardData = {
      totalImages,
      totalContainers,
      runningContainers,
      recentActivity
    }

    const responseToClient = NextResponse.json(dashboardData)
    // Copy Set-Cookie headers from either response if any
    imagesResponse.headers.forEach((value, key) => {
      if (key.toLowerCase() === 'set-cookie') {
        responseToClient.headers.append('Set-Cookie', value)
      }
    })
    containersResponse.headers.forEach((value, key) => {
      if (key.toLowerCase() === 'set-cookie') {
        responseToClient.headers.append('Set-Cookie', value)
      }
    })

    return responseToClient

  } catch (error) {
    console.error('Dashboard API error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
} 