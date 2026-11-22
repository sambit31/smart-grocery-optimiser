import { useEffect, useState } from 'react'
import Modal from '../common/Modal'

const EMPTY = {
  name: '',
  category: 'Rice and Grains',
  unit: 'kg',
  unit_price: '',
  priority: 'Essential',
  description: '',
  initial_monthly_estimate: '',
}

/** Add / edit grocery item dialog. `item` = null means "add new". */
export default function GroceryForm({ open, item, options, onClose, onSave }) {
  const [form, setForm] = useState(EMPTY)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!open) return
    setError('')
    setForm(
      item
        ? {
            ...EMPTY,
            ...item,
            description: item.description || '',
            initial_monthly_estimate: item.initial_monthly_estimate ?? '',
          }
        : EMPTY,
    )
  }, [open, item])

  const handleChange = (event) => setForm({ ...form, [event.target.name]: event.target.value })

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (!form.name.trim()) return setError('Item name is required.')
    if (!(Number(form.unit_price) > 0)) return setError('Unit price must be greater than zero.')
    if (form.initial_monthly_estimate !== '' && Number(form.initial_monthly_estimate) < 0) {
      return setError('Initial estimate cannot be negative.')
    }
    setSaving(true)
    setError('')
    try {
      await onSave({
        name: form.name.trim(),
        category: form.category,
        unit: form.unit,
        unit_price: Number(form.unit_price),
        priority: form.priority,
        description: form.description.trim() || null,
        initial_monthly_estimate: form.initial_monthly_estimate === '' ? null : Number(form.initial_monthly_estimate),
      })
    } catch (message) {
      setError(String(message))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal
      open={open}
      title={item ? 'Edit grocery item' : 'Add grocery item'}
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
          <button type="submit" form="grocery-form" className="btn btn-primary" disabled={saving}>
            {saving ? 'Saving…' : 'Save item'}
          </button>
        </>
      }
    >
      <form id="grocery-form" onSubmit={handleSubmit} className="space-y-4" noValidate>
        {error && <div role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}
        <div>
          <label htmlFor="g-name" className="label">Item name</label>
          <input id="g-name" name="name" className="input" value={form.name} onChange={handleChange} maxLength={120} placeholder="e.g. Toor Dal" />
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label htmlFor="g-category" className="label">Category</label>
            <select id="g-category" name="category" className="input" value={form.category} onChange={handleChange}>
              {options.categories.map((c) => <option key={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor="g-priority" className="label">Priority</label>
            <select id="g-priority" name="priority" className="input" value={form.priority} onChange={handleChange}>
              {options.priorities.map((p) => <option key={p}>{p}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor="g-unit" className="label">Unit</label>
            <select id="g-unit" name="unit" className="input" value={form.unit} onChange={handleChange}>
              {options.units.map((u) => <option key={u}>{u}</option>)}
            </select>
            {item && <p className="help-text">Unit can’t change once the item has stock or history.</p>}
          </div>
          <div>
            <label htmlFor="g-price" className="label">Price per {form.unit} (₹)</label>
            <input id="g-price" name="unit_price" type="number" min="0.01" step="0.01" className="input" value={form.unit_price} onChange={handleChange} />
          </div>
        </div>
        <div>
          <label htmlFor="g-estimate" className="label">Initial monthly estimate ({form.unit}) — optional</label>
          <input id="g-estimate" name="initial_monthly_estimate" type="number" min="0" step="any" className="input" value={form.initial_monthly_estimate} onChange={handleChange} />
          <p className="help-text">Used only until you have consumption history. Shown as “Your estimate” in predictions.</p>
        </div>
        <div>
          <label htmlFor="g-description" className="label">Description — optional</label>
          <textarea id="g-description" name="description" rows={2} className="input" value={form.description} onChange={handleChange} maxLength={500} />
        </div>
      </form>
    </Modal>
  )
}
