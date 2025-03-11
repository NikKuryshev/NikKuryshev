import requests
import json
import asyncio
import os
from telegram import Bot
from telegram.error import TelegramError

# Настройки
filename = 'last_week_results.json'
access_token = os.environ['ACCESS_TOKEN']
club_id = '1426803'
headers = {'Authorization': f'Bearer {access_token}'}
telegram_bot_token = os.environ['TELEGRAM_BOT_TOKEN']
chat_id = 50820587

def load_past_week_activities(filename):
    """Загрузить данные прошлой недели из файла."""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_current_week_activities(filename, data):
    """Сохранить текущие данные в файл. Укажем, что источник - Strava."""
    data_with_source = [{'data': act, 'source': 'Strava'} for act in data]
    with open(filename, 'w') as f:
        json.dump(data_with_source, f, ensure_ascii=False, indent=4)

def calculate_distances(activities):
    """Вычисление суммарных расстояний для каждого спортсмена из всех источников."""
    result = {}
    for act in activities:
        source = act.get("source", "")
        athlete_info = {}
        
        # Извлечение информации в зависимости от источника
        if source == "Strava":
            athlete_info = act.get("data", {}).get("athlete", {})
            distance = act.get("data", {}).get("distance", 0)
        elif source == "Telegram":
            athlete_info = act.get("athlete", {})
            distance = act.get("distance", 0)
        
        athlete_name = athlete_info.get("firstname", "Unknown") + " " + athlete_info.get("lastname", "")
        result[athlete_name] = result.get(athlete_name, 0) + distance
    return result

async def send_message_to_telegram(bot_token, chat_id, text, delay_seconds):
    """Асинхронная отправка сообщения в Telegram."""
    print(f"Сообщение будет отправлено через {delay_seconds / 3600:.2f} часов...")
    await asyncio.sleep(delay_seconds)
    bot = Bot(token=bot_token)
    try:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode='Markdown')
        print("✅ Сообщение отправлено в Телеграм!")
    except TelegramError as e:
        print(f"❌ Telegram API error: {e}")

# Загрузка прошлой недели активности
past_week_activities = load_past_week_activities(filename)

# Получение данных этой недели из Strava API
response = requests.get(f'https://www.strava.com/api/v3/clubs/{club_id}/activities', headers=headers)

if response.status_code == 200:
    api_response = response.json()
    print("✅ Активности получены, количество:", len(api_response))
else:
    print(f"❌ Strava API ошибка: {response.status_code}")
    api_response = []

# Подсчет и вычисление прогресса
# Мы предполагаем, что в прошлых данных тоже может быть несколько источников
last_week_distances = calculate_distances(past_week_activities)
# Преобразуем данные текущей недели к новому виду
current_week_distances = calculate_distances([{'data': act, 'source': 'Strava'} for act in api_response])

# Рассчитываем разницу
difference = {}
for athlete in current_week_distances:
    prev_distance = last_week_distances.get(athlete, 0)
    current_distance = current_week_distances[athlete]
    difference[athlete] = current_distance - prev_distance

sorted_difference = sorted(
    [(athlete, diff) for athlete, diff in difference.items() if diff > 0],
    key=lambda x: x[1], reverse=True
)

# Формирование сообщения в Telegram
message = "🏆 *Рейтинг спортсменов за неделю* 🏃‍♂️\n\n"
if sorted_difference:
    for i, (name, diff_distance) in enumerate(sorted_difference, 1):
        message += f"{i}. {name} — {diff_distance / 1000:.1f} км\n"
else:
    message += "Прироста активности за текущую неделю нет 🤷‍♂️"

message += "\nХорошей всем недели 🚴‍♀️🏅"

# Сохранение текущей недели данных для следующего использования
save_current_week_activities(filename, api_response)

# Запуск асинхронности для отправки сообщения в Telegram
asyncio.run(send_message_to_telegram(telegram_bot_token, chat_id, message, delay_seconds=10))
