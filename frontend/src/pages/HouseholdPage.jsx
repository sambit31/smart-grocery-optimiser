import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { Home } from 'lucide-react'
import { getErrorMessage } from '../api/axios'
import { createHousehold, updateHousehold } from '../api/householdApi'
import LoadingSpinner from '../components/common/LoadingSpinner'
import PageHeader from '../components/common/PageHeader'
import { useAuth } from '../context/AuthContext'
import { useOptions } from '../hooks/useOptions'
import { formatCurrency } from '../utils/formatCurrency'

const EMPTY = {
  household_name: '',
  family_size: 4,
  shopping_frequency: 'Monthly',
  monthly_budget: '',
  planning_period_days: 30,
}

export default function HouseholdPage() {
  const { household, setHousehold } = useAuth()
  const options = useOptions()
  const navigate = useNavigate()
  const [form, setForm] = useState(EMPTY)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const isNew = !household

  useEffect(() => {
    if (household) setForm({ ...EMPTY, ...household })
  }, [household])

  if (!options) return <LoadingSpinner />

  const handleChange = (event) => {
    const { name, value } = event.target
    const next = { ...form, [name]: value }
    // Suggest a planning period that matches how often they shop.
    if (name === 'shopping_frequency') next.planning_period_days = options.frequency_days[value] || 30
    setForm(next)
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    if (!form.household_name.trim()) return setError('Please enter a household name.')
    if (!(Number(form.family_size) >= 1 && Number(form.family_size) <= 30)) return setError('Family size must be between 1 and 30.')
    if (!(Number(form.monthly_budget) > 0)) return setError('Monthly budget must be greater than zero.')

    const payload = {
      household_name: form.household_name,
      family_size: Number(form.family_size),
      shopping_frequency: form.shopping_frequency,
      monthly_budget: Number(form.monthly_budget),
      planning_period_days: Number(form.planning_period_days),
    }
    setSaving(true)
    try {
      const result = isNew ? await createHousehold(payload) : await updateHousehold(payload)
      setHousehold(result.household)
      toast.success(isNew ? 'Household created! Next, add your grocery items.' : 'Household updated.')
      if (isNew) navigate('/app/groceries')
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  const planBudget = (Number(form.monthly_budget || 0) * Number(form.planning_period_days || 30)) / 30

  return (
    <>
      <PageHeader
        title={isNew ? 'Set up your household' : 'Household settings'}
        description="These details drive every prediction and budget calculation."
      />
      {isNew && (
        <div className="mb-6 flex items-start gap-3 rounded-xl border border-brand-200 bg-brand-50 p-4 text-sm text-brand-900">
          <Home className="mt-0.5 h-5 w-5 shrink-0" aria-hidden="true" />
          <p>Welcome! Tell us about your household first. You can change these settings at any time.</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="card max-w-2xl space-y-5 p-6" noValidate>
        {error && <div role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}

        <div>
          <label htmlFor="household_name" className="label">Household name</label>
          <input id="household_name" name="household_name" className="input" value={form.household_name} onChange={handleChange} maxLength={120} placeholder="e.g. Sharma Family" />
        </div>

        <div className="grid gap-5 sm:grid-cols-2">
          <div>
            <label htmlFor="family_size" className="label">Family size</label>
            <input id="family_size" name="family_size" type="number" min="1" max="30" className="input" value={form.family_size} onChange={handleChange} />
          </div>
          <div>
            <label htmlFor="monthly_budget" className="label">Monthly grocery budget (₹)</label>
            <input id="monthly_budget" name="monthly_budget" type="number" min="1" step="0.01" className="input" value={form.monthly_budget} onChange={handleChange} placeholder="6000" />
          </div>
          <div>
            <label htmlFor="shopping_frequency" className="label">Shopping frequency</label>
            <select id="shopping_frequency" name="shopping_frequency" className="input" value={form.shopping_frequency} onChange={handleChange}>
              {options.shopping_frequencies.map((f) => <option key={f}>{f}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor="planning_period_days" className="label">Planning period (days)</label>
            <input id="planning_period_days" name="planning_period_days" type="number" min="1" max="90" className="input" value={form.planning_period_days} onChange={handleChange} />
            <p className="help-text">How many days each grocery plan should cover.</p>
          </div>
        </div>

        <div className="rounded-lg bg-slate-50 p-3 text-sm text-slate-600">
          Budget for each {form.planning_period_days}-day plan: <strong className="text-slate-900">{formatCurrency(planBudget)}</strong>
          <span className="block text-xs text-slate-500">(monthly budget × planning days ÷ 30)</span>
        </div>

        <div className="flex justify-end">
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? 'Saving…' : isNew ? 'Create household' : 'Save changes'}
          </button>
        </div>
      </form>
    </>
  )
}
