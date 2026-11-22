import api, { unwrap } from './axios'

export const generatePlan = (payload = {}) => api.post('/predictions/generate', payload).then(unwrap)
export const fetchLatestPlan = () => api.get('/predictions/latest').then(unwrap)
export const fetchPlans = () => api.get('/recommendations').then(unwrap)
export const fetchPlan = (id) => api.get(`/recommendations/${id}`).then(unwrap)
export const updatePlanItem = (planId, lineId, payload) =>
  api.patch(`/recommendations/${planId}/items/${lineId}`, payload).then(unwrap)
export const markPlanItemPurchased = (planId, lineId, payload = {}) =>
  api.post(`/recommendations/${planId}/items/${lineId}/mark-purchased`, payload).then(unwrap)
