import { createBrowserRouter, Navigate } from "react-router-dom"

import { ProtectedRoute } from "@/components/ProtectedRoute"
import { RoleRoute } from "@/components/RoleRoute"
import { AppLayout } from "@/components/layout/AppLayout"
import { LoginPage } from "@/features/auth/LoginPage"
import { CategoriesPage } from "@/features/categories/CategoriesPage"
import { DashboardPage } from "@/features/dashboard/DashboardPage"
import { UnitsPage } from "@/features/units/UnitsPage"
import { NotFoundPage } from "@/features/misc/NotFoundPage"

export const router = createBrowserRouter([
  {
    path: "/login",
    element: <LoginPage />,
  },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { index: true, element: <Navigate to="/dashboard" replace /> },
          {
            element: <RoleRoute permission="dashboard.view" />,
            children: [{ path: "dashboard", element: <DashboardPage /> }],
          },
          {
            element: <RoleRoute permission="category.view" />,
            children: [{ path: "categories", element: <CategoriesPage /> }],
          },
          {
            element: <RoleRoute permission="unit.view" />,
            children: [{ path: "units", element: <UnitsPage /> }],
          },
        ],
      },
    ],
  },
  {
    path: "*",
    element: <NotFoundPage />,
  },
])
