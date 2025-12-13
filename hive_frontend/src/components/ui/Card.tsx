interface CardProps {
  title: string
  subtitle?: string
  desc?: string
  hours?: number
  distanceKm?: number
  tags?: string[]
  cta?: string
  onClick?: () => void
  onTagClick?: (tag: string) => void
  onOwnerClick?: (ownerId: number) => void
  ownerId?: number
  ownerName?: string
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
  onTagClick,
  onOwnerClick,
  ownerId,
  ownerName: propOwnerName,
}: CardProps) {
  const subtitleParts = subtitle?.split(' • ') || []
  const subtitleOwnerName = subtitleParts[0]?.trim()
  const ownerName = propOwnerName || subtitleOwnerName

  return (
    <div className="rounded-2xl border border-gray-200 bg-white/80 backdrop-blur shadow-sm p-4 flex flex-col gap-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 
            className={`text-base font-semibold text-gray-900 ${onClick ? 'hover:underline cursor-pointer' : ''}`}
            onClick={onClick}
            role={onClick ? 'button' : undefined}
            tabIndex={onClick ? 0 : undefined}
            onKeyDown={onClick ? (e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault()
                onClick()
              }
            } : undefined}
          >
            {title}
          </h3>
          {(subtitle || ownerName) && (
            <p className="text-sm text-gray-600">
              {ownerName && ownerId && onOwnerClick ? (
                <>
                  <span
                    onClick={(e) => {
                      e.preventDefault()
                      e.stopPropagation()
                      console.log('Owner clicked:', ownerId, ownerName)
                      onOwnerClick(ownerId)
                    }}
                    className="hover:underline cursor-pointer font-medium text-gray-800"
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault()
                        e.stopPropagation()
                        onOwnerClick(ownerId)
                      }
                    }}
                  >
                    {ownerName}
                  </span>
                  {subtitle && ` • ${subtitle}`}
                </>
              ) : (
                <>
                  {ownerName && `${ownerName}`}
                  {ownerName && subtitle && ` • `}
                  {subtitle}
                </>
              )}
            </p>
          )}
        </div>
        {(hours !== undefined || distanceKm !== undefined) && (
          <div className="text-right">
            {hours !== undefined && (
              <div className="text-sm font-semibold">⏱️ {hours} hours</div>
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
              onClick={(e) => {
                e.stopPropagation()
                if (onTagClick) {
                  onTagClick(t)
                }
              }}
              className={`px-2 py-0.5 text-xs rounded-full border border-gray-300 bg-white/70 ${
                onTagClick ? 'cursor-pointer hover:bg-gray-100 hover:border-gray-400' : ''
              }`}
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

