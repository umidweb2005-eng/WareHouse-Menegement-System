import { ChevronLeft, ChevronRight } from "lucide-react"

import { Button } from "@/components/ui/button"
import type { PageMeta } from "@/types"

export function Pagination({
  meta,
  onPageChange,
}: {
  meta: PageMeta
  onPageChange: (page: number) => void
}) {
  return (
    <div className="flex flex-col items-center justify-between gap-3 sm:flex-row">
      <p className="text-sm text-muted-foreground">
        Jami {meta.total} ta · {meta.page}/{Math.max(meta.total_pages, 1)}-sahifa
      </p>
      <div className="flex gap-2">
        <Button
          variant="outline"
          size="sm"
          disabled={!meta.has_prev}
          onClick={() => onPageChange(meta.page - 1)}
        >
          <ChevronLeft className="h-4 w-4" />
          Oldingi
        </Button>
        <Button
          variant="outline"
          size="sm"
          disabled={!meta.has_next}
          onClick={() => onPageChange(meta.page + 1)}
        >
          Keyingi
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}
