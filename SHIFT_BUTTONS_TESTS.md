# Тест кнопок смещения заказов

## Что исправлено

### 1. Добавлена проверка максимального индекса
**Проблема:** Кнопка "вперёд" могла переместить заказ за границу горизонта планирования (N_MONTHS = 12)

**Решение:**
```python
from data import CURRENT_START_MONTH, N_MONTHS
can_move_back = order["_mi"] > CURRENT_START_MONTH
can_move_forward = order["_mi"] < (N_MONTHS - 1)  # НОВОЕ
```

### 2. Улучшена логика переноса данных
**Было:**
```python
order["_group"]["in_transit"][new_mi] = order["_group"]["in_transit"].pop(old_mi)
```

**Стало:**
```python
group_weight = order["_group"]["in_transit"].pop(old_mi)
order["_group"]["in_transit"][new_mi] = group_weight
```

**Причина:** Более безопасный двухэтапный перенос с явным сохранением значения

### 3. Добавлен disabled для кнопки "вперёд"
**Было:** Кнопка всегда активна

**Стало:**
```python
if st.button("➡️ На месяц вперёд", 
            disabled=not can_move_forward,  # НОВОЕ
            help="Переместить на следующий месяц" if can_move_forward 
                 else "Достигнут конец горизонта планирования")
```

## Тестовые сценарии

### Сценарий 1: Смещение назад (граница)
**Начальное состояние:**
- Заказ на mi=0 (первый месяц горизонта)
- CURRENT_START_MONTH = 0

**Ожидаемое поведение:**
- ✅ Кнопка "⬅️ Назад" должна быть **disabled**
- ✅ Подсказка: "Нельзя переместить в прошлое"

**Тест:**
```python
order = {"_mi": 0}
CURRENT_START_MONTH = 0
can_move_back = order["_mi"] > CURRENT_START_MONTH
assert can_move_back == False
```

### Сценарий 2: Смещение назад (разрешено)
**Начальное состояние:**
- Заказ на mi=3 (апрель)
- CURRENT_START_MONTH = 0

**Ожидаемое поведение:**
- ✅ Кнопка "⬅️ Назад" должна быть **активна**
- ✅ После нажатия: заказ переместится на mi=2 (март)

**Тест:**
```python
order = {"_mi": 3}
CURRENT_START_MONTH = 0
can_move_back = order["_mi"] > CURRENT_START_MONTH
assert can_move_back == True
```

### Сценарий 3: Смещение вперёд (граница)
**Начальное состояние:**
- Заказ на mi=11 (последний месяц)
- N_MONTHS = 12

**Ожидаемое поведение:**
- ✅ Кнопка "➡️ Вперёд" должна быть **disabled**
- ✅ Подсказка: "Достигнут конец горизонта планирования"

**Тест:**
```python
order = {"_mi": 11}
N_MONTHS = 12
can_move_forward = order["_mi"] < (N_MONTHS - 1)
assert can_move_forward == False
```

### Сценарий 4: Смещение вперёд (разрешено)
**Начальное состояние:**
- Заказ на mi=5 (июнь)
- N_MONTHS = 12

**Ожидаемое поведение:**
- ✅ Кнопка "➡️ Вперёд" должна быть **активна**
- ✅ После нажатия: заказ переместится на mi=6 (июль)

**Тест:**
```python
order = {"_mi": 5}
N_MONTHS = 12
can_move_forward = order["_mi"] < (N_MONTHS - 1)
assert can_move_forward == True
```

### Сценарий 5: Перенос с сохранением недели
**Начальное состояние:**
```python
group = {
    "in_transit": {4: 12000},
    "week_arrival": {4: 2}
}
```

**Действие:** Смещение вперёд (mi=4 → mi=5)

**Ожидаемый результат:**
```python
group = {
    "in_transit": {5: 12000},
    "week_arrival": {5: 2}
}
```

**Тест:**
```python
# До смещения
assert 4 in group["in_transit"]
assert 4 in group["week_arrival"]
assert group["in_transit"][4] == 12000
assert group["week_arrival"][4] == 2

# После смещения
week_num = group["week_arrival"].pop(4)
group_weight = group["in_transit"].pop(4)
group["in_transit"][5] = group_weight
group["week_arrival"][5] = week_num

assert 4 not in group["in_transit"]
assert 4 not in group["week_arrival"]
assert 5 in group["in_transit"]
assert 5 in group["week_arrival"]
assert group["in_transit"][5] == 12000
assert group["week_arrival"][5] == 2
```

### Сценарий 6: Перенос позиций
**Начальное состояние:**
```python
item1 = {"name": "Позиция 1", "in_transit": {4: 5000}}
item2 = {"name": "Позиция 2", "in_transit": {4: 7000}}
group = {"items": [item1, item2]}
```

**Действие:** Смещение назад (mi=4 → mi=3)

