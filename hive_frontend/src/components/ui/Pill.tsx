interface PillProps {
  children: React.ReactNode
  active?: boolean
  onClick?: () => void
  className?: string
}

export default function Pill({ children, active = false, onClick, className = "" }: PillProps) {
  return (
    <button
      onClick={onClick}
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

