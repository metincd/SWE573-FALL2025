import React from 'react'

interface TextInputProps {
  label?: string
  type?: string
  value: string
  onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => void
  onFocus?: (e: React.FocusEvent<HTMLInputElement | HTMLTextAreaElement>) => void
  onKeyDown?: (e: React.KeyboardEvent<HTMLInputElement | HTMLTextAreaElement>) => void
  placeholder?: string
  autoComplete?: string
  rightSlot?: React.ReactNode
  name?: string
  className?: string
  required?: boolean
  multiline?: boolean
  rows?: number
  min?: string | number
  step?: string | number
}

const TextInput = React.forwardRef<HTMLInputElement | HTMLTextAreaElement, TextInputProps>(({
  label,
  type = "text",
  value,
  onChange,
  onFocus,
  onKeyDown,
  placeholder,
  autoComplete,
  rightSlot,
  name,
  className = "",
  required = false,
  multiline = false,
  rows = 3,
  min,
  step,
}, ref) => {
  const inputClassName = "w-full rounded-2xl border border-gray-300 bg-white/90 backdrop-blur px-4 py-3 pr-12 outline-none ring-0 focus:border-gray-400 focus:outline-none"
  
  return (
    <label className={`block ${className}`}>
      {label && <span className="text-sm font-medium text-gray-700">{label}</span>}
      <div className="mt-1 relative">
        {multiline ? (
          <textarea
            ref={ref as React.Ref<HTMLTextAreaElement>}
            name={name}
            value={value}
            onChange={onChange}
            onFocus={onFocus}
            onKeyDown={onKeyDown}
            placeholder={placeholder}
            required={required}
            rows={rows}
            className={inputClassName}
          />
        ) : (
          <input
            ref={ref as React.Ref<HTMLInputElement>}
            name={name}
            type={type}
            value={value}
            onChange={onChange}
            onFocus={onFocus}
            onKeyDown={onKeyDown}
            placeholder={placeholder}
            autoComplete={autoComplete}
            required={required}
            min={min}
            step={step}
            className={inputClassName}
          />
        )}
        {rightSlot && !multiline && (
          <div className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-500 cursor-pointer select-none">
            {rightSlot}
          </div>
        )}
      </div>
    </label>
  )
})

TextInput.displayName = 'TextInput'

export default TextInput

