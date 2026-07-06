import { useEffect } from "react"

import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { toast } from "sonner"

import { Spinner } from "@/components/common/Loading"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Textarea } from "@/components/ui/textarea"
import { normalizeError } from "@/lib/axios"
import type { Product } from "@/types"

import { useCategoryOptions, useCreateProduct, useUnitOptions, useUpdateProduct } from "./queries"
import { productSchema, type ProductFormValues } from "./schema"

const EMPTY: ProductFormValues = {
  name: "",
  sku: "",
  barcode: "",
  category_id: 0,
  unit_id: 0,
  purchase_price: 0,
  sale_price: 0,
  min_quantity: 0,
  quantity: 0,
  description: "",
  is_active: true,
}

function orNull(value: string): string | null {
  const trimmed = value.trim()
  return trimmed ? trimmed : null
}

export function ProductFormDialog({
  open,
  onOpenChange,
  product,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  product: Product | null
}) {
  const isEdit = Boolean(product)
  const createMutation = useCreateProduct()
  const updateMutation = useUpdateProduct()
  const pending = createMutation.isPending || updateMutation.isPending

  const categoryOptions = useCategoryOptions()
  const unitOptions = useUnitOptions()
  const categories = categoryOptions.data?.items ?? []
  const units = unitOptions.data?.items ?? []

  const form = useForm<ProductFormValues>({
    resolver: zodResolver(productSchema),
    defaultValues: EMPTY,
  })

  useEffect(() => {
    if (open) {
      form.reset(
        product
          ? {
              name: product.name,
              sku: product.sku,
              barcode: product.barcode ?? "",
              category_id: product.category_id,
              unit_id: product.unit_id,
              purchase_price: Number(product.purchase_price),
              sale_price: Number(product.sale_price),
              min_quantity: Number(product.min_quantity),
              quantity: Number(product.quantity),
              description: product.description ?? "",
              is_active: product.is_active,
            }
          : EMPTY,
      )
    }
  }, [open, product, form])

  async function onSubmit(values: ProductFormValues) {
    const base = {
      name: values.name.trim(),
      sku: values.sku.trim(),
      barcode: orNull(values.barcode),
      category_id: values.category_id,
      unit_id: values.unit_id,
      purchase_price: values.purchase_price,
      sale_price: values.sale_price,
      min_quantity: values.min_quantity,
      description: orNull(values.description),
      is_active: values.is_active,
    }
    try {
      if (isEdit && product) {
        // ProductUpdate has no `quantity` (managed by stock operations).
        await updateMutation.mutateAsync({ id: product.id, payload: base })
        toast.success("Mahsulot yangilandi")
      } else {
        await createMutation.mutateAsync({ ...base, quantity: values.quantity })
        toast.success("Mahsulot qo'shildi")
      }
      onOpenChange(false)
    } catch (error) {
      const apiError = normalizeError(error)
      toast.error(apiError.message)
      if (apiError.status === 409) {
        form.setError("sku", { message: apiError.message })
      }
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>{isEdit ? "Mahsulotni tahrirlash" : "Yangi mahsulot"}</DialogTitle>
          <DialogDescription>Mahsulot ma'lumotlarini kiriting.</DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Nomi</FormLabel>
                  <FormControl>
                    <Input placeholder="Masalan: Ammiakli selitra" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="sku"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>SKU (kod)</FormLabel>
                    <FormControl>
                      <Input placeholder="SKU-001" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="barcode"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Shtrix kod</FormLabel>
                    <FormControl>
                      <Input placeholder="Ixtiyoriy" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="category_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Kategoriya</FormLabel>
                    <Select
                      value={field.value ? String(field.value) : ""}
                      onValueChange={(value) => field.onChange(Number(value))}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Tanlang" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {categories.map((category) => (
                          <SelectItem key={category.id} value={String(category.id)}>
                            {category.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="unit_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Birlik</FormLabel>
                    <Select
                      value={field.value ? String(field.value) : ""}
                      onValueChange={(value) => field.onChange(Number(value))}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Tanlang" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {units.map((unit) => (
                          <SelectItem key={unit.id} value={String(unit.id)}>
                            {unit.name} ({unit.short_name})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="purchase_price"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Sotib olish narxi</FormLabel>
                    <FormControl>
                      <Input type="number" min="0" step="0.01" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="sale_price"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Sotish narxi</FormLabel>
                    <FormControl>
                      <Input type="number" min="0" step="0.01" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="min_quantity"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Minimal miqdor</FormLabel>
                    <FormControl>
                      <Input type="number" min="0" step="0.001" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              {!isEdit && (
                <FormField
                  control={form.control}
                  name="quantity"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Boshlang'ich miqdor</FormLabel>
                      <FormControl>
                        <Input type="number" min="0" step="0.001" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              )}
            </div>

            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Izoh</FormLabel>
                  <FormControl>
                    <Textarea rows={2} placeholder="Ixtiyoriy" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="is_active"
              render={({ field }) => (
                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-3">
                  <FormLabel>Faol</FormLabel>
                  <FormControl>
                    <Switch checked={field.value} onCheckedChange={field.onChange} />
                  </FormControl>
                </FormItem>
              )}
            />

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={pending}
              >
                Bekor qilish
              </Button>
              <Button type="submit" disabled={pending}>
                {pending && <Spinner className="mr-2 h-4 w-4" />}
                {isEdit ? "Saqlash" : "Qo'shish"}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
