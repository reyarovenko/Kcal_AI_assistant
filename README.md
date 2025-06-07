A Telegram bot that helps users track meals, calculate calories and macronutrients (proteins, fats, carbs), and manage meal history. Supports both 🇬🇧 English and 🇺🇦 Ukrainian.

⸻

Features
	•	Language selection: English or Ukrainian
	•	Add meals with type and description
	•	Automatically calculates calories, protein, fat, and carbs using OpenAI GPT
	•	View daily summary
	•	Delete meal entries from the list
	•	Stores data locally in data.json
	•	Understands natural-language commands like summary, food today, що я їв сьогодні

⸻

Project Structure

project/
│
├── bot.py                # Main Telegram bot logic
├── gpt_agent.py          # GPT-3.5 based nutrition estimation
├── storage.py            # Saving and summarizing entries
├── utils.py              # Command parsing and localization
├── .env                  # API keys
└── data.json             # Meal data storage


⸻

Installation & Run

	1.	Clone the project

git clone https://github.com/your-username/kcal-ai-assistant.git
cd kcal-ai-assistant

	2.	Create a virtual environment

python3 -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

	3.	Install dependencies

pip install -r requirements.txt

	4.	Set up your .env file

Create a .env file with the following content:

TELEGRAM_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key

	5.	Run the bot

python bot.py


⸻

Technologies Used
	•	Python 3.10+
	•	python-telegram-bot
	•	OpenAI GPT-3.5
	•	python-dotenv
	•	Local JSON file storage

⸻


TODO
	•	Voice/Image input support
	•	Use SQLite or Firebase for storage
	•	Nutrition goals & alerts

⸻
