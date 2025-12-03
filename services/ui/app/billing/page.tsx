'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { billingService, BillingSummary } from '@/services/billingService'
import { containerService, ImageWithContainers } from '@/services/containerService'
import { useAuth } from '@/contexts/AuthContext'
import Navbar from '@/components/Navbar'
import LoadingSpinner from '@/components/LoadingSpinner'

export default function BillingPage() {
  const router = useRouter()
  const { user, loading: authLoading } = useAuth()
  const [summaries, setSummaries] = useState<BillingSummary[]>([])
  const [images, setImages] = useState<ImageWithContainers[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login')
    }
    if (user) {
      fetchData()
    }
  }, [authLoading, user, router])

  const fetchData = async () => {
    try {
      setLoading(true)
      setError('')
      const [fetchedSummaries, fetchedImages] = await Promise.all([
        billingService.getAllBillingSummaries(),
        containerService.getImagesWithContainers(),
      ])
      setSummaries(fetchedSummaries)
      setImages(fetchedImages)
    } catch (error) {
      console.error('Error fetching billing summaries:', error)
      setError(error instanceof Error ? error.message : 'Failed to load billing information. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount)
  }

  const getImageDisplay = (imageId: number): string => {
    const image = images.find((img) => img.id === imageId)
    if (!image) {
      return `Image #${imageId}`
    }

    const base = `${image.name}:${image.tag}`
    if (image.website_url) {
      return `${base} → ${image.website_url}`
    }
    return base
  }

  const formatDate = (dateString: string | null): string => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleString()
  }

  const formatMinutes = (minutes: number): string => {
    if (minutes < 60) {
      return `${minutes} min`
    }
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`
  }

  if (authLoading) {
    return <LoadingSpinner />
  }
  if (!user) {
    return null
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="modern-card p-8 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <div className="text-xl text-gray-700">Loading billing information...</div>
        </div>
      </div>
    )
  }

  // Calculate totals
  const totalCost = summaries.reduce((sum, s) => sum + s.total_cost, 0)
  const totalContainers = summaries.reduce((sum, s) => sum + s.total_containers, 0)
  const totalMinutes = summaries.reduce((sum, s) => sum + s.total_minutes, 0)
  const activeContainers = summaries.reduce((sum, s) => sum + s.active_containers, 0)

  return (
    <div className="min-h-screen p-4">
      <Navbar/>

      {/* Error Message */}
      {error && (
        <div className="max-w-7xl mx-auto mb-6">
          <div className="modern-card p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center">
              <svg className="w-5 h-5 text-red-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
              <p className="text-red-700 font-medium">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="max-w-7xl mx-auto">
        {/* Header with Total Summary */}
        <div className="modern-card p-8 mb-6 fade-in">
          <h1 className="text-3xl font-bold text-gray-900 mb-6">Billing Overview</h1>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-gradient-to-r from-blue-50 to-blue-100 p-6 rounded-xl">
              <div className="text-sm font-semibold text-blue-700 mb-1">Total Cost</div>
              <div className="text-2xl font-bold text-blue-900">{formatCurrency(totalCost)}</div>
            </div>
            <div className="bg-gradient-to-r from-green-50 to-green-100 p-6 rounded-xl">
              <div className="text-sm font-semibold text-green-700 mb-1">Total Containers</div>
              <div className="text-2xl font-bold text-green-900">{totalContainers}</div>
            </div>
            <div className="bg-gradient-to-r from-purple-50 to-purple-100 p-6 rounded-xl">
              <div className="text-sm font-semibold text-purple-700 mb-1">Total Usage</div>
              <div className="text-2xl font-bold text-purple-900">{formatMinutes(totalMinutes)}</div>
            </div>
            <div className="bg-gradient-to-r from-orange-50 to-orange-100 p-6 rounded-xl">
              <div className="text-sm font-semibold text-orange-700 mb-1">Active Containers</div>
              <div className="text-2xl font-bold text-orange-900">{activeContainers}</div>
            </div>
          </div>
        </div>

        {/* Billing by Image */}
        {summaries.length > 0 ? (
          <div className="modern-card p-8 fade-in">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Billing by Image</h2>
            <div className="space-y-4">
              {summaries.map((summary) => (
                <div key={summary.image_id} className="modern-card p-6 hover:scale-[1.01] transition-transform">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-green-600 rounded-xl flex items-center justify-center">
                        <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </div>
                      <div>
                        <div className="flex items-center space-x-3">
                          <h3 className="text-lg font-semibold text-gray-900">
                            {getImageDisplay(summary.image_id)}
                          </h3>
                          <span className="text-xs text-gray-400">
                            (ID: {summary.image_id})
                          </span>
                          {summary.active_containers > 0 && (
                            <span className="status-badge status-registered">
                              {summary.active_containers} Active
                            </span>
                          )}
                        </div>
                        <div className="mt-2 flex items-center space-x-4 text-sm text-gray-600">
                          <span>Containers: {summary.total_containers}</span>
                          <span>•</span>
                          <span>Usage: {formatMinutes(summary.total_minutes)}</span>
                          <span>•</span>
                          <span>Cost: {formatCurrency(summary.total_cost)}</span>
                          {summary.last_activity && (
                            <>
                              <span>•</span>
                              <span>Last Activity: {formatDate(summary.last_activity)}</span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                    <Link
                      href={`/billing/${summary.image_id}`}
                      className="btn-modern"
                    >
                      View Details
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="modern-card p-12 text-center fade-in">
            <div className="w-24 h-24 bg-gradient-to-r from-green-500 to-green-600 rounded-3xl flex items-center justify-center mx-auto mb-6">
              <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-2">No billing records yet</h3>
            <p className="text-gray-600 mb-8">Billing information will appear here once you create and use containers.</p>
            <Link href="/images" className="btn-modern">
              Go to Images
            </Link>
          </div>
        )}
      </div>
    </div>
  )
}


