import { useEffect, useState } from 'react'
import { fetchOptions } from '../api/householdApi'

// Categories, units and priorities come from the backend (single source of truth).
let cached = null

export function useOptions() {
  const [options, setOptions] = useState(cached)

  useEffect(() => {
    if (cached) return
    fetchOptions()
      .then((data) => {
        cached = data
        setOptions(data)
      })
      .catch(() => setOptions({ categories: [], units: [], priorities: [], shopping_frequencies: [], frequency_days: {} }))
  }, [])

  return options
}
