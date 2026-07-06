import { useState } from "react"

import { zodResolver } from "@hookform/resolvers/zod"
import { LogIn, Warehouse } from "lucide-react"
import { useForm } from "react-hook-form"
import { Navigate, useLocation, useNavigate } from "react-router-dom"
import { toast } from "sonner"
import { z } from "zod"

import { Spinner } from "@/components/common/Loading"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { normalizeError } from "@/lib/axios"
import { useAuth } from "@/providers/auth-provider"

const loginSchema = z.object({
  username: z.string().min(1, "Login kiriting"),
  password: z.string().min(1, "Parol kiriting"),
})

type LoginValues = z.infer<typeof loginSchema>

export function LoginPage() {
  const { login, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [submitting, setSubmitting] = useState(false)

  const form = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { username: "", password: "" },
  })

  const from = (location.state as { from?: string } | null)?.from ?? "/dashboard"

  if (isAuthenticated) {
    return <Navigate to={from} replace />
  }

  async function onSubmit(values: LoginValues) {
    setSubmitting(true)
    try {
      await login(values.username, values.password)
      toast.success("Tizimga muvaffaqiyatli kirdingiz")
      navigate(from, { replace: true })
    } catch (error) {
      const apiError = normalizeError(error)
      const message =
        apiError.status === 401 ? "Login yoki parol noto'g'ri" : apiError.message
      toast.error(message)
      form.setError("password", { message })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/40 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-3 text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-primary text-primary-foreground">
            <Warehouse className="h-7 w-7" />
          </div>
          <div className="space-y-1">
            <CardTitle className="text-2xl">Ombor Boshqaruv Tizimi</CardTitle>
            <CardDescription>
              Davom etish uchun tizimga kiring
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-5">
              <FormField
                control={form.control}
                name="username"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Login</FormLabel>
                    <FormControl>
                      <Input placeholder="admin" autoComplete="username" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Parol</FormLabel>
                    <FormControl>
                      <Input
                        type="password"
                        placeholder="••••••••"
                        autoComplete="current-password"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <Button type="submit" size="lg" className="w-full" disabled={submitting}>
                {submitting ? <Spinner /> : <LogIn />}
                Kirish
              </Button>
            </form>
          </Form>
        </CardContent>
      </Card>
    </div>
  )
}
