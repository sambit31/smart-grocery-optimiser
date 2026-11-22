import api, { unwrap } from './axios'

export const optimisePlanBudget = (planId) =>
  api.post(`/recommendations/${planId}/optimise-budget`).then(unwrap)
