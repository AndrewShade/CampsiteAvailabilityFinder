import { useQuery } from '@tanstack/react-query'
import { CheckCircle, Eye, PauseCircle, Tent } from 'lucide-react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import WatchlistCard from '../components/WatchlistCard'
import type { WatchlistEntry } from '../types'

export default function Dashboard() {
  const { data: entries = [], isLoading } = useQuery({
    queryKey: ['watchlist'],
    queryFn: api.watchlist.list,
    refetchInterval: 60_000,
  })

  const watching = entries.filter((e) => e.status === 'watching').length
  const found = entries.filter((e) => e.status === 'found').length
  const paused = entries.filter((e) => e.status === 'paused').length

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-100">Dashboard</h1>
        <p className="text-slate-400 mt-1">
          Monitoring {entries.length} campground{entries.length !== 1 ? 's' : ''} for availability
        </p>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-8">
        <StatCard icon={Eye} label="Watching" value={watching} color="blue" />
        <StatCard icon={CheckCircle} label="Available" value={found} color="green" />
        <StatCard icon={PauseCircle} label="Paused" value={paused} color="slate" />
      </div>

      {isLoading && (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-28 rounded-xl bg-slate-900 border border-slate-800 animate-pulse" />
          ))}
        </div>
      )}

      {!isLoading && entries.length === 0 && (
        <div className="text-center py-20 border border-dashed border-slate-800 rounded-xl">
          <Tent className="size-12 text-slate-700 mx-auto mb-4" />
          <p className="text-slate-400 font-medium">No campgrounds being monitored</p>
          <p className="text-slate-600 text-sm mt-1 mb-6">Search for a campground to get started</p>
          <Link
            to="/search"
            className="inline-flex items-center px-4 py-2 rounded-lg bg-green-500 hover:bg-green-400 text-slate-950 font-medium text-sm transition-colors"
          >
            Search Campgrounds
          </Link>
        </div>
      )}

      {!isLoading && entries.length > 0 && (
        <div className="space-y-4">
          {entries.map((entry: WatchlistEntry) => (
            <WatchlistCard key={entry.id} entry={entry} />
          ))}
        </div>
      )}
    </div>
  )
}

function StatCard({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: React.ElementType
  label: string
  value: number
  color: 'blue' | 'green' | 'slate'
}) {
  const iconColors = { blue: 'bg-blue-500/10 text-blue-400', green: 'bg-green-500/10 text-green-400', slate: 'bg-slate-500/10 text-slate-400' }
  return (
    <div className="rounded-xl bg-slate-900 border border-slate-800 p-4">
      <div className={`inline-flex p-2 rounded-lg mb-3 ${iconColors[color]}`}>
        <Icon className="size-5" />
      </div>
      <p className="text-2xl font-bold text-slate-100">{value}</p>
      <p className="text-sm text-slate-500 mt-0.5">{label}</p>
    </div>
  )
}
