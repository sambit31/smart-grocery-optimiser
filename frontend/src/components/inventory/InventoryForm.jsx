import { useEffect, useState } from 'react'
import Modal from '../common/Modal'
import { unitStep } from '../../utils/formatQuantity'

/**
 * Add stock for a new item (record = null) or edit an existing record
 * (sets the absolute quantity, low-stock level and expiry date).
 */
export default function InventoryForm({ open, record, untrackedItems, onClose, onSave }) {
  const [form, setForm] = useState({ item_id: '', quantity: '', low_stock_threshold: '', expiry_date: '' })
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!open) return
    setError('')
    setForm(
      record
        ? {
            item_id: record.item_id,
            quantity: record.quantity,
            low_stock_threshold: record.low_stock_threshold,
            expiry_date: record.expiry_date || '',
          }
        : { item_id: untrackedItems[0]?.id || '', quantity: '', low_stock_threshold: '', expiry_date: '' },
    )
  }, [open, record, untrackedItems])

  const unit = record ? record.unit : untrackedItems.find((i) => String(i.id) === String(form.item_id))?.unit
  const handleChange = (event) => setForm({ ...form, [event.target.name]: event.target.value })

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (!form.item_id) return setError('Please choose an item.')
    if (form.quantity === '' || Number(form.quantity) < 0) return setError('Quantity must be zero or greater.')
    if (form.low_stock_threshold !== '' && Number(form.low_stock_threshold) < 0) return setError('Low-stock level cannot be negative.')
    setSaving(true)
    setError('')
    try {
      await onSave({
        item_id: Number(form.item_id),
        quantity: Number(form.quantity),
        low_stock_threshold: form.low_stock_threshold === '' ? 0 : Number(form.low_stock_threshold),
        expiry_date: form.expiry_date || null,
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
      title={record ? `Update ${record.item_name}` : 'Add item to inventory'}
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
          <button type="submit" form="inventory-form" className="btn btn-primary" disabled={saving}>{saving ? 'Saving…' : 'Save'}</button>
        </>
      }
    >
      <form id="inventory-form" onSubmit={handleSubmit} className="space-y-4" noValidate>
        {error && <div role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}
        {!record && (
          <div>
            <label htmlFor="inv-item" className="label">Item</label>
            <select id="inv-item" name="item_id" className="input" value={form.item_id} onChange={handleChange}>
              {untrackedItems.map((item) => <option key={item.id} value={item.id}>{item.name} ({item.unit})</option>)}
            </select>
          </div>
        )}
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label htmlFor="inv-qty" className="label">Current quantity {unit && `(${unit})`}</label>
            <input id="inv-qty" name="quantity" type="number" min="0" step={unitStep(unit) === '1' ? '1' : 'any'} className="input" value={form.quantity} onChange={handleChange} />
          </div>
          <div>
            <label htmlFor="inv-low" className="label">Low-stock level {unit && `(${unit})`}</label>
            <input id="inv-low" name="low_stock_threshold" type="number" min="0" step="any" className="input" value={form.low_stock_threshold} onChange={handleChange} />
            <p className="help-text">Flagged as low when stock is at or below this.</p>
          </div>
        </div>
        <div>
          <label htmlFor="inv-expiry" className="label">Expiry date — optional</label>
          <input id="inv-expiry" name="expiry_date" type="date" className="input" value={form.expiry_date} onChange={handleChange} />
        </div>
        {record && <p className="text-xs text-slate-500">Setting the quantity directly is logged as a manual stock correction.</p>}
      </form>
    </Modal>
  )
}
