import { z } from "zod"

export const categorySchema = z.object({
  name: z.string().min(1, "Nomi majburiy").max(150, "Nomi juda uzun (maks. 150)"),
  description: z.string().max(1000, "Izoh juda uzun"),
  is_active: z.boolean(),
})

export type CategoryFormValues = z.infer<typeof categorySchema>
