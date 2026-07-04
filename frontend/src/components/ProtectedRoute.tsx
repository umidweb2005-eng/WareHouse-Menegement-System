import { Navigate, Outlet, useLocation } from "react-router-dom"

import { FullPageLoader } from "@/components/common/Loading"
import { useAuth } from "@/providers/auth-provider"

/** Requires an authenticated session; otherwise redirects to /login. */
export function ProtectedRoute() {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return <FullPageLoader />
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  return <Outlet />
}
