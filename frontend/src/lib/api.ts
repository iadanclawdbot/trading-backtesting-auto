const API_URL = process.env.NEXT_PUBLIC_API_URL;

if (!API_URL) {
  throw new Error("NEXT_PUBLIC_API_URL no esta definida en .env.local");
}

export async function fetcher<T>(endpoint: string): Promise<T> {
  const res = await fetch(`${API_URL}${endpoint}`, {
    next: { revalidate: 0 }, // siempre fetch fresco en server
  });

  if (!res.ok) {
    throw new Error(`Error ${res.status} en ${endpoint}`);
  }

  return res.json();
}
