"""
Веб-приложение для системы планирования закупок
Интерактивный интерфейс для редактирования данных и просмотра результатов
"""

import streamlit as st
import pandas as pd
from data import GROUPS, N_MONTHS
from simulation import (
    run_all_simulations, 
    get_summary_stats, 
    get_critical_groups,
    get_plan
)

# Настройка страницы
st.set_page_config(
    page_title="Система планирования закупок",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ========== АУТЕНТИФИКАЦИЯ ==========
def check_password():
    """Проверка пароля для доступа к приложению с двумя уровнями"""
    
    def password_entered():
        """Проверяет введённый пароль и определяет уровень доступа"""
        entered_password = st.session_state["password"]
        
        # Проверяем admin пароль
        if entered_password == st.secrets["passwords"]["admin"]:
            st.session_state["password_correct"] = True
            st.session_state["user_role"] = "admin"
            del st.session_state["password"]
            return
        
        # Проверяем viewer пароль
        if entered_password == st.secrets["passwords"]["viewer"]:
            st.session_state["password_correct"] = True
            st.session_state["user_role"] = "viewer"
            del st.session_state["password"]
            return
        
        # Пароль неверный
        st.session_state["password_correct"] = False
        st.session_state["user_role"] = None

    # Первый запуск - показываем форму входа
    if "password_correct" not in st.session_state:
        st.markdown("### 🔐 Вход в систему планирования")
        st.text_input(
            "Введите пароль:",
            type="password",
            on_change=password_entered,
            key="password"
        )
        st.info("💡 Пароль можно получить у администратора системы")
        return False
    
    # Пароль неверный - показываем ошибку
    elif not st.session_state["password_correct"]:
        st.markdown("### 🔐 Вход в систему планирования")
        st.text_input(
            "Введите пароль:",
            type="password",
            on_change=password_entered,
            key="password"
        )
        st.error("❌ Неверный пароль. Попробуйте ещё раз.")
        return False
    
    # Пароль верный - доступ разрешён
    else:
        return True

# Проверяем пароль перед показом приложения
if not check_password():
    st.stop()  # Останавливаем выполнение если пароль не введён

# ========== КОНЕЦ АУТЕНТИФИКАЦИИ ==========

# Инициализация session state
if 'groups' not in st.session_state:
    st.session_state.groups = GROUPS
if 'results' not in st.session_state:
    st.session_state.results = None
if 'need_recalc' not in st.session_state:
    st.session_state.need_recalc = True


def format_number(num):
    """Форматировать число с разделителями тысяч"""
    return f"{num:,}".replace(",", " ")


def get_month_label(mi):
    """Получить название месяца по индексу"""
    months = ['Янв','Фев','Мар','Апр','Май','Июн','Июл','Авг','Сен','Окт','Ноя','Дек']
    y = 2026 + (3 + mi) // 12
    m = (3 + mi) % 12
    return f"{months[m]} {y}"


def recalculate():
    """Пересчитать симуляцию"""
    with st.spinner('Пересчёт симуляции...'):
        st.session_state.results = run_all_simulations(st.session_state.groups)
        st.session_state.need_recalc = False


# Боковое меню
with st.sidebar:
    st.title("📊 Навигация")
    
    # Показываем роль пользователя
    user_role = st.session_state.get("user_role", "viewer")
    if user_role == "admin":
        st.success("👤 Администратор (полный доступ)")
    else:
        st.info("👤 Пользователь (только просмотр)")
    
    st.divider()
    
    page = st.radio(
        "Выберите страницу:",
        ["🏠 Главная", "📊 Редактор данных", "📅 Календарь заказов", "📈 Детальный просмотр"],
        label_visibility="collapsed"
    )
    
    st.divider()
    
    # Кнопка пересчёта (только для администраторов)
    if user_role == "admin":
        if st.session_state.need_recalc:
            st.warning("⚠️ Есть несохранённые изменения")
        
        if st.button("🔄 Пересчитать", type="primary", use_container_width=True):
            recalculate()
            st.success("✅ Пересчёт завершён!")
            st.rerun()
    
    st.divider()
    
    # Кнопка экспорта
    if st.button("💾 Экспорт в Excel", use_container_width=True):
        st.info("Экспорт будет добавлен позже")


# ========== ГЛАВНАЯ СТРАНИЦА ==========
if page == "🏠 Главная":
    st.title("📊 Система планирования закупок")
    st.caption("18-месячный горизонт планирования контейнерных поставок")
    
    # Пересчёт если нужно
    if st.session_state.need_recalc or st.session_state.results is None:
        recalculate()
    
    results = st.session_state.results
    stats = get_summary_stats(results)
    
    # Метрики
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Контейнеров",
            format_number(stats["total_containers"]),
            help="Общее количество заказов на 18 месяцев"
        )
    with col2:
        st.metric(
            "Общий объём",
            f"{format_number(stats['total_kg'])} кг",
            help="Общий вес всех заказов"
        )
    with col3:
        st.metric(
            "Групп товаров",
            stats["num_groups"],
            help="Количество товарных групп"
        )
    
    st.divider()
    
    # Критичные группы
    st.subheader("⚠️ Критичные группы (буфер < 1 месяц)")
    critical = get_critical_groups(results, threshold=1.0)
    
    if critical:
        critical_df = pd.DataFrame([
            {
                "Группа": c["group"],
                "Месяц": get_month_label(c["month"]),
                "Буфер (мес)": round(c["buffer"], 2)
            }
            for c in critical[:10]  # Топ-10
        ])
        st.dataframe(critical_df, use_container_width=True, hide_index=True)
    else:
        st.success("✅ Нет критичных групп")
    
    st.divider()
    
    # Ближайшие заказы
    st.subheader("📦 Ближайшие заказы")
    
    # Собираем заказы по месяцам
    orders_by_month = {}
    for group_name, group_results in results.items():
        for r in group_results[:6]:  # Первые 6 месяцев
            if r["containers"] > 0:
                month = get_month_label(r["mi"])
                if month not in orders_by_month:
                    orders_by_month[month] = []
                orders_by_month[month].append({
                    "group": group_name,
                    "containers": r["containers"],
                    "kg": r["order_kg"]
                })
    
    for month in sorted(orders_by_month.keys())[:3]:  # Первые 3 месяца
        orders = orders_by_month[month]
        total_cont = sum(o["containers"] for o in orders)
        
        with st.expander(f"**{month}**: {total_cont} контейнеров"):
            for order in orders:
                st.write(f"• {order['group']}: {order['containers']} конт. ({format_number(order['kg'])} кг)")


