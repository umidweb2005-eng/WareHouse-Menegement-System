import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query"

import { queryKeys, type ListParams } from "@/lib/query-keys"
import type { SupplierInput } from "@/types"

import { suppliersApi } from "./api"

export function useSuppliers(params: ListParams) {
  return useQuery({
    queryKey: queryKeys.suppliers.list(params),
    queryFn: () => suppliersApi.list(params),
    placeholderData: keepPreviousData,
  })
}

export function useCreateSupplier() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: SupplierInput) => suppliersApi.create(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.suppliers.all }),
  })
}

export function useUpdateSupplier() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: SupplierInput }) =>
      suppliersApi.update(id, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.suppliers.all }),
  })
}

export function useDeleteSupplier() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => suppliersApi.remove(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.suppliers.all }),
  })
}
