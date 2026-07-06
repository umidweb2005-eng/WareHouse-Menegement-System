import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query"

import { queryKeys, type ListParams } from "@/lib/query-keys"
import type { UnitInput } from "@/types"

import { unitsApi } from "./api"

export function useUnits(params: ListParams) {
  return useQuery({
    queryKey: queryKeys.units.list(params),
    queryFn: () => unitsApi.list(params),
    placeholderData: keepPreviousData,
  })
}

export function useCreateUnit() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: UnitInput) => unitsApi.create(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.units.all }),
  })
}

export function useUpdateUnit() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: UnitInput }) =>
      unitsApi.update(id, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.units.all }),
  })
}

export function useDeleteUnit() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => unitsApi.remove(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.units.all }),
  })
}
