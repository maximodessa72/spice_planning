"""
Данные для системы планирования закупок
"""

from datetime import datetime

# Сезонные планы
KARDAMON_SEASONAL = {0: 50, 1: 50, 2: 0, 3: 302, 4: 199, 5: 484, 6: 458, 7: 202, 8: 111, 9: 400, 10: 150, 11: 130}
PDG_SEASONAL = {0: 3200, 1: 3200, 2: 3200, 3: 3200, 4: 3200, 5: 4500, 6: 7000, 7: 3200, 8: 3200, 9: 3200, 10: 3200, 11: 3200}

# Константы
BUFFER_DEFAULT = 1.0
BUFFER_GROUP4 = 1.2
BAG = 25
N_MONTHS = 12  # Планирование на 12 месяцев вперёд

# АВТООПРЕДЕЛЕНИЕ текущего месяца (для закупок)
_current_date = datetime.now()
BASE_YEAR = _current_date.year
BASE_MONTH = _current_date.month  # Текущий месяц (май)

def get_current_start_month():
    """
    Получить индекс стартового месяца для текущей даты
    Возвращает количество месяцев от базовой даты
    """
    now = datetime.now()
    current_year = now.year
    current_month = now.month
    
    # Вычисляем разницу в месяцах от базовой даты
    months_diff = (current_year - BASE_YEAR) * 12 + (current_month - BASE_MONTH)
    
    return max(0, months_diff)  # Не может быть отрицательным

# Текущий стартовый месяц (динамически вычисляется)
CURRENT_START_MONTH = get_current_start_month()