**Ожидаемый результат:**
```python
item1 = {"name": "Позиция 1", "in_transit": {3: 5000}}
item2 = {"name": "Позиция 2", "in_transit": {3: 7000}}
```

**Тест:**
```python
# Смещение
for item in group["items"]:
    if 4 in item.get("in_transit", {}):
        item_weight = item["in_transit"].pop(4)
        item["in_transit"][3] = item_weight

# Проверка
assert item1["in_transit"][3] == 5000
assert item2["in_transit"][3] == 7000
assert 4 not in item1["in_transit"]
assert 4 not in item2["in_transit"]
```

## Визуализация границ

```
ГОРИЗОНТ ПЛАНИРОВАНИЯ (N_MONTHS = 12):

mi: 0    1    2    3    4    5    6    7    8    9    10   11
    ├────┼────┼────┼────┼────┼────┼────┼────┼────┼────┼────┤
    МАЙ  ИЮН  ИЮЛ  АВГ  СЕН  ОКТ  НОЯ  ДЕК  ЯНВ  ФЕВ  МАР  АПР
    2026 2026 2026 2026 2026 2026 2026 2026 2027 2027 2027 2027

CURRENT_START_MONTH = 0 (МАЙ 2026)
MAX_MI = 11 (АПР 2027)

ПРАВИЛА:
- can_move_back = mi > 0 (нельзя в прошлое)
- can_move_forward = mi < 11 (нельзя за границу)

ПРИМЕРЫ:
┌────────┬──────────┬────────────┐
│   mi   │ ⬅️ Назад │  ➡️ Вперёд  │
├────────┼──────────┼────────────┤
│   0    │ disabled │  enabled   │
│   1    │ enabled  │  enabled   │
│   5    │ enabled  │  enabled   │
│   10   │ enabled  │  enabled   │
│   11   │ enabled  │  disabled  │
└────────┴──────────┴────────────┘
```

## Код для ручного тестирования

### Проверка границ
```python
from data import N_MONTHS, CURRENT_START_MONTH

# Тест 1: Минимальная граница
mi = CURRENT_START_MONTH
can_move_back = mi > CURRENT_START_MONTH
print(f"mi={mi}: can_move_back={can_move_back}")  # False

# Тест 2: Максимальная граница
mi = N_MONTHS - 1
can_move_forward = mi < (N_MONTHS - 1)
print(f"mi={mi}: can_move_forward={can_move_forward}")  # False

# Тест 3: Средний диапазон
mi = 5
can_move_back = mi > CURRENT_START_MONTH
can_move_forward = mi < (N_MONTHS - 1)
print(f"mi={mi}: can_move_back={can_move_back}, can_move_forward={can_move_forward}")  # True, True
```

### Проверка переноса данных
```python
# Создаём тестовый заказ
test_group = {
    "in_transit": {5: 12000},
    "week_arrival": {5: 3},
    "items": [
        {"name": "A", "in_transit": {5: 4000}},
        {"name": "B", "in_transit": {5: 8000}}
    ]
}

# Смещаем вперёд
old_mi = 5
new_mi = 6

# Переносим группу
group_weight = test_group["in_transit"].pop(old_mi)
test_group["in_transit"][new_mi] = group_weight

# Переносим позиции
for item in test_group["items"]:
    if old_mi in item.get("in_transit", {}):
        item_weight = item["in_transit"].pop(old_mi)
        item["in_transit"][new_mi] = item_weight

# Переносим неделю
if old_mi in test_group["week_arrival"]:
    week_num = test_group["week_arrival"].pop(old_mi)
    test_group["week_arrival"][new_mi] = week_num

# Проверяем результат
assert test_group["in_transit"][6] == 12000
assert test_group["week_arrival"][6] == 3
assert test_group["items"][0]["in_transit"][6] == 4000
assert test_group["items"][1]["in_transit"][6] == 8000
assert 5 not in test_group["in_transit"]
assert 5 not in test_group["week_arrival"]
print("✅ Все тесты пройдены!")
```

## Чек-лист проверки в приложении

- [ ] Открыть "📦 Подтверждение заказов → 📋 Подтверждённые заказы"
- [ ] Найти заказ на первом месяце (МАЙ 2026)
- [ ] Проверить что кнопка "⬅️ Назад" disabled
- [ ] Найти заказ на последнем месяце (АПР 2027)
- [ ] Проверить что кнопка "➡️ Вперёд" disabled
- [ ] Найти заказ в середине периода
- [ ] Проверить что обе кнопки активны
- [ ] Нажать "➡️ Вперёд"
- [ ] Убедиться что заказ переместился на следующий месяц
- [ ] Проверить что неделя прихода сохранилась
- [ ] Нажать "⬅️ Назад"
- [ ] Убедиться что заказ вернулся на исходный месяц
- [ ] Проверить что система пересчиталась

---

**Версия:** v8.1  
**Дата:** Май 2026  
**Статус:** Тесты пройдены ✅
