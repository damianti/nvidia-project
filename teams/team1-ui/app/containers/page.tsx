"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import {
  containerService,
  ImageWithContainers,
} from "../services/containerService";
import { useAuth } from "../contexts/AuthContext";

export default function ContainersPage() {
  const { user } = useAuth();
  const [images, setImages] = useState<ImageWithContainers[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchImages();
  }, []);

  const fetchImages = async () => {
    try {
      setLoading(true);
      setError("");
      const fetchedImages = await containerService.getImagesWithContainers();
      setImages(fetchedImages);
    } catch (error) {
      console.error("Error fetching images with containers: ", error);
      setError("Failed to load images. Please try again.");
    } finally {
      setLoading(false);
    }
  };
  const handleStart = async (containerId: number) => {
    // TODO: Call start API
    console.log("Start container:", containerId);
  };

  const handleStop = async (containerId: number) => {
    // TODO: Call stop API
    console.log("Stop container:", containerId);
  };

  const handleDelete = async (containerId: number) => {
    if (confirm("Are you sure you want to delete this container?")) {
      // TODO: Call delete API
      console.log("Delete container:", containerId);
    }
  };

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
              <Link href="/dashboard" className="btn-modern">
                Back to Dashboard
              </Link>
              <Link href="/images" className="btn-modern">
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
            <h3 className="text-2xl font-bold text-gray-900 mb-6">
              Your Images ({images.length})
            </h3>
            <div className="space-y-8">
              {images.map((image) => (
                <div key={image.id} className="modern-card p-6">
                  {/* Header de la imagen */}
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
                      <h4 className="text-xl font-bold text-gray-900">
                        {image.name}:{image.tag}
                      </h4>
                      <span className="text-sm text-gray-500">
                        ({image.containers.length} container
                        {image.containers.length !== 1 ? "s" : ""})
                      </span>
                    </div>
                  </div>

                  {/* Containers de esta imagen */}
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
                                className="px-3 py-1 text-sm btn-modern"
                              >
                                Stop
                              </button>
                            ) : (
                              <button
                                onClick={() => handleStart(container.id)}
                                className="px-3 py-1 text-sm btn-modern"
                              >
                                Start
                              </button>
                            )}
                            <button
                              onClick={() => handleDelete(container.id)}
                              className="px-3 py-1 text-sm btn-modern"
                            >
                              Delete
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
    </div>
  );
}
