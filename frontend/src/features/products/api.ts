import { api } from "@/lib/axios"
import type { ProductListParams } from "@/lib/query-keys"
import type { MessageResponse, Paginated, Product, ProductInput } from "@/types"

export const productsApi = {
  async list(params: ProductListParams): Promise<Paginated<Product>> {
    const { data } = await api.get<Paginated<Product>>("/products", { params })
    return data
  },
  async create(payload: ProductInput): Promise<Product> {
    const { data } = await api.post<Product>("/products", payload)
    return data
  },
  async update(id: number, payload: ProductInput): Promise<Product> {
    const { data } = await api.put<Product>(`/products/${id}`, payload)
    return data
  },
  async remove(id: number): Promise<MessageResponse> {
    const { data } = await api.delete<MessageResponse>(`/products/${id}`)
    return data
  },
}
