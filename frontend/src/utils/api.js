export async function apiFetch(url, options = {}) {
  const token = localStorage.getItem('token');
  const headers = new Headers(options.headers || {});
  
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  if (!headers.has('Content-Type') && !(options.body instanceof FormData) && !options.isFormEncoded) {
      headers.set('Content-Type', 'application/json');
  } else if (options.isFormEncoded) {
      headers.set('Content-Type', 'application/x-www-form-urlencoded');
  }

  const res = await fetch(url, {
    ...options,
    headers,
  });

  if (res.status === 401) {
    localStorage.removeItem('token');
    window.location.href = '/login';
  }

  return res;
}
