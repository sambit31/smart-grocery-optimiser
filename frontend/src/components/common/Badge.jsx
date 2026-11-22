const TONES = {
  green: 'bg-brand-50 text-brand-800 ring-brand-200',
  amber: 'bg-amber-50 text-amber-800 ring-amber-200',
  red: 'bg-red-50 text-red-700 ring-red-200',
  blue: 'bg-sky-50 text-sky-800 ring-sky-200',
  slate: 'bg-slate-100 text-slate-700 ring-slate-200',
  violet: 'bg-violet-50 text-violet-700 ring-violet-200',
}

export default function Badge({ tone = 'slate', children }) {
  return (
    <span className={`inline-flex items-center whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${TONES[tone]}`}>
      {children}
    </span>
  )
}

export function PriorityBadge({ priority }) {
  const tone = { Essential: 'red', Important: 'amber', Optional: 'slate' }[priority] || 'slate'
  return <Badge tone={tone}>{priority}</Badge>
}

const SOURCE_LABELS = {
  consumption_history: ['From history', 'green'],
  user_estimate: ['Your estimate', 'blue'],
  no_data: ['Needs data', 'slate'],
}
export function SourceBadge({ source }) {
  const [label, tone] = SOURCE_LABELS[source] || [source, 'slate']
  return <Badge tone={tone}>{label}</Badge>
}

const SUFFICIENCY = {
  good: ['Good data', 'green'],
  limited: ['Limited data', 'amber'],
  estimate: ['Estimate', 'blue'],
  insufficient: ['No data', 'slate'],
}
export function SufficiencyBadge({ value }) {
  const [label, tone] = SUFFICIENCY[value] || [value, 'slate']
  return <Badge tone={tone}>{label}</Badge>
}

const PLAN_STATUS = {
  full: ['In plan', 'green'],
  reduced: ['Reduced', 'amber'],
  removed: ['Removed', 'slate'],
  unaffordable: ['Over budget', 'red'],
  not_needed: ['In stock', 'blue'],
  needs_data: ['Needs data', 'slate'],
  edited: ['Edited', 'violet'],
}
export function PlanStatusBadge({ status }) {
  const [label, tone] = PLAN_STATUS[status] || [status, 'slate']
  return <Badge tone={tone}>{label}</Badge>
}

const BUDGET_STATUS = {
  within_budget: ['Within Budget', 'green'],
  optimised_to_fit: ['Optimised to fit', 'green'],
  needs_optimisation: ['Over budget — optimise', 'amber'],
  over_budget: ['Over Budget', 'red'],
}
export function BudgetStatusBadge({ status }) {
  const [label, tone] = BUDGET_STATUS[status] || [status, 'slate']
  return <Badge tone={tone}>{label}</Badge>
}