# ========== РЕДАКТОР ДАННЫХ ==========
elif page == "📊 Редактор данных":
    st.title("📊 Редактор данных")
    st.caption("Изменение остатков, планов и фиксированных приходов")
    
    # Проверка прав доступа
    if st.session_state.get("user_role") != "admin":
        st.warning("⚠️ У вас нет прав для редактирования данных")
        st.info("📖 Доступен только режим просмотра. Для редактирования обратитесь к администратору.")
        st.stop()
    
    # Выбор группы
    group_names = [g["name"] for g in st.session_state.groups]
    selected_group_name = st.selectbox("Выберите группу:", group_names)
    
    # Находим группу
    group_idx = group_names.index(selected_group_name)
    group = st.session_state.groups[group_idx]
    
    st.divider()
    
    # Информация о группе
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Цикл поставки", f"{group['cycle']} дней")
    with col2:
        st.metric("Размер контейнера", f"{format_number(group['container'])} кг")
    
    st.divider()
    
    # Редактор позиций
    st.subheader("Позиции в группе")
    
    for item_idx, item in enumerate(group["items"]):
        with st.expander(f"**{item['name']}**", expanded=len(group["items"]) == 1):
            col1, col2 = st.columns(2)
            
            with col1:
                # Остаток на начало
                new_balance = st.number_input(
                    "Остаток на начало (кг)",
                    min_value=0,
                    value=item["balance"],
                    step=100,
                    key=f"balance_{group_idx}_{item_idx}"
                )
                if new_balance != item["balance"]:
                    item["balance"] = new_balance
                    st.session_state.need_recalc = True
                
                # План потребления
                new_plan = st.number_input(
                    "План потребления (кг/мес)",
                    min_value=0,
                    value=item["plan"],
                    step=100,
                    key=f"plan_{group_idx}_{item_idx}"
                )
                if new_plan != item["plan"]:
                    item["plan"] = new_plan
                    st.session_state.need_recalc = True
            
            with col2:
                # Фиксированные приходы
                st.write("**Фиксированные приходы:**")
                
                if item.get("in_transit"):
                    for mi, kg in sorted(item["in_transit"].items()):
                        month = get_month_label(mi)
                        st.write(f"• {month}: {format_number(kg)} кг")
                else:
                    st.write("_Нет фиксированных приходов_")
                
                # TODO: Добавить возможность редактировать фиксированные приходы


