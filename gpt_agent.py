# GPT communication function
import json
import re
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def clean_json_string(s: str) -> str:
    s = re.sub(r'(\d)[,](\d)', r'\1.\2', s)  # 10,5 → 10.5
    s = re.sub(r'(\d+(\.\d+)?)[ ]?(г|g|гр|ккал|мл|кал\.?)', r'\1', s, flags=re.IGNORECASE)
    return s


def is_meal_description(text: str, lang: str) -> bool:
    prompt_uk = f"""
Це повідомлення користувача: "{text}"
Чи це опис прийому їжі? Відповідай ТІЛЬКИ "yes" або "no".
"""
    prompt_en = f"""
This is a user message: "{text}"
Is it a meal description? Reply ONLY "yes" or "no".
"""

    prompt = prompt_uk if lang == "uk" else prompt_en

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    reply = response.choices[0].message.content.strip().lower()
    return "yes" in reply or "так" in reply or "true" in reply


def estimate_kbju(meal_text: str, lang: str) -> dict:
    if lang == "uk":
        prompt = f"""
Ти — дієтолог. Оціни якомога точно вміст калорій, білків, жирів і вуглеводів у цьому прийомі їжі.
Розрахуй максимально точно, орієнтуючись на середні значення КБЖУ для сирих продуктів з таблиць харчової цінності. Не занижуй.
Визнач назву прийому їжі (наприклад, сніданок, обід, вечеря або перекус) та виведи у форматі:

{{
  "назва": "<сніданок / обід / вечеря / перекус>",
  "calories": <число>,
  "protein": <число>,
  "fat": <число>,
  "carbs": <число>
}}

Прийом їжі: {meal_text}
"""
    else:
        prompt = f"""
You are a nutritionist. Estimate calories, protein, fat, and carbs for this meal as precise as possible.
Estimate as accurately as possible using average nutritional data for raw ingredients. Do not underestimate. 
Detect the meal type (breakfast, lunch, dinner or snack) and respond in this format:

{{
  "meal": "<breakfast / lunch / dinner / snack>",
  "calories": <number>,
  "protein": <number>,
  "fat": <number>,
  "carbs": <number>
}}

Meal: {meal_text}
"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=200
    )

    reply = response.choices[0].message.content.strip()

    try:
        cleaned = clean_json_string(reply)
        return json.loads(cleaned)
    except Exception as e:
        print(reply)
        raise e
