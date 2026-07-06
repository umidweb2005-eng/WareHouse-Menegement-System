import { useEffect, useMemo, useState } from "react"

import { Pencil, Plus, Trash2, Truck } from "lucide-react"
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
import type { Supplier } from "@/types"

import { SupplierFormDialog } from "./SupplierFormDialog"
import { useDeleteSupplier, useSuppliers } from "./queries"

export function SuppliersPage() {
  const { user } = useAuth()
  const canManage = hasPermission(user, "supplier.manage")

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

  const { data, isLoading, isError, error, refetch, isFetching } =
    useSuppliers(listParams)

  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<Supplier | null>(null)
  const [deleting, setDeleting] = useState<Supplier | null>(null)
  const deleteMutation = useDeleteSupplier()

  function openCreate() {
    setEditing(null)
    setFormOpen(true)
  }

  function openEdit(supplier: Supplier) {
    setEditing(supplier)
    setFormOpen(true)
  }

  async function confirmDelete() {
    if (!deleting) return
    try {
      await deleteMutation.mutateAsync(deleting.id)
      toast.success("Yetkazib beruvchi o'chirildi")
      setDeleting(null)
    } catch (err) {
      toast.error(normalizeError(err).message)
    }
  }

  const items = data?.items ?? []
  const columnCount = canManage ? 5 : 4

  return (
    <div className="space-y-6">
      <PageHeader
        title="Yetkazib beruvchilar"
        description="Mahsulot yetkazib beruvchilarni boshqaring"
        action={
          canManage ? (
            <Button onClick={openCreate}>
              <Plus /> Yangi yetkazib beruvchi
            </Button>
          ) : undefined
        }
      />

      <Card>
        <CardHeader>
          <SearchInput
            value={searchText}
            onChange={setSearchText}
            placeholder="Nomi, telefon yoki mas'ul shaxs bo'yicha qidirish..."
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
                      <TableHead>Telefon</TableHead>
                      <TableHead>Mas'ul shaxs</TableHead>
                      <TableHead>Holat</TableHead>
                      {canManage && <TableHead className="text-right">Amallar</TableHead>}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {isLoading ? (
                      <TableSkeleton rows={5} columns={columnCount} />
                    ) : items.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={columnCount} className="border-0">
                          <EmptyState
                            icon={Truck}
                            title="Yetkazib beruvchilar topilmadi"
                            description={
                              search
                                ? "Qidiruv bo'yicha natija yo'q"
                                : "Hozircha yetkazib beruvchi qo'shilmagan"
                            }
                            action={
                              canManage && !search ? (
                                <Button onClick={openCreate}>
                                  <Plus /> Yetkazib beruvchi qo'shish
                                </Button>
                              ) : undefined
                            }
                          />
                        </TableCell>
                      </TableRow>
                    ) : (
                      items.map((supplier) => (
                        <TableRow key={supplier.id}>
                          <TableCell className="font-medium">{supplier.name}</TableCell>
                          <TableCell className="text-muted-foreground">
                            {supplier.phone || "—"}
                          </TableCell>
                          <TableCell className="text-muted-foreground">
                            {supplier.responsible_person || "—"}
                          </TableCell>
                          <TableCell>
                            {supplier.is_active ? (
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
                                  onClick={() => openEdit(supplier)}
                                >
                                  <Pencil className="h-4 w-4" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  aria-label="O'chirish"
                                  className="text-destructive hover:text-destructive"
                                  onClick={() => setDeleting(supplier)}
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

      <SupplierFormDialog open={formOpen} onOpenChange={setFormOpen} supplier={editing} />

      <ConfirmDialog
        open={Boolean(deleting)}
        onOpenChange={(open) => {
          if (!open) setDeleting(null)
        }}
        title="Yetkazib beruvchini o'chirish"
        description={`"${deleting?.name ?? ""}" o'chirilsinmi?`}
        confirmLabel="O'chirish"
        destructive
        loading={deleteMutation.isPending}
        onConfirm={confirmDelete}
      />
    </div>
  )
}
