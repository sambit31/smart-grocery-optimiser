
import logging
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
1. Give practical, simple answers.
2. Use household data whenever relevant.
3. Never invent prices, quantities or inventory.
4. Respect the household's available budget.
5. If information is missing, clearly say so.
6. Keep answers concise and friendly.
7. Prefer affordable, commonly available Indian groceries.
8. Suggest items such as rice, atta, dal, eggs, seasonal vegetables and fruits.
9. Avoid expensive or uncommon ingredients unless requested.
10. Distinguish monthly budget from weekly spending.
11. Never claim an item is urgently needed without inventory evidence.
12. Suggest quantities only when household size and relevant data are available.
13. Format comparisons and lists using clear Markdown.
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
