import { NextRequest, NextResponse } from 'next/server'
import { config } from '@/utils/config'

// Helper function to get auth token from cookies
function getAuthToken(request: NextRequest): string | null {
  return request.cookies.get('auth-token')?.value || null
}

// GET /api/dashboard - Get dashboard statistics
export async function GET(request: NextRequest) {
  try {
    const token = getAuthToken(request)
    
    if (!token) {
      return NextResponse.json(
        { error: 'Authentication required' },
        { status: 401 }
      )
    }

    // Fetch images and containers in parallel
    const [imagesResponse, containersResponse] = await Promise.all([
      fetch(`${config.apiGatewayUrl}/api/images`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      }),
      fetch(`${config.apiGatewayUrl}/api/containers`, {
        headers: {
          'Authorization': `Bearer ${token}`,
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

    return NextResponse.json(dashboardData)

  } catch (error) {
    console.error('Dashboard API error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
} 