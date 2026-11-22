"""Rule-based budget optimisation (deterministic, not mathematical optimisation).

RULES (all configurable below, in this one place)
-------------------------------------------------
1. Cost of each line = quantity × unit price. Total = sum of lines.
2. If the total is within budget, nothing changes ("Within Budget").
3. Otherwise items are reduced tier by tier in REDUCTION_ORDER:
   Optional first, then Important. Inside a tier, the most expensive line is
   reduced first (it frees the most money). Each line is reduced only by as
   much as is needed (rounded to the unit's buying step), and the total is
   recalculated after every adjustment.
4. Essential items are PROTECTED: they are never cut automatically. If the
   protected items alone exceed the budget, they are all kept, the plan is
   marked "Over Budget", the shortfall is reported, and the essentials that do
   not fit (cheapest are counted as fitting first) are flagged "unaffordable"
   so the user can decide what to do.
"""
from decimal import ROUND_CEILING, Decimal

from app.utils.numbers import round_money, round_qty, to_decimal, unit_step

REDUCTION_ORDER = ["Optional", "Important"]
PROTECTED_PRIORITIES = ["Essential"]

STATUS_WITHIN = "within_budget"
STATUS_OPTIMISED = "optimised_to_fit"
STATUS_OVER = "over_budget"


def line_cost(quantity, unit_price):
    return round_money(to_decimal(quantity) * to_decimal(unit_price))


def total_cost(lines):
    return sum((line["estimated_cost"] for line in lines), Decimal("0"))


def _fmt(value):
    return f"{to_decimal(value).normalize():f}"


def _quantity_to_cut(line, amount_over):
    """Smallest quantity (in buying steps) whose cost covers amount_over."""
    step = unit_step(line["unit"])
    price = to_decimal(line["unit_price"])
    if price <= 0:
        return Decimal("0")
    steps = (amount_over / (price * step)).to_integral_value(rounding=ROUND_CEILING)
    return min(line["final_quantity"], round_qty(steps * step))


def optimise(lines, budget):
    """Fit plan lines into the budget.

    Each line is a dict with: item_name, unit, unit_price, priority,
    recommended_quantity. Returns (lines, summary). Lines gain:
    final_quantity, estimated_cost, plan_status, adjustment_note.
    """
    budget = to_decimal(budget)
    explanation = []

    for line in lines:
        line["final_quantity"] = round_qty(line["recommended_quantity"])
        line["estimated_cost"] = line_cost(line["final_quantity"], line["unit_price"])
        line["adjustment_note"] = None
        if line.get("plan_status") == "needs_data":
            continue
        line["plan_status"] = "full" if line["final_quantity"] > 0 else "not_needed"

    original_total = total_cost(lines)
    running_total = original_total

    if running_total <= budget:
        explanation.append(
            f"Estimated cost ₹{original_total:,.2f} is within the budget of ₹{budget:,.2f}. No changes needed."
        )
        return lines, _summary(original_total, running_total, budget, STATUS_WITHIN, explanation, lines)

    explanation.append(
        f"Estimated cost ₹{original_total:,.2f} is ₹{original_total - budget:,.2f} over the budget of "
        f"₹{budget:,.2f}. Reducing Optional items first, then Important items. Essential items are protected."
    )

    for priority in REDUCTION_ORDER:
        tier = [l for l in lines if l["priority"] == priority and l["final_quantity"] > 0]
        tier.sort(key=lambda l: (-l["estimated_cost"], l["item_name"]))  # deterministic order
        for line in tier:
            amount_over = running_total - budget
            if amount_over <= 0:
                break
            cut = _quantity_to_cut(line, amount_over)
            if cut <= 0:
                continue
            old_quantity = line["final_quantity"]
            old_cost = line["estimated_cost"]
            line["final_quantity"] = round_qty(old_quantity - cut)
            line["estimated_cost"] = line_cost(line["final_quantity"], line["unit_price"])
            running_total = running_total - old_cost + line["estimated_cost"]

            if line["final_quantity"] == 0:
                line["plan_status"] = "removed"
                line["adjustment_note"] = (
                    f"Removed ({priority}): {_fmt(old_quantity)} {line['unit']} dropped to save "
                    f"₹{old_cost:,.2f}."
                )
            else:
                line["plan_status"] = "reduced"
                line["adjustment_note"] = (
                    f"Reduced ({priority}) from {_fmt(old_quantity)} to {_fmt(line['final_quantity'])} "
                    f"{line['unit']}, saving ₹{old_cost - line['estimated_cost']:,.2f}."
                )
            explanation.append(f"{line['item_name']}: {line['adjustment_note']} New total ₹{running_total:,.2f}.")

    if running_total <= budget:
        explanation.append(f"Plan now fits the budget. Final total ₹{running_total:,.2f}.")
        return lines, _summary(original_total, running_total, budget, STATUS_OPTIMISED, explanation, lines)

    # Still over budget: only protected (Essential) items remain.
    _flag_unaffordable_essentials(lines, budget, running_total, explanation)
    explanation.append(
        f"Essential items alone cost ₹{running_total:,.2f}, which is ₹{running_total - budget:,.2f} more than "
        f"the budget. They were NOT removed automatically — please review the flagged items or increase the budget."
    )
    return lines, _summary(original_total, running_total, budget, STATUS_OVER, explanation, lines)


def _flag_unaffordable_essentials(lines, budget, running_total, explanation):
    """Mark essentials that fall outside the budget, cheapest counted first."""
    spent_on_others = sum(
        (l["estimated_cost"] for l in lines if l["priority"] not in PROTECTED_PRIORITIES), Decimal("0")
    )
    available = budget - spent_on_others
    essentials = [l for l in lines if l["priority"] in PROTECTED_PRIORITIES and l["final_quantity"] > 0]
    essentials.sort(key=lambda l: (l["estimated_cost"], l["item_name"]))
    for line in essentials:
        if line["estimated_cost"] <= available:
            available -= line["estimated_cost"]
        else:
            line["plan_status"] = "unaffordable"
            line["adjustment_note"] = (
                f"Essential item kept, but its cost (₹{line['estimated_cost']:,.2f}) does not fit in the "
                f"remaining budget."
            )
            explanation.append(f"{line['item_name']}: flagged — does not fit the budget.")


def _summary(predicted_total, final_total, budget, status, explanation, lines):
    shortfall = max(Decimal("0"), final_total - budget)
    return {
        "predicted_total_cost": round_money(predicted_total),
        "final_total_cost": round_money(final_total),
        "budget": round_money(budget),
        "remaining_budget": round_money(budget - final_total),
        "shortfall": round_money(shortfall),
        "budget_status": status,
        "explanation": explanation,
        "unaffordable_items": [l["item_name"] for l in lines if l.get("plan_status") == "unaffordable"],
    }
