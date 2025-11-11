interface TextInputProps {
  label?: string
  type?: string
  value: string
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  placeholder?: string
  autoComplete?: string
  rightSlot?: React.ReactNode
  name?: string
  className?: string
  required?: boolean
}

export default function TextInput({
  label,
  type = "text",
  value,
  onChange,
  placeholder,
  autoComplete,
  rightSlot,
  name,
  className = "",
  required = false,
}: TextInputProps) {
  return (
    <label className={`block ${className}`}>
      {label && <span className="text-sm font-medium text-gray-700">{label}</span>}
      <div className="mt-1 relative">
        <input
          name={name}
          type={type}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          autoComplete={autoComplete}
          required={required}
          className="w-full rounded-2xl border border-gray-300 bg-white/90 backdrop-blur px-4 py-3 pr-12 outline-none ring-0 focus:border-gray-400 focus:outline-none"
        />
        {rightSlot && (
          <div className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-500 cursor-pointer select-none">
            {rightSlot}
          </div>
        )}
      </div>
    </label>
  )
}

