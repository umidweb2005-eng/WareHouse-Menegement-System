import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query"

import { queryKeys, type ListParams } from "@/lib/query-keys"
import type { CategoryInput } from "@/types"

import { categoriesApi } from "./api"

export function useCategories(params: ListParams) {
  return useQuery({
    queryKey: queryKeys.categories.list(params),
    queryFn: () => categoriesApi.list(params),
    placeholderData: keepPreviousData,
  })
}

export function useCreateCategory() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: CategoryInput) => categoriesApi.create(payload),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.categories.all }),
  })
}

export function useUpdateCategory() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: CategoryInput }) =>
      categoriesApi.update(id, payload),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.categories.all }),
  })
}

export function useDeleteCategory() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => categoriesApi.remove(id),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.categories.all }),
  })
}
