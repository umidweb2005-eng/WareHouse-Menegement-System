import { useEffect, useMemo, useState } from "react"

import { Package, Pencil, Plus, Trash2 } from "lucide-react"
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
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
import { formatMoney } from "@/lib/format"
import { hasPermission } from "@/config/permissions"
import { useAuth } from "@/providers/auth-provider"
import type { Product } from "@/types"

import { ProductFormDialog } from "./ProductFormDialog"
import { useCategoryOptions, useDeleteProduct, useProducts } from "./queries"

const ALL = "all"

export function ProductsPage() {
  const { user } = useAuth()
  const canManage = hasPermission(user, "product.manage")

  const { page, pageSize, search, setPage, setSearch } = useListParams()
  const [searchText, setSearchText] = useState(search)
  const debouncedSearch = useDebounce(searchText, 400)
  const [categoryId, setCategoryId] = useState<string>(ALL)
  const [lowStock, setLowStock] = useState(false)

  useEffect(() => {
    if (debouncedSearch !== search) {
      setSearch(debouncedSearch)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedSearch])

  const categoryOptions = useCategoryOptions()
  const categories = categoryOptions.data?.items ?? []

  const listParams = useMemo(
    () => ({
      page,
      page_size: pageSize,
      search: search || undefined,
      category_id: categoryId !== ALL ? Number(categoryId) : undefined,
      low_stock: lowStock || undefined,
    }),
    [page, pageSize, search, categoryId, lowStock],
  )

  const { data, isLoading, isError, error, refetch, isFetching } = useProducts(listParams)

  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<Product | null>(null)
  const [deleting, setDeleting] = useState<Product | null>(null)
  const deleteMutation = useDeleteProduct()

  function openCreate() {
    setEditing(null)
    setFormOpen(true)
  }

  function openEdit(product: Product) {
    setEditing(product)
    setFormOpen(true)
  }

  function handleCategoryFilter(value: string) {
    setCategoryId(value)
    setPage(1)
  }

  function toggleLowStock() {
    setLowStock((prev) => !prev)
    setPage(1)
  }

  async function confirmDelete() {
    if (!deleting) return
    try {
      await deleteMutation.mutateAsync(deleting.id)
      toast.success("Mahsulot o'chirildi")
      setDeleting(null)
    } catch (err) {
      toast.error(normalizeError(err).message)
    }
  }

  const items = data?.items ?? []
  const columnCount = canManage ? 6 : 5

  return (
    <div className="space-y-6">
      <PageHeader
        title="Mahsulotlar"
        description="Ombordagi mahsulotlarni boshqaring"
        action={
          canManage ? (
            <Button onClick={openCreate}>
              <Plus /> Yangi mahsulot
            </Button>
          ) : undefined
        }
      />

      <Card>
        <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <SearchInput
            value={searchText}
            onChange={setSearchText}
            placeholder="Nomi, SKU yoki shtrix kod bo'yicha qidirish..."
          />
          <div className="flex gap-3">
            <Select value={categoryId} onValueChange={handleCategoryFilter}>
              <SelectTrigger className="w-full sm:w-52">
                <SelectValue placeholder="Kategoriya" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL}>Barcha kategoriyalar</SelectItem>
                {categories.map((category) => (
                  <SelectItem key={category.id} value={String(category.id)}>
                    {category.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button
              variant={lowStock ? "default" : "outline"}
              onClick={toggleLowStock}
              className="shrink-0"
            >
              Kam qolganlar
            </Button>
          </div>
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
                      <TableHead>Mahsulot</TableHead>
                      <TableHead>Kategoriya</TableHead>
                      <TableHead>Sotish narxi</TableHead>
                      <TableHead>Miqdor</TableHead>
                      <TableHead>Holat</TableHead>
                      {canManage && <TableHead className="text-right">Amallar</TableHead>}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {isLoading ? (
                      <TableSkeleton rows={6} columns={columnCount} />
                    ) : items.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={columnCount} className="border-0">
                          <EmptyState
                            icon={Package}
                            title="Mahsulotlar topilmadi"
                            description={
                              search || categoryId !== ALL || lowStock
                                ? "Filtr bo'yicha natija yo'q"
                                : "Hozircha mahsulot qo'shilmagan"
                            }
                            action={
                              canManage && !search && categoryId === ALL && !lowStock ? (
                                <Button onClick={openCreate}>
                                  <Plus /> Mahsulot qo'shish
                                </Button>
                              ) : undefined
                            }
                          />
                        </TableCell>
                      </TableRow>
                    ) : (
                      items.map((product) => (
                        <TableRow key={product.id}>
                          <TableCell>
                            <div className="font-medium">{product.name}</div>
                            <div className="text-xs text-muted-foreground">{product.sku}</div>
                          </TableCell>
                          <TableCell className="text-muted-foreground">
                            {product.category?.name ?? "—"}
                          </TableCell>
                          <TableCell>{formatMoney(product.sale_price)}</TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <span>
                                {formatMoney(product.quantity)} {product.unit?.short_name ?? ""}
                              </span>
                              {product.is_low_stock && (
                                <Badge variant="destructive">Kam</Badge>
                              )}
                            </div>
                          </TableCell>
                          <TableCell>
                            {product.is_active ? (
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
                                  onClick={() => openEdit(product)}
                                >
                                  <Pencil className="h-4 w-4" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  aria-label="O'chirish"
                                  className="text-destructive hover:text-destructive"
                                  onClick={() => setDeleting(product)}
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

      <ProductFormDialog open={formOpen} onOpenChange={setFormOpen} product={editing} />

      <ConfirmDialog
        open={Boolean(deleting)}
        onOpenChange={(open) => {
          if (!open) setDeleting(null)
        }}
        title="Mahsulotni o'chirish"
        description={`"${deleting?.name ?? ""}" mahsulotini o'chirmoqchimisiz?`}
        confirmLabel="O'chirish"
        destructive
        loading={deleteMutation.isPending}
        onConfirm={confirmDelete}
      />
    </div>
  )
}
