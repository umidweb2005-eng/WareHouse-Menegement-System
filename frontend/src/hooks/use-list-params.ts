import { useSearchParams } from "react-router-dom"

/**
 * URL-backed list state (page + search) so lists are deep-linkable and survive
 * refresh. Reused by every resource list page.
 */
export function useListParams(pageSize = 20) {
  const [searchParams, setSearchParams] = useSearchParams()

  const page = Math.max(1, Number(searchParams.get("page")) || 1)
  const search = searchParams.get("search") ?? ""

  function setPage(next: number) {
    setSearchParams(
      (prev) => {
        const params = new URLSearchParams(prev)
        params.set("page", String(next))
        return params
      },
      { replace: true },
    )
  }

  function setSearch(value: string) {
    setSearchParams(
      (prev) => {
        const params = new URLSearchParams(prev)
        if (value) params.set("search", value)
        else params.delete("search")
        params.set("page", "1")
        return params
      },
      { replace: true },
    )
  }

  return { page, pageSize, search, setPage, setSearch }
}
