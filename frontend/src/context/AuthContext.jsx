import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import toast from 'react-hot-toast'
import { fetchCurrentUser, loginUser, logoutUser, registerUser } from '../api/authApi'
import { fetchHousehold } from '../api/householdApi'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [household, setHousehold] = useState(null)
  const [loading, setLoading] = useState(true)

  const loadSession = useCallback(async () => {
    try {
      const { user: currentUser } = await fetchCurrentUser()
      setUser(currentUser)
      const { household: currentHousehold } = await fetchHousehold()
      setHousehold(currentHousehold)
    } catch {
      setUser(null)
      setHousehold(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadSession()
  }, [loadSession])

  // Fired by the Axios interceptor when the backend answers 401.
  useEffect(() => {
    const onExpired = () => {
      if (user) toast.error('Your session has expired. Please log in again.')
      setUser(null)
      setHousehold(null)
    }
    window.addEventListener('auth:expired', onExpired)
    return () => window.removeEventListener('auth:expired', onExpired)
  }, [user])

  const login = async (credentials) => {
    const { user: loggedIn } = await loginUser(credentials)
    setUser(loggedIn)
    const { household: existing } = await fetchHousehold()
    setHousehold(existing)
    return { user: loggedIn, household: existing }
  }

  const register = async (details) => {
    const { user: created } = await registerUser(details)
    setUser(created)
    setHousehold(null)
    return created
  }

  const logout = async () => {
    try {
      await logoutUser()
    } finally {
      setUser(null)
      setHousehold(null)
    }
  }

  const value = useMemo(
    () => ({ user, household, setHousehold, loading, login, register, logout }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [user, household, loading],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside <AuthProvider>')
  return context
}
