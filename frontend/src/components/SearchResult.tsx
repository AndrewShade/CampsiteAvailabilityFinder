import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { MapPin, Plus, X } from 'lucide-react'
import { api } from '../api/client'
import type { CampgroundResult } from '../types'

export default function SearchResult({ campground }: { campground: CampgroundResult }) {
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({ start_date: '', end_date: '', min_nights: 1, site_types: '' })
  const qc = useQueryClient()

  const addMutation = useMutation({
    mutationFn: () =>
      api.watchlist.create({
        campground_id: campground.facility_id,
        campground_name: campground.facility_name,
        park_name: campground.parent_name || campground.facility_name,
        ...form,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['watchlist'] })
      setOpen(false)
    },
  })

  const field = (id: keyof typeof form) => ({
    className:
      'w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none focus:ring-1 focus:ring-green-500',
  })

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="font-medium text-slate-100">{campground.facility_name}</h3>
          {campground.parent_name && (
            <p className="text-sm text-slate-400 mt-0.5">{campground.parent_name}</p>
          )}
          {(campground.city || campground.state) && (
            <p className="flex items-center gap-1 text-xs text-slate-500 mt-1">
              <MapPin className="size-3" />
              {[campground.city, campground.state].filter(Boolean).join(', ')}
            </p>
          )}
          {campground.description && (
            <p className="text-xs text-slate-500 mt-2 line-clamp-2">{campground.description}</p>
          )}
        </div>

        <button
          onClick={() => setOpen((o) => !o)}
          className="shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-green-500/10 text-green-400 hover:bg-green-500/20 transition-colors text-sm font-medium"
        >
          {open ? <X className="size-4" /> : <Plus className="size-4" />}
          {open ? 'Cancel' : 'Watch'}
        </button>
      </div>

      {open && (
        <form
          className="mt-4 pt-4 border-t border-slate-800 grid grid-cols-2 gap-3"
          onSubmit={(e) => { e.preventDefault(); addMutation.mutate() }}
        >
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Start date</label>
            <input
              type="date"
              required
              value={form.start_date}
              onChange={(e) => setForm((f) => ({ ...f, start_date: e.target.value }))}
              {...field('start_date')}
            />
          </div>
          <div>
            <label className="text-xs text-slate-400 mb-1 block">End date</label>
            <input
              type="date"
              required
              value={form.end_date}
              onChange={(e) => setForm((f) => ({ ...f, end_date: e.target.value }))}
              {...field('end_date')}
            />
          </div>
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Min nights</label>
            <input
              type="number"
              min={1}
              value={form.min_nights}
              onChange={(e) => setForm((f) => ({ ...f, min_nights: +e.target.value }))}
              {...field('min_nights')}
            />
          </div>
          <div>
            <label className="text-xs text-slate-400 mb-1 block">
              Site types <span className="text-slate-600">(optional)</span>
            </label>
            <input
              type="text"
              placeholder="e.g. STANDARD ELECTRIC"
              value={form.site_types}
              onChange={(e) => setForm((f) => ({ ...f, site_types: e.target.value }))}
              {...field('site_types')}
            />
          </div>
          <div className="col-span-2 flex items-center justify-between">
            {addMutation.isError && (
              <p className="text-xs text-red-400">{(addMutation.error as Error).message}</p>
            )}
            <button
              type="submit"
              disabled={addMutation.isPending}
              className="ml-auto px-4 py-2 rounded-lg bg-green-500 hover:bg-green-400 text-slate-950 font-medium text-sm transition-colors disabled:opacity-50"
            >
              {addMutation.isPending ? 'Adding…' : 'Add to Watchlist'}
            </button>
          </div>
        </form>
      )}
    </div>
  )
}
