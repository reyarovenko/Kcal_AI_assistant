# Date parsing, formatting, helper functions
from datetime import datetime, date
import re


MESSAGES = {
    "uk": {
        "start": "Привіт! Надішли, що ти їв(-ла), і я порахую КБЖВ. Наприклад:\n\nсніданок: вівсянка 50г, банан, арахісова паста",
        "saved": "✅ Збережено",
        "summary_command": "підсумок",
        "calories": "Калорії",
        "protein": "Білки",
        "fat": "Жири",
        "carbs": "Вуглеводи"
    },
    "en": {
        "start": "Hi! Send me what you ate and I will calculate your calories and macros. For example:\n\nBreakfast: oatmeal 50g, banana, peanut butter",
        "saved": "✅ Saved",
        "summary_command": "summary",
        "calories": "Calories",
        "protein": "Protein",
        "fat": "Fat",
        "carbs": "Carbs"
    }
}

SUMMARY_PATTERNS = {
    "uk": [
        r"\bпідсумок\b",
        r"\bїжа за день\b",
        r"\bщо я їв\b",
        r"\bпокажи їжу\b",
        r"\bсумарно\b",
        r"\bсьогодні\b",
        r"\bрезультат\b"
    ],
    "en": [
        r"\bsummary\b",
        r"\bfood today\b",
        r"\bwhat i ate\b",
        r"\bshow me food\b",
        r"\bdaily total\b",
        r"\bresult\b"
    ]
}


def parse_summary_command(text: str, lang: str):
    if lang == "uk" and "з" in text and "по" in text:
        match = re.search(r"з (\d{1,2}) (\w+) по (\d{1,2}) (\w+)", text)
    elif lang == "en" and "from" in text and "to" in text:
        match = re.search(r"from (\d{1,2}) (\w+) to (\d{1,2}) (\w+)", text)
    else:
        match = None

    if match:
        day1, month1, day2, month2 = match.groups()
        m1 = month_str_to_number(month1.lower(), lang)
        m2 = month_str_to_number(month2.lower(), lang)
        year = datetime.now().year
        return date(year, m1, int(day1)), date(year, m2, int(day2))

    return datetime.now().date(), datetime.now().date()


def month_str_to_number(month, lang):
    months_uk = {
        "січня": 1, "лютого": 2, "березня": 3, "квітня": 4,
        "травня": 5, "червня": 6, "липня": 7, "серпня": 8,
        "вересня": 9, "жовтня": 10, "листопада": 11, "грудня": 12
    }
    months_en = {
        "january": 1, "february": 2, "march": 3, "april": 4,
        "may": 5, "june": 6, "july": 7, "august": 8,
        "september": 9, "october": 10, "november": 11, "december": 12
    }
    if lang == "uk":
        return months_uk.get(month, datetime.now().month)
    return months_en.get(month, datetime.now().month)
