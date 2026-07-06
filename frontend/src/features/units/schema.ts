import { z } from "zod"

export const unitSchema = z.object({
  name: z.string().min(1, "Nomi majburiy").max(50, "Nomi juda uzun (maks. 50)"),
  short_name: z
    .string()
    .min(1, "Qisqartma majburiy")
    .max(20, "Qisqartma juda uzun (maks. 20)"),
  is_active: z.boolean(),
})

export type UnitFormValues = z.infer<typeof unitSchema>
