import requests
import json
import os
import datetime

# Настройки
filename = 'last_week_results.json'
access_token = os.environ['ACCESS_TOKEN']
club_id = '1426803'
headers = {'Authorization': f'Bearer {access_token}'}

def load_existing_activities(filename):
    """Загрузить существующие данные из файла."""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_activities_with_date(filename, new_activities):
    """Сохранить новые активности с датой в файл."""
    today_date = datetime.date.today().isoformat()
    existing_activities = load_existing_activities(filename)

    # Подготовка новых данных с датой
    new_data = [{'data': act, 'source': 'Strava', 'date': today_date} for act in new_activities]

    # Объединение старых и новых данных
    all_activities = existing_activities + new_data

    with open(filename, 'w') as f:
        json.dump(all_activities, f, ensure_ascii=False, indent=4)

# Получение данных из Strava API
response = requests.get(f'https://www.strava.com/api/v3/clubs/{club_id}/activities', headers=headers)

if response.status_code == 200:
    api_response = response.json()
    print("✅ Получены новые активности из Strava, количество записей:", len(api_response))
    save_activities_with_date(filename, api_response)
else:
    print(f"❌ Ошибка Strava API: {response.status_code}")
