'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter, useParams } from 'next/navigation'
import { billingService, BillingDetail } from '@/services/billingService'
import { containerService, ImageWithContainers } from '@/services/containerService'
import { useAuth } from '@/contexts/AuthContext'
import Navbar from '@/components/Navbar'
import LoadingSpinner from '@/components/LoadingSpinner'

export default function BillingDetailPage() {
  const router = useRouter()
  const params = useParams()
  const { user, loading: authLoading } = useAuth()
  const [billingDetail, setBillingDetail] = useState<BillingDetail | null>(null)
  const [images, setImages] = useState<ImageWithContainers[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const imageId = params?.imageId ? parseInt(params.imageId as string, 10) : null

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login')
      return
    }
    if (user && imageId && !isNaN(imageId)) {
      fetchData(imageId)
    } else {
      setError('Invalid image ID')
      setLoading(false)
    }
  }, [authLoading, user, router, imageId])

  const fetchData = async (imageId: number) => {
    try {
      setLoading(true)
      setError('')
      const [detail, fetchedImages] = await Promise.all([
        billingService.getImageBilling(imageId),
        containerService.getImagesWithContainers(),
      ])
      setBillingDetail(detail)
      setImages(fetchedImages)
    } catch (error) {
      console.error('Error fetching billing detail:', error)
      setError(error instanceof Error ? error.message : 'Failed to load billing detail. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const formatCurrency = (amount: number | null): string => {
    if (amount === null) return 'N/A'
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

  const formatMinutes = (minutes: number | null): string => {
    if (minutes === null) return 'N/A'
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
          <div className="text-xl text-gray-700">Loading billing detail...</div>
        </div>
      </div>
    )
  }

  if (error && !billingDetail) {
    return (
      <div className="min-h-screen p-4">
        <Navbar/>
        <div className="max-w-7xl mx-auto">
          <div className="modern-card p-8 text-center">
            <div className="text-red-600 mb-4">{error}</div>
            <Link href="/billing" className="btn-modern">
              Back to Billing
            </Link>
          </div>
        </div>
      </div>
    )
  }

  if (!billingDetail) {
    return null
  }

  const { summary, containers } = billingDetail

  return (
    <div className="min-h-screen p-4">
      <Navbar/>

      {/* Error Message */}
      {error && (
        <div className="max-w-7xl mx-auto mb-6">
          <div className="modern-card p-4 bg-red-50 border border-red-200">
            <p className="text-red-600">{error}</p>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="max-w-7xl mx-auto">
        {/* Back Button */}
        <div className="mb-6">
          <Link href="/billing" className="text-blue-600 hover:text-blue-800 flex items-center">
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Billing Overview
          </Link>
        </div>

        {/* Summary Card */}
        <div className="modern-card p-8 mb-6 fade-in">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Billing Detail - {getImageDisplay(summary.image_id)}
          </h1>
          <p className="text-sm text-gray-500 mb-6">
            Image ID: {summary.image_id}
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-gradient-to-r from-blue-50 to-blue-100 p-6 rounded-xl">
              <div className="text-sm font-semibold text-blue-700 mb-1">Total Cost</div>
              <div className="text-2xl font-bold text-blue-900">{formatCurrency(summary.total_cost)}</div>
            </div>
            <div className="bg-gradient-to-r from-green-50 to-green-100 p-6 rounded-xl">
              <div className="text-sm font-semibold text-green-700 mb-1">Total Containers</div>
              <div className="text-2xl font-bold text-green-900">{summary.total_containers}</div>
            </div>
            <div className="bg-gradient-to-r from-purple-50 to-purple-100 p-6 rounded-xl">
              <div className="text-sm font-semibold text-purple-700 mb-1">Total Usage</div>
              <div className="text-2xl font-bold text-purple-900">{formatMinutes(summary.total_minutes)}</div>
            </div>
            <div className="bg-gradient-to-r from-orange-50 to-orange-100 p-6 rounded-xl">
              <div className="text-sm font-semibold text-orange-700 mb-1">Active Containers</div>
              <div className="text-2xl font-bold text-orange-900">{summary.active_containers}</div>
            </div>
          </div>
        </div>

        {/* Containers List */}
        <div className="modern-card p-8 fade-in">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Container Usage Records</h2>
          
          {containers.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Container</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Status</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Start Time</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">End Time</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Duration</th>
                    <th className="text-right py-3 px-4 font-semibold text-gray-700">Cost</th>
                  </tr>
                </thead>
                <tbody>
                  {containers.map((container) => (
                    <tr key={container.id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-4 text-sm text-gray-600">
                        <div className="flex items-center space-x-2">
                          <span className="font-mono text-xs bg-gray-100 px-2 py-1 rounded">
                            {container.container_id.substring(0, 12)}
                          </span>
                          <span className="text-gray-400 text-xs" title={container.container_id}>
                            ...
                          </span>
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <span className={`status-badge ${
                          container.status === 'Active' 
                            ? 'status-registered' 
                            : 'bg-gray-200 text-gray-700'
                        }`}>
                          {container.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-600">
                        {formatDate(container.start_time)}
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-600">
                        {formatDate(container.end_time)}
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-600">
                        {formatMinutes(container.duration_minutes)}
                      </td>
                      <td className="py-3 px-4 text-sm font-semibold text-right">
                        {formatCurrency(container.cost)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500">
              No container usage records found.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}


