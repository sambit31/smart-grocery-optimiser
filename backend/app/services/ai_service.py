
import logging
import json
from groq import Groq
from flask import current_app

logger = logging.getLogger(__name__)


def generate_grocery_insights(data):
    api_key = current_app.config.get("GROQ_API_KEY")

    if not api_key:
        raise ValueError("Groq API key is not configured.")

    client = Groq(api_key=api_key)

    prompt = f"""
    You are a helpful Smart Grocery Assistant.

    Analyse this household grocery data:
    {data}

    Give the user:
    1. Spending insights
    2. Consumption observations
    3. Inventory suggestions
    4. Practical grocery recommendations

    Use simple language.
    Do not invent numbers or facts.
    Keep the response concise.
    """

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": "You are a practical grocery planning assistant."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.4,
        max_tokens=800,
    )

    return response.choices[0].message.content.strip()



def chat_with_grocery_assistant(question, data, history=None):
    api_key = current_app.config.get("GROQ_API_KEY")

    if not api_key:
        raise ValueError("Groq API key is not configured.")

    client = Groq(api_key=api_key)

    messages = [
        {
            "role": "system",
            "content": f"""
You are an intelligent AI Grocery Shopping Assistant.

Help users with:
- Grocery shopping recommendations
- Budget planning and savings
- Inventory and low-stock suggestions
- Consumption analysis
- Shopping list ideas

Use this household data:
{data}

Rules:
1. Give practical, simple and concise answers.
2. Use actual household data whenever relevant.
3. Never invent prices, quantities, spending or inventory.
4. Treat monthly_budget as a MONTHLY budget, never a weekly budget.
5. Calculate remaining budget using the supplied data.
6. Never describe the entire remaining monthly budget as available for one week.
7. Use low_stock_items and upcoming_purchases to prioritise shopping.
8. If low_stock_items is empty, do not invent urgent purchases.
9. Prefer affordable, commonly available Indian groceries.
10. Do not suggest exact category budgets without reliable price data.
11. Do not call old spending records current-month spending.
12. If household size or inventory details are missing, ask the user.
13. Clearly distinguish actual data from general suggestions.
14. Check all arithmetic before presenting totals.
15. Never claim that an item is necessary without supporting data.
16. Use current_date and current_month to identify the reporting period.
17. Use spent_this_month for current-month spending.
18. Treat monthly_spending as historical chart data.
19. Never label previous-month spending as current-month spending.
"""
        }
    ]

    if history:
        messages.extend(history[-10:])

    messages.append({
        "role": "user",
        "content": question
    })

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages,
        temperature=0.4,
        max_tokens=800,
    )

    return response.choices[0].message.content.strip()





def generate_shopping_recommendations(data):
    api_key = current_app.config.get("GROQ_API_KEY")

    if not api_key:
        raise ValueError("Groq API key is not configured.")

    client = Groq(api_key=api_key)

    prompt = f"""
You are an AI grocery shopping recommendation assistant.

Analyse this verified household shopping plan and inventory data:

{json.dumps(data, indent=2)}

Your tasks:
1. Identify the most important items to buy.
2. Explain why each item deserves attention.
3. Consider current stock and expiry dates.
4. Consider the existing ML recommendation and budget status.
5. Highlight items with insufficient prediction data.
6. Give practical money-saving suggestions.
Strict rules:
- Treat the ML shopping plan as the source of truth.
- Never change predicted quantities, prices, or budget decisions.
- Respect the Essential and Optional classifications.
- Never describe an Optional item as Essential or High Priority.
- Do not recommend items with final_quantity = 0 as purchases.
- Explain insufficient prediction data clearly.
- Recommend ONLY items present in the supplied shopping plan.
- Never invent grocery items, prices or quantities.
- Do not recommend already purchased items.
- Clearly distinguish ML results from general suggestions.
- Keep recommendations concise and practical.
- All monetary values are in Indian Rupees (INR ₹).
- Never use £, $, or any other currency symbol.
- Preserve the exact numeric prices supplied in the data.
- Never upgrade an item's ML priority.
- Never recommend purchasing an item with final_quantity = 0.
- Expired inventory must be reported separately as a safety alert.
- Do not suggest replacing expired stock unless the ML plan recommends a purchase.
- Keep purchase recommendations separate from inventory warnings.
- Never confuse item category with purchase urgency.
- Essential, Important and Optional are item classifications, not priority levels.
- Priority must be based on the actual purchase requirement.
- If final_quantity is 0, the item must never appear as a purchase recommendation.
- If final_quantity is greater than 0, recommend only that exact quantity.
- Never upgrade Optional items to Essential or Important.
- Items with insufficient prediction data must be clearly marked as Needs Data.
- Report expired inventory separately under Inventory Alerts.
- Never tell users to purchase expired items unless the shopping plan contains a positive final_quantity.
- Do not invent urgency, quantities, prices or budget figures.
- Use ₹ for all monetary values, assuming the supplied values are in INR.
- Use normal Markdown formatting. Do not output escaped HTML such as \<br>.
- Do not put bullet points or HTML tags inside Markdown table cells.

Format:
## High Priority
## Medium Priority
## Low Priority
## Budget Advice
## Additional Suggestions

If a priority category has no suitable items, say so.
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": "You provide evidence-based grocery shopping recommendations."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3,
        max_tokens=1000,
    )
    result = response.choices[0].message.content.strip()

# Display household currency consistently.
    result = result.replace("£", "₹")

    return result