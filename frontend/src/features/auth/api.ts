import { api } from "@/lib/axios"
import type { MessageResponse, Token, User } from "@/types"

export const authApi = {
  /** OAuth2 password login — must be sent as form-urlencoded. */
  async login(username: string, password: string): Promise<Token> {
    const body = new URLSearchParams()
    body.set("username", username)
    body.set("password", password)
    const { data } = await api.post<Token>("/auth/login", body, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    })
    return data
  },

  async me(): Promise<User> {
    const { data } = await api.get<User>("/auth/me")
    return data
  },

  async logout(): Promise<MessageResponse> {
    const { data } = await api.post<MessageResponse>("/auth/logout")
    return data
  },
}
