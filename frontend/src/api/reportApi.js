import api, { unwrap } from './axios'

export const fetchDashboardSummary = () => api.get('/dashboard/summary').then(unwrap)
export const fetchSpendingReport = (months) => api.get('/reports/spending', { params: { months } }).then(unwrap)
export const fetchConsumptionReport = (params) => api.get('/reports/consumption', { params }).then(unwrap)
export const fetchRecommendationReport = () => api.get('/reports/recommendations').then(unwrap)
