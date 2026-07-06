import {
  ArrowDownToLine,
  ArrowUpFromLine,
  CreditCard,
  FileBarChart,
  FolderTree,
  LayoutDashboard,
  Package,
  Ruler,
  ScrollText,
  Settings,
  Shield,
  Truck,
  UserCog,
  Users,
  type LucideIcon,
} from "lucide-react"

export interface NavItem {
  label: string
  path: string
  icon: LucideIcon
  /** Permission code required to see this item. */
  permission: string
  /** Whether the route is implemented yet (Phase 1 = dashboard only). */
  enabled: boolean
}

export interface NavGroup {
  title: string
  items: NavItem[]
}

/**
 * Full planned navigation. Items whose feature route is not implemented yet are
 * marked `enabled: false` and rendered as disabled (no broken links).
 */
export const NAV_GROUPS: NavGroup[] = [
  {
    title: "Umumiy",
    items: [
      { label: "Boshqaruv paneli", path: "/dashboard", icon: LayoutDashboard, permission: "dashboard.view", enabled: true },
    ],
  },
  {
    title: "Katalog",
    items: [
      { label: "Mahsulotlar", path: "/products", icon: Package, permission: "product.view", enabled: false },
      { label: "Kategoriyalar", path: "/categories", icon: FolderTree, permission: "category.view", enabled: true },
      { label: "Birliklar", path: "/units", icon: Ruler, permission: "unit.view", enabled: true },
    ],
  },
  {
    title: "Kontragentlar",
    items: [
      { label: "Yetkazib beruvchilar", path: "/suppliers", icon: Truck, permission: "supplier.view", enabled: false },
      { label: "Mijozlar", path: "/customers", icon: Users, permission: "customer.view", enabled: false },
    ],
  },
  {
    title: "Operatsiyalar",
    items: [
      { label: "Kirim", path: "/stock-in", icon: ArrowDownToLine, permission: "stock_in.view", enabled: false },
      { label: "Chiqim", path: "/stock-out", icon: ArrowUpFromLine, permission: "stock_out.view", enabled: false },
    ],
  },
  {
    title: "Moliya",
    items: [
      { label: "Qarzlar", path: "/debts", icon: CreditCard, permission: "debt.view", enabled: false },
      { label: "Hisobotlar", path: "/reports", icon: FileBarChart, permission: "report.view", enabled: false },
    ],
  },
  {
    title: "Tizim",
    items: [
      { label: "Foydalanuvchilar", path: "/users", icon: UserCog, permission: "user.view", enabled: false },
      { label: "Rollar", path: "/roles", icon: Shield, permission: "role.view", enabled: false },
      { label: "Audit jurnali", path: "/audit-logs", icon: ScrollText, permission: "audit.view", enabled: false },
      { label: "Sozlamalar", path: "/settings", icon: Settings, permission: "setting.manage", enabled: false },
    ],
  },
]