# ========== КАЛЕНДАРЬ ЗАКАЗОВ ==========
elif page == "📅 Календарь заказов":
    st.title("📅 Календарь заказов")
    st.caption("Визуализация помесячных заказов по всем группам")
    
    # Пересчёт если нужно
    if st.session_state.need_recalc or st.session_state.results is None:
        recalculate()
    
    results = st.session_state.results
    
    # Создаём таблицу: группы × месяцы
    calendar_data = []
    
    for group in st.session_state.groups:
        row = {"Группа": group["name"]}
        group_results = results[group["name"]]
        
        for mi in range(N_MONTHS):
            month = get_month_label(mi)
            containers = group_results[mi]["containers"]
            row[month] = containers if containers > 0 else ""
        
        calendar_data.append(row)
    
    df = pd.DataFrame(calendar_data)
    
    # Отображаем таблицу
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        height=800
    )


# ========== ДЕТАЛЬНЫЙ ПРОСМОТР ==========
elif page == "📈 Детальный просмотр":
    st.title("📈 Детальный просмотр")
    st.caption("Подробная информация по выбранной группе")
    
    # Пересчёт если нужно
    if st.session_state.need_recalc or st.session_state.results is None:
        recalculate()
    
    results = st.session_state.results
    
    # Выбор группы
    group_names = [g["name"] for g in st.session_state.groups]
    selected_group_name = st.selectbox("Выберите группу:", group_names)
    
    # Находим группу и результаты
    group_idx = group_names.index(selected_group_name)
    group = st.session_state.groups[group_idx]
    group_results = results[selected_group_name]
    
    st.divider()
    
    # Таблица по месяцам
    table_data = []
    
    for r in group_results[:12]:  # Первые 12 месяцев
        month = get_month_label(r["mi"])
        
        # Суммарный остаток на начало
        total_balance = sum(r["bsi"].values())
        
        # Приход
        arrive_str = format_number(r["arrive"]) if r["arrive"] > 0 else "—"
        
        # Буфер
        buffer_str = f"{r['w_buf_after']:.2f}"
        
        # Заказ
        order_str = f"{r['containers']} конт." if r["containers"] > 0 else "—"
        
        table_data.append({
            "Месяц": month,
            "Остаток (кг)": format_number(int(total_balance)),
            "Приход (кг)": arrive_str,
            "Буфер (мес)": buffer_str,
            "Заказ": order_str
        })
    
    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # Детали по позициям
    st.subheader("Детали по позициям")
    
    selected_month = st.selectbox(
        "Выберите месяц:",
        [get_month_label(i) for i in range(12)]
    )
    
    # Находим индекс месяца
    mi = [get_month_label(i) for i in range(12)].index(selected_month)
    r = group_results[mi]
    
    # Создаём таблицу по позициям
    items_data = []
    for item in group["items"]:
        items_data.append({
            "Позиция": item["name"],
            "Остаток начало": format_number(int(r["bsi"][item["name"]])),
            "Приход": format_number(int(r["ia"][item["name"]])) if r["ia"][item["name"]] > 0 else "—",
            "План": format_number(get_plan(item, mi)),
            "Буфер после": f"{r['ica'][item['name']]:.2f}"
        })
    
    items_df = pd.DataFrame(items_data)
    st.dataframe(items_df, use_container_width=True, hide_index=True)


# Футер
st.divider()
st.caption("Система планирования закупок на 18 месяцев | v1.0")
