import { useState } from 'react'
import TextInput from './TextInput'

interface PasswordInputProps {
  label?: string
  value: string
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  name?: string
  placeholder?: string
}

export default function PasswordInput({
  label,
  value,
  onChange,
  name,
  placeholder,
}: PasswordInputProps) {
  const [show, setShow] = useState(false)

  return (
    <TextInput
      name={name}
      label={label}
      type={show ? "text" : "password"}
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      autoComplete="new-password"
      rightSlot={
        <button
          type="button"
          onClick={() => setShow((s) => !s)}
          aria-label={show ? "Hide password" : "Show password"}
          className="opacity-80 hover:opacity-100"
        >
          <span className="text-xl" role="img" aria-hidden>
            {show ? "🕵️" : "🐻"}
          </span>
        </button>
      }
    />
  )
}

