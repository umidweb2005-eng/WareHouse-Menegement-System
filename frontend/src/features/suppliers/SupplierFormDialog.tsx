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
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Switch } from "@/components/ui/switch"
import { Textarea } from "@/components/ui/textarea"
import { normalizeError } from "@/lib/axios"
import type { Supplier } from "@/types"

import { useCreateSupplier, useUpdateSupplier } from "./queries"
import { supplierSchema, type SupplierFormValues } from "./schema"

const EMPTY: SupplierFormValues = {
  name: "",
  phone: "",
  responsible_person: "",
  address: "",
  description: "",
  is_active: true,
}

/** Convert an optional trimmed string to null when empty (backend contract). */
function orNull(value: string): string | null {
  const trimmed = value.trim()
  return trimmed ? trimmed : null
}

export function SupplierFormDialog({
  open,
  onOpenChange,
  supplier,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  supplier: Supplier | null
}) {
  const isEdit = Boolean(supplier)
  const createMutation = useCreateSupplier()
  const updateMutation = useUpdateSupplier()
  const pending = createMutation.isPending || updateMutation.isPending

  const form = useForm<SupplierFormValues>({
    resolver: zodResolver(supplierSchema),
    defaultValues: EMPTY,
  })

  useEffect(() => {
    if (open) {
      form.reset(
        supplier
          ? {
              name: supplier.name,
              phone: supplier.phone ?? "",
              responsible_person: supplier.responsible_person ?? "",
              address: supplier.address ?? "",
              description: supplier.description ?? "",
              is_active: supplier.is_active,
            }
          : EMPTY,
      )
    }
  }, [open, supplier, form])

  async function onSubmit(values: SupplierFormValues) {
    const payload = {
      name: values.name.trim(),
      phone: orNull(values.phone),
      responsible_person: orNull(values.responsible_person),
      address: orNull(values.address),
      description: orNull(values.description),
      is_active: values.is_active,
    }
    try {
      if (isEdit && supplier) {
        await updateMutation.mutateAsync({ id: supplier.id, payload })
        toast.success("Yetkazib beruvchi yangilandi")
      } else {
        await createMutation.mutateAsync(payload)
        toast.success("Yetkazib beruvchi qo'shildi")
      }
      onOpenChange(false)
    } catch (error) {
      toast.error(normalizeError(error).message)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {isEdit ? "Yetkazib beruvchini tahrirlash" : "Yangi yetkazib beruvchi"}
          </DialogTitle>
          <DialogDescription>Yetkazib beruvchi ma'lumotlarini kiriting.</DialogDescription>
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
                    <Input placeholder="Masalan: Agro Trade MChJ" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <div className="grid gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="phone"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Telefon</FormLabel>
                    <FormControl>
                      <Input placeholder="+998 90 123 45 67" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="responsible_person"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Mas'ul shaxs</FormLabel>
                    <FormControl>
                      <Input placeholder="Ixtiyoriy" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            <FormField
              control={form.control}
              name="address"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Manzil</FormLabel>
                  <FormControl>
                    <Input placeholder="Ixtiyoriy" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
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
                  <div className="space-y-0.5">
                    <FormLabel>Faol</FormLabel>
                    <FormDescription>Nofaol yetkazib beruvchilar ro'yxatda ko'rinmaydi.</FormDescription>
                  </div>
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
