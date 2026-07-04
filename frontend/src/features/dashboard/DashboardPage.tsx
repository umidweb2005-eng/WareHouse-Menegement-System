import { CalendarClock, ShieldCheck, UserCircle } from "lucide-react"

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { formatDateTime } from "@/lib/format"
import { useAuth } from "@/providers/auth-provider"

const ROLE_LABELS: Record<string, string> = {
  admin: "Administrator",
  manager: "Menejer",
  warehouse_worker: "Ombor xodimi",
  cashier: "Kassir",
  viewer: "Kuzatuvchi",
}

export function DashboardPage() {
  const { user } = useAuth()
  const roleLabel = user?.role?.name
    ? (ROLE_LABELS[user.role.name] ?? user.role.name)
    : "—"

  const cards = [
    {
      title: "Foydalanuvchi",
      icon: UserCircle,
      value: user?.full_name ?? "—",
      sub: `@${user?.username ?? ""}`,
    },
    {
      title: "Rol",
      icon: ShieldCheck,
      value: roleLabel,
      sub: user?.is_superuser ? "To'liq huquqli" : "Rol asosida",
    },
    {
      title: "Oxirgi kirish",
      icon: CalendarClock,
      value: formatDateTime(user?.last_login_at),
      sub: "Joriy sessiya",
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Boshqaruv paneli</h1>
        <p className="text-muted-foreground">
          Xush kelibsiz, {user?.full_name ?? "foydalanuvchi"}
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {cards.map((card) => {
          const Icon = card.icon
          return (
            <Card key={card.title}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  {card.title}
                </CardTitle>
                <Icon className="h-5 w-5 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-xl font-semibold">{card.value}</div>
                <p className="text-xs text-muted-foreground">{card.sub}</p>
              </CardContent>
            </Card>
          )
        })}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Ombor Boshqaruv Tizimi</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Statistika, savdo grafiklari va operatsion ko'rsatkichlar keyingi
          bosqichda shu panelga qo'shiladi. Chap menyudagi bo'limlar orqali
          tizim imkoniyatlaridan foydalanishingiz mumkin.
        </CardContent>
      </Card>
    </div>
  )
}
