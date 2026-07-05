import { api } from "@/lib/axios"
import type { ListParams } from "@/lib/query-keys"
import type { Category, CategoryInput, MessageResponse, Paginated } from "@/types"

export const categoriesApi = {
  async list(params: ListParams): Promise<Paginated<Category>> {
    const { data } = await api.get<Paginated<Category>>("/categories", { params })
    return data
  },
  async create(payload: CategoryInput): Promise<Category> {
    const { data } = await api.post<Category>("/categories", payload)
    return data
  },
  async update(id: number, payload: CategoryInput): Promise<Category> {
    const { data } = await api.put<Category>(`/categories/${id}`, payload)
    return data
  },
  async remove(id: number): Promise<MessageResponse> {
    const { data } = await api.delete<MessageResponse>(`/categories/${id}`)
    return data
  },
}
