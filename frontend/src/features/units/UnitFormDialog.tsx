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
import { normalizeError } from "@/lib/axios"
import type { Unit } from "@/types"

import { useCreateUnit, useUpdateUnit } from "./queries"
import { unitSchema, type UnitFormValues } from "./schema"

export function UnitFormDialog({
  open,
  onOpenChange,
  unit,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  unit: Unit | null
}) {
  const isEdit = Boolean(unit)
  const createMutation = useCreateUnit()
  const updateMutation = useUpdateUnit()
  const pending = createMutation.isPending || updateMutation.isPending

  const form = useForm<UnitFormValues>({
    resolver: zodResolver(unitSchema),
    defaultValues: { name: "", short_name: "", is_active: true },
  })

  useEffect(() => {
    if (open) {
      form.reset({
        name: unit?.name ?? "",
        short_name: unit?.short_name ?? "",
        is_active: unit?.is_active ?? true,
      })
    }
  }, [open, unit, form])

  async function onSubmit(values: UnitFormValues) {
    const payload = {
      name: values.name.trim(),
      short_name: values.short_name.trim(),
      is_active: values.is_active,
    }
    try {
      if (isEdit && unit) {
        await updateMutation.mutateAsync({ id: unit.id, payload })
        toast.success("Birlik yangilandi")
      } else {
        await createMutation.mutateAsync(payload)
        toast.success("Birlik qo'shildi")
      }
      onOpenChange(false)
    } catch (error) {
      const apiError = normalizeError(error)
      toast.error(apiError.message)
      if (apiError.status === 409) {
        form.setError("name", { message: apiError.message })
      }
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{isEdit ? "Birlikni tahrirlash" : "Yangi birlik"}</DialogTitle>
          <DialogDescription>O'lchov birligi ma'lumotlarini kiriting.</DialogDescription>
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
                    <Input placeholder="Masalan: Kilogramm" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="short_name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Qisqartma</FormLabel>
                  <FormControl>
                    <Input placeholder="Masalan: kg" {...field} />
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
                    <FormDescription>Nofaol birliklar tanlovda ko'rinmaydi.</FormDescription>
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
