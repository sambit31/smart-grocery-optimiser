import api, { unwrap } from './axios'

export const fetchGroceries = (params) => api.get('/groceries', { params }).then(unwrap)
export const fetchGrocery = (id) => api.get(`/groceries/${id}`).then(unwrap)
export const createGrocery = (payload) => api.post('/groceries', payload).then((r) => r.data)
export const updateGrocery = (id, payload) => api.put(`/groceries/${id}`, payload).then(unwrap)
export const deleteGrocery = (id) => api.delete(`/groceries/${id}`).then((r) => r.data)

/** All active items (for dropdowns). */
export const fetchAllGroceries = () =>
  fetchGroceries({ per_page: 100, sort: 'name' }).then((d) => d.items)
