interface PillProps {
  children: React.ReactNode
  active?: boolean
  onClick?: (e?: React.MouseEvent) => void
  className?: string
}

export default function Pill({ children, active = false, onClick, className = "" }: PillProps) {
  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (onClick) {
      onClick(e)
    }
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      className={`px-3 py-1 rounded-full border text-sm transition ${
        active
          ? "bg-black text-white border-black"
          : "bg-white/80 backdrop-blur border-gray-300 hover:bg-white"
      } ${className}`}
    >
      {children}
    </button>
  )
}