# Все группы товаров
GROUPS = [
    {
        "name": "1. Єгипет (трави)",
        "cycle": 60,
        "container": 40000,
        "unit_container": 20000,
        "in_transit": {0: 36700, 1: 60150},
        "items": [
            {"name": "Базилік зелень (В)", "balance": 156, "plan": 5225, "in_transit": {0: 7500, 1: 6450}},
            {"name": "Базилік зелень (С)", "balance": 4037, "plan": 1500, "in_transit": {1: 0}},
            {"name": "Кріп зелень (А)", "balance": 26, "plan": 1600, "in_transit": {0: 3000, 1: 1250}},
            {"name": "Кріп зелень (А) МС", "balance": 4575, "plan": 450, "in_transit": {1: 0}},
            {"name": "Кріп зелень (В)", "balance": 363, "plan": 5000, "in_transit": {0: 5600, 1: 7700}},
            {"name": "Кріп зелень (С)", "balance": 450, "plan": 975, "in_transit": {1: 0}},
            {"name": "Лемонграс", "balance": 0, "plan": 1450, "in_transit": {0: 2100, 1: 0}},
            {"name": "М'ята зелень", "balance": 5044, "plan": 2275, "in_transit": {0: 1500, 1: 2250}},
            {"name": "М'ята перцева", "balance": 12000, "plan": 0, "in_transit": {0: 9000, 1: 20000}, "plan_override": {0: 12000, 1: 9000, 2: 10000, 3: 10000}},
            {"name": "Майоран зелень (А)", "balance": 911, "plan": 600, "in_transit": {1: 0}},
            {"name": "Майоран зелень (В)", "balance": 2003, "plan": 1000, "in_transit": {1: 0}},
            {"name": "Орегано зелень", "balance": 2185, "plan": 2250, "in_transit": {0: 2100, 1: 2500}},
            {"name": "Петрушка зелень (А)", "balance": 0, "plan": 1000, "in_transit": {0: 3000, 1: 0}},
            {"name": "Петрушка зелень (В)", "balance": 636, "plan": 5000, "in_transit": {0: 5000, 1: 8350}},
            {"name": "Петрушка зелень (С)", "balance": 1005, "plan": 1000, "in_transit": {0: 500, 1: 1700}},
            {"name": "Розмарин зелень", "balance": 272, "plan": 2200, "in_transit": {0: 2100, 1: 3700}},
            {"name": "Селера зелень", "balance": 255, "plan": 750, "in_transit": {0: 1000, 1: 1000}},
            {"name": "Чебрець зелень", "balance": 489, "plan": 1800, "in_transit": {0: 1700, 1: 2400}},
            {"name": "Чабер зелень", "balance": 326, "plan": 575, "in_transit": {0: 500, 1: 1000}},
            {"name": "Аніс", "balance": 1088, "plan": 200, "in_transit": {1: 0}},
            {"name": "Фенхель", "balance": 1003, "plan": 1125, "in_transit": {0: 1100, 1: 1850}},
        ]
    },
    {
        "name": "2. В'єтнам (перець)",
        "cycle": 110,
        "container": 28000,
        "in_transit": {2: 28000},
        "items": [
            {"name": "Перець білий горошок (630) ASTA", "balance": 3172, "plan": 500, "in_transit": {}},
            {"name": "Перець чорний горошок (500) FAQ", "balance": 11622, "plan": 5100, "in_transit": {2: 12500}},
            {"name": "Перець чорний горошок (ASTA 500)", "balance": 4157, "plan": 8500, "in_transit": {2: 15500}},
        ]
    },
    {
        "name": "3. Китай (овощі)",
        "cycle": 110,
        "container": 25000,
        "in_transit": {2: 25000},
        "items": [
            {"name": "Паприка подрібнена 3х3 зелена (Китай)", "balance": 3036, "plan": 975, "in_transit": {2: 1600}},
            {"name": "Паприка подрібнена 6х6 зелена (Китай)", "balance": 2246, "plan": 650, "in_transit": {2: 1900}},
            {"name": "Паприка подрібнена 3х3 червона (Китай)", "balance": 10808, "plan": 4000, "in_transit": {2: 6900}},
            {"name": "Паприка подрібнена 6х6 червона (Китай)", "balance": 364, "plan": 1000, "in_transit": {2: 4400}},
            {"name": "Паприка подрібнена 9х9 червона (Китай)", "balance": 2334, "plan": 1000, "in_transit": {2: 900}},
            {"name": "Томат подрібнений 3х3 (Китай)", "balance": 5900, "plan": 2600, "in_transit": {2: 8800}},
            {"name": "Томат подрібнений 6х6 (Китай)", "balance": 2800, "plan": 500, "in_transit": {2: 500}},
        ]
    },
    {
        "name": "4. Китай (морква)",
        "cycle": 110,
        "container": 27000,
        "in_transit": {3: 27000},
        "items": [
            {"name": "Морква (3х3)", "balance": 37617, "plan": 6000, "in_transit": {3: 27000}},
        ]
    },
    {
        "name": "5. Китай (часник)",
        "cycle": 110,
        "container": 27000,
        "in_transit": {0: 27200, 1: 27200, 2: 26300},
        "items": [
            {"name": "Часник 40/60 (Китай)", "balance": 31282, "plan": 19000, "in_transit": {0: 17800, 1: 15700, 2: 12800}},
            {"name": "Часник 26/40 (Китай)", "balance": 873, "plan": 1000, "in_transit": {0: 500, 1: 500, 2: 2500}},
            {"name": "Часник 8/16 (Китай)", "balance": 6180, "plan": 5000, "in_transit": {0: 3350, 1: 6000, 2: 6000}},
            {"name": "Часник пластівці (Китай)", "balance": 7019, "plan": 1300, "in_transit": {0: 2300, 1: 1800, 2: 1800}},
            {"name": "Часник мелений Китай", "balance": 371, "plan": 3000, "in_transit": {0: 3250, 1: 3200, 2: 3200}},
        ]
    },
    {
        "name": "6. Китай (паприка і чилі)",
        "cycle": 110,
        "container": 28000,
        "in_transit": {1: 28000, 2: 28000},
        "items": [
            {"name": "Паприка мелена (ASTA  40)", "balance": 5748, "plan": 2500, "in_transit": {1: 0, 2: 0}},
            {"name": "Паприка мелена (ASTA  80)", "balance": 6931, "plan": 4500, "in_transit": {1: 4500, 2: 4400}},
            {"name": "Паприка мелена (ASTA 100)", "balance": 5108, "plan": 3000, "in_transit": {1: 2500}},
            {"name": "Паприка мелена (ASTA 120)", "balance": 299, "plan": 4500, "in_transit": {1: 5900, 2: 7500}},
            {"name": "Паприка мелена (ASTA 140)", "balance": 269, "plan": 4000, "in_transit": {1: 4000, 2: 7200}},
            {"name": "Перець червоний мелений Чилі (25-30к, ASTA 60) Китай", "balance": 6569, "plan": 4850, "in_transit": {1: 8200, 2: 6500}},
            {"name": "Перець Чилі подрібнений 3х3 (Китай)", "balance": 238, "plan": 2200, "in_transit": {1: 2900, 2: 2400}},
        ]
    },
    {
        "name": "7. Іспанія (паприка копч.)",
        "cycle": 14,
        "container": 10000,
        "in_transit": {0: 10000},
        "items": [
            {"name": "Паприка мелена копчена (ASTA 130) Іспанія", "balance": 2664, "plan": 1500, "in_transit": {0: 10000}},
        ]
    },
    {
        "name": "8. Індія (цибуля)",
        "cycle": 90,
        "container": 17000,
        "in_transit": {1: 35000},
        "items": [
            {"name": "Цибуля ріпчаста пластівці 10/20", "balance": 14075, "plan": 5500, "in_transit": {1: 15000}, "bag": 14},
            {"name": "Цибуля ріпчаста подрібнена  1/3", "balance": 8300, "plan": 7000, "in_transit": {1: 17000}, "bag": 20},
            {"name": "Цибуля мелена (Індія)", "balance": 2, "plan": 1500, "in_transit": {1: 3000}},
        ]
    },
    {
        "name": "9. Індія (кунжут)",
        "cycle": 90,
        "container": 56000,
        "unit_container": 28000,
        "in_transit": {0: 54000},
        "items": [
            {"name": "Кунжут білий 99,90", "balance": 28517, "plan": 20000, "in_transit": {0: 29400}},
            {"name": "Кунжут білий 99,98", "balance": 38630, "plan": 14000, "in_transit": {0: 19000}},
            {"name": "Кунжут чорний Рremium", "balance": 3772, "plan": 3500, "in_transit": {0: 5600}},
        ]
    },
    {
        "name": "10. Індія (спеції)",
        "cycle": 90,
        "container": 25000,
        "in_transit": {},
        "items": [
            {"name": "Фенугрек Індія", "balance": 566, "plan": 2500, "in_transit": {}},
            {"name": "Зіра (А)", "balance": 525, "plan": 1000, "in_transit": {}},
            {"name": "Калінджі Індія", "balance": 5450, "plan": 1800, "in_transit": {}},
        ]
    },
    {
        "name": "11. Індонезія (спеції)",
        "cycle": 90,
        "container": 10000,
        "in_transit": {},
        "items": [
            {"name": "Гвоздика", "balance": 2477, "plan": 1600, "in_transit": {}},
            {"name": "Мускатний горіх (ABCD)", "balance": 81, "plan": 150, "in_transit": {}},
        ]
    },
    {
        "name": "12. Індія (куркума)",
        "cycle": 90,
        "container": 28000,
        "in_transit": {1: 28000},
        "items": [
            {"name": "Куркума корінь Індія", "balance": 757, "plan": 1800, "in_transit": {1: 5500}},
            {"name": "Куркума мелена (2%) Індія", "balance": 9432, "plan": 950, "in_transit": {1: 0}},
            {"name": "Куркума мелена (2,5%) Індія", "balance": 4084, "plan": 4500, "in_transit": {1: 13000}},
            {"name": "Куркума мелена (3%) Індія", "balance": 9696, "plan": 1300, "in_transit": {1: 9500}},
            {"name": "Куркума мелена (3,5%) Індія", "balance": 5959, "plan": 800, "in_transit": {1: 0}},
        ]
    },
    {
        "name": "13. Іран (Родзинка)",
        "cycle": 60,
        "container": 21000,
        "in_transit": {0: 42000},
        "items": [
            {"name": "Родзинка малояр ААА", "balance": 20861, "plan": 10000, "in_transit": {0: 42000}},
        ]
    },
    {
        "name": "14. ЄС (Кмин)",
        "cycle": 21,
        "container": 21000,
        "in_transit": {0: 21000},
        "items": [
            {"name": "Кмин Прибалтика", "balance": 7042, "plan": 7000, "in_transit": {0: 21000}},
        ]
    },
    {
        "name": "15. Єгипет (Кмин)",
        "cycle": 60,
        "container": 18000,
        "in_transit": {0: 7300},
        "items": [
            {"name": "Кмин Єгипет", "balance": 7131, "plan": 4000, "in_transit": {0: 7300}},
        ]
    },
    {
        "name": "16. Нігерія (гібіскус)",
        "cycle": 120,
        "container": 12000,
        "in_transit": {1: 26000},
        "items": [
            {"name": "Гібіскус", "balance": 3033, "plan": 6050, "in_transit": {1: 26000}},
        ]
    },
    {
        "name": "17. Мексика (ПДГ)",
        "cycle": 100,
        "container": 12000,
        "in_transit": {0: 25000},
        "items": [
            {"name": "Перець духмяний горошок Premium", "balance": 4149, "plan": 3625, "in_transit": {0: 25000}, "seasonal": True, "plan_override": {0: 3200, 1: 3200, 2: 3200, 3: 3200, 4: 3200, 5: 4500, 6: 7000, 7: 3200, 8: 3200, 9: 3200, 10: 3200, 11: 3200}},
        ]
    },
    {
        "name": "18. В'єтнам (кориця і бадьян)",
        "cycle": 110,
        "container": 24000,
        "in_transit": {3: 21800},
        "items": [
            {"name": "Бадьян", "balance": 382, "plan": 393, "in_transit": {3: 2000}, "seasonal": True, "plan_override": {0: 200, 1: 100, 2: 10, 3: 10, 4: 100, 5: 650, 6: 1100, 7: 650, 8: 750, 9: 750, 10: 200, 11: 200}},
            {"name": "Кориця мелена 2% (В'єтнам)", "balance": 1692, "plan": 2500, "in_transit": {3: 8700}},
            {"name": "Кориця мелена 3% (В'єтнам)", "balance": 5787, "plan": 2500, "in_transit": {3: 4000}},
            {"name": "Кориця палички (8) В'єтнам", "balance": 46, "plan": 683, "in_transit": {3: 3000}, "seasonal": True, "plan_override": {0: 50, 1: 50, 2: 50, 3: 50, 4: 300, 5: 850, 6: 2000, 7: 900, 8: 2000, 9: 1250, 10: 500, 11: 200}},
            {"name": "Кориця палички (6) В'єтнам", "balance": 231, "plan": 198, "in_transit": {3: 1600}, "seasonal": True, "plan_override": {0: 100, 1: 50, 2: 10, 3: 10, 4: 200, 5: 200, 6: 300, 7: 300, 8: 300, 9: 300, 10: 300, 11: 300}},
            {"name": "Кориця подрібнена (лом) Екстра", "balance": 5, "plan": 100, "in_transit": {3: 1000}, "seasonal": True, "plan_override": {0: 0, 1: 0, 2: 0, 3: 0, 4: 100, 5: 100, 6: 200, 7: 200, 8: 200, 9: 200, 10: 200, 11: 1}},
            {"name": "Кориця подрібнена 3% (лом)", "balance": 165, "plan": 325, "in_transit": {3: 1500}, "seasonal": True, "plan_override": {0: 100, 1: 100, 2: 50, 3: 50, 4: 100, 5: 500, 6: 500, 7: 500, 8: 500, 9: 500, 10: 500, 11: 500}},
        ]
    },
    {
        "name": "19. Індія (арахіс)",
        "cycle": 60,
        "container": 26000,
        "in_transit": {},
        "items": [
            {"name": "Арахіс 50/60 Болд Індія", "balance": 250, "plan": 15000, "in_transit": {}},
        ]
    },
    {
        "name": "20. Бразилія (арахіс)",
        "cycle": 90,
        "container": 52000,
        "unit_container": 26000,
        "in_transit": {},
        "items": [
            {"name": "Арахіс 38/42 Раннер (бланш) Бразилія", "balance": 2800, "plan": 5000, "in_transit": {}},
            {"name": "Арахіс 38/42 Раннер (бланш/половинки) Бразилія", "balance": 16027, "plan": 20000, "in_transit": {}},
        ]
    },
    {
        "name": "21. Індонезія (кокос)",
        "cycle": 90,
        "container": 25000,
        "in_transit": {},
        "items": [
            {"name": "Кокосова стружка HF Файн Індонезія", "balance": 16019, "plan": 2000, "in_transit": {}},
            {"name": "Кокосова стружка HF Медіум Індонезія", "balance": 9072, "plan": 4000, "in_transit": {}},
        ]
    },
    {
        "name": "22. Мак",
        "cycle": 60,
        "container": 20000,
        "in_transit": {},
        "items": [
            {"name": "Мак блакитний", "balance": 60, "plan": 5000, "in_transit": {}},
        ]
    },
    {
        "name": "23. Спент",
        "cycle": 90,
        "container": 22000,
        "in_transit": {2: 22000},
        "items": [
            {"name": "Спент ПЧГ (3-5 мм)", "balance": 74, "plan": 750, "in_transit": {2: 5000}},
            {"name": "Спент ПЧГ (1-2 мм)", "balance": 15060, "plan": 3200, "in_transit": {2: 15000}},
            {"name": "Кардамон зелений (6-7 мм)", "balance": 787, "plan": 300, "in_transit": {2: 2000}, "seasonal": True, "plan_override": {0: 50, 1: 50, 2: 0, 3: 302, 4: 199, 5: 484, 6: 458, 7: 202, 8: 111, 9: 400, 10: 150, 11: 130}},
        ]
    },
    {
        "name": "24. Лавр",
        "cycle": 60,
        "container": 13000,
        "in_transit": {},
        "items": [
            {"name": "Лавровий лист Єгипет (Преміум)", "balance": 2979, "plan": 800, "in_transit": {}},
            {"name": "Лавровий лист Єгипет (А)", "balance": 16560, "plan": 2200, "in_transit": {}},
            {"name": "Лавровий лист Єгипет (В)", "balance": 2846, "plan": 1300, "in_transit": {}},
        ]
    },
]

# Инициализация пустых словарей для групп и позиций
for g in GROUPS:
    if "in_transit" not in g:
        g["in_transit"] = {}
    if "active" not in g:
        g["active"] = True  # Все группы активны по умолчанию
    for it in g["items"]:
        if "in_transit" not in it:
            it["in_transit"] = {}
