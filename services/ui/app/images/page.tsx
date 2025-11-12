'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'


import { imageService, Image, CreateImageRequest } from '@/services/imageService'
import { useAuth } from '@/contexts/AuthContext'
import Navbar from '@/components/Navbar'
import LoadingSpinner from '@/components/LoadingSpinner'

export default function ImagesPage() {
  const router = useRouter()
  const { user, loading: authLoading } = useAuth()
  const [images, setImages] = useState<Image[]>([])
  const [loading, setLoading] = useState(true)
  const [showUploadForm, setShowUploadForm] = useState(false)
  const [uploadLoading, setUploadLoading] = useState(false)
  const [error, setError] = useState('')
  const [uploadForm, setUploadForm] = useState<CreateImageRequest>({
    name: '',
    tag: 'latest',
    website_url: '',
    min_instances: 1,
    max_instances: 3,
    cpu_limit: '0.5',
    memory_limit: '512m',
    user_id: 0
  })

  
  useEffect(() => {
    if (!authLoading && !user) {
        router.push('/login')
    }
    fetchImages()
  }, [authLoading, user, router])

  const fetchImages = async () => {
    try {
      setLoading(true)
      setError('')
      const fetchedImages = await imageService.getImages()
      setImages(fetchedImages)
    } catch (error) {
      console.error('Error fetching images:', error)
      setError('Failed to load images. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!user) {
      setError('You must be logged in to upload images')
      return
    }
    
    setUploadLoading(true)
    setError('')
    
    try {
      // Create the image using the service with user_id
      const imageData = {
        ...uploadForm,
        user_id: user.id
      }
      const newImage = await imageService.createImage(imageData)
      
      // Add the new image to the list
      setImages(prevImages => [newImage, ...prevImages])
      
      // Reset form and close modal
      setUploadForm({
        name: '',
        tag: 'latest',
        website_url: '',
        min_instances: 1,
        max_instances: 3,
        cpu_limit: '0.5',
        memory_limit: '512m',
        user_id: 0
      })
      setShowUploadForm(false)
      
    } catch (error) {
      console.error('Error uploading image:', error)
      setError(error instanceof Error ? error.message : 'Failed to upload image')
    } finally {
      setUploadLoading(false)
    }
  }

  const handleDelete = async (imageId: number) => {
    if (!confirm('Are you sure you want to delete this image?')) {
      return
    }

    try {
      setError('')
      await imageService.deleteImage(imageId)
      
      // Remove the image from the list
      setImages(prevImages => prevImages.filter(img => img.id !== imageId))
      
    } catch (error) {
      console.error('Error deleting image:', error)
      setError(error instanceof Error ? error.message : 'Failed to delete image')
    }
  }

  if (authLoading) {
    return <LoadingSpinner />
  }
  if (!user){
    return null
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="modern-card p-8 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <div className="text-xl text-gray-700">Loading images...</div>
        </div>
      </div>
    )
  }

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
        {/* Upload Form Modal */}
        {showUploadForm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center p-4">
            <div className="modern-card w-full max-w-md p-8 fade-in">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-2xl font-bold text-gray-900">Upload New Image</h3>
                <button
                  onClick={() => setShowUploadForm(false)}
                  className="text-gray-400 hover:text-gray-600 text-2xl"
                >
                  ×
                </button>
              </div>
              <form onSubmit={handleUpload} className="space-y-6">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Image Name</label>
                  <input
                    type="text"
                    required
                    className="modern-input w-full"
                    placeholder="e.g., nginx, python, redis"
                    value={uploadForm.name}
                    onChange={(e) => setUploadForm({...uploadForm, name: e.target.value})}
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Tag</label>
                  <input
                    type="text"
                    required
                    className="modern-input w-full"
                    placeholder="e.g., latest, 3.9, alpine"
                    value={uploadForm.tag}
                    onChange={(e) => setUploadForm({...uploadForm, tag: e.target.value})}
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Website URL</label>
                  <input
                    type="url"
                    required
                    className="modern-input w-full"
                    placeholder="https://example.com"
                    value={uploadForm.website_url}
                    onChange={(e) => setUploadForm({...uploadForm, website_url: e.target.value})}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Min Instances</label>
                    <input
                      type="number"
                      min="1"
                      className="modern-input w-full"
                      value={uploadForm.min_instances}
                      onChange={(e) => setUploadForm({...uploadForm, min_instances: parseInt(e.target.value)})}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Max Instances</label>
                    <input
                      type="number"
                      min="1"
                      className="modern-input w-full"
                      value={uploadForm.max_instances}
                      onChange={(e) => setUploadForm({...uploadForm, max_instances: parseInt(e.target.value)})}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">CPU Limit</label>
                    <input
                      type="text"
                      className="modern-input w-full"
                      placeholder="e.g., 0.5, 1.0"
                      value={uploadForm.cpu_limit}
                      onChange={(e) => setUploadForm({...uploadForm, cpu_limit: e.target.value})}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Memory Limit</label>
                    <input
                      type="text"
                      className="modern-input w-full"
                      placeholder="e.g., 512m, 1g"
                      value={uploadForm.memory_limit}
                      onChange={(e) => setUploadForm({...uploadForm, memory_limit: e.target.value})}
                    />
                  </div>
                </div>
                <div className="flex justify-end space-x-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowUploadForm(false)}
                    className="px-6 py-3 border border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={uploadLoading}
                    className="btn-modern disabled:opacity-50"
                  >
                    {uploadLoading ? (
                      <div className="flex items-center">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Uploading...
                      </div>
                    ) : (
                      'Upload'
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Images List */}
        {images.length > 0 ? (
          <div className="modern-card p-8 fade-in">
            <h3 className="text-2xl font-bold text-gray-900 mb-6">Your Images ({images.length})</h3>
            <div className="space-y-6">
              {images.map((image) => (
                <div key={image.id} className="modern-card p-6 hover:scale-[1.02] transition-transform">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-blue-600 rounded-xl flex items-center justify-center">
                        <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                      </div>
                      <div>
                        <div className="flex items-center space-x-3">
                          <h4 className="text-lg font-semibold text-gray-900">
                          <span>{image.name}:{image.tag} → {image.website_url}</span>
                          </h4>
                          <span className="status-badge status-registered">
                            {image.status}
                          </span>
                        </div>
                        <div className="mt-2 flex items-center space-x-4 text-sm text-gray-600">
                          <span>Created: {new Date(image.created_at).toLocaleDateString()}</span>
                          <span>•</span>
                          <span>Instances: {image.min_instances}-{image.max_instances}</span>
                          <span>•</span>
                          <span>CPU: {image.cpu_limit}</span>
                          <span>•</span>
                          <span>Memory: {image.memory_limit}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex space-x-3">
                      <Link
                        href={`/containers?image=${image.id}`}
                        className="btn-modern"
                      >
                        View Containers
                      </Link>
                      <button
                        onClick={() => handleDelete(image.id)}
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
            <div className="w-24 h-24 bg-gradient-to-r from-blue-500 to-purple-600 rounded-3xl flex items-center justify-center mx-auto mb-6">
              <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-2">No images yet</h3>
            <p className="text-gray-600 mb-8">Get started by uploading your first Docker image.</p>
            <button
              onClick={() => setShowUploadForm(true)}
              className="btn-modern"
            >
              Upload Your First Image
            </button>
          </div>
        )}
      </div>
    </div>
  )
} 