import { AlertTriangle } from "lucide-react"

import { Button } from "@/components/ui/button"

export function ErrorState({
  message,
  onRetry,
}: {
  message?: string
  onRetry?: () => void
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10">
        <AlertTriangle className="h-6 w-6 text-destructive" />
      </div>
      <div className="space-y-1">
        <h3 className="font-semibold">Xatolik yuz berdi</h3>
        <p className="text-sm text-muted-foreground">
          {message ?? "Ma'lumotlarni yuklab bo'lmadi"}
        </p>
      </div>
      {onRetry && (
        <Button variant="outline" onClick={onRetry}>
          Qayta urinish
        </Button>
      )}
    </div>
  )
}
