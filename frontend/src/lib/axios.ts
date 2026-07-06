import axios, {
  AxiosError,
  type AxiosRequestConfig,
  type InternalAxiosRequestConfig,
} from "axios"

import type { ApiError, Token } from "@/types"

import { tokenStorage } from "./token-storage"

const BASE_URL = import.meta.env.VITE_API_URL || "/api/v1"

export const api = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
})

// ---------------------------------------------------------------------------
// Request: attach bearer token
// ---------------------------------------------------------------------------
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = tokenStorage.getAccess()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ---------------------------------------------------------------------------
// Response: refresh access token once on 401, then retry the original request
// ---------------------------------------------------------------------------
let isRefreshing = false
let waiters: Array<(token: string | null) => void> = []

function onRefreshed(token: string | null) {
  waiters.forEach((cb) => cb(token))
  waiters = []
}

function forceLogout() {
  tokenStorage.clear()
  if (window.location.pathname !== "/login") {
    window.location.assign("/login")
  }
}

async function requestNewAccessToken(): Promise<string | null> {
  const refresh = tokenStorage.getRefresh()
  if (!refresh) return null
  try {
    // Use a bare axios call to avoid interceptor recursion.
    const { data } = await axios.post<Token>(`${BASE_URL}/auth/refresh`, {
      refresh_token: refresh,
    })
    tokenStorage.set(data.access_token, data.refresh_token)
    return data.access_token
  } catch {
    return null
  }
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as (AxiosRequestConfig & { _retry?: boolean }) | undefined
    const status = error.response?.status

    const isAuthEndpoint =
      typeof original?.url === "string" &&
      (original.url.includes("/auth/login") || original.url.includes("/auth/refresh"))

    if (status === 401 && original && !original._retry && !isAuthEndpoint) {
      original._retry = true

      if (isRefreshing) {
        // Queue until the in-flight refresh completes.
        return new Promise((resolve, reject) => {
          waiters.push((token) => {
            if (!token) {
              reject(error)
              return
            }
            original.headers = { ...original.headers, Authorization: `Bearer ${token}` }
            resolve(api(original))
          })
        })
      }

      isRefreshing = true
      const newToken = await requestNewAccessToken()
      isRefreshing = false
      onRefreshed(newToken)

      if (!newToken) {
        forceLogout()
        return Promise.reject(error)
      }
      original.headers = { ...original.headers, Authorization: `Bearer ${newToken}` }
      return api(original)
    }

    return Promise.reject(error)
  },
)

/** Convert any axios error into a stable, UI-friendly shape. */
export function normalizeError(error: unknown): ApiError {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status ?? 0
    const data = error.response?.data as
      | { detail?: string; errors?: Array<{ loc?: (string | number)[]; msg?: string }> }
      | undefined

    const fieldErrors: Record<string, string> = {}
    if (Array.isArray(data?.errors)) {
      for (const e of data.errors) {
        const field = e.loc?.[e.loc.length - 1]
        if (field !== undefined && e.msg) fieldErrors[String(field)] = e.msg
      }
    }

    return {
      status,
      message:
        data?.detail ||
        (status === 0 ? "Serverga ulanib bo'lmadi" : "Kutilmagan xatolik yuz berdi"),
      fieldErrors: Object.keys(fieldErrors).length ? fieldErrors : undefined,
    }
  }
  return { status: 0, message: "Kutilmagan xatolik yuz berdi" }
}
