"""
Модуль симуляции системы планирования закупок
Содержит всю логику расчётов, балансировки и оптимизации
"""

import math
from typing import Dict, List, Any
from data import BUFFER_DEFAULT, BUFFER_GROUP4, BAG, N_MONTHS


def get_plan(item: Dict, mi: int) -> int:
    """Получить план потребления для позиции на месяц mi"""
    if item.get("seasonal") and "plan_override" in item:
        return item["plan_override"][mi % 12]  # Сезонность повторяется каждый год
    return item.get("plan_override", {}).get(mi, item["plan"])


def get_group_plan(group: Dict, mi: int) -> int:
    """Получить общий план потребления группы на месяц mi"""
    return sum(get_plan(it, mi) for it in group["items"])


def get_week(w: float) -> tuple:
    """
    Определить недельный буфер и цвет
    Возвращает: (метка, цвет_hex)
    """
    if w < 0.5:
        return "⚠️ пред.міс", "FF0000"
    elif w < 0.75:
        return "Тиж. 1", "E65100"
    elif w < 1.0:
        return "Тиж. 2", "F9A825"
    elif w < 1.25:
        return "Тиж. 3", "2E7D32"
    else:
        return "Тиж. 4", "1565C0"


def get_arrival_day_from_week(week_label: str) -> int:
    """
    Получить день прихода по метке недели
    
    пред.мес / Тиж. 1 → 5-е число
    Тиж. 2 → 10-е число
    Тиж. 3 → 15-е число
    Тиж. 4 → 20-е число
    """
    if "пред" in week_label.lower() or "1" in week_label:
        return 5
    elif "2" in week_label:
        return 10
    elif "3" in week_label:
        return 15
    elif "4" in week_label:
        return 20
    else:
        return 5  # По умолчанию начало месяца


def calculate_proportional_plan(monthly_plan: float, arrival_day: int) -> float:
    """
    Рассчитать пропорциональный план продаж после прихода товара
    
    Args:
        monthly_plan: полный план продаж на месяц
        arrival_day: день прихода (5, 10, 15, 20)
    
    Returns:
        Пропорциональный план с учётом оставшихся рабочих дней
    """
    # Всего рабочих дней в месяце (примерно)
    TOTAL_WORKING_DAYS = 21
    
    # Рабочие дни после прихода (примерная оценка)
    # 5-е число → ~17 дней (21 - 4)
    # 10-е число → ~14 дней (21 - 7)
    # 15-е число → ~10 дней (21 - 11)
    # 20-е число → ~6 дней (21 - 15)
    days_mapping = {
        5: 17,   # неделя 1
        10: 14,  # неделя 2
        15: 10,  # неделя 3
        20: 6    # неделя 4
    }
    
    days_after_arrival = days_mapping.get(arrival_day, 17)
    
    # Пропорциональный план
    proportional_plan = monthly_plan * (days_after_arrival / TOTAL_WORKING_DAYS)
    
    return proportional_plan


def get_buffer_color(w: float) -> str:
    """
    Получить цвет для ячейки буфера (светлая палитра)
    """
    if w < 1.0:
        return "FFCCBC"  # Персиковый
    elif w < 1.25:
        return "FFECB3"  # Светло-жёлтый
    else:
        return "D5F5E3"  # Светло-зелёный


def future_bal(bal: float, pend: Dict, si: int, cm: int, group: Dict, buffer: float) -> float:
    """
    Рассчитать будущий баланс через cycle_months
    """
    b = bal
    p = dict(pend)
    for i in range(si + 1, si + 1 + cm):
        b = max(0, b + p.pop(i, 0) - get_group_plan(group, i))
    return b


def get_season_type(mi: int) -> str:
    """Определить тип сезона для группы 16 (корица)"""
    m = (3 + mi) % 12
    if m in [6, 7]:
        return "start"
    elif m in [9]:
        return "mid"
    elif m in [0, 1]:
        return "spring"
    return "start"


def item_bag(item: Dict) -> int:
    """Получить размер мешка для позиции"""
    return item.get("bag", BAG)


