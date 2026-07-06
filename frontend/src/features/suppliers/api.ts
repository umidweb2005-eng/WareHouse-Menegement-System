import { api } from "@/lib/axios"
import type { ListParams } from "@/lib/query-keys"
import type { MessageResponse, Paginated, Supplier, SupplierInput } from "@/types"

export const suppliersApi = {
  async list(params: ListParams): Promise<Paginated<Supplier>> {
    const { data } = await api.get<Paginated<Supplier>>("/suppliers", { params })
    return data
  },
  async create(payload: SupplierInput): Promise<Supplier> {
    const { data } = await api.post<Supplier>("/suppliers", payload)
    return data
  },
  async update(id: number, payload: SupplierInput): Promise<Supplier> {
    const { data } = await api.put<Supplier>(`/suppliers/${id}`, payload)
    return data
  },
  async remove(id: number): Promise<MessageResponse> {
    const { data } = await api.delete<MessageResponse>(`/suppliers/${id}`)
    return data
  },
}
