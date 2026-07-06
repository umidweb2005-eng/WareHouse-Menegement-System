/** Shared formatting helpers. */

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return "—"
  return new Intl.DateTimeFormat("uz-UZ", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date)
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return "—"
  return new Intl.DateTimeFormat("uz-UZ", { dateStyle: "medium" }).format(date)
}

export function formatMoney(value: string | number | null | undefined): string {
  const num = typeof value === "string" ? Number(value) : (value ?? 0)
  const safe = Number.isFinite(num) ? num : 0
  return new Intl.NumberFormat("uz-UZ", { maximumFractionDigits: 2 }).format(safe)
}
