import { ShieldAlert } from "lucide-react"
import { Outlet } from "react-router-dom"

import { hasPermission } from "@/config/permissions"
import { useAuth } from "@/providers/auth-provider"

/** Guards a route by a required permission code (mirrors backend RBAC). */
export function RoleRoute({ permission }: { permission: string }) {
  const { user } = useAuth()

  if (!hasPermission(user, permission)) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <ShieldAlert className="h-12 w-12 text-destructive" />
        <h2 className="mt-4 text-xl font-semibold">Ruxsat yo'q</h2>
        <p className="mt-1 max-w-sm text-muted-foreground">
          Bu bo'limni ko'rish uchun sizda yetarli ruxsat mavjud emas.
        </p>
      </div>
    )
  }

  return <Outlet />
}
