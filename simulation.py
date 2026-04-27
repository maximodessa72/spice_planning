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
    """
    active = [it for it in items if it["plan"] > 0]
    if not active:
        return {it["name"]: 0 for it in items}
    
    tp = sum(it["plan"] for it in active)
    tb = sum(ibs[it["name"]] for it in active)
    T = (ckg + tb) / tp if tp > 0 else 0
    
    opts = {
        it["name"]: round_to(T * it["plan"] - ibs[it["name"]], item_bag(it)) if it["plan"] > 0 else 0
        for it in items
    }
    
    # Подгонка
    diff = sum(opts.values()) - ckg
    if diff > 0:
        for it in sorted(active, key=lambda x: opts[x["name"]], reverse=True):
            if diff <= 0:
                break
            mult = item_bag(it)
            cut = (min(diff, opts[it["name"]]) // mult) * mult
            if cut > 0:
                opts[it["name"]] -= cut
                diff -= cut
    elif diff < 0:
        top = max(active, key=lambda x: opts[x["name"]])
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
    pending = {k: v for k, v in group["in_transit"].items() if v > 0}
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
        
        # Обновляем остатки позиций
        for it in group["items"]:
            item_state[it["name"]] = max(0, item_state[it["name"]] + ia[it["name"]] - get_plan(it, i))
        
        # Проверка необходимости заказа
        bf = future_bal(balance + arrive, pending, i, cycle_m, group, buffer)
        containers = 0
        order_kg = 0
        if bf < total_plan * buffer:
            need = total_plan * buffer - bf
            containers = math.ceil(need / ckg)
            order_kg = containers * ckg
            pending[i + cycle_m] = pending.get(i + cycle_m, 0) + order_kg
        
        # Итоговый буфер группы ПОСЛЕ прихода
        gba = sum(bsi[it["name"]] + ia[it["name"]] for it in group["items"])
        gca = round(gba / tpi, 2) if tpi > 0 else 99
        
        # Сохраняем результаты месяца
        in_tr = i in group["in_transit"] and group["in_transit"].get(i, 0) > 0
        
        results.append({
            "mi": i,
            "arrive": arrive,
            "in_transit": in_tr,
            "containers": containers,
            "order_kg": order_kg,
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
        
        balance = max(0, balance + arrive - tpi)
    
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
            all_results[group["name"]] = run_simulation(group)
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
