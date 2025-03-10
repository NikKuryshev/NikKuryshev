import requests
import json
import asyncio
import os
from telegram import Bot
from telegram.error import TelegramError

# Настройки
filename = 'last_week_results.json'
access_token = os.environ['ACCESS_TOKEN']  # Теперь токен извлекается из переменной окружения
club_id = '1426803'
headers = {'Authorization': f'Bearer {access_token}'}
telegram_bot_token = os.environ['TELEGRAM_BOT_TOKEN']  # Тоже из окружения
chat_id = 50820587

# Читаем файл прошлой недели
try:
    with open(filename, 'r') as f:
        past_week_activities = json.load(f)
except FileNotFoundError:
    past_week_activities = []

# Получаем данные этой недели из Strava API (синхронно)
response = requests.get(f'https://www.strava.com/api/v3/clubs/{club_id}/activities', headers=headers)

if response.status_code == 200:
    api_response = response.json()
    print("✅ Активности получены, количество:", len(api_response))
else:
    print(f"❌ Страва API ошибка: {response.status_code}")
    api_response = []

def calculate_distances(activities):
    result = {}
    for act in activities:
        athlete_info = act.get("athlete", {})
        athlete_name = athlete_info.get("firstname", "Unknown") + " " + athlete_info.get("lastname", "")
        distance = act.get("distance", 0)
        result[athlete_name] = result.get(athlete_name, 0) + distance
    return result

# Подсчет и вычисление прогресса
last_week_distances = calculate_distances(past_week_activities)
current_week_distances = calculate_distances(api_response)

difference = {}
for athlete in current_week_distances:
    prev_distance = last_week_distances.get(athlete, 0)
    current_distance = current_week_distances[athlete]
    difference[athlete] = current_distance - prev_distance

sorted_difference = sorted(
    [(athlete, diff) for athlete, diff in difference.items() if diff > 0],
    key=lambda x: x[1], reverse=True
)

# Формируем сообщение в Telegram
message = "🏆 *Рейтинг спортсменов за неделю* 🏃‍♂️\n\n"
if sorted_difference:
    for i, (name, diff_distance) in enumerate(sorted_difference, 1):
        message += f"{i}. {name} — {diff_distance / 1000:.1f} км\n"
else:
    message += "Прироста активности за текущую неделю нет 🤷‍♂️"

message += "\nХорошей всем недели 🚴‍♀️🏅"

# Сохраняем текущее состояние на следующую неделю
with open(filename, 'w') as f:
    json.dump(api_response, f)

# Асинхронная функция отправки сообщения в Telegram
async def send_message_to_telegram(bot_token, chat_id, text, delay_seconds):
    print(f"Сообщение будет отправлено через {delay_seconds / 3600:.2f} часов...")
    await asyncio.sleep(delay_seconds)  # ждём нужное время перед отправкой
    bot = Bot(token=bot_token)
    try:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode='Markdown')
        print("✅ Сообщение отправлено в Телеграм!")
    except TelegramError as e:
        print(f"❌ Telegram API error: {e}")

# Запускаем асинхронность отправки сообщения
asyncio.run(send_message_to_telegram(telegram_bot_token, chat_id, message, delay_seconds=10))
