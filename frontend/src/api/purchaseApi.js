import api, { unwrap } from './axios'

export const fetchPurchases = (params) => api.get('/purchases', { params }).then(unwrap)
export const createPurchase = (payload) => api.post('/purchases', payload).then(unwrap)
export const updatePurchase = (id, payload) => api.put(`/purchases/${id}`, payload).then(unwrap)
export const deletePurchase = (id) => api.delete(`/purchases/${id}`).then(unwrap)
