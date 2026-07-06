import { Spinner } from "@/components/common/Loading"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { buttonVariants } from "@/components/ui/button"
import { cn } from "@/lib/utils"

export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel = "Tasdiqlash",
  cancelLabel = "Bekor qilish",
  onConfirm,
  loading = false,
  destructive = false,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description?: string
  confirmLabel?: string
  cancelLabel?: string
  onConfirm: () => void
  loading?: boolean
  destructive?: boolean
}) {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{title}</AlertDialogTitle>
          {description && <AlertDialogDescription>{description}</AlertDialogDescription>}
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={loading}>{cancelLabel}</AlertDialogCancel>
          <AlertDialogAction
            onClick={(event) => {
              event.preventDefault()
              onConfirm()
            }}
            disabled={loading}
            className={cn(destructive && buttonVariants({ variant: "destructive" }))}
          >
            {loading && <Spinner className="mr-2 h-4 w-4" />}
            {confirmLabel}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
