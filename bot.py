# -*- coding: utf-8 -*-
import os
import telebot
import subprocess
import re
import requests
import threading
from flask import Flask

# Получаем токен из переменных окружения
TOKEN = os.environ.get('BOT_TOKEN', '8523670344:AAFNlyL2tI9A9tmyHJjnAG5z0HH9nULJSqw')
bot = telebot.TeleBot(TOKEN)

# Создаем Flask приложение для порта
app = Flask(__name__)

@app.route('/')
def home():
    return "Telegram Bot is running!"

@app.route('/health')
def health():
    return "OK", 200

def transliterate_russian(text):
    """Транслитерирует русский текст в латиницу"""
    translit_dict = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        ' ': '_', '-': '-', '.': '.'
    }
    
    result = []
    for char in text.lower():
        if char in translit_dict:
            result.append(translit_dict[char])
        elif char.isalnum():
            result.append(char)
        else:
            result.append('_')
    
    return ''.join(result)

def is_phone_number(text):
    """Проверяет, является ли текст номером телефона"""
    clean_text = ''.join(filter(str.isdigit, text))
    return len(clean_text) >= 10 and len(clean_text) <= 15

def find_by_phone(phone_number):
    """Поиск по номеру телефона"""
    print(f"📱 Ищем по номеру: {phone_number}")
    
    clean_phone = ''.join(filter(str.isdigit, phone_number))
    profiles = []
    
    # Поиск в Telegram по номеру
    try:
        telegram_url = f'https://t.me/{clean_phone}'
        response = requests.get(telegram_url, timeout=5)
        if response.status_code == 200:
            profiles.append({
                'url': telegram_url,
                'website': 'Telegram'
            })
            print("✅ Найден в Telegram")
    except Exception as e:
        print(f"❌ Ошибка Telegram: {e}")
    
    # Поиск в WhatsApp по номеру
    try:
        whatsapp_url = f'https://wa.me/{clean_phone}'
        response = requests.get(whatsapp_url, timeout=5)
        if response.status_code == 200:
            profiles.append({
                'url': whatsapp_url,
                'website': 'WhatsApp'
            })
            print("✅ Найден в WhatsApp")
    except Exception as e:
        print(f"❌ Ошибка WhatsApp: {e}")
    
    return profiles

def find_in_vk(username):
    """Поиск во ВКонтакте"""
    try:
        vk_url = f'https://vk.com/{username}'
        response = requests.get(vk_url, timeout=5)
        
        # Проверяем что страница существует (не перенаправляет на главную)
        if response.status_code == 200 and 'error' not in response.url:
            return {
                'url': vk_url,
                'website': 'VK'
            }
    except Exception as e:
        print(f"❌ Ошибка VK: {e}")
    
    return None

def find_in_telegram(username):
    """Поиск в Telegram"""
    try:
        telegram_url = f'https://t.me/{username}'
        response = requests.get(telegram_url, timeout=5)
        
        # Проверяем что страница существует
        if response.status_code == 200 and 'tgme_page_title' in response.text:
            return {
                'url': telegram_url,
                'website': 'Telegram'
            }
    except Exception as e:
        print(f"❌ Ошибка Telegram: {e}")
    
    return None

