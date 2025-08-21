'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

interface Container {
  id: number
  container_id: string
  name: string
  port: number
  status: string
  cpu_usage: string
  memory_usage: string
  created_at: string
  image: {
    name: string
    tag: string
  }
}

export default function ContainersPage() {
  const [containers, setContainers] = useState<Container[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // TODO: Fetch containers from API
    const fetchContainers = async () => {
      try {
        // Mock data for now
        setContainers([
          {
            id: 1,
            container_id: 'abc123def456',
            name: 'nginx-web-server',
            port: 8080,
            status: 'running',
            cpu_usage: '0.3',
            memory_usage: '45m',
            created_at: '2024-01-15T10:30:00Z',
            image: { name: 'nginx', tag: 'latest' }
          },
          {
            id: 2,
            container_id: 'def789ghi012',
            name: 'python-api',
            port: 5000,
            status: 'running',
            cpu_usage: '0.7',
            memory_usage: '120m',
            created_at: '2024-01-14T15:45:00Z',
            image: { name: 'python', tag: '3.9' }
          },
          {
            id: 3,
            container_id: 'ghi345jkl678',
            name: 'redis-cache',
            port: 6379,
            status: 'stopped',
            cpu_usage: '0.0',
            memory_usage: '0m',
            created_at: '2024-01-13T09:20:00Z',
            image: { name: 'redis', tag: 'alpine' }
          }
        ])
      } catch (error) {
        console.error('Error fetching containers:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchContainers()
  }, [])

  const handleStart = async (containerId: number) => {
    // TODO: Call start API
    console.log('Start container:', containerId)
  }

  const handleStop = async (containerId: number) => {
    // TODO: Call stop API
    console.log('Stop container:', containerId)
  }

  const handleDelete = async (containerId: number) => {
    if (confirm('Are you sure you want to delete this container?')) {
      // TODO: Call delete API
      console.log('Delete container:', containerId)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="modern-card p-8 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <div className="text-xl text-gray-700">Loading containers...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen p-4">
      {/* Header */}
      <div className="modern-nav rounded-2xl mb-8">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent">
                Containers
              </h1>
              <p className="mt-2 text-gray-600">
                Monitor and manage your running containers
              </p>
            </div>
            <div className="flex space-x-4">
              <Link
                href="/dashboard"
                className="btn-modern"
              >
                Back to Dashboard
              </Link>
              <Link
                href="/images"
                className="btn-modern"
              >
                Manage Images
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto">
        {/* Stats Summary */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="stats-card fade-in">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-green-600 rounded-xl flex items-center justify-center">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
                  </svg>
                </div>
              </div>
              <div className="ml-6">
                <p className="text-sm font-medium text-gray-600">Running</p>
                <p className="text-3xl font-bold text-gray-900">
                  {containers.filter(c => c.status === 'running').length}
                </p>
              </div>
            </div>
          </div>

          <div className="stats-card fade-in">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-gradient-to-r from-red-500 to-red-600 rounded-xl flex items-center justify-center">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </div>
              </div>
              <div className="ml-6">
                <p className="text-sm font-medium text-gray-600">Stopped</p>
                <p className="text-3xl font-bold text-gray-900">
                  {containers.filter(c => c.status === 'stopped').length}
                </p>
              </div>
            </div>
          </div>

          <div className="stats-card fade-in">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-blue-600 rounded-xl flex items-center justify-center">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
              </div>
              <div className="ml-6">
                <p className="text-sm font-medium text-gray-600">Total CPU</p>
                <p className="text-3xl font-bold text-gray-900">
                  {containers.reduce((sum, c) => sum + parseFloat(c.cpu_usage), 0).toFixed(1)}
                </p>
              </div>
            </div>
          </div>

          <div className="stats-card fade-in">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-purple-600 rounded-xl flex items-center justify-center">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4" />
                  </svg>
                </div>
              </div>
              <div className="ml-6">
                <p className="text-sm font-medium text-gray-600">Total Memory</p>
                <p className="text-3xl font-bold text-gray-900">
                  {containers.reduce((sum, c) => {
                    const mem = parseInt(c.memory_usage.replace('m', '').replace('g', '000'))
                    return sum + mem
                  }, 0)}m
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Containers List */}
        {containers.length > 0 ? (
          <div className="modern-card p-8 fade-in">
            <h3 className="text-2xl font-bold text-gray-900 mb-6">Your Containers</h3>
            <div className="space-y-6">
              {containers.map((container) => (
                <div key={container.id} className="modern-card p-6 hover:scale-[1.02] transition-transform">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-green-600 rounded-xl flex items-center justify-center">
                        <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
                        </svg>
                      </div>
                      <div>
                        <div className="flex items-center space-x-3">
                          <h4 className="text-lg font-semibold text-gray-900">
                            {container.name}
                          </h4>
                          <span className={`status-badge ${
                            container.status === 'running' ? 'status-running' : 'status-stopped'
                          }`}>
                            {container.status}
                          </span>
                        </div>
                        <div className="mt-2 flex items-center space-x-4 text-sm text-gray-600">
                          <span>Image: {container.image.name}:{container.image.tag}</span>
                          <span>•</span>
                          <span>Port: {container.port}</span>
                          <span>•</span>
                          <span>CPU: {container.cpu_usage}</span>
                          <span>•</span>
                          <span>Memory: {container.memory_usage}</span>
                          <span>•</span>
                          <span>Created: {new Date(container.created_at).toLocaleDateString()}</span>
                        </div>
                        <div className="mt-1 text-xs text-gray-400">
                          ID: {container.container_id}
                        </div>
                      </div>
                    </div>
                    <div className="flex space-x-3">
                                             {container.status === 'running' ? (
                         <button
                           onClick={() => handleStop(container.id)}
                           className="btn-modern"
                         >
                           Stop
                         </button>
                       ) : (
                         <button
                           onClick={() => handleStart(container.id)}
                           className="btn-modern"
                         >
                           Start
                         </button>
                       )}
                       <button
                         onClick={() => handleDelete(container.id)}
                         className="btn-modern"
                       >
                         Delete
                       </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="modern-card p-12 text-center fade-in">
            <div className="w-24 h-24 bg-gradient-to-r from-green-500 to-blue-600 rounded-3xl flex items-center justify-center mx-auto mb-6">
              <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
              </svg>
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-2">No containers yet</h3>
            <p className="text-gray-600 mb-8">Start by creating containers from your images.</p>
            <Link
              href="/images"
              className="btn-modern"
            >
              Manage Images
            </Link>
          </div>
        )}
      </div>
    </div>
  )
} 