import type { AppSettings, CampgroundResult, WatchlistEntry, Webhook } from '../types'

const BASE = '/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(body.detail ?? 'Request failed')
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const api = {
  search: (q: string) =>
    request<CampgroundResult[]>(`/search?q=${encodeURIComponent(q)}`),

  watchlist: {
    list: () => request<WatchlistEntry[]>('/watchlist'),
    create: (body: object) =>
      request<WatchlistEntry>('/watchlist', { method: 'POST', body: JSON.stringify(body) }),
    update: (id: number, body: object) =>
      request<WatchlistEntry>(`/watchlist/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
    delete: (id: number) => request<void>(`/watchlist/${id}`, { method: 'DELETE' }),
    check: (id: number) =>
      request<WatchlistEntry>(`/watchlist/${id}/check`, { method: 'POST' }),
  },

  settings: {
    app: () => request<AppSettings>('/settings/app'),
    webhooks: () => request<Webhook[]>('/settings/webhooks'),
    createWebhook: (body: object) =>
      request<Webhook>('/settings/webhooks', { method: 'POST', body: JSON.stringify(body) }),
    updateWebhook: (id: number, body: object) =>
      request<Webhook>(`/settings/webhooks/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
    deleteWebhook: (id: number) =>
      request<void>(`/settings/webhooks/${id}`, { method: 'DELETE' }),
  },
}
