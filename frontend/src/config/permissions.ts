/**
 * Client-side mirror of the backend RBAC (app/permissions/constants.py).
 * The backend's /auth/me does not return permission codes, so the UI derives
 * capabilities from the (fixed, system) role name. Every gate is also enforced
 * server-side; a 403 is still handled gracefully at the API layer.
 */
import type { RoleName, User } from "@/types"

const ALL: string[] = [
  "user.view", "user.manage",
  "role.view", "role.manage", "permission.view",
  "category.view", "category.manage",
  "unit.view", "unit.manage",
  "product.view", "product.manage",
  "supplier.view", "supplier.manage",
  "customer.view", "customer.manage",
  "stock_in.view", "stock_in.manage",
  "stock_out.view", "stock_out.manage",
  "payment_method.view", "payment_method.manage",
  "debt.view", "debt.manage",
  "dashboard.view", "report.view", "audit.view", "setting.manage",
]

const VIEW_ONLY = ALL.filter((c) => c.endsWith(".view"))

export const ROLE_PERMISSIONS: Record<RoleName, string[]> = {
  admin: ALL,
  manager: Array.from(
    new Set([
      ...VIEW_ONLY,
      "category.manage", "unit.manage", "product.manage",
      "supplier.manage", "customer.manage",
      "stock_in.manage", "stock_out.manage", "debt.manage",
      "report.view", "dashboard.view",
    ]),
  ),
  warehouse_worker: [
    "product.view", "category.view", "unit.view", "supplier.view", "customer.view",
    "stock_in.view", "stock_in.manage",
    "stock_out.view", "stock_out.manage",
    "dashboard.view",
  ],
  cashier: [
    "product.view", "customer.view", "customer.manage",
    "stock_out.view", "stock_out.manage",
    "payment_method.view", "debt.view", "debt.manage",
    "dashboard.view",
  ],
  viewer: Array.from(new Set([...VIEW_ONLY, "dashboard.view"])),
}

export function hasPermission(user: User | null, code: string): boolean {
  if (!user) return false
  if (user.is_superuser) return true
  const roleName = user.role?.name as RoleName | undefined
  if (!roleName) return false
  return (ROLE_PERMISSIONS[roleName] ?? []).includes(code)
}
