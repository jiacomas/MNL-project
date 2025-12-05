import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const PENALTIES_BASE = `${API_URL}/penalties`;

export async function searchPenalties({ token, filters, page, pageSize }) {
  const params = {
    page,
    page_size: pageSize,
  };

  if (filters.user_id) params.user_id = filters.user_id;
  if (filters.penalty_type) params.penalty_type = filters.penalty_type;
  if (filters.severity) params.severity = filters.severity;
  if (filters.is_active !== '') params.is_active = filters.is_active === 'true';

  const res = await axios.get(`${PENALTIES_BASE}/search`, {
    headers: { Authorization: `Bearer ${token}` },
    params,
  });

  return res.data;
}

export async function createPenalty({ token, data }) {
  const res = await axios.post(`${PENALTIES_BASE}/`, data, {
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });
  return res.data;
}

export async function updatePenalty({ token, penaltyId, data }) {
  const res = await axios.patch(`${PENALTIES_BASE}/${penaltyId}`, data, {
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });
  return res.data;
}

export async function deletePenalty({ token, penaltyId }) {
  await axios.delete(`${PENALTIES_BASE}/${penaltyId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function deactivatePenalty({ token, penaltyId }) {
  await axios.post(
    `${PENALTIES_BASE}/${penaltyId}/deactivate`,
    null,
    {
      headers: { Authorization: `Bearer ${token}` },
    }
  );
}
