import { api } from "@/lib/axios"
import type { ListParams } from "@/lib/query-keys"
import type { MessageResponse, Paginated, Unit, UnitInput } from "@/types"

export const unitsApi = {
  async list(params: ListParams): Promise<Paginated<Unit>> {
    const { data } = await api.get<Paginated<Unit>>("/units", { params })
    return data
  },
  async create(payload: UnitInput): Promise<Unit> {
    const { data } = await api.post<Unit>("/units", payload)
    return data
  },
  async update(id: number, payload: UnitInput): Promise<Unit> {
    const { data } = await api.put<Unit>(`/units/${id}`, payload)
    return data
  },
  async remove(id: number): Promise<MessageResponse> {
    const { data } = await api.delete<MessageResponse>(`/units/${id}`)
    return data
  },
}
