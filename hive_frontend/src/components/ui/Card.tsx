interface CardProps {
  title: string
  subtitle?: string
  desc?: string
  hours?: number
  distanceKm?: number
  tags?: string[]
  cta?: string
  onClick?: () => void
}

export default function Card({
  title,
  subtitle,
  desc,
  hours,
  distanceKm,
  tags = [],
  cta,
  onClick,
}: CardProps) {
  return (
    <div className="rounded-2xl border border-gray-200 bg-white/80 backdrop-blur shadow-sm p-4 flex flex-col gap-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-gray-900">{title}</h3>
          {subtitle && <p className="text-sm text-gray-600">{subtitle}</p>}
        </div>
        {(hours !== undefined || distanceKm !== undefined) && (
          <div className="text-right">
            {hours !== undefined && (
              <div className="text-sm font-semibold">⏱️ {hours} saat</div>
            )}
            {distanceKm !== undefined && (
              <div className="text-xs text-gray-500">📍 {distanceKm.toFixed(1)} km</div>
            )}
          </div>
        )}
      </div>
      {desc && <p className="text-sm text-gray-700 leading-relaxed">{desc}</p>}
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {tags.map((t) => (
            <span
              key={t}
              className="px-2 py-0.5 text-xs rounded-full border border-gray-300 bg-white/70"
            >
              #{t}
            </span>
          ))}
        </div>
      )}
      {cta && (
        <div className="pt-1">
          <button
            onClick={onClick}
            className="w-full rounded-xl bg-black text-white py-2 text-sm font-medium hover:opacity-90"
          >
            {cta}
          </button>
        </div>
      )}
    </div>
  )
}

