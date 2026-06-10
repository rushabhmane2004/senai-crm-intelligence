const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export async function fetchStats() {
  const res = await fetch(`${API_BASE_URL}/dashboard/stats`);
  if (!res.ok) throw new Error('Failed to fetch dashboard stats');
  return res.json();
}

export async function fetchEmailStatus(messageId) {
  const res = await fetch(`${API_BASE_URL}/api/status/${messageId}`);
  if (!res.ok) throw new Error(`Failed to fetch status for ${messageId}`);
  return res.json();
}

export async function fetchEmailAction(messageId) {
  const res = await fetch(`${API_BASE_URL}/api/actions/${messageId}`);
  if (!res.ok) throw new Error(`Failed to fetch action plan for ${messageId}`);
  return res.json();
}

export async function fetchThreadHistory(contactEmail) {
  const res = await fetch(`${API_BASE_URL}/threads/${contactEmail}`);
  if (!res.ok) throw new Error(`Failed to fetch thread history for ${contactEmail}`);
  return res.json();
}
