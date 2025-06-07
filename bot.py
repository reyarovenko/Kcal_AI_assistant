import json
import os
from datetime import datetime, date
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import utils
from gpt_agent import estimate_kbju, is_meal_description
from storage import save_entry, format_summary_table, data_file, get_summary_for_period
from utils import MESSAGES

load_dotenv()

user_languages = {}
user_meal_stage = {}
user_delete_stage = {}

MEAL_CHOICES = {
    "uk": ["Сніданок", "Обід", "Вечеря", "Перекус"],
    "en": ["Breakfast", "Lunch", "Dinner", "Snack"]
}


def get_entries_for_period(start_date, end_date):
    try:
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return []
    result = []
    for entry in data:
        entry_date = datetime.strptime(entry["date"], "%Y-%m-%d").date()
        if start_date <= entry_date <= end_date:
            result.append(entry)
    return result


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[KeyboardButton("🇺🇦 Українська")], [KeyboardButton("🇬🇧 English")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("⬇️ Виберіть мову / Choose language:", reply_markup=reply_markup)


async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[KeyboardButton("🇺🇦 Українська")], [KeyboardButton("🇬🇧 English")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Виберіть мову / Choose language:", reply_markup=reply_markup)


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    if "Українська" in text:
        user_languages[user_id] = "uk"
        await update.message.reply_text("✅ Мову встановлено: українська")
        await update.message.reply_text(MESSAGES["uk"]["start"])
        await show_main_menu(update, context)
    elif "English" in text:
        user_languages[user_id] = "en"
        await update.message.reply_text("✅ Language set to: English")
        await update.message.reply_text(MESSAGES["en"]["start"])
        await show_main_menu(update, context)


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in user_languages:
        await start(update, context)
        return

    lang = user_languages[user_id]

    if lang == "uk":
        keyboard = [
            ["➕ Додати прийом їжі", "🗑️ Видалити прийом їжі"],
            ["📊 Підсумок за день"],
            ["🌐 Змінити мову"]
        ]
        prompt = "📋 Оберіть дію:"
    else:
        keyboard = [
            ["➕ Add a meal", "🗑️ Delete a meal"],
            ["📊 Summary for today"],
            ["🌐 Change language"]
        ]
        prompt = "📋 Choose an action:"

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    await update.message.reply_text(prompt, reply_markup=reply_markup)


async def add_meal_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in user_languages:
        await start(update, context)
        return

    lang = user_languages[user_id]

    user_meal_stage[user_id] = {"lang": lang, "awaiting_meal_type": True}

    keyboard = [[m] for m in MEAL_CHOICES[lang]]
    back_button = "⬅️ Назад" if lang == "uk" else "⬅️ Back"
    keyboard.append([back_button])

    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        "🍽 Оберіть прийом їжі:" if lang == "uk" else "🍽 Choose your meal:",
        reply_markup=reply_markup
    )


async def delete_meal_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in user_languages:
        await start(update, context)
        return

    lang = user_languages[user_id]

    user_delete_stage[user_id] = {"lang": lang, "awaiting_meal_type": True}

    keyboard = [[m] for m in MEAL_CHOICES[lang]]
    back_button = "⬅️ Назад" if lang == "uk" else "⬅️ Back"
    keyboard.append([back_button])

    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        "🗑️ Оберіть тип прийому їжі для видалення:" if lang == "uk"
        else "🗑️ Choose meal type to delete:",
        reply_markup=reply_markup
    )


def get_entries_by_meal_type(meal_type, target_date=None):
    if target_date is None:
        target_date = date.today()

    try:
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return []

    result = []
    for i, entry in enumerate(data):
        entry_date = datetime.strptime(entry["date"], "%Y-%m-%d").date()
        if (entry_date == target_date and
                entry["description"].startswith(meal_type + ":")):
            result.append({"entry": entry, "index": i})

    return result


