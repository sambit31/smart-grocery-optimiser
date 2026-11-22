import api, { unwrap } from './axios'

export const fetchInventory = (params) => api.get('/inventory', { params }).then(unwrap)
export const addInventory = (payload) => api.post('/inventory', payload).then(unwrap)
export const updateInventory = (id, payload) => api.put(`/inventory/${id}`, payload).then(unwrap)
export const adjustInventory = (id, change, reason) =>
  api.patch(`/inventory/${id}/quantity`, { change, reason }).then(unwrap)
