import api, { unwrap } from './axios'

export const fetchConsumption = (params) => api.get('/consumption', { params }).then(unwrap)
export const createConsumption = (payload) => api.post('/consumption', payload).then(unwrap)
export const updateConsumption = (id, payload) => api.put(`/consumption/${id}`, payload).then(unwrap)
export const deleteConsumption = (id) => api.delete(`/consumption/${id}`).then(unwrap)
