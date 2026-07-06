import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query"

import { categoriesApi } from "@/features/categories/api"
import { unitsApi } from "@/features/units/api"
import { queryKeys, type ProductListParams } from "@/lib/query-keys"
import type { ProductInput } from "@/types"

import { productsApi } from "./api"

// Selector option sets reuse the existing category/unit APIs (no duplication).
const OPTIONS_PARAMS = { page: 1, page_size: 200 } as const

export function useProducts(params: ProductListParams) {
  return useQuery({
    queryKey: queryKeys.products.list(params),
    queryFn: () => productsApi.list(params),
    placeholderData: keepPreviousData,
  })
}

export function useCategoryOptions() {
  return useQuery({
    queryKey: queryKeys.categories.list(OPTIONS_PARAMS),
    queryFn: () => categoriesApi.list(OPTIONS_PARAMS),
    staleTime: 60_000,
  })
}

export function useUnitOptions() {
  return useQuery({
    queryKey: queryKeys.units.list(OPTIONS_PARAMS),
    queryFn: () => unitsApi.list(OPTIONS_PARAMS),
    staleTime: 60_000,
  })
}

export function useCreateProduct() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: ProductInput) => productsApi.create(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.products.all }),
  })
}

export function useUpdateProduct() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: ProductInput }) =>
      productsApi.update(id, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.products.all }),
  })
}

export function useDeleteProduct() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => productsApi.remove(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.products.all }),
  })
}
