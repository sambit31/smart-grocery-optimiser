import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { getErrorMessage } from '../api/axios'
import { useAuth } from '../context/AuthContext'

const EMPTY = { name: '', email: '', password: '', confirm_password: '' }

// Same rules as the backend (backend re-checks everything).
function validate(form) {
  if (!form.name.trim()) return 'Please enter your name.'
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(form.email)) return 'Please enter a valid email address.'
  if (form.password.length < 8) return 'Password must be at least 8 characters long.'
  if (!/[A-Za-z]/.test(form.password) || !/\d/.test(form.password)) {
    return 'Password must contain at least one letter and one number.'
  }
  if (form.password !== form.confirm_password) return 'Passwords do not match.'
  return ''
}

export default function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState(EMPTY)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handleChange = (event) => setForm({ ...form, [event.target.name]: event.target.value })

  const handleSubmit = async (event) => {
    event.preventDefault()
    const problem = validate(form)
    setError(problem)
    if (problem) return
    setSubmitting(true)
    try {
      await register(form)
      toast.success('Account created! Now set up your household.')
      navigate('/app/household', { replace: true })
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <h1 className="text-2xl font-semibold text-slate-900">Create your account</h1>
      <p className="mt-1 text-sm text-slate-500">Free, and your data stays in your own database.</p>

      <form onSubmit={handleSubmit} className="mt-8 space-y-4" noValidate>
        {error && (
          <div role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>
        )}
        <div>
          <label htmlFor="name" className="label">Full name</label>
          <input id="name" name="name" autoComplete="name" className="input" value={form.name} onChange={handleChange} maxLength={100} />
        </div>
        <div>
          <label htmlFor="email" className="label">Email</label>
          <input id="email" name="email" type="email" autoComplete="email" className="input" value={form.email} onChange={handleChange} />
        </div>
        <div>
          <label htmlFor="password" className="label">Password</label>
          <input id="password" name="password" type="password" autoComplete="new-password" className="input" value={form.password} onChange={handleChange} />
          <p className="help-text">At least 8 characters, with a letter and a number.</p>
        </div>
        <div>
          <label htmlFor="confirm_password" className="label">Confirm password</label>
          <input id="confirm_password" name="confirm_password" type="password" autoComplete="new-password" className="input" value={form.confirm_password} onChange={handleChange} />
        </div>
        <button type="submit" className="btn btn-primary w-full" disabled={submitting}>
          {submitting ? 'Creating account…' : 'Create account'}
        </button>
      </form>

      <p className="mt-6 text-center text-sm text-slate-500">
        Already registered? <Link to="/login" className="font-medium text-brand-700 hover:underline">Log in</Link>
      </p>
    </>
  )
}
