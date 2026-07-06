import { z } from "zod"

const nonNegative = z.coerce
  .number({ invalid_type_error: "Raqam kiriting" })
  .min(0, "Manfiy bo'lishi mumkin emas")

export const productSchema = z.object({
  name: z.string().min(1, "Nomi majburiy").max(200, "Nomi juda uzun (maks. 200)"),
  sku: z.string().min(1, "SKU majburiy").max(60, "SKU juda uzun (maks. 60)"),
  barcode: z.string().max(60, "Shtrix kod juda uzun (maks. 60)"),
  category_id: z.coerce
    .number({ invalid_type_error: "Kategoriyani tanlang" })
    .int()
    .positive("Kategoriyani tanlang"),
  unit_id: z.coerce
    .number({ invalid_type_error: "Birlikni tanlang" })
    .int()
    .positive("Birlikni tanlang"),
  purchase_price: nonNegative,
  sale_price: nonNegative,
  min_quantity: nonNegative,
  quantity: nonNegative,
  description: z.string().max(1000, "Izoh juda uzun"),
  is_active: z.boolean(),
})

export type ProductFormValues = z.infer<typeof productSchema>
