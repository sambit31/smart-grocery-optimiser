import api, { unwrap } from './axios'

export const fetchHousehold = () => api.get('/household').then(unwrap)
export const createHousehold = (payload) => api.post('/household', payload).then(unwrap)
export const updateHousehold = (payload) => api.put('/household', payload).then(unwrap)
export const fetchOptions = () => api.get('/meta/options').then(unwrap)
