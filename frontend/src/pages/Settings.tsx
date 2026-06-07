import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AlertCircle, CheckCircle, Plus, ToggleLeft, ToggleRight, Trash2 } from 'lucide-react'
import { api } from '../api/client'
import type { Webhook } from '../types'

export default function Settings() {
  const qc = useQueryClient()
  const { data: appSettings } = useQuery({ queryKey: ['app-settings'], queryFn: api.settings.app })
  const { data: webhooks = [] } = useQuery({ queryKey: ['webhooks'], queryFn: api.settings.webhooks })

  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ name: '', webhook_type: 'discord', url: '' })

  const invalidateWebhooks = () => qc.invalidateQueries({ queryKey: ['webhooks'] })

  const createMutation = useMutation({
    mutationFn: () => api.settings.createWebhook(form),
    onSuccess: () => {
      invalidateWebhooks()
      setForm({ name: '', webhook_type: 'discord', url: '' })
      setShowForm(false)
    },
  })

  const toggleMutation = useMutation({
    mutationFn: (wh: Webhook) => api.settings.updateWebhook(wh.id, { enabled: !wh.enabled }),
    onSuccess: invalidateWebhooks,
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.settings.deleteWebhook(id),
    onSuccess: invalidateWebhooks,
  })

  const inputClass =
    'w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none focus:ring-1 focus:ring-green-500'

  return (
    <div className="p-8 max-w-3xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Settings</h1>
        <p className="text-slate-400 mt-1">Configure your availability checker</p>
      </div>

      {/* Status */}
      <Section title="Status">
        <StatusRow
          label="RIDB API Key"
          ok={appSettings?.ridb_api_key_configured ?? false}
          okText="Configured"
          failText="Not set — search is disabled. Get a free key at ridb.recreation.gov/apikeys and set RIDB_API_KEY in .env"
        />
        <div className="flex items-center justify-between text-sm pt-2 border-t border-slate-800">
          <span className="text-slate-300">Check interval</span>
          <span className="text-slate-400">
            {appSettings ? `${appSettings.check_interval_minutes} min` : '—'}
          </span>
        </div>
      </Section>

      {/* Webhooks */}
      <Section
        title="Webhooks"
        action={
          <button
            onClick={() => setShowForm((f) => !f)}
            className="flex items-center gap-1.5 text-sm text-green-400 hover:text-green-300 transition-colors"
          >
            <Plus className="size-4" />
            Add webhook
          </button>
        }
      >
        {showForm && (
          <form
            onSubmit={(e) => { e.preventDefault(); createMutation.mutate() }}
            className="mb-4 p-4 rounded-lg bg-slate-800 border border-slate-700 grid grid-cols-2 gap-3"
          >
            <div className="col-span-2">
              <label className="text-xs text-slate-400 mb-1 block">Name</label>
              <input
                required
                placeholder="My Discord server"
                value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                className={inputClass}
              />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Type</label>
              <select
                value={form.webhook_type}
                onChange={(e) => setForm((f) => ({ ...f, webhook_type: e.target.value }))}
                className={inputClass}
              >
                <option value="discord">Discord</option>
                <option value="slack">Slack</option>
                <option value="generic">Generic (JSON POST)</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Webhook URL</label>
              <input
                required
                type="url"
                placeholder="https://discord.com/api/webhooks/…"
                value={form.url}
                onChange={(e) => setForm((f) => ({ ...f, url: e.target.value }))}
                className={inputClass}
              />
            </div>
            <div className="col-span-2 flex items-center justify-between">
              {createMutation.isError && (
                <p className="text-xs text-red-400">{(createMutation.error as Error).message}</p>
              )}
              <div className="flex gap-2 ml-auto">
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="px-3 py-2 text-sm text-slate-400 hover:text-slate-100 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="px-4 py-2 rounded-lg bg-green-500 hover:bg-green-400 text-slate-950 font-medium text-sm transition-colors disabled:opacity-50"
                >
                  {createMutation.isPending ? 'Adding…' : 'Add'}
                </button>
              </div>
            </div>
          </form>
        )}

        {webhooks.length === 0 && !showForm ? (
          <p className="text-sm text-slate-500 py-4 text-center">
            No webhooks configured. Add one to receive notifications.
          </p>
        ) : (
          <div className="space-y-0 divide-y divide-slate-800">
            {webhooks.map((wh) => (
              <div key={wh.id} className="flex items-center justify-between py-3">
                <div>
                  <p className="text-sm text-slate-200">{wh.name}</p>
                  <p className="text-xs text-slate-500 mt-0.5 capitalize">
                    {wh.webhook_type} · {wh.url.length > 50 ? `${wh.url.slice(0, 50)}…` : wh.url}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => toggleMutation.mutate(wh)}
                    title={wh.enabled ? 'Disable' : 'Enable'}
                    className="transition-colors"
                  >
                    {wh.enabled ? (
                      <ToggleRight className="size-6 text-green-400 hover:text-green-300" />
                    ) : (
                      <ToggleLeft className="size-6 text-slate-500 hover:text-slate-300" />
                    )}
                  </button>
                  <button
                    onClick={() => deleteMutation.mutate(wh.id)}
                    title="Delete"
                    className="text-slate-500 hover:text-red-400 transition-colors"
                  >
                    <Trash2 className="size-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Section>
    </div>
  )
}

function Section({
  title,
  action,
  children,
}: {
  title: string
  action?: React.ReactNode
  children: React.ReactNode
}) {
  return (
    <section className="rounded-xl bg-slate-900 border border-slate-800 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{title}</h2>
        {action}
      </div>
      <div className="space-y-3">{children}</div>
    </section>
  )
}

function StatusRow({
  label,
  ok,
  okText,
  failText,
}: {
  label: string
  ok: boolean
  okText: string
  failText: string
}) {
  return (
    <div className="flex items-start justify-between gap-4 text-sm">
      <span className="text-slate-300 shrink-0">{label}</span>
      <div className={`flex items-start gap-1.5 text-right ${ok ? 'text-green-400' : 'text-amber-400'}`}>
        {ok ? <CheckCircle className="size-4 shrink-0 mt-0.5" /> : <AlertCircle className="size-4 shrink-0 mt-0.5" />}
        <span>{ok ? okText : failText}</span>
      </div>
    </div>
  )
}
