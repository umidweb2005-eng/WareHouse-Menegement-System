import { z } from "zod"

export const supplierSchema = z.object({
  name: z.string().min(1, "Nomi majburiy").max(200, "Nomi juda uzun (maks. 200)"),
  phone: z.string().max(30, "Telefon juda uzun (maks. 30)"),
  responsible_person: z.string().max(150, "Juda uzun (maks. 150)"),
  address: z.string().max(255, "Manzil juda uzun (maks. 255)"),
  description: z.string().max(1000, "Izoh juda uzun"),
  is_active: z.boolean(),
})

export type SupplierFormValues = z.infer<typeof supplierSchema>
