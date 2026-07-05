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
import type { Category } from "@/types"

import { useCreateCategory, useUpdateCategory } from "./queries"
import { categorySchema, type CategoryFormValues } from "./schema"

export function CategoryFormDialog({
  open,
  onOpenChange,
  category,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  category: Category | null
}) {
  const isEdit = Boolean(category)
  const createMutation = useCreateCategory()
  const updateMutation = useUpdateCategory()
  const pending = createMutation.isPending || updateMutation.isPending

  const form = useForm<CategoryFormValues>({
    resolver: zodResolver(categorySchema),
    defaultValues: { name: "", description: "", is_active: true },
  })

  useEffect(() => {
    if (open) {
      form.reset({
        name: category?.name ?? "",
        description: category?.description ?? "",
        is_active: category?.is_active ?? true,
      })
    }
  }, [open, category, form])

  async function onSubmit(values: CategoryFormValues) {
    const payload = {
      name: values.name.trim(),
      description: values.description.trim() ? values.description.trim() : null,
      is_active: values.is_active,
    }
    try {
      if (isEdit && category) {
        await updateMutation.mutateAsync({ id: category.id, payload })
        toast.success("Kategoriya yangilandi")
      } else {
        await createMutation.mutateAsync(payload)
        toast.success("Kategoriya qo'shildi")
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
          <DialogTitle>
            {isEdit ? "Kategoriyani tahrirlash" : "Yangi kategoriya"}
          </DialogTitle>
          <DialogDescription>Kategoriya ma'lumotlarini kiriting.</DialogDescription>
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
                    <Input placeholder="Masalan: O'g'itlar" {...field} />
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
                    <Textarea rows={3} placeholder="Ixtiyoriy" {...field} />
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
                    <FormDescription>Nofaol kategoriyalar ro'yxatda ko'rinmaydi.</FormDescription>
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
