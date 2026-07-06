export interface ListParams {
  page: number
  page_size: number
  search?: string
}

/** Central query-key factory for stable, granular cache invalidation. */
export const queryKeys = {
  categories: {
    all: ["categories"] as const,
    list: (params: ListParams) => ["categories", "list", params] as const,
    detail: (id: number) => ["categories", "detail", id] as const,
  },
  units: {
    all: ["units"] as const,
    list: (params: ListParams) => ["units", "list", params] as const,
    detail: (id: number) => ["units", "detail", id] as const,
  },
}
