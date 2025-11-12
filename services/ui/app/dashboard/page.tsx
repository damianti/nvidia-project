'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import Navbar from '@/components/Navbar'
import { useAuth } from '@/contexts/AuthContext'
import LoadingSpinner from '@/components/LoadingSpinner'

interface DashboardStats {
  totalImages: number
  runningContainers: number
  totalContainers: number
  recentActivity: Array<{
    id: string
    type: 'image' | 'container'
    action: string
    timestamp: string
  }>
}

export default function DashboardPage() {
  const router = useRouter()
  const { user, loading: authLoading } = useAuth()

  useEffect(() => {
    if (!authLoading && !user){
      router.push('/login')
    }
  }, [authLoading, user, router])

  if (authLoading) {
    return <LoadingSpinner />
  }
  
  if (!user){
    return null
  }

  return (
    <div className="min-h-screen p-4">
      <Navbar />
      {/* Main Content */}
      <div className="max-w-7xl mx-auto mt-8">
        <div className="modern-card p-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Welcome, {user.username}!
          </h1>
          <p className="text-lg text-gray-600 mb-8">
            Manage your Docker images and containers from one place.
          </p>
          
          {/* Quick Actions */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Link href="/images" className="group">
              <div className="stats-card hover:shadow-xl transition-all duration-300 cursor-pointer">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-blue-600 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform">
                      <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                    </div>
                  </div>
                  <div className="ml-6">
                    <p className="text-2xl font-bold text-gray-900">Images</p>
                    <p className="text-sm text-gray-600 mt-1">View and manage Docker images</p>
                  </div>
                </div>
              </div>
            </Link>

            <Link href="/containers" className="group">
              <div className="stats-card hover:shadow-xl transition-all duration-300 cursor-pointer">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-16 h-16 bg-gradient-to-r from-green-500 to-green-600 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform">
                      <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                      </svg>
                    </div>
                  </div>
                  <div className="ml-6">
                    <p className="text-2xl font-bold text-gray-900">Containers</p>
                    <p className="text-sm text-gray-600 mt-1">View and manage Docker containers</p>
                  </div>
                </div>
              </div>
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
} 