async def show_meal_entries_for_delete(update: Update, context: ContextTypes.DEFAULT_TYPE, meal_type: str):
    user_id = update.effective_user.id
    lang = user_languages[user_id]

    entries_with_index = get_entries_by_meal_type(meal_type)

    if not entries_with_index:
        await update.message.reply_text(
            f"Немає записів типу '{meal_type}' за сьогодні." if lang == "uk"
            else f"No '{meal_type}' entries found for today."
        )
        await show_main_menu(update, context)
        return

    keyboard = []
    for i, item in enumerate(entries_with_index):
        entry = item["entry"]
        description = entry['description'].replace(f"{meal_type}: ", "")
        short_desc = description[:25] + "..." if len(description) > 25 else description
        keyboard.append([f"🗑️ {i + 1}. {short_desc}"])

    back_button = "⬅️ Назад" if lang == "uk" else "⬅️ Back"
    keyboard.append([back_button])

    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    user_delete_stage[user_id] = {
        "lang": lang,
        "meal_type": meal_type,
        "entries": entries_with_index,
        "awaiting_entry_selection": True
    }

    await update.message.reply_text(
        f"🗑️ Оберіть запис '{meal_type}' для видалення:" if lang == "uk"
        else f"🗑️ Select '{meal_type}' entry to delete:",
        reply_markup=reply_markup
    )


def delete_entry_by_index(index):
    try:
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return None

    if 0 <= index < len(data):
        deleted_entry = data.pop(index)

        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return deleted_entry
    return None


