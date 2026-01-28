"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";
import { useAuth } from "@/contexts/AuthContext";
import LoadingSpinner from "@/components/LoadingSpinner";
import { billingService, BillingSummary } from "@/services/billingService";
import { metricsService, GlobalMetrics } from "@/services/metricsService";
import MetricsCard from "@/components/MetricsCard";

export default function DashboardPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [billingSummaries, setBillingSummaries] = useState<BillingSummary[]>(
    []
  );
  const [billingLoading, setBillingLoading] = useState(true);

  const [metrics, setMetrics] = useState<GlobalMetrics | null>(null);
  const [metricsLoading, setMetricsLoading] = useState(true);

  const fetchBillingData = useCallback(async () => {
    try {
      setBillingLoading(true);
      const summaries = await billingService.getAllBillingSummaries();
      setBillingSummaries(summaries);
    } catch (error) {
      console.error("Error fetching billing data:", error);
      // Silently fail - billing data is optional for dashboard
    } finally {
      setBillingLoading(false);
    }
  }, []);

  const fetchMetrics = useCallback(async () => {
    if (!user) return;

    try {
      setMetricsLoading(true);
      // Get metrics filtered by authenticated user
      const data = await metricsService.getMetricsByUserId(user.id);
      setMetrics(data);
    } catch (error) {
      console.error("Error fetching metrics:", error);
      // Silently fail - metrics data is optional for dashboard
      setMetrics(null);
    } finally {
      setMetricsLoading(false);
    }
  }, [user]);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
    }
  }, [authLoading, user, router]);

  useEffect(() => {
    if (user) {
      fetchBillingData();
      fetchMetrics();
      
    }
  }, [user, fetchBillingData, fetchMetrics]);
  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  };

  const formatMinutes = (minutes: number): string => {
    if (minutes < 60) {
      return `${minutes} min`;
    }
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
  };

  // Calculate billing totals
  const totalCost = billingSummaries.reduce((sum, s) => sum + s.total_cost, 0);
  const totalMinutes = billingSummaries.reduce(
    (sum, s) => sum + s.total_minutes,
    0
  );
  const activeContainers = billingSummaries.reduce(
    (sum, s) => sum + s.active_containers,
    0
  );

  if (authLoading) {
    return <LoadingSpinner />;
  }

  if (!user) {
    return null;
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

          {/* Metrics Overview */}
          {!metricsLoading && metrics && (
            <div className="mb-8">
              <MetricsCard metrics={metrics} title="API Gateway Metrics" />
            </div>
          )}

          {/* Billing Overview */}
          {!billingLoading && billingSummaries.length > 0 && (
            <div className="mb-8">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-bold text-gray-900">
                  Billing Overview
                </h2>
                <Link
                  href="/billing"
                  className="text-blue-600 hover:text-blue-800 text-sm font-semibold"
                >
                  View Details →
                </Link>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-gradient-to-r from-blue-50 to-blue-100 p-6 rounded-xl">
                  <div className="text-sm font-semibold text-blue-700 mb-1">
                    Total Cost
                  </div>
                  <div className="text-3xl font-bold text-blue-900">
                    {formatCurrency(totalCost)}
                  </div>
                </div>
                <div className="bg-gradient-to-r from-purple-50 to-purple-100 p-6 rounded-xl">
                  <div className="text-sm font-semibold text-purple-700 mb-1">
                    Total Usage
                  </div>
                  <div className="text-3xl font-bold text-purple-900">
                    {formatMinutes(totalMinutes)}
                  </div>
                </div>
                <div className="bg-gradient-to-r from-orange-50 to-orange-100 p-6 rounded-xl">
                  <div className="text-sm font-semibold text-orange-700 mb-1">
                    Active Containers
                  </div>
                  <div className="text-3xl font-bold text-orange-900">
                    {activeContainers}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Quick Actions */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Link href="/images" className="group">
              <div className="stats-card hover:shadow-xl transition-all duration-300 cursor-pointer">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-blue-600 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform">
                      <svg
                        className="w-8 h-8 text-white"
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
                  </div>
                  <div className="ml-6">
                    <p className="text-2xl font-bold text-gray-900">Images</p>
                    <p className="text-sm text-gray-600 mt-1">
                      View and manage Docker images
                    </p>
                  </div>
                </div>
              </div>
            </Link>

            <Link href="/containers" className="group">
              <div className="stats-card hover:shadow-xl transition-all duration-300 cursor-pointer">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-16 h-16 bg-gradient-to-r from-green-500 to-green-600 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform">
                      <svg
                        className="w-8 h-8 text-white"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
                        />
                      </svg>
                    </div>
                  </div>
                  <div className="ml-6">
                    <p className="text-2xl font-bold text-gray-900">
                      Containers
                    </p>
                    <p className="text-sm text-gray-600 mt-1">
                      View and manage Docker containers
                    </p>
                  </div>
                </div>
              </div>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
