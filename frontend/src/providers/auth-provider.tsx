import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react"

import { authApi } from "@/features/auth/api"
import { tokenStorage } from "@/lib/token-storage"
import type { User } from "@/types"

interface AuthContextValue {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Bootstrap the session from a stored token on first load.
  useEffect(() => {
    let active = true
    async function bootstrap() {
      if (!tokenStorage.getAccess()) {
        setIsLoading(false)
        return
      }
      try {
        const me = await authApi.me()
        if (active) setUser(me)
      } catch {
        tokenStorage.clear()
      } finally {
        if (active) setIsLoading(false)
      }
    }
    void bootstrap()
    return () => {
      active = false
    }
  }, [])

  const login = useCallback(async (username: string, password: string) => {
    const token = await authApi.login(username, password)
    tokenStorage.set(token.access_token, token.refresh_token)
    const me = await authApi.me()
    setUser(me)
  }, [])

  const logout = useCallback(async () => {
    try {
      await authApi.logout()
    } catch {
      // Logout is best-effort; clear the client session regardless.
    }
    tokenStorage.clear()
    setUser(null)
  }, [])

  const value: AuthContextValue = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    logout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
