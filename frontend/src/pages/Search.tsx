import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { AlertCircle, Search as SearchIcon } from 'lucide-react'
import { api } from '../api/client'
import SearchResult from '../components/SearchResult'

export default function Search() {
  const [input, setInput] = useState('')
  const [query, setQuery] = useState('')

  const { data, isLoading, error } = useQuery({
    queryKey: ['search', query],
    queryFn: () => api.search(query),
    enabled: query.length >= 2,
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = input.trim()
    if (trimmed.length >= 2) setQuery(trimmed)
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-100">Search Campgrounds</h1>
        <p className="text-slate-400 mt-1">
          Find campgrounds on Recreation.gov to add to your watchlist
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex gap-3 mb-8">
        <div className="relative flex-1">
          <SearchIcon className="absolute left-3.5 top-1/2 -translate-y-1/2 size-4 text-slate-500 pointer-events-none" />
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Search by park or campground name…"
            className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-10 pr-4 py-3 text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-green-500"
          />
        </div>
        <button
          type="submit"
          disabled={input.trim().length < 2}
          className="px-5 py-3 rounded-xl bg-green-500 hover:bg-green-400 text-slate-950 font-semibold transition-colors disabled:opacity-40"
        >
          Search
        </button>
      </form>

      {error && (
        <div className="flex items-start gap-2 text-sm text-red-400 mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20">
          <AlertCircle className="size-4 shrink-0 mt-0.5" />
          {(error as Error).message}
        </div>
      )}

      {isLoading && (
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-24 rounded-xl bg-slate-900 border border-slate-800 animate-pulse" />
          ))}
        </div>
      )}

      {data && data.length === 0 && (
        <p className="text-center text-slate-500 py-16">No campgrounds found for "{query}"</p>
      )}

      {data && data.length > 0 && (
        <div className="space-y-3">
          {data.map((cg) => (
            <SearchResult key={cg.facility_id} campground={cg} />
          ))}
        </div>
      )}
    </div>
  )
}
