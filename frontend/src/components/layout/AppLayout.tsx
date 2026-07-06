import { Outlet } from "react-router-dom"

import { Header } from "@/components/layout/Header"
import { Sidebar } from "@/components/layout/Sidebar"

export function AppLayout() {
  return (
    <div className="flex min-h-screen bg-background">
      {/* Desktop sidebar */}
      <aside className="hidden w-64 shrink-0 border-r lg:block">
        <div className="fixed h-screen w-64">
          <Sidebar />
        </div>
      </aside>

      {/* Main column */}
      <div className="flex min-w-0 flex-1 flex-col">
        <Header />
        <main className="flex-1 p-4 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