def find_profiles_fast(username):
    """Быстрый поиск по username"""
    try:
        print(f"🔍 Ищем username: {username}")
        
        # Сначала проверяем VK и Telegram вручную
        manual_profiles = []
        
        vk_profile = find_in_vk(username)
        if vk_profile:
            manual_profiles.append(vk_profile)
        
        telegram_profile = find_in_telegram(username)
        if telegram_profile:
            manual_profiles.append(telegram_profile)
        
        # Затем используем Sherlock для остальных сайтов
        cmd = [
            'sherlock', username, 
            '--timeout', '3', 
            '--print-found',
            '--site', 'GitHub',
            '--site', 'Twitter',
            '--site', 'Instagram',
            '--site', 'Reddit', 
            '--site', 'Pinterest',
            '--site', 'Tumblr',
            '--site', 'Facebook',
            '--site', 'LinkedIn'
        ]
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True,
            encoding='utf-8',
            timeout=15
        )
        
        sherlock_profiles = []
        
        if result.stdout:
            for line in result.stdout.split('\n'):
                if '[+]' in line and 'http' in line:
                    parts = line.split(':', 2)
                    if len(parts) >= 3:
                        website = parts[1].strip()
                        url = parts[2].strip()
                        sherlock_profiles.append({
                            'url': url,
                            'website': website
                        })
                        print(f"✅ Найден: {website}")
        
        # Объединяем результаты
        all_profiles = manual_profiles + sherlock_profiles
        print(f"🎯 Всего найдено профилей: {len(all_profiles)}")
        return all_profiles
        
    except subprocess.TimeoutExpired:
        print("⏰ Поиск занял слишком много времени")
        # Возвращаем хотя бы ручные результаты
        return manual_profiles
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return []

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "👋 Привет! Я бот для поиска профилей в социальных сетях.\n\n"
        "🔍 Теперь можно искать:\n"
        "• По username: test, john, admin\n"
        "• По русским именам: иван, анна\n"
        "• По номеру телефона: +79123456789\n\n"
        "🌐 Поиск по 10+ платформам включая:\n"
        "• ВКонтакте, Telegram, WhatsApp\n"
        "• GitHub, Instagram, Twitter\n"
        "• Facebook, Reddit и другие\n\n"
        "💡 Просто отправьте имя, username или номер телефона"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "📋 Как пользоваться:\n\n"
        "Отправьте:\n"
        "• Username: test, john, admin\n"
        "• Русское имя: иван, анна, геннадий\n"
        "• Номер телефона: +79123456789\n\n"
        "🔍 Поиск работает по:\n"
        "• ВКонтакте, Telegram, WhatsApp\n"
        "• GitHub, Instagram, Twitter\n"
        "• Facebook, Reddit, Pinterest\n"
        "• LinkedIn, Tumblr\n\n"
        "⚡ Быстрый поиск - до 15 секунд"
    )
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['sites'])
def show_sites(message):
    sites_text = (
        "🌐 Полный список сайтов для поиска:\n\n"
        "📱 Мессенджеры:\n"
        "• Telegram, WhatsApp\n\n"
        "🇷🇺 Русские сети:\n"
        "• ВКонтакте\n\n"
        "💻 Социальные сети:\n"
        "• Facebook, Instagram, Twitter\n"
        "• LinkedIn, Pinterest, Tumblr\n\n"
        "👨‍💻 Разработчики:\n"
        "• GitHub, Reddit\n\n"
        "🔍 Всего: 12 платформ"
    )
    bot.reply_to(message, sites_text)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        search_query = message.text.strip()
        
        if not search_query:
            bot.reply_to(message, "❌ Введите данные для поиска")
            return
        
        processing_msg = bot.reply_to(message, f"🔍 Обрабатываю запрос...")
        
        # Определяем тип поиска
        if is_phone_number(search_query):
            # Поиск по номеру телефона
            profiles = find_by_phone(search_query)
            search_type = "номеру телефона"
        else:
            # Поиск по username
            if any(cyrillic in search_query for cyrillic in 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'):
                # Русское имя - транслитерируем
                latin_username = transliterate_russian(search_query)
                bot.send_message(message.chat.id, f"🔄 Преобразовал '{search_query}' → '{latin_username}'")
                profiles = find_profiles_fast(latin_username)
            else:
                # Латинский username
                profiles = find_profiles_fast(search_query)
            search_type = "username"
        
        # Формируем ответ
        if profiles:
            response = f"✅ Найдено по {search_type} '{search_query}': {len(profiles)}\n\n"
            
            for i, profile in enumerate(profiles, 1):
                response += f"{i}. {profile['website']}\n"
                response += f"   {profile['url']}\n\n"
                
        else:
            response = (
                f"❌ По {search_type} '{search_query}' ничего не найдено\n\n"
                "💡 Попробуйте:\n"
                "• Другой username или имя\n"
                "• Использовать латинские буквы\n"
                "• Проверить номер телефона\n\n"
                "📋 Примеры: test, john, иван, +79123456789"
            )
        
        # Отправляем результаты
        bot.send_message(message.chat.id, response)
        
        # Удаляем сообщение "идет поиск"
        try:
            bot.delete_message(message.chat.id, processing_msg.message_id)
        except:
            pass
        
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")

def run_bot():
    """Запускает бота"""
    print("🚀 Бот запущен!")
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        print(f"❌ Ошибка бота: {e}")

if __name__ == "__main__":
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    print("✅ Бот запущен в фоновом режиме")
    
    # Запускаем Flask для порта
    port = int(os.environ.get("PORT", 10000))
    print(f"🌐 Веб-сервер запущен на порту {port}")
    
    # Отключаем предупреждение разработки
    import os
    os.environ['FLASK_ENV'] = 'production'
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)