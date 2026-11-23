import api, { unwrap } from "./axios";

export const getAIInsights = async () => {
  const response = await api.post("/ai/insights");
  return unwrap(response);
};

export const sendAIMessage = async (question, history = []) => {
  const response = await api.post("/ai/chat", {
    question,
    history,
  });

  return unwrap(response);
};

export const getAIShoppingRecommendations = async () => {
  const response = await api.post("/ai/recommendations");
  return unwrap(response);
};