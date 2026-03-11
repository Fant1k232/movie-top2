"""
Утиліта для зміни пароля адміністратора.
Запуск: python hash_password.py
"""
import hashlib
import getpass

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

print("=" * 50)
print("  MovieTop — Генератор хешу пароля")
print("=" * 50)

username = input("\nВведіть новий логін [admin]: ").strip() or "admin"
password = getpass.getpass("Введіть новий пароль: ")
confirm  = getpass.getpass("Підтвердіть пароль:  ")

if password != confirm:
    print("\n❌ Паролі не збігаються!")
    exit(1)

if len(password) < 6:
    print("\n❌ Пароль має бути не менше 6 символів!")
    exit(1)

hashed = hash_password(password)

print("\n✅ Готово! Вставте наступне в app.py:\n")
print(f'ADMIN_USERNAME = "{username}"')
print(f'ADMIN_PASSWORD_HASH = "{hashed}"')
print("\nАбо використайте змінні середовища (.env):\n")
print(f'ADMIN_USERNAME={username}')
print(f'ADMIN_PASSWORD_HASH={hashed}')
print(f'SECRET_KEY=your-random-secret-key-here')
