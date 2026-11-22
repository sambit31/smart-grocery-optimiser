import { Bar, CartesianGrid, ComposedChart, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { formatCurrency, formatCurrencyShort } from '../../utils/formatCurrency'

/** Monthly spending bars with the monthly budget as a reference line. */
export default function SpendingChart({ data, height = 260 }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
        <XAxis dataKey="label" tick={{ fontSize: 12, fill: '#64748b' }} tickLine={false} axisLine={false} />
        <YAxis tickFormatter={formatCurrencyShort} tick={{ fontSize: 12, fill: '#64748b' }} tickLine={false} axisLine={false} width={72} />
        <Tooltip formatter={(value, name) => [formatCurrency(value), name]} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Bar dataKey="total" name="Spent" fill="#15803d" radius={[4, 4, 0, 0]} maxBarSize={44} />
        <Line dataKey="budget" name="Budget" stroke="#f59e0b" strokeWidth={2} strokeDasharray="5 4" dot={false} />
      </ComposedChart>
    </ResponsiveContainer>
  )
}
