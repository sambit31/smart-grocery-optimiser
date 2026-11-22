import api, { unwrap } from './axios'

export const registerUser = (payload) => api.post('/auth/register', payload).then(unwrap)
export const loginUser = (payload) => api.post('/auth/login', payload).then(unwrap)
export const logoutUser = () => api.post('/auth/logout').then(unwrap)
export const fetchCurrentUser = () => api.get('/auth/me').then(unwrap)
