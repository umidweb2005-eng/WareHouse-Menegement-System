import { useState } from "react"

import { LogOut, Menu } from "lucide-react"
import { useNavigate } from "react-router-dom"
import { toast } from "sonner"

import { Sidebar } from "@/components/layout/Sidebar"
import { ThemeToggle } from "@/components/layout/ThemeToggle"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet"
import { useAuth } from "@/providers/auth-provider"

const ROLE_LABELS: Record<string, string> = {
  admin: "Administrator",
  manager: "Menejer",
  warehouse_worker: "Ombor xodimi",
  cashier: "Kassir",
  viewer: "Kuzatuvchi",
}

function getInitials(name: string): string {
  return name
    .trim()
    .split(/\s+/)
    .map((part) => part[0])
    .slice(0, 2)
    .join("")
    .toUpperCase()
}

export function Header() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [mobileOpen, setMobileOpen] = useState(false)

  async function handleLogout() {
    await logout()
    toast.success("Tizimdan chiqdingiz")
    navigate("/login", { replace: true })
  }

  const roleLabel = user?.role?.name
    ? (ROLE_LABELS[user.role.name] ?? user.role.name)
    : ""

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/60 lg:px-8">
      <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
        <SheetTrigger asChild>
          <Button variant="ghost" size="icon" className="lg:hidden" aria-label="Menyu">
            <Menu className="h-5 w-5" />
          </Button>
        </SheetTrigger>
        <SheetContent side="left" className="w-72 p-0">
          <SheetTitle className="sr-only">Navigatsiya</SheetTitle>
          <Sidebar onNavigate={() => setMobileOpen(false)} />
        </SheetContent>
      </Sheet>

      <div className="flex-1" />

      <ThemeToggle />

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" className="h-auto gap-2 px-2 py-1.5">
            <Avatar className="h-9 w-9">
              <AvatarFallback>{user ? getInitials(user.full_name) : "?"}</AvatarFallback>
            </Avatar>
            <span className="hidden text-left sm:block">
              <span className="block text-sm font-medium leading-tight">
                {user?.full_name}
              </span>
              <span className="block text-xs text-muted-foreground">{roleLabel}</span>
            </span>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-56">
          <DropdownMenuLabel>
            <div className="flex flex-col">
              <span>{user?.full_name}</span>
              <span className="text-xs font-normal text-muted-foreground">
                @{user?.username}
              </span>
            </div>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem
            onClick={handleLogout}
            className="text-destructive focus:text-destructive"
          >
            <LogOut /> Chiqish
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </header>
  )
}
