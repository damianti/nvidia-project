"use client";

import { GlobalMetrics } from "@/services/metricsService";

interface MetricsCardProps {
  metrics: GlobalMetrics;
  title?: string;
}

export default function MetricsCard({
  metrics,
  title = "API Metrics",
}: MetricsCardProps) {
  const formatNumber = (num: number): string => {
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(1)}M`;
    }
    if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}K`;
    }
    return num.toString();
  };

  const formatLatency = (ms: number): string => {
    if (ms < 1) {
      return `${(ms * 1000).toFixed(0)}μs`;
    }
    if (ms < 1000) {
      return `${ms.toFixed(1)}ms`;
    }
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const errorRate =
    metrics.total_requests > 0
      ? ((metrics.total_errors / metrics.total_requests) * 100).toFixed(2)
      : "0.00";

  return (
    <div className="mb-8">
      <h2 className="text-2xl font-bold text-gray-900 mb-4">{title}</h2>

      {/* Cards principales */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        {/* Total Requests */}
        <div className="bg-gradient-to-r from-blue-50 to-blue-100 p-6 rounded-xl">
          <div className="text-sm font-semibold text-blue-700 mb-1">
            Total Requests
          </div>
          <div className="text-3xl font-bold text-blue-900">
            {formatNumber(metrics.total_requests)}
          </div>
        </div>

        {/* Total Errors */}
        <div className="bg-gradient-to-r from-red-50 to-red-100 p-6 rounded-xl">
          <div className="text-sm font-semibold text-red-700 mb-1">
            Total Errors
          </div>
          <div className="text-3xl font-bold text-red-900">
            {formatNumber(metrics.total_errors)}
          </div>
        </div>

        {/* Error Rate */}
        <div className="bg-gradient-to-r from-orange-50 to-orange-100 p-6 rounded-xl">
          <div className="text-sm font-semibold text-orange-700 mb-1">
            Error Rate
          </div>
          <div className="text-3xl font-bold text-orange-900">{errorRate}%</div>
        </div>

        {/* Average Latency */}
        <div className="bg-gradient-to-r from-green-50 to-green-100 p-6 rounded-xl">
          <div className="text-sm font-semibold text-green-700 mb-1">
            Avg Latency
          </div>
          <div className="text-3xl font-bold text-green-900">
            {formatLatency(metrics.avg_latency_ms)}
          </div>
        </div>
      </div>

      {/* Status Codes Distribution */}
      {Object.keys(metrics.status_codes).length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">
            Status Codes
          </h3>
          <div className="flex flex-wrap gap-2">
            {Object.entries(metrics.status_codes).map(([code, count]) => (
              <div
                key={code}
                className={`px-4 py-2 rounded-lg ${
                  code.startsWith("2")
                    ? "bg-green-100 text-green-800"
                    : code.startsWith("4")
                    ? "bg-yellow-100 text-yellow-800"
                    : "bg-red-100 text-red-800"
                }`}
              >
                <span className="font-semibold">{code}:</span>{" "}
                {formatNumber(count)}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Métrics by App Hostname */}
      {metrics.by_app_hostname &&
        Object.keys(metrics.by_app_hostname).length > 0 && (
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">
              Metrics by App Hostname
            </h3>
            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        App Hostname
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Requests
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Errors
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Avg Latency
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {Object.entries(metrics.by_app_hostname).map(
                      ([hostname, data]) => (
                        <tr key={hostname} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {hostname}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {formatNumber(data.requests)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            <span
                              className={
                                data.errors > 0
                                  ? "text-red-600 font-semibold"
                                  : "text-gray-500"
                              }
                            >
                              {formatNumber(data.errors)}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {formatLatency(data.avg_latency_ms)}
                          </td>
                        </tr>
                      )
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

      {/* Métrics by User */}
      {metrics.by_user && Object.keys(metrics.by_user).length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">
            Metrics by User
          </h3>
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      User ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Requests
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Errors
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Avg Latency
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {Object.entries(metrics.by_user).map(([userId, data]) => (
                    <tr key={userId} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        User {userId}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatNumber(data.requests)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <span
                          className={
                            data.errors > 0
                              ? "text-red-600 font-semibold"
                              : "text-gray-500"
                          }
                        >
                          {formatNumber(data.errors)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatLatency(data.avg_latency_ms)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Metricss by Container */}
      {metrics.by_container && Object.keys(metrics.by_container).length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">
            Metrics by Container
          </h3>
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Container ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Requests
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Errors
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Avg Latency
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {Object.entries(metrics.by_container).map(
                    ([containerId, data]) => (
                      <tr key={containerId} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
                          {containerId.substring(0, 12)}...
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatNumber(data.requests)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <span
                            className={
                              data.errors > 0
                                ? "text-red-600 font-semibold"
                                : "text-gray-500"
                            }
                          >
                            {formatNumber(data.errors)}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatLatency(data.avg_latency_ms)}
                        </td>
                      </tr>
                    )
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
