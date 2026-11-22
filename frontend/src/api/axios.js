import axios from 'axios'

// One shared Axios instance for every API call.
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  withCredentials: true, // send the HttpOnly auth cookie
  headers: { 'Content-Type': 'application/json' },
})

function readCookie(name) {
  const match = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'))
  return match ? decodeURIComponent(match[1]) : null
}

// CSRF protection: Flask-JWT-Extended sets a readable csrf_access_token
// cookie; we echo it back in a header on every state-changing request.
api.interceptors.request.use((config) => {
  const method = (config.method || 'get').toLowerCase()
  if (!['get', 'head', 'options'].includes(method)) {
    const token = readCookie('csrf_access_token')
    if (token) config.headers['X-CSRF-TOKEN'] = token
  }
  return config
})

// If the session expired, tell the app so it can return to the login page.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const url = error.config?.url || ''
    if (error.response?.status === 401 && !url.includes('/auth/')) {
      window.dispatchEvent(new CustomEvent('auth:expired'))
    }
    return Promise.reject(error)
  },
)

/** Turn any Axios error into a readable message for toasts and forms. */
export function getErrorMessage(error, fallback = 'Something went wrong. Please try again.') {
  if (error?.response?.data?.message) return error.response.data.message
  if (error?.request && !error.response) return 'Cannot reach the server. Is the backend running?'
  return fallback
}

/** Unwrap the { success, message, data } envelope. */
export const unwrap = (response) => response.data.data

export default api
