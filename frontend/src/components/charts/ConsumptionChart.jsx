import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { formatQuantity } from '../../utils/formatQuantity'

/** Monthly consumption trend for ONE item (one unit, so values are comparable). */
export default function ConsumptionChart({ data, unit, height = 260 }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
        <XAxis dataKey="label" tick={{ fontSize: 12, fill: '#64748b' }} tickLine={false} axisLine={false} />
        <YAxis tick={{ fontSize: 12, fill: '#64748b' }} tickLine={false} axisLine={false} width={56} />
        <Tooltip formatter={(value) => [formatQuantity(value, unit), 'Consumed']} />
        <Line type="monotone" dataKey="quantity" stroke="#15803d" strokeWidth={2.5} dot={{ r: 3.5 }} activeDot={{ r: 5 }} />
      </LineChart>
    </ResponsiveContainer>
  )
}
