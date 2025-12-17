"use client";

import { useState, useEffect, Suspense, useCallback } from "react";
import { useSearchParams } from 'next/navigation'
import Link from "next/link";
import { useRouter } from "next/navigation";

import { containerService, ImageWithContainers, } from "@/services/containerService";
import { useAuth } from "@/contexts/AuthContext";
import Navbar from "@/components/Navbar";
import LoadingSpinner from "@/components/LoadingSpinner";

function ContainersPageContent() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const searchParams = useSearchParams();
  const imageFilter = searchParams.get('image');

  const [images, setImages] = useState<ImageWithContainers[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [actionLoading, setActionLoading] = useState<{ [key: number]: string }>({}); // Track loading per container
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [selectedImageId, setSelectedImageId] = useState<number | null>(null)
  const [containerCount, setContainerCount] = useState(1)

  useEffect(() => {
    if (!authLoading && !user){
      router.push('/login')
    }
  }, [authLoading, user, router]);

  const fetchImages = useCallback(async () => {
    try {
      setLoading(true);
      setError("");
      const fetchedImages = await containerService.getImagesWithContainers();
      
      // Filter images if imageFilter is present
      if (imageFilter) {
        const filteredImages = fetchedImages.filter(img => img.id.toString() === imageFilter);
        setImages(filteredImages);
      } else {
        setImages(fetchedImages);
      }
    } catch (error) {
      console.error("Error fetching images with containers: ", error);
      setError("Failed to load images. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [imageFilter]);

  useEffect(() => {
    if (user) {
      fetchImages();
    }
  }, [user, fetchImages]);

  // Reset containerCount when image selection changes to ensure it's within valid range
  useEffect(() => {
    const imageId = imageFilter ? Number(imageFilter) : selectedImageId;
    if (imageId) {
      const selectedImage = images.find(img => img.id === imageId);
      if (selectedImage) {
        const existingCount = selectedImage.containers?.length || 0;
        const maxAllowed = Math.max(1, selectedImage.max_instances - existingCount);
        if (containerCount > maxAllowed) {
          setContainerCount(maxAllowed);
        }
      }
    }
  }, [selectedImageId, imageFilter, images, containerCount]);
  const handleStart = async (containerId: number) => {
    try {
      setActionLoading(prev => ({ ...prev, [containerId]: 'starting' }));
      setError("");
      setSuccess("");
      await containerService.startContainer(containerId);
      setSuccess("Container started successfully");
      await fetchImages();
      setTimeout(() => setSuccess(""), 3000);
    }
    catch (error){
      console.error ("Error starting container: ", error);
      setError("Failed to start container. Please try again");
      setTimeout(() => setError(""), 5000);
    }
    finally {
      setActionLoading(prev => {
        const newState = { ...prev };
        delete newState[containerId];
        return newState;
      });
    }
  };

  const handleStop = async (containerId: number) => {
    try {
      setActionLoading(prev => ({ ...prev, [containerId]: 'stopping' }));
      setError("");
      setSuccess("");
      await containerService.stopContainer(containerId);
      setSuccess("Container stopped successfully");
      await fetchImages();
      setTimeout(() => setSuccess(""), 3000);
    }
    catch (error){
      console.error ("Error stopping container: ", error);
      setError("Failed to stop container. Please try again");
      setTimeout(() => setError(""), 5000);
    }
    finally {
      setActionLoading(prev => {
        const newState = { ...prev };
        delete newState[containerId];
        return newState;
      });
    }
  };

  const handleDelete = async (containerId: number) => {
    if (confirm("Are you sure you want to delete this container?")) {
      try {
        setActionLoading(prev => ({ ...prev, [containerId]: 'deleting' }));
        setError("");
        setSuccess("");
        await containerService.deleteContainer(containerId);
        setSuccess("Container deleted successfully");
        await fetchImages();
        setTimeout(() => setSuccess(""), 3000);
      }
      catch (error){
        console.error("Error deleting container: ", error);
        setError("Failed to delete container. Please try again");
        setTimeout(() => setError(""), 5000);
      }
      finally {
        setActionLoading(prev => {
          const newState = { ...prev };
          delete newState[containerId];
          return newState;
        });
      }  
    }
  };
  const handleCreateContainer = async () => {
    try {
      setLoading(true);
      setError('');
      setSuccess('');
      const imageId = imageFilter ? Number(imageFilter) : selectedImageId
      if (!imageId){
        setError('Please select an image');
        setLoading(false);
        return;
      }
      
      // Find selected image to check max_instances
      const selectedImage = images.find(img => img.id === imageId);
      if (!selectedImage) {
        setError('Selected image not found');
        setLoading(false);
        return;
      }
      
      // Calculate max allowed based on existing containers
      const existingCount = selectedImage.containers?.length || 0;
      const maxAllowed = selectedImage.max_instances - existingCount;
      
      if (maxAllowed <= 0) {
        setError(`Cannot create containers: image already has ${existingCount} containers (max: ${selectedImage.max_instances})`);
        setLoading(false);
        return;
      }
      
      if (containerCount < 1) {
        setError('Container count must be at least 1');
        setLoading(false);
        return;
      }
      
      if (containerCount > maxAllowed) {
        setError(`Cannot create more than ${maxAllowed} container(s). Image limit: ${selectedImage.max_instances}, existing: ${existingCount}`);
        setLoading(false);
        return;
      }
      
      await containerService.createContainer(imageId, undefined, containerCount);
      setSuccess(`Successfully created ${containerCount} container(s)`);
      setShowCreateModal(false);
      setContainerCount(1);
      await fetchImages();
      setTimeout(() => setSuccess(""), 3000);
    }
    catch (error){
      console.error('Error creating container:', error);
      setError(error instanceof Error ? error.message : 'Failed to create container. Please try again');
      setTimeout(() => setError(""), 5000);
    }
    finally {
      setLoading(false);
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
          <div className="text-xl text-gray-700">Loading containers...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-4">
      <Navbar/>
      
      {/* Success Message */}
      {success && (
        <div className="max-w-7xl mx-auto mb-6">
          <div className="modern-card p-4 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-center">
              <svg className="w-5 h-5 text-green-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <p className="text-green-700 font-medium">{success}</p>
            </div>
          </div>
        </div>
      )}

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
        {/* Stats Summary */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="stats-card fade-in">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-green-600 rounded-xl flex items-center justify-center">
                  <svg
                    className="w-6 h-6 text-white"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01"
                    />
                  </svg>
                </div>
              </div>
              <div className="ml-6">
                <p className="text-sm font-medium text-gray-600">Running</p>
                <p className="text-3xl font-bold text-gray-900">
                  {images.reduce(
                    (sum, img) =>
                      sum +
                      img.containers.filter((c) => c.status === "running")
                        .length,
                    0
                  )}
                </p>
              </div>
            </div>
          </div>

          <div className="stats-card fade-in">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-gradient-to-r from-red-500 to-red-600 rounded-xl flex items-center justify-center">
                  <svg
                    className="w-6 h-6 text-white"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </div>
              </div>
              <div className="ml-6">
                <p className="text-sm font-medium text-gray-600">Stopped</p>
                <p className="text-3xl font-bold text-gray-900">
                  {images.reduce(
                    (sum, img) =>
                      sum +
                      img.containers.filter((c) => c.status === "stopped")
                        .length,
                    0
                  )}
                </p>
              </div>
            </div>
          </div>

          <div className="stats-card fade-in">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-blue-600 rounded-xl flex items-center justify-center">
                  <svg
                    className="w-6 h-6 text-white"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                    />
                  </svg>
                </div>
              </div>
              <div className="ml-6">
                <p className="text-sm font-medium text-gray-600">Total CPU</p>
                <p className="text-3xl font-bold text-gray-900">
                  {images
                    .reduce(
                      (sum, img) =>
                        sum +
                        img.containers.reduce(
                          (s, c) => s + parseFloat(c.cpu_usage),
                          0
                        ),
                      0
                    )
                    .toFixed(1)}
                </p>
              </div>
            </div>
          </div>

          <div className="stats-card fade-in">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-purple-600 rounded-xl flex items-center justify-center">
                  <svg
                    className="w-6 h-6 text-white"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4"
                    />
                  </svg>
                </div>
              </div>
              <div className="ml-6">
                <p className="text-sm font-medium text-gray-600">
                  Total Memory
                </p>
                <p className="text-3xl font-bold text-gray-900">
                  {images.reduce(
                    (sum, img) =>
                      sum +
                      img.containers.reduce((s, c) => {
                        const mem = parseInt(
                          c.memory_usage.replace("m", "").replace("g", "000")
                        );
                        return s + mem;
                      }, 0),
                    0
                  )}
                  m
                </p>
              </div>
            </div>
          </div>
        </div>

        {images.length > 0 ? (
          <div className="modern-card p-8 fade-in">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-2xl font-bold text-gray-900">
                Your Images ({images.length})
              </h3>
              <button
                onClick={() => {
                  setSelectedImageId(null);
                  setContainerCount(1);
                  setShowCreateModal(true);
                }}
                className="btn-modern"
              >
                <svg className="w-5 h-5 mr-2 inline-block" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Create Container
              </button>
            </div>
            <div className="space-y-8">
              {images.map((image) => (
                <div key={image.id} className="modern-card p-6">
                  {/* Image header */}
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
                        <svg
                          className="w-5 h-5 text-white"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                          />
                        </svg>
                      </div>
                      <div>
                        <h4 className="text-xl font-bold text-gray-900">
                          {image.name}:{image.tag}
                        </h4>
                        {image.app_hostname && (
                          <p className="text-sm text-blue-600 mt-1">
                            {image.app_hostname}
                          </p>
                        )}
                      </div>
                      <span className="text-sm text-gray-500">
                        ({image.containers.length} container
                        {image.containers.length !== 1 ? "s" : ""})
                      </span>
                    </div>
                    <button
                      onClick={() => {
                        setSelectedImageId(image.id);
                        setContainerCount(1);
                        setShowCreateModal(true);
                      }}
                      className="btn-modern text-sm"
                    >
                      <svg className="w-4 h-4 mr-1 inline-block" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                      </svg>
                      Add Container
                    </button>
                  </div>

                  {/* Containers for this image */}
                  {image.containers.length > 0 ? (
                    <div className="space-y-3 pl-4 border-l-2 border-blue-200">
                      {image.containers.map((container) => (
                        <div
                          key={container.id}
                          className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                        >
                          <div className="flex items-center space-x-3">
                            <div className="w-8 h-8 bg-gradient-to-r from-green-500 to-green-600 rounded-lg flex items-center justify-center">
                              <svg
                                className="w-4 h-4 text-white"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                              >
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01"
                                />
                              </svg>
                            </div>
                            <div>
                              <div className="flex items-center space-x-2">
                                <span className="font-semibold text-gray-900">
                                  {container.name}
                                </span>
                                <span
                                  className={`status-badge ${
                                    container.status === "running"
                                      ? "status-running"
                                      : "status-stopped"
                                  }`}
                                >
                                  {container.status}
                                </span>
                              </div>
                              <div className="flex items-center space-x-3 text-xs text-gray-600 mt-1">
                                {image.app_hostname && (
                                  <>
                                    <span className="text-blue-600 font-medium">{image.app_hostname}</span>
                                    <span>•</span>
                                  </>
                                )}
                                <span>Port: {container.port}</span>
                                <span>•</span>
                                <span>CPU: {container.cpu_usage}</span>
                                <span>•</span>
                                <span>Memory: {container.memory_usage}</span>
                              </div>
                            </div>
                          </div>
                          <div className="flex space-x-2">
                            {container.status === "running" ? (
                              <button
                                onClick={() => handleStop(container.id)}
                                disabled={actionLoading[container.id] !== undefined}
                                className="px-3 py-1 text-sm btn-modern disabled:opacity-50 disabled:cursor-not-allowed"
                              >
                                {actionLoading[container.id] === 'stopping' ? (
                                  <span className="flex items-center">
                                    <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white mr-1"></div>
                                    Stopping...
                                  </span>
                                ) : (
                                  'Stop'
                                )}
                              </button>
                            ) : (
                              <button
                                onClick={() => handleStart(container.id)}
                                disabled={actionLoading[container.id] !== undefined}
                                className="px-3 py-1 text-sm btn-modern disabled:opacity-50 disabled:cursor-not-allowed"
                              >
                                {actionLoading[container.id] === 'starting' ? (
                                  <span className="flex items-center">
                                    <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white mr-1"></div>
                                    Starting...
                                  </span>
                                ) : (
                                  'Start'
                                )}
                              </button>
                            )}
                            <button
                              onClick={() => handleDelete(container.id)}
                              disabled={actionLoading[container.id] !== undefined}
                              className="px-3 py-1 text-sm btn-modern disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                              {actionLoading[container.id] === 'deleting' ? (
                                <span className="flex items-center">
                                  <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white mr-1"></div>
                                  Deleting...
                                </span>
                              ) : (
                                'Delete'
                              )}
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-4 text-gray-500">
                      No containers for this image yet
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="modern-card p-12 text-center fade-in">
            <div className="w-24 h-24 bg-gradient-to-r from-green-500 to-blue-600 rounded-3xl flex items-center justify-center mx-auto mb-6">
              <svg
                className="w-12 h-12 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01"
                />
              </svg>
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-2">
              No images with containers yet
            </h3>
            <p className="text-gray-600 mb-8">
              Start by creating containers from your images.
            </p>
            <Link href="/images" className="btn-modern">
              Manage Images
            </Link>
          </div>
        )}
      </div>
    {/* {Create Container Modal} */}
    {showCreateModal && (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="modern-card p-8 max-w-md w-full mx-4">
          <h3 className="text-2xl font-bold text-gray-900 mb-6"> Create Container</h3>
          {imageFilter ? (
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Image:
              </label>
              <div className="p-3 bg-gray-100 rounded-lg">
                {images.find(img => img.id.toString() === imageFilter)?.name}:{images.find(img => img.id.toString() === imageFilter)?.tag} → {images.find(img => img.id.toString() === imageFilter)?.app_hostname}
              </div>

            </div>
          ) : (
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                SELECT IMAGE:
              </label>
              <select
                value={selectedImageId || ''}
                onChange={(e)=> setSelectedImageId(Number(e.target.value))}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value=""> Choose an image... </option>
                {images.map((image)=> (
                  <option key={image.id} value={image.id}>
                    {image.name}:{image.tag} → {image.app_hostname}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Number of Containers
              {(() => {
                const imageId = imageFilter ? Number(imageFilter) : selectedImageId;
                const selectedImage = imageId ? images.find(img => img.id === imageId) : null;
                if (selectedImage) {
                  const existingCount = selectedImage.containers?.length || 0;
                  const maxAllowed = selectedImage.max_instances - existingCount;
                  return maxAllowed > 0 ? (
                    <span className="text-sm text-gray-500 ml-2">
                      (Max: {maxAllowed}, Existing: {existingCount}/{selectedImage.max_instances})
                    </span>
                  ) : (
                    <span className="text-sm text-red-500 ml-2">
                      (Limit reached: {existingCount}/{selectedImage.max_instances})
                    </span>
                  );
                }
                return null;
              })()}
            </label>
            <input
            type="number"
            min="1"
            max={(() => {
              const imageId = imageFilter ? Number(imageFilter) : selectedImageId;
              const selectedImage = imageId ? images.find(img => img.id === imageId) : null;
              if (selectedImage) {
                const existingCount = selectedImage.containers?.length || 0;
                return Math.max(1, selectedImage.max_instances - existingCount);
              }
              return 10;
            })()}
            value={containerCount}
            onChange={(e)=> setContainerCount(Number(e.target.value))}
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div className="flex space-x-4">
            <button
              onClick={() => setShowCreateModal(false)}
              className="flex-1 px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={handleCreateContainer}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Create
            </button>
          </div>
        </div>
      </div>
    )}
    </div>
  );
}

export default function ContainersPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <div className="modern-card p-8 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <div className="text-xl text-gray-700">Loading containers...</div>
        </div>
      </div>
    }>
      <ContainersPageContent />
    </Suspense>
  );
}
