"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "./contexts/AuthContext";
import LoadingSpinner from "./components/LoadingSpinner";

export default function HomePage() {
  const router = useRouter();
  const { user, loading } = useAuth();

  useEffect(() => {
    if (!loading) {
      if (user) {
        router.push("/dashboard");
      } else {
        router.push("/login");
      }
    }
  }, [user, loading, router]);

  return <LoadingSpinner />;
}
