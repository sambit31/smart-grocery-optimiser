import ShoppingListItem from './ShoppingListItem'

/** Groups lines by category for easier in-store shopping. */
export default function ShoppingList({ lines, ...handlers }) {
  const groups = lines.reduce((acc, line) => {
    ;(acc[line.category] ||= []).push(line)
    return acc
  }, {})

  return (
    <div className="space-y-4">
      {Object.entries(groups).map(([category, groupLines]) => (
        <section key={category} className="card overflow-hidden">
          <h3 className="border-b border-slate-100 bg-slate-50 px-5 py-2 text-xs font-semibold tracking-wide text-slate-500 uppercase">
            {category} · {groupLines.length}
          </h3>
          <ul className="divide-y divide-slate-100">
            {groupLines.map((line) => <ShoppingListItem key={line.id} line={line} {...handlers} />)}
          </ul>
        </section>
      ))}
    </div>
  )
}