def round_to(kg: float, mult: int) -> int:
    """Округлить вверх до кратного mult"""
    return int(math.ceil(max(0, kg) / mult) * mult)


def round_bags(kg: float) -> int:
    """Округлить до мешков (25 кг)"""
    return round_to(kg, BAG)


def balance_g16(ckg: int, ibs: Dict, items: List, mi: int) -> Dict:
    """
    Балансировка для группы 16 (корица и бадьян)
    Учитывает сезонность
    """
    season = get_season_type(mi)
    si = [it for it in items if it.get("seasonal")]
    ri = [it for it in items if not it.get("seasonal") and it["plan"] > 0]
    opts = {it["name"]: 0 for it in items}
    
    if season in ("start", "mid"):
        look = 5 if season == "mid" else 4
        sr = 0
        for it in si:
            demand = sum(get_plan(it, mi + k) for k in range(0, look))
            opts[it["name"]] = round_bags(max(0, demand - ibs[it["name"]]))
            sr += opts[it["name"]]
        
        rem = max(0, ckg - sr)
        if ri and rem > 0:
            tp = sum(it["plan"] for it in ri)
            tb = sum(ibs[it["name"]] for it in ri)
            T = (rem + tb) / tp if tp > 0 else 0
            for it in ri:
                opts[it["name"]] = max(0, round_bags(T * it["plan"] - ibs[it["name"]]))
    else:
        rr = 0
        for it in ri:
            opts[it["name"]] = max(0, round_bags(it["plan"] * 6 - ibs[it["name"]]))
            rr += opts[it["name"]]
        
        for it in si:
            demand = sum(get_plan(it, mi + k) for k in range(0, 2))
            opts[it["name"]] = max(0, round_bags(demand - ibs[it["name"]]))
        
        excess = rr + sum(opts[it["name"]] for it in si) - ckg
        if excess > 0:
            for it in sorted(ri, key=lambda x: opts[x["name"]], reverse=True):
                if excess <= 0:
                    break
                cut = (min(excess, opts[it["name"]]) // BAG) * BAG
                if cut > 0:
                    opts[it["name"]] -= cut
                    excess -= cut
    
    # Подгонка к размеру контейнера
    diff = sum(opts.values()) - ckg
    if diff > 0:
        for it in sorted(ri, key=lambda x: opts[x["name"]], reverse=True):
            if diff <= 0:
                break
            cut = (min(diff, opts[it["name"]]) // BAG) * BAG
            if cut > 0:
                opts[it["name"]] -= cut
                diff -= cut
        
        if diff > 0:
            for it in sorted(si, key=lambda x: opts[x["name"]], reverse=True):
                if diff <= 0:
                    break
                cut = (min(diff, opts[it["name"]]) // BAG) * BAG
                if cut > 0:
                    opts[it["name"]] -= cut
                    diff -= cut
    elif diff < 0:
        top = max(ri, key=lambda x: x["plan"]) if ri else max(si, key=lambda x: opts[x["name"]])
        opts[top["name"]] += round_bags(-diff)
    
    return opts


def opt_rb(ckg: int, ibs: Dict, items: List, mi: int) -> Dict:
    """
    Оптимизация для групп со спентом (учёт сезонности)
    """
    look = 3
    si = [it for it in items if it.get("seasonal")]
    ri = [it for it in items if not it.get("seasonal") and it["plan"] > 0]
    opts = {it["name"]: 0 for it in items}
    sr = 0
    
    for it in si:
        demand = sum(get_plan(it, mi + k) for k in range(0, look + 1))
        buf = get_plan(it, mi + look + 1)
        opts[it["name"]] = round_to(max(0, demand + buf - ibs[it["name"]]), item_bag(it))
        sr += opts[it["name"]]
    
    rem = max(0, ckg - sr)
    if ri and rem > 0:
        tp = sum(it["plan"] for it in ri)
        tb = sum(ibs[it["name"]] for it in ri)
        T = (rem + tb) / tp if tp > 0 else 0
        for it in ri:
            opts[it["name"]] = max(0, round_to(T * it["plan"] - ibs[it["name"]], item_bag(it)))
    
    # Подгонка
    diff = sum(opts.values()) - ckg
    if diff > 0:
        for it in sorted(ri, key=lambda x: opts[x["name"]], reverse=True):
            if diff <= 0:
                break
            mult = item_bag(it)
            cut = (min(diff, opts[it["name"]]) // mult) * mult
            if cut > 0:
                opts[it["name"]] -= cut
                diff -= cut
    elif diff < 0:
        top = max(ri, key=lambda x: x["plan"]) if ri else max(si, key=lambda x: opts[x["name"]])
        opts[top["name"]] += round_to(-diff, item_bag(top))
    
    return opts


def opt_std(ckg: int, ibs: Dict, items: List) -> Dict:
    """
    Стандартная оптимизация (пропорциональное распределение)
    
    Итеративный поиск коэффициента T чтобы все позиции получили
    одинаковый буфер после округления и сумма = контейнер
    
    УЧИТЫВАЕМ НЕДЕЛЮ ПРИХОДА: по умолчанию неделя 2 (10-е число)
    для расчёта пропорционального плана после прихода
    """
    active = [it for it in items if it["plan"] > 0]
    if not active:
        return {it["name"]: 0 for it in items}
    
    # Неделя прихода для нефиксированных заказов (по умолчанию неделя 2)
    DEFAULT_ARRIVAL_DAY = 10  # 10-е число → ~14 дней продаж из 21
    days_after_arrival = 14  # Рабочих дней после прихода
    days_total = 21
    plan_coefficient = days_after_arrival / days_total  # 14/21 = 0.67
    
    tp = sum(it["plan"] for it in active)
    tb = sum(ibs[it["name"]] for it in active)
    
    # Начальная оценка T с учётом пропорционального плана
    # Формула: (остаток + заказ - план×0.67) / план = T (буфер целевой)
    # Упрощённо: T_initial ≈ (контейнер + остатки) / (планы × 0.67)
    T_initial = (ckg + tb) / (tp * plan_coefficient) if tp > 0 else 0
    
    # Итеративный поиск оптимального T
    T_min = 0.0
    T_max = T_initial * 2
    T = T_initial
    best_T = T
    best_diff = float('inf')
    
    # Бинарный поиск оптимального T
    for iteration in range(50):
        opts_temp = {}
        for it in items:
            if it["plan"] > 0:
                balance_start = ibs[it["name"]]
                plan_full = it["plan"]
                
                # ЕДИНАЯ ФОРМУЛА для всех позиций (независимо от остатка):
                # Целевой буфер = T
                # Остаток после = остаток + заказ - план×0.67
                # T × план = остаток + заказ - план×0.67
                # заказ = T × план + план×0.67 - остаток
                raw_order = T * plan_full + plan_full * plan_coefficient - balance_start
                
                opts_temp[it["name"]] = round_to(max(0, raw_order), item_bag(it))
            else:
                opts_temp[it["name"]] = 0
        
        total = sum(opts_temp.values())
        diff = total - ckg
        
        if abs(diff) < abs(best_diff):
            best_diff = diff
            best_T = T
        
        if abs(diff) <= 25:
            break
        
        if diff > 0:
            T_max = T
        else:
            T_min = T
        
        T = (T_min + T_max) / 2
    
    # Финальный расчёт с найденным T
    opts = {}
    for it in items:
        if it["plan"] > 0:
            balance_start = ibs[it["name"]]
            plan_full = it["plan"]
            
            # ЕДИНАЯ ФОРМУЛА для всех позиций
            # заказ = T × план + план×0.67 - остаток
            raw_order = best_T * plan_full + plan_full * plan_coefficient - balance_start
            
            opts[it["name"]] = round_to(max(0, raw_order), item_bag(it))
        else:
            opts[it["name"]] = 0
    
    # Финальная подгонка если нужно
    diff = sum(opts.values()) - ckg
    if abs(diff) > 25:
        if diff > 0:
            for it in sorted(active, key=lambda x: ibs[x["name"]], reverse=True):
                if diff <= 0:
                    break
                mult = item_bag(it)
                cut = (min(diff, opts[it["name"]]) // mult) * mult
                if cut > 0:
                    opts[it["name"]] -= cut
                    diff -= cut
        elif diff < 0:
            top = max(active, key=lambda x: x["plan"])
            opts[top["name"]] += round_to(-diff, item_bag(top))
    
    return opts


def run_simulation(group: Dict) -> List[Dict]:
    """
    Запустить симуляцию для одной группы на 18 месяцев
    
    Возвращает список результатов по месяцам с полной информацией:
    - Остатки по позициям
    - Приходы
    - Буферы
    - Заказы
    """
    # Определяем тип группы
    is_g4 = "часник" in group["name"].lower() or "чеснок" in group["name"].lower()
    is_g16 = "кориц" in group["name"].lower() or "корица" in group["name"].lower()
    is_spent = "Спент" in group["name"]
    has_seasonal = any(it.get("seasonal") for it in group["items"])
    
    buffer = BUFFER_GROUP4 if is_g4 else BUFFER_DEFAULT
    cycle_m = math.ceil(group["cycle"] / 30)
    ckg = group["container"]
    total_plan = sum(it["plan"] for it in group["items"])
    
    # Формируем pending из ДВУХ источников:
    # 1. Фиксированные заказы (in_transit)
    pending = {k: v for k, v in group["in_transit"].items() if v > 0}
    
    # 2. Автоматические заказы (auto_orders, добавленные wrapper)
    auto_orders = group.get("auto_orders", {})
    for k, v in auto_orders.items():
        pending[k] = pending.get(k, 0) + v
    
    balance = sum(it["balance"] for it in group["items"])
    item_state = {it["name"]: it["balance"] for it in group["items"]}
    
    results = []
    
    for i in range(N_MONTHS):
        # Состояние на начало месяца
        bsi = {it["name"]: item_state[it["name"]] for it in group["items"]}
        arrive = pending.pop(i, 0)
        tpi = get_group_plan(group, i)
        
        # Взвешенный буфер ДО прихода
        wn = 0
        wd = 0
        for it in group["items"]:
            pi = get_plan(it, i)
            if pi > 0:
                wn += (bsi[it["name"]] / pi) * pi
                wd += pi
        w_buf_before = round(wn / wd, 2) if wd > 0 else 99
        
        # Проверяем есть ли зафиксированный номер недели в week_arrival
        if "week_arrival" in group and i in group["week_arrival"]:
            week_num = group["week_arrival"][i]
            # Формируем метку из номера недели
            week_labels = {
                1: ("Тиж. 1", "E65100"),
                2: ("Тиж. 2", "F9A825"),
                3: ("Тиж. 3", "2E7D32"),
                4: ("Тиж. 4", "1565C0")
            }
            wl, wc = week_labels.get(week_num, get_week(w_buf_before))
        else:
            # Автоматическое определение по буферу
            wl, wc = get_week(w_buf_before)
        
        # Распределение прихода по позициям
        ia = {}
        for it in group["items"]:
            if i in it.get("in_transit", {}):
                ia[it["name"]] = it["in_transit"][i]
            elif i in group["in_transit"] and i not in it.get("in_transit", {}):
                ia[it["name"]] = 0
            else:
                ia[it["name"]] = 0
        
        # Проверяем фиксированный заказ
        is_fixed = i in group["in_transit"] and all(i in it.get("in_transit", {}) for it in group["items"])
        
        # Если приход есть и НЕ фиксированный - балансируем
        if arrive > 0 and not is_fixed:
            if len(group["items"]) > 1:
                ibs = {it["name"]: item_state[it["name"]] for it in group["items"]}
                
                if is_g16:
                    opts = balance_g16(arrive, ibs, group["items"], i)
                elif has_seasonal and is_spent:
                    opts = opt_rb(arrive, ibs, group["items"], i)
                else:
                    opts = opt_std(arrive, ibs, group["items"])
                
                for it in group["items"]:
                    if i not in it.get("in_transit", {}):
                        ia[it["name"]] = opts[it["name"]]
            else:
                it = group["items"][0]
                if i not in it.get("in_transit", {}):
                    ia[it["name"]] = arrive
        
        # Буфер по позициям ДО и ПОСЛЕ прихода (БЕЗ округления для точных цветов)
        icb = {
            it["name"]: bsi[it["name"]] / get_plan(it, i) if get_plan(it, i) > 0 else 99
            for it in group["items"]
        }
        ica = {
            it["name"]: (bsi[it["name"]] + ia[it["name"]]) / get_plan(it, i) 
            if get_plan(it, i) > 0 else 99
            for it in group["items"]
        }
        
        # Сохраняем остаток на начало месяца для расчётов
        balance_start = balance
        
        # Обновляем остатки позиций с учётом недели прихода
        for it in group["items"]:
            item_balance_start = item_state[it["name"]]
            item_arrival = ia[it["name"]]
            item_plan = get_plan(it, i)
            
            # ВАЖНО: проверяем остаток ПОЗИЦИИ, а не группы!
            if item_balance_start >= item_plan:
                # СЛУЧАЙ 1: Товара ЭТОЙ позиции хватает на весь месяц
                item_state[it["name"]] = max(0, item_balance_start + item_arrival - item_plan)
                
            elif item_arrival > 0:
                # СЛУЧАЙ 2: Товара не хватает на весь месяц, но есть приход
                arrival_day = get_arrival_day_from_week(wl)
                
                # calculate_proportional_plan возвращает план ПОСЛЕ прихода
                item_plan_after = calculate_proportional_plan(item_plan, arrival_day)
                
                # План ДО прихода
                item_plan_before = item_plan - item_plan_after
                
                if item_balance_start >= item_plan_before:
                    # ПОДСЛУЧАЙ 2А: Хватает до прихода → выполним полный план
                    item_state[it["name"]] = max(0, item_balance_start + item_arrival - item_plan)
                else:
                    # ПОДСЛУЧАЙ 2Б: НЕ хватает до прихода → продали только после
                    item_state[it["name"]] = max(0, item_arrival - item_plan_after)
            else:
                # СЛУЧАЙ 3: Нет прихода
                item_state[it["name"]] = max(0, item_balance_start - item_plan)
        
        # Итоговый буфер группы ПОСЛЕ прихода
        gba = sum(bsi[it["name"]] + ia[it["name"]] for it in group["items"])
        gca = round(gba / tpi, 2) if tpi > 0 else 99
        
        # Сохраняем результаты месяца
        # Разделяем фиксированные и автоматические заказы
        is_fixed = i in group["in_transit"] and group["in_transit"].get(i, 0) > 0
        is_auto = i in auto_orders and auto_orders.get(i, 0) > 0
        
        # Пока не заполняем containers, order_kg, order_month
        # Это будет сделано ПОСЛЕ цикла, идя от конца к началу
        containers = 0
        order_kg = 0
        order_month = None
        
        results.append({
            "mi": i,
            "arrive": arrive,
            "in_transit": is_fixed,      # Фиксированный приход
            "is_auto_order": is_auto,    # Автоматический приход
            "containers": containers,
            "order_kg": order_kg,
            "order_month": order_month,  # Месяц размещения заказа (i - cycle_m)
            "w_buf_before": w_buf_before,
            "w_buf_after": gca,
            "wl": wl,
            "wc": wc,
            "gca": gca,
            "bsi": bsi,
            "ia": ia,
            "icb": icb,
            "ica": ica,
            "tpi": tpi
        })
        
        # Расчёт остатка на конец месяца с учётом недели прихода
        
        if balance_start >= tpi:
            # СЛУЧАЙ 1: Товара хватает на весь месяц
            balance = balance_start + arrive - tpi
            
        elif arrive > 0:
            # СЛУЧАЙ 2: Товара НЕ хватает на весь месяц, но есть приход
            arrival_day = get_arrival_day_from_week(wl)
            plan_after_arrival = calculate_proportional_plan(tpi, arrival_day)
            plan_before_arrival = tpi - plan_after_arrival
            
            if balance_start >= plan_before_arrival:
                # ПОДСЛУЧАЙ 2А: Товара ХВАТАЕТ до прихода
                balance = balance_start + arrive - tpi
            else:
                # ПОДСЛУЧАЙ 2Б: Товара НЕ ХВАТАЕТ до прихода
                balance = max(0, arrive - plan_after_arrival)
        else:
            # СЛУЧАЙ 3: Нет прихода, товара не хватало
            balance = max(0, balance_start - tpi)
    
    # НОВАЯ ЛОГИКА ЗАПОЛНЕНИЯ ЗАКАЗОВ:
    # Идём от ПОСЛЕДНЕГО месяца к ПЕРВОМУ
    # Если в месяце i есть приход → в месяце (i - cycle_m) был размещён заказ
    for i in range(len(results) - 1, -1, -1):
        if results[i]["arrive"] > 0:
            # Есть приход в месяце i
            order_placed_month = i - cycle_m
            
            if order_placed_month >= 0:
                # Заказ был размещён в пределах горизонта
                results[order_placed_month]["containers"] = 1
                results[order_placed_month]["order_kg"] = ckg
                results[order_placed_month]["order_month"] = i  # Приход будет в месяце i
    
    return results


def run_simulation_with_auto_orders(group: Dict) -> List[Dict]:
    """
    Wrapper над run_simulation с автоматическим добавлением заказов
    
    ИТЕРАТИВНЫЙ ПОДХОД:
    1. Запускаем симуляцию с фиксированными заказами
    2. Проверяем каждый месяц: буфер < минимум и нет прихода?
    3. Добавляем такие месяцы в auto_orders (НЕ in_transit!)
    4. Повторяем пока не останется месяцев с низким буфером
    """
    # Определяем параметры группы
    is_g4 = "часник" in group["name"].lower() or "чеснок" in group["name"].lower()
    buffer_threshold = BUFFER_GROUP4 if is_g4 else BUFFER_DEFAULT
    ckg = group["container"]
    
    # Копируем group чтобы не менять оригинал
    group_copy = group.copy()
    group_copy["in_transit"] = {k: v for k, v in group["in_transit"].items()}  # Фиксированные (не трогаем)
    group_copy["auto_orders"] = {}  # Автоматические (добавляем сюда)
    
    max_iterations = 10
    
    for iteration in range(max_iterations):
        # Запускаем симуляцию
        results = run_simulation(group_copy)
        
        # Проверяем все месяцы
        orders_added = False
        added_months = []
        
        # Определяем cycle_m для проверки будущих приходов
        cycle_m = math.ceil(group["cycle"] / 30)
        
        # ВАЖНО: Автоматические заказы можно добавлять только начиная с месяца
        # где заказ ещё возможен (текущий момент + cycle_m)
        # Месяц 0 = апрель 2026, но сейчас уже май 2026 (mi=1)
        # Значит первый возможный автоматический приход: 1 + cycle_m
        min_auto_month = 0 + cycle_m  # Упрощённо: считаем что "сейчас" это месяц 0
        
        for j in range(len(results)):
            month_result = results[j]
            
            # 0. НОВАЯ ПРОВЕРКА: пропускаем месяцы где автоматический заказ невозможен
            if j < min_auto_month:
                continue  # Слишком рано для автоматического заказа
            
            # 1. Есть ли УЖЕ приход в этом месяце?
            if month_result["in_transit"] or month_result.get("is_auto_order", False) or month_result["arrive"] > 0:
                continue  # Приход есть → пропускаем
            
            # 2. Проверяем буфер на начало месяца
            buf_before = month_result["w_buf_before"]
            
            # 3. Проверяем: есть ли уже приход в следующие cycle_m месяцев?
            has_future_arrival = False
            for future_month in range(j + 1, min(j + cycle_m + 1, len(results))):
                if results[future_month]["arrive"] > 0:
                    has_future_arrival = True
                    break
            
            # 4. Добавляем заказ только если:
            #    - Буфер низкий (< 1.0)
            #    - И НЕТ прихода в ближайшие cycle_m месяцев
            if buf_before < buffer_threshold and not has_future_arrival:
                # Нужен приход в месяце j!
                group_copy["auto_orders"][j] = ckg
                orders_added = True
                added_months.append(j)
                # ВАЖНО: Добавляем только ОДИН заказ, потом пересчитываем!
                break  # Выходим из цикла по месяцам
        
        # Если заказов не добавлено → готово!
        if not orders_added:
            break
    
    # Возвращаем финальные results
    return results


def run_all_simulations(groups: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Запустить симуляцию для всех групп
    
    Пропускает деактивированные группы (active=False)
    
    Возвращает: {имя_группы: результаты_симуляции}
    """
    all_results = {}
    for group in groups:
        # Пропускаем деактивированные группы
        if not group.get("active", True):
            # Создаём пустые результаты для неактивной группы
            all_results[group["name"]] = [
                {
                    "mi": i,
                    "arrive": 0,
                    "in_transit": False,
                    "containers": 0,
                    "order_kg": 0,
                    "w_buf_before": 99,
                    "w_buf_after": 99,
                    "wl": "",
                    "wc": "",
                    "gca": 99,
                    "bsi": {it["name"]: 0 for it in group["items"]},
                    "ia": {it["name"]: 0 for it in group["items"]},
                    "icb": {it["name"]: 99 for it in group["items"]},
                    "ica": {it["name"]: 99 for it in group["items"]},
                    "tpi": 0
                }
                for i in range(18)
            ]
        else:
            all_results[group["name"]] = run_simulation_with_auto_orders(group)
    return all_results


def get_summary_stats(all_results: Dict[str, List[Dict]]) -> Dict:
    """
    Получить сводную статистику по всем группам за первые 12 месяцев
    """
    total_containers = 0
    total_kg = 0
    
    for group_name, results in all_results.items():
        # Считаем только первые 12 месяцев
        for r in results[:12]:
            total_containers += r["containers"]
            total_kg += r["order_kg"]
    
    return {
        "total_containers": total_containers,
        "total_kg": total_kg,
        "num_groups": len(all_results)
    }


def get_critical_groups(all_results: Dict[str, List[Dict]], threshold: float = 1.0) -> List[Dict]:
    """
    Найти группы с критично низким буфером
    
    Args:
        threshold: порог буфера (по умолчанию 1.0 месяц)
    
    Returns:
        Список словарей с информацией о критичных группах
    """
    critical = []
    
    for group_name, results in all_results.items():
        for r in results:
            if r["w_buf_after"] < threshold and r["mi"] < 6:  # Смотрим первые 6 месяцев
                critical.append({
                    "group": group_name,
                    "month": r["mi"],
                    "buffer": r["w_buf_after"]
                })
    
    return sorted(critical, key=lambda x: x["buffer"])


def get_bottleneck_recommendations(group: Dict, results: List[Dict]) -> List[Dict]:
    """
    PREVIEW-функция "Требует решения" (узкое место внутри группы).

    Групповой буфер считается как сумма остатков / сумма планов, поэтому
    позиция с маленьким остатком может "прятаться" за позициями с большим
    избытком — групповой сигнал не сработает, хотя конкретная позиция
    вот-вот уйдёт в ноль.

    Эта функция НИЧЕГО не меняет и не сохраняет (не пишет в in_transit/
    auto_orders, не влияет на pending и на run_simulation) — preview-слой
    поверх готовых results.

    ЛОГИКА (месяц j = "сейчас", месяц j+cycle_m = когда пришёл бы заказ,
    если разместить его в j — та же длительность цикла, что и у реальных
    заказов):
      - Смотрим на буфер позиций в месяце (j + cycle_m) — том, где был бы
        приход, если заказать СЕЙЧАС.
      - Если к этому моменту какая-то позиция ниже порога, и в промежутке
        нет уже запланированного прихода, который бы это закрыл — считаем
        гипотетический заказ на балансах месяца j (когда его реально
        нужно было бы разместить).
      - Рекомендация показывается заранее, в месяце j, а не постфактум.

    ЭСКАЛАЦИЯ: если по группе уже показывали сигнал и его не приняли (не
    заказали) — молчим, ПОКА список критичных позиций не изменится (не
    появится хотя бы одна НОВАЯ критичная позиция). Если ситуация
    ухудшилась — сигнал появляется снова. Если у группы случается реальный
    приход (заказ сделан) — история сбрасывается, дальше считаем заново.

    Returns:
        Список словарей (может быть пустым), каждый — отдельная точка
        эскалации:
        {
            "mi": месяц показа рекомендации (= месяц гипотетического заказа),
            "target_mi": месяц, к которому относится дефицит (mi + cycle_m),
            "critical_items": [все критичные позиции на этот момент],
            "new_items": [позиции, которые стали критичными впервые],
            "order_kg": {позиция: рекомендуемый приход, кг},
            "buf_after": {позиция: буфер после рекомендации},
        }
    """
    is_g4 = "часник" in group["name"].lower() or "чеснок" in group["name"].lower()
    is_g16 = "кориц" in group["name"].lower() or "корица" in group["name"].lower()
    is_spent = "Спент" in group["name"]
    has_seasonal = any(it.get("seasonal") for it in group["items"])
    buffer_threshold = BUFFER_GROUP4 if is_g4 else BUFFER_DEFAULT
    ckg = group["container"]
    cycle_m = math.ceil(group["cycle"] / 30)

    recommendations = []
    already_flagged_items = set()

    for j in range(len(results)):
        r_j = results[j]

        # У группы в месяце j уже есть реальный приход (фикс./авто) —
        # проблема так или иначе решается реальным заказом, сбрасываем историю
        if r_j["in_transit"] or r_j.get("is_auto_order", False) or r_j["arrive"] > 0:
            already_flagged_items = set()
            continue

        target_mi = j + cycle_m
        if target_mi >= len(results):
            break

        # Есть ли уже запланированный приход между j и target_mi включительно?
        has_future_arrival = any(
            results[k]["arrive"] > 0 for k in range(j + 1, target_mi + 1)
        )
        if has_future_arrival:
            continue

        icb_target = results[target_mi]["icb"]  # буфер позиций к моменту дефицита
        critical_items = {name for name, buf in icb_target.items() if buf < buffer_threshold}

        if not critical_items:
            continue

        new_items = critical_items - already_flagged_items
        if not new_items:
            continue  # ситуация не изменилась с прошлого раза — не повторяем сигнал

        # Считаем гипотетический заказ на балансах МЕСЯЦА ПРИХОДА (target_mi) —
        # ровно так же, как в реальных заказах: opt_std в run_simulation
        # балансирует по остаткам месяца, где происходит приход, а не
        # месяца размещения заказа.
        ibs_target = results[target_mi]["bsi"]

        if len(group["items"]) > 1:
            if is_g16:
                order_kg = balance_g16(ckg, ibs_target, group["items"], target_mi)
            elif has_seasonal and is_spent:
                order_kg = opt_rb(ckg, ibs_target, group["items"], target_mi)
            else:
                order_kg = opt_std(ckg, ibs_target, group["items"])
        else:
            order_kg = {group["items"][0]["name"]: ckg}

        buf_after = {}
        for it in group["items"]:
            pi = get_plan(it, target_mi)
            arr = order_kg.get(it["name"], 0)
            buf_after[it["name"]] = round((ibs_target[it["name"]] + arr) / pi, 2) if pi > 0 else 99

        recommendations.append({
            "mi": j,             # месяц показа текстовой метки "Требует решения"
            "target_mi": target_mi,  # месяц, где показываем цифры (гипотетический приход)
            "critical_items": sorted(critical_items),
            "new_items": sorted(new_items),
            "order_kg": order_kg,
            "buf_after": buf_after,
        })

        already_flagged_items |= critical_items

    return recommendations
