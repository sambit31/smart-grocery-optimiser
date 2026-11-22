const qty = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 3 })

/** formatQuantity(2.5, 'kg') -> "2.5 kg" */
export function formatQuantity(value, unit) {
  if (value === null || value === undefined) return '—'
  return `${qty.format(Number(value))}${unit ? ` ${unit}` : ''}`
}

/** Smallest step for a quantity input, matching the backend unit rules. */
export function unitStep(unit) {
  return ['kg', 'litre'].includes(unit) ? '0.1' : '1'
}

export function isWholeUnit(unit) {
  return ['piece', 'packet', 'g', 'ml'].includes(unit)
}

export function formatDate(value) {
  if (!value) return '—'
  return new Date(value.length === 10 ? `${value}T00:00:00` : value).toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

export function todayISO() {
  const now = new Date()
  const offset = now.getTimezoneOffset() * 60000
  return new Date(now - offset).toISOString().slice(0, 10)
}

export function newClientReference() {
  return window.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(16).slice(2)}`
}
