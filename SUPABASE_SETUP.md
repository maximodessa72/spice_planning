# Настройка PostgreSQL через Supabase

## Шаг 1: Создать проект

1. Зайти на https://supabase.com
2. Sign up (бесплатно)
3. New project:
   - Name: `spice-planning`
   - Database Password: (придумать) → **СОХРАНИТЬ**
   - Region: Europe (Frankfurt)
   - Create project (ждать 2 минуты)

## Шаг 2: Получить connection string

1. Project Settings → Database
2. Найти "Connection string" → URI
3. Скопировать строку:
   ```
   postgresql://postgres.xxxxx:[YOUR-PASSWORD]@aws-0-eu-central-1.pooler.supabase.com:6543/postgres
   ```
4. Заменить `[YOUR-PASSWORD]` на реальный пароль

## Шаг 3: Добавить в Streamlit Secrets

1. Streamlit Cloud → App → Settings → Secrets
2. Добавить:
```toml
[postgres]
url = "postgresql://postgres.xxxxx:ВАШ_ПАРОЛЬ@aws-0-eu-central-1.pooler.supabase.com:6543/postgres"
```

3. Save

## Шаг 4: Развернуть код

```bash
git add app.py requirements.txt
git commit -m "Автосохранение через PostgreSQL"
git push
```

## Готово!

Теперь:
- ✅ Данные автоматически сохраняются в БД после каждого изменения
- ✅ При перезагрузке приложения данные автоматически восстанавливаются
- ✅ Все пользователи видят актуальные данные
- ✅ JSON бэкап всё равно работает (на всякий случай)

## Проверка

После развёртывания:
1. Подтверди заказ
2. Перезагрузи приложение (Ctrl+R)
3. Заказ должен остаться ✅

---

**Бесплатно:** 500 MB, без ограничений по времени
**Поддержка:** support@supabase.io
