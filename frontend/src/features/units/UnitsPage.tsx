import { useEffect, useMemo, useState } from "react"

import { Pencil, Plus, Ruler, Trash2 } from "lucide-react"
import { toast } from "sonner"

import { ConfirmDialog } from "@/components/common/ConfirmDialog"
import { EmptyState } from "@/components/common/EmptyState"
import { ErrorState } from "@/components/common/ErrorState"
import { PageHeader } from "@/components/common/PageHeader"
import { Pagination } from "@/components/data-table/Pagination"
import { SearchInput } from "@/components/data-table/SearchInput"
import { TableSkeleton } from "@/components/data-table/TableSkeleton"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { useDebounce } from "@/hooks/use-debounce"
import { useListParams } from "@/hooks/use-list-params"
import { normalizeError } from "@/lib/axios"
import { hasPermission } from "@/config/permissions"
import { useAuth } from "@/providers/auth-provider"
import type { Unit } from "@/types"

import { UnitFormDialog } from "./UnitFormDialog"
import { useDeleteUnit, useUnits } from "./queries"

export function UnitsPage() {
  const { user } = useAuth()
  const canManage = hasPermission(user, "unit.manage")

  const { page, pageSize, search, setPage, setSearch } = useListParams()
  const [searchText, setSearchText] = useState(search)
  const debouncedSearch = useDebounce(searchText, 400)

  useEffect(() => {
    if (debouncedSearch !== search) {
      setSearch(debouncedSearch)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedSearch])

  const listParams = useMemo(
    () => ({ page, page_size: pageSize, search: search || undefined }),
    [page, pageSize, search],
  )

  const { data, isLoading, isError, error, refetch, isFetching } = useUnits(listParams)

  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<Unit | null>(null)
  const [deleting, setDeleting] = useState<Unit | null>(null)
  const deleteMutation = useDeleteUnit()

  function openCreate() {
    setEditing(null)
    setFormOpen(true)
  }

  function openEdit(unit: Unit) {
    setEditing(unit)
    setFormOpen(true)
  }

  async function confirmDelete() {
    if (!deleting) return
    try {
      await deleteMutation.mutateAsync(deleting.id)
      toast.success("Birlik o'chirildi")
      setDeleting(null)
    } catch (err) {
      toast.error(normalizeError(err).message)
    }
  }

  const items = data?.items ?? []

  return (
    <div className="space-y-6">
      <PageHeader
        title="Birliklar"
        description="O'lchov birliklarini boshqaring"
        action={
          canManage ? (
            <Button onClick={openCreate}>
              <Plus /> Yangi birlik
            </Button>
          ) : undefined
        }
      />

      <Card>
        <CardHeader>
          <SearchInput
            value={searchText}
            onChange={setSearchText}
            placeholder="Nomi yoki qisqartma bo'yicha qidirish..."
          />
        </CardHeader>
        <CardContent>
          {isError ? (
            <ErrorState message={normalizeError(error).message} onRetry={() => refetch()} />
          ) : (
            <>
              <div className={isFetching ? "opacity-60 transition-opacity" : undefined}>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Nomi</TableHead>
                      <TableHead>Qisqartma</TableHead>
                      <TableHead>Holat</TableHead>
                      {canManage && <TableHead className="text-right">Amallar</TableHead>}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {isLoading ? (
                      <TableSkeleton rows={5} columns={canManage ? 4 : 3} />
                    ) : items.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={canManage ? 4 : 3} className="border-0">
                          <EmptyState
                            icon={Ruler}
                            title="Birliklar topilmadi"
                            description={
                              search
                                ? "Qidiruv bo'yicha natija yo'q"
                                : "Hozircha birlik qo'shilmagan"
                            }
                            action={
                              canManage && !search ? (
                                <Button onClick={openCreate}>
                                  <Plus /> Birlik qo'shish
                                </Button>
                              ) : undefined
                            }
                          />
                        </TableCell>
                      </TableRow>
                    ) : (
                      items.map((unit) => (
                        <TableRow key={unit.id}>
                          <TableCell className="font-medium">{unit.name}</TableCell>
                          <TableCell className="text-muted-foreground">
                            {unit.short_name}
                          </TableCell>
                          <TableCell>
                            {unit.is_active ? (
                              <Badge variant="success">Faol</Badge>
                            ) : (
                              <Badge variant="secondary">Nofaol</Badge>
                            )}
                          </TableCell>
                          {canManage && (
                            <TableCell className="text-right">
                              <div className="flex justify-end gap-1">
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  aria-label="Tahrirlash"
                                  onClick={() => openEdit(unit)}
                                >
                                  <Pencil className="h-4 w-4" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  aria-label="O'chirish"
                                  className="text-destructive hover:text-destructive"
                                  onClick={() => setDeleting(unit)}
                                >
                                  <Trash2 className="h-4 w-4" />
                                </Button>
                              </div>
                            </TableCell>
                          )}
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>

              {data && items.length > 0 && (
                <div className="mt-4">
                  <Pagination meta={data.meta} onPageChange={setPage} />
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      <UnitFormDialog open={formOpen} onOpenChange={setFormOpen} unit={editing} />

      <ConfirmDialog
        open={Boolean(deleting)}
        onOpenChange={(open) => {
          if (!open) setDeleting(null)
        }}
        title="Birlikni o'chirish"
        description={`"${deleting?.name ?? ""}" birligini o'chirmoqchimisiz?`}
        confirmLabel="O'chirish"
        destructive
        loading={deleteMutation.isPending}
        onConfirm={confirmDelete}
      />
    </div>
  )
}
