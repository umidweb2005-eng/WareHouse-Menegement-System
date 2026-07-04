import { Loader2 } from "lucide-react"

import { cn } from "@/lib/utils"

export function Spinner({ className }: { className?: string }) {
  return <Loader2 className={cn("h-5 w-5 animate-spin", className)} />
}

export function FullPageLoader({ label = "Yuklanmoqda..." }: { label?: string }) {
  return (
    <div className="flex h-screen w-full flex-col items-center justify-center gap-3 text-muted-foreground">
      <Loader2 className="h-8 w-8 animate-spin text-primary" />
      <p className="text-sm">{label}</p>
    </div>
  )
}
