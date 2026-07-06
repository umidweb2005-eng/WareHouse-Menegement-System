export interface ListParams {
  page: number
  page_size: number
  search?: string
}

export interface ProductListParams extends ListParams {
  category_id?: number
  low_stock?: boolean
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
  suppliers: {
    all: ["suppliers"] as const,
    list: (params: ListParams) => ["suppliers", "list", params] as const,
    detail: (id: number) => ["suppliers", "detail", id] as const,
  },
  products: {
    all: ["products"] as const,
    list: (params: ProductListParams) => ["products", "list", params] as const,
    detail: (id: number) => ["products", "detail", id] as const,
  },
}