async def handle_meal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_input = update.message.text.strip()

    if user_id not in user_languages:
        await start(update, context)
        return

    lang = user_languages[user_id]

    # Handle back button first
    if user_input in ["⬅️ Назад", "⬅️ Back"]:
        if user_id in user_meal_stage:
            del user_meal_stage[user_id]
        if user_id in user_delete_stage:
            del user_delete_stage[user_id]
        await show_main_menu(update, context)
        return

    # Handle main menu actions
    if user_input in ["🗑️ Видалити прийом їжі", "🗑️ Delete a meal"]:
        await delete_meal_action(update, context)
        return

    if user_input in ["➕ Додати прийом їжі", "➕ Add a meal"]:
        await add_meal_action(update, context)
        return

    if user_input in ["📊 Підсумок за день", "📊 Summary for today"]:
        today = date.today()
        entries = get_entries_for_period(today, today)
        if entries:
            summary_text = format_summary_table(entries, lang)
            await update.message.reply_text(summary_text, parse_mode="Markdown")
        else:
            await update.message.reply_text("Немає даних за день. Спочатку додайте їжу" if lang == "uk" else
                                            "No data. Add food first.")
        await show_main_menu(update, context)
        return

    # Handle ADD MEAL process
    if user_id in user_meal_stage:
        stage = user_meal_stage[user_id]

        if stage.get("awaiting_meal_type", True):
            if user_input in MEAL_CHOICES[lang]:
                user_meal_stage[user_id] = {"lang": lang, "meal": user_input, "awaiting_meal_type": False}
                await update.message.reply_text(
                    "📝 Тепер введіть, що ви їли (наприклад: вівсянка в сухому вигляді 100г, банан 130г, мед 20г):"
                    if lang == "uk"
                    else "📝 Now enter what you ate (e.g. oatmeal not cooked 100g, banana 130g, honey 20g):"
                )
                return
            else:
                available_choices = ", ".join(MEAL_CHOICES[lang])
                await update.message.reply_text(
                    f"Будь ласка, виберіть прийом їжі з кнопок: {available_choices}"
                    if lang == "uk"
                    else f"Please select a meal type from the buttons: {available_choices}"
                )
                return
        else:
            # User has entered food description
            selected_meal = stage["meal"]
            full_description = f"{selected_meal}: {user_input}"
            del user_meal_stage[user_id]

            try:
                kbju = estimate_kbju(full_description, lang)
                save_entry(full_description, kbju)

                response = (
                    f"{MESSAGES[lang]['saved']}:\n{full_description}\n\n"
                    f"{MESSAGES[lang]['calories']}: {kbju['calories']} ккал\n"
                    f"{MESSAGES[lang]['protein']}: {kbju['protein']} г\n"
                    f"{MESSAGES[lang]['fat']}: {kbju['fat']} г\n"
                    f"{MESSAGES[lang]['carbs']}: {kbju['carbs']} г"
                )
                await update.message.reply_text(response)
            except Exception as e:
                await update.message.reply_text(
                    f"Помилка при обчисленні КБЖУ: {str(e)}"
                    if lang == "uk"
                    else f"Error calculating calories: {str(e)}"
                )

            await show_main_menu(update, context)
            return

    # Handle DELETE MEAL process
    if user_id in user_delete_stage:
        delete_stage = user_delete_stage[user_id]

        if delete_stage.get("awaiting_meal_type", False):
            if user_input in MEAL_CHOICES[lang]:
                await show_meal_entries_for_delete(update, context, user_input)
                return
            else:
                available_choices = ", ".join(MEAL_CHOICES[lang])
                await update.message.reply_text(
                    f"Будь ласка, оберіть тип прийому їжі: {available_choices}" if lang == "uk"
                    else f"Please select a meal type: {available_choices}"
                )
                return

        elif delete_stage.get("awaiting_entry_selection", False):
            if user_input.startswith("🗑️"):
                try:
                    entry_num = int(user_input.split(".")[0].replace("🗑️", "").strip())
                    entries = delete_stage["entries"]

                    if 1 <= entry_num <= len(entries):
                        selected_item = entries[entry_num - 1]
                        actual_index = selected_item["index"]

                        deleted_entry = delete_entry_by_index(actual_index)
                        if deleted_entry:
                            await update.message.reply_text(
                                f"✅ Запис видалено:\n{deleted_entry['description']}" if lang == "uk"
                                else f"✅ Entry deleted:\n{deleted_entry['description']}"
                            )
                        else:
                            await update.message.reply_text(
                                "❌ Помилка при видаленні запису." if lang == "uk"
                                else "❌ Error deleting entry."
                            )
                    else:
                        await update.message.reply_text(
                            "❌ Невірний номер запису." if lang == "uk"
                            else "❌ Invalid entry number."
                        )

                except (ValueError, IndexError):
                    await update.message.reply_text(
                        "❌ Невірний формат вибору." if lang == "uk"
                        else "❌ Invalid selection format."
                    )

                del user_delete_stage[user_id]
                await show_main_menu(update, context)
                return

    # Handle summary commands
    if user_input.lower().startswith(MESSAGES[lang]["summary_command"]):
        try:
            start_date, end_date = utils.parse_summary_command(user_input, lang)
            summary = get_summary_for_period(start_date, end_date, lang)
            await update.message.reply_text(summary)
        except Exception as e:
            await update.message.reply_text(
                f"Помилка при створенні підсумку: {str(e)}"
                if lang == "uk"
                else f"Error creating summary: {str(e)}"
            )
        return

    # Try to detect if input is a meal description
    try:
        if is_meal_description(user_input, lang):
            user_meal_stage[user_id] = {"lang": lang, "awaiting_meal_type": True}
            await add_meal_action(update, context)
            return
    except Exception as e:
        print(f"Error checking meal description: {e}")

    # Default help message
    await update.message.reply_text(
        "🔎 Я рахую КБЖВ для їжі. Обери прийом їжі, напиши, що ти їв(-ла), "
        "для точнішого розрахунку вказуючи вагу та готовність продукту.\n"
        "Наприклад:\n🍽 вівсянка в сирому вигляді 100г, банан 130г, мед 20г"
        if lang == "uk"
        else
        "🔎 I calculate calories and macros for food. Choose meal type and write what you ate, "
        "including weight and preparation state.\nFor example:\n🍽 raw oats 100g, banana 130g, honey 20g"
    )
    await show_main_menu(update, context)


if __name__ == '__main__':
    try:
        app = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()

        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("language", choose_language))

        app.add_handler(MessageHandler(filters.TEXT & filters.Regex("🇺🇦 Українська|🇬🇧 English"), set_language))

        app.add_handler(
            MessageHandler(filters.TEXT & filters.Regex("^➕ Додати прийом їжі$|^➕ Add a meal$"), add_meal_action))

        app.add_handler(
            MessageHandler(filters.TEXT & filters.Regex("^🌐 Змінити мову$|^🌐 Change language$"), choose_language))

        app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^⬅️ Назад$|^⬅️ Back$"), show_main_menu))

        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_meal))

        print("Bot started successfully!")
        app.run_polling()

    except Exception as e:
        print(f"Error starting bot: {e}")
        print("Check your .env file and make sure TELEGRAM_TOKEN is set correctly")
