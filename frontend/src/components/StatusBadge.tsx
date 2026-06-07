import clsx from 'clsx'

const VARIANTS = {
  watching: 'bg-blue-500/10 text-blue-400 ring-blue-500/20',
  found: 'bg-green-500/10 text-green-400 ring-green-500/20',
  paused: 'bg-slate-500/10 text-slate-400 ring-slate-500/20',
} as const

type Status = keyof typeof VARIANTS

export default function StatusBadge({ status }: { status: Status }) {
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ring-1 ring-inset',
        VARIANTS[status],
      )}
    >
      {status === 'watching' && (
        <span className="size-1.5 rounded-full bg-blue-400 animate-pulse" />
      )}
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  )
}
