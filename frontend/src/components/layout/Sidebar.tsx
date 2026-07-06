import { Warehouse } from "lucide-react"
import { NavLink } from "react-router-dom"

import { NAV_GROUPS } from "@/config/nav"
import { hasPermission } from "@/config/permissions"
import { cn } from "@/lib/utils"
import { useAuth } from "@/providers/auth-provider"

export function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const { user } = useAuth()

  return (
    <div className="flex h-full flex-col">
      <div className="flex h-16 items-center gap-3 border-b px-6">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <Warehouse className="h-5 w-5" />
        </div>
        <span className="text-lg font-semibold">WMS</span>
      </div>

      <nav className="flex-1 space-y-6 overflow-y-auto px-3 py-4">
        {NAV_GROUPS.map((group) => {
          const visibleItems = group.items.filter((item) =>
            hasPermission(user, item.permission),
          )
          if (visibleItems.length === 0) return null

          return (
            <div key={group.title}>
              <p className="px-3 pb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                {group.title}
              </p>
              <ul className="space-y-1">
                {visibleItems.map((item) => {
                  const Icon = item.icon
                  if (!item.enabled) {
                    return (
                      <li key={item.path}>
                        <span
                          className="flex cursor-not-allowed items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-muted-foreground/60"
                          title="Keyingi bosqichda qo'shiladi"
                        >
                          <Icon className="h-5 w-5" />
                          <span className="flex-1">{item.label}</span>
                          <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] font-medium">
                            tez orada
                          </span>
                        </span>
                      </li>
                    )
                  }
                  return (
                    <li key={item.path}>
                      <NavLink
                        to={item.path}
                        onClick={onNavigate}
                        className={({ isActive }) =>
                          cn(
                            "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                            isActive
                              ? "bg-primary text-primary-foreground"
                              : "text-foreground hover:bg-accent hover:text-accent-foreground",
                          )
                        }
                      >
                        <Icon className="h-5 w-5" />
                        {item.label}
                      </NavLink>
                    </li>
                  )
                })}
              </ul>
            </div>
          )
        })}
      </nav>
    </div>
  )
}
