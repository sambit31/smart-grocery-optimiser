const inr = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

const inrCompact = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 0,
})

/** 123456.5 -> "₹1,23,456.50" (Indian digit grouping) */
export function formatCurrency(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '—'
  return inr.format(Number(value))
}

/** Whole-rupee format for chart axes. */
export function formatCurrencyShort(value) {
  return inrCompact.format(Number(value || 0))
}
