export async function api(path, { token, headers, ...options } = {}) {
  const response = await fetch(`/api/v1${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...headers, ...(token ? { Authorization: `Bearer ${token}` } : {}) },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const message = typeof body.detail === 'string' ? body.detail : Array.isArray(body.detail)
      ? body.detail.map(item => `${item.loc.slice(1).join('.')}: ${item.msg}`).join(';')
      : 'Request failed. Check your input and try again.';
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }
  return response.status === 204 ? null : response.json();
}
