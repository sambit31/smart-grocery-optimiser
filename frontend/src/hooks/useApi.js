import { useCallback, useEffect, useState } from 'react'
import { getErrorMessage } from '../api/axios'

/**
 * Load data from an API function and track loading / error state.
 *   const { data, loading, error, reload } = useApi(() => fetchThing(id), [id])
 */
export function useApi(loader, deps = []) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const run = useCallback(loader, deps)

  const reload = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await run()
      setData(result)
      return result
    } catch (err) {
      setError(getErrorMessage(err))
      return null
    } finally {
      setLoading(false)
    }
  }, [run])

  useEffect(() => {
    reload()
  }, [reload])

  return { data, setData, loading, error, reload }
}
