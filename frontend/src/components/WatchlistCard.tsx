import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ChevronDown, ChevronUp, ExternalLink, Pause, Play, RefreshCw, Trash2 } from 'lucide-react'
import { format } from 'date-fns'
import clsx from 'clsx'
import { api } from '../api/client'
import type { WatchlistEntry } from '../types'
import StatusBadge from './StatusBadge'

export default function WatchlistCard({ entry }: { entry: WatchlistEntry }) {
  const [expanded, setExpanded] = useState(entry.status === 'found')
  const qc = useQueryClient()
  const invalidate = () => qc.invalidateQueries({ queryKey: ['watchlist'] })

  const checkMutation = useMutation({ mutationFn: () => api.watchlist.check(entry.id), onSuccess: invalidate })
  const togglePause = useMutation({
    mutationFn: () =>
      api.watchlist.update(entry.id, { status: entry.status === 'paused' ? 'watching' : 'paused' }),
    onSuccess: invalidate,
  })
  const deleteMutation = useMutation({ mutationFn: () => api.watchlist.delete(entry.id), onSuccess: invalidate })

  return (
    <div
      className={clsx(
        'rounded-xl border bg-slate-900 overflow-hidden',
        entry.status === 'found' ? 'border-green-500/30' : 'border-slate-800',
      )}
    >
      {/* Header */}
      <div className="px-5 py-4">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="font-semibold text-slate-100 truncate">{entry.campground_name}</h3>
              <StatusBadge status={entry.status} />
            </div>
            <p className="text-sm text-slate-400 mt-0.5">{entry.park_name}</p>
          </div>

          <div className="flex items-center gap-1 shrink-0">
            <button
              onClick={() => checkMutation.mutate()}
              disabled={checkMutation.isPending}
              title="Check now"
              className="p-2 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={clsx('size-4', checkMutation.isPending && 'animate-spin')} />
            </button>
            <button
              onClick={() => togglePause.mutate()}
              title={entry.status === 'paused' ? 'Resume' : 'Pause'}
              className="p-2 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-colors"
            >
              {entry.status === 'paused' ? <Play className="size-4" /> : <Pause className="size-4" />}
            </button>
            <button
              onClick={() => deleteMutation.mutate()}
              title="Delete"
              className="p-2 rounded-lg text-slate-400 hover:text-red-400 hover:bg-slate-800 transition-colors"
            >
              <Trash2 className="size-4" />
            </button>
          </div>
        </div>

        <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-sm text-slate-400">
          <span>
            <span className="text-slate-500">Dates: </span>
            {entry.start_date} → {entry.end_date}
          </span>
          <span>
            <span className="text-slate-500">Min nights: </span>
            {entry.min_nights}
          </span>
          {entry.site_types && (
            <span>
              <span className="text-slate-500">Types: </span>
              {entry.site_types}
            </span>
          )}
          {entry.last_checked && (
            <span className="text-slate-600 text-xs self-center">
              Checked {format(new Date(entry.last_checked), 'MMM d, h:mm a')}
            </span>
          )}
        </div>
      </div>

      {/* Available sites */}
      {entry.results.length > 0 && (
        <>
          <button
            onClick={() => setExpanded((e) => !e)}
            className="w-full px-5 py-2.5 border-t border-slate-800 flex items-center justify-between hover:bg-slate-800/50 transition-colors"
          >
            <span className="text-sm font-medium text-green-400">
              {entry.results.length} site{entry.results.length !== 1 ? 's' : ''} available
            </span>
            {expanded ? (
              <ChevronUp className="size-4 text-slate-500" />
            ) : (
              <ChevronDown className="size-4 text-slate-500" />
            )}
          </button>

          {expanded && (
            <div className="divide-y divide-slate-800/60">
              {entry.results.map((result) => {
                const dates: string[] = JSON.parse(result.available_dates)
                return (
                  <div key={result.id} className="px-5 py-3 flex items-start justify-between gap-4">
                    <div>
                      <p className="text-sm font-medium text-slate-200">{result.campsite_name}</p>
                      <p className="text-xs text-slate-500 mt-0.5">
                        {result.site_type}
                        {result.loop ? ` · ${result.loop}` : ''}
                      </p>
                      <p className="text-xs text-green-400 mt-1">
                        {dates[0]}
                        {dates.length > 1 ? ` – ${dates[dates.length - 1]}` : ''}
                        <span className="text-slate-500">
                          {' '}({dates.length} night{dates.length !== 1 ? 's' : ''})
                        </span>
                      </p>
                    </div>
                    <a
                      href={`https://www.recreation.gov/camping/campsites/${result.campsite_id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="shrink-0 flex items-center gap-1.5 text-xs text-green-400 hover:text-green-300 transition-colors mt-0.5"
                    >
                      Book <ExternalLink className="size-3" />
                    </a>
                  </div>
                )
              })}
            </div>
          )}
        </>
      )}
    </div>
  )
}
