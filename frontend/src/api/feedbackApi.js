import api, { unwrap } from './axios'

export const fetchFeedback = () => api.get('/feedback').then(unwrap)
export const submitFeedback = (payload) => api.post('/feedback', payload).then(unwrap)
