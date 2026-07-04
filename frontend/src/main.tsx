import { StrictMode } from "react"

import { QueryClientProvider } from "@tanstack/react-query"
import { createRoot } from "react-dom/client"
import { RouterProvider } from "react-router-dom"

import { Toaster } from "@/components/ui/sonner"
import { queryClient } from "@/lib/query-client"
import { AuthProvider } from "@/providers/auth-provider"
import { ThemeProvider } from "@/providers/theme-provider"
import { router } from "@/router"

import "./index.css"

const rootElement = document.getElementById("root")
if (!rootElement) {
  throw new Error("Root element #root not found")
}

createRoot(rootElement).render(
  <StrictMode>
    <ThemeProvider defaultTheme="system">
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <RouterProvider router={router} />
          <Toaster />
        </AuthProvider>
      </QueryClientProvider>
    </ThemeProvider>
  </StrictMode>,
)
