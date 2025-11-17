# app.py
import subprocess
import json

def find_profiles(username):
    try:
        print(f"🔍 Sherlock ищет: {username}")
        
        # Команда sherlock - только найденные профили в JSON
        cmd = ['sherlock', username, '--timeout', '5', '--json', '--print-found']
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True,
            encoding='utf-8',
            timeout=60
        )
        
        profiles = []
        
        if result.stdout:
            # Обрабатываем каждую JSON строку
            for line in result.stdout.strip().split('\n'):
                line = line.strip()
                if line and line.startswith('{'):
                    try:
                        data = json.loads(line)
                        # Проверяем что профиль найден
                        if data.get('url') and data.get('status', '').lower() == 'found':
                            profiles.append({
                                'url': data['url'],
                                'website': data.get('name', 'Unknown')
                            })
                    except json.JSONDecodeError:
                        continue
        
        print(f"✅ Найдено профилей: {len(profiles)}")
        return profiles
        
    except subprocess.TimeoutExpired:
        print("⏰ Время поиска истекло")
        return []
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return []

if __name__ == "__main__":
    # Тест для проверки
    findings = find_profiles("test")
    print(f"Тестовый результат: {len(findings)} профилей")