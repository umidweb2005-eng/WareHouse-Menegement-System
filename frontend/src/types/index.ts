/**
 * API types mirroring the FastAPI backend contracts (app/schemas).
 * Phase 1 only needs the auth-related shapes; later phases extend this file
 * (or replace it with `openapi-typescript` generated types).
 */

export type RoleName =
  | "admin"
  | "manager"
  | "warehouse_worker"
  | "cashier"
  | "viewer"

export interface Token {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface RoleSummary {
  id: number
  name: string
}

export interface User {
  id: number
  username: string
  full_name: string
  email: string | null
  phone: string | null
  is_active: boolean
  is_superuser: boolean
  role_id: number
  role: RoleSummary | null
  last_login_at: string | null
  created_at: string
}

export interface PageMeta {
  page: number
  page_size: number
  total: number
  total_pages: number
  has_next: boolean
  has_prev: boolean
}

export interface Paginated<T> {
  items: T[]
  meta: PageMeta
}

export interface MessageResponse {
  detail: string
}

/** Normalised error shape produced by the axios interceptor. */
export interface ApiError {
  status: number
  message: string
  fieldErrors?: Record<string, string>
}


// --- Categories ---
export interface Category {
  id: number
  name: string
  description: string | null
  is_active: boolean
  created_at: string
}

/** Payload for creating/updating a category (CategoryCreate / CategoryUpdate). */
export interface CategoryInput {
  name: string
  description?: string | null
  is_active: boolean
}


// --- Units ---
export interface Unit {
  id: number
  name: string
  short_name: string
  is_active: boolean
}

/** Payload for creating/updating a unit (UnitCreate / UnitUpdate). */
export interface UnitInput {
  name: string
  short_name: string
  is_active: boolean
}
