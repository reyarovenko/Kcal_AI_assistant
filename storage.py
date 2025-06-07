# JSON save and read operations
import json
from datetime import datetime

data_file = "data.json"

MEAL_TRANSLATIONS = {
    "сніданок": "breakfast",
    "обід": "lunch",
    "вечеря": "dinner",
    "перекус": "snack",
    "breakfast": "breakfast",
    "lunch": "lunch",
    "dinner": "dinner",
    "snack": "snack",
}

MEAL_UI_NAMES = {
    "uk": {
        "breakfast": "Сніданок",
        "lunch": "Обід",
        "dinner": "Вечеря",
        "snack": "Перекус"
    },
    "en": {
        "breakfast": "Breakfast",
        "lunch": "Lunch",
        "dinner": "Dinner",
        "snack": "Snack"
    }
}


def save_entry(description, kbju, selected_meal=None):
    raw_meal = (selected_meal or kbju.get("meal") or kbju.get("назва") or "other").lower()
    normalized_meal = MEAL_TRANSLATIONS.get(raw_meal, "other")

    entry = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "description": description,
        "meal": normalized_meal,
        "calories": kbju["calories"],
        "protein": kbju["protein"],
        "fat": kbju["fat"],
        "carbs": kbju["carbs"]
    }

    try:
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = []

    data.append(entry)
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_summary_for_period(start_date, end_date, lang):
    try:
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return "Немає даних." if lang == "uk" else "No data."

    total = {"calories": 0, "protein": 0, "fat": 0, "carbs": 0}
    for entry in data:
        entry_date = datetime.strptime(entry["date"], "%Y-%m-%d").date()
        if start_date <= entry_date <= end_date:
            total["calories"] += entry["calories"]
            total["protein"] += entry["protein"]
            total["fat"] += entry["fat"]
            total["carbs"] += entry["carbs"]

    if lang == "uk":
        return (
            f"📊 Підсумок з {start_date} по {end_date}:\n"
            f"Калорії: {total['calories']} ккал\n"
            f"Білки: {total['protein']} г\n"
            f"Жири: {total['fat']} г\n"
            f"Вуглеводи: {total['carbs']} г"
        )
    else:
        return (
            f"📊 Summary from {start_date} to {end_date}:\n"
            f"Calories: {total['calories']} kcal\n"
            f"Protein: {total['protein']} g\n"
            f"Fat: {total['fat']} g\n"
            f"Carbs: {total['carbs']} g"
        )


def format_summary_table(data, lang):
    lines = []

    if lang == "uk":
        header = f"{'🍽 Прийом їжі':<30} {'Ккал':>6} {'Білки':>6} {'Жири':>6} {'Вугл.':>6}"
        total_label = "🔢 Всього"
    else:
        header = f"{'🍽 Meal':<30} {'Kcal':>6} {'Prot':>6} {'Fat':>6} {'Carb':>6}"
        total_label = "🔢 Total"

    lines.append(header)
    lines.append("─" * len(header))

    total = {"calories": 0, "protein": 0, "fat": 0, "carbs": 0}

    for entry in data:
        meal_label = MEAL_UI_NAMES[lang].get(entry["meal"], "Other")
        desc = entry['description'].strip()

        if not desc.lower().startswith(meal_label.lower()):
            desc = f"{meal_label}: {desc}"

        desc = desc[:28]

        kcal = entry["calories"]
        prot = entry["protein"]
        fat = entry["fat"]
        carb = entry["carbs"]

        lines.append(f"{desc:<30} {kcal:>6} {prot:>6} {fat:>6} {carb:>6}")

        total["calories"] += kcal
        total["protein"] += prot
        total["fat"] += fat
        total["carbs"] += carb

    lines.append("─" * len(header))
    lines.append(
        f"{total_label:<30} {total['calories']:>6} {total['protein']:>6} {total['fat']:>6} {total['carbs']:>6}")

    return "```\n" + "\n".join(lines) + "\n```"
