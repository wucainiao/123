import math
import math


def exp_for_level(level: int) -> int:
    """Experience required for given level (formula)."""
    return int(500 * (level ** 2) * math.exp(0.05 * (level - 1)))


def realm_coefficient_map():
    return {
        '凡人期': 0.0,
        '炼气期': 0.5,
        '筑基期': 1.2,
        '金丹期': 2.5,
        '元婴期': 4.0,
        '化神期': 7.0,
        '炼虚期': 10.0,
        '合体期': 14.0,
        '大乘期': 19.0,
        '渡劫期': 25.0,
    }


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def compute_battle_power(attr, equipments=None, mantras=None, treasures=None,
                         atk_weight=1.0, def_weight=0.6, hp_weight=0.2):
    """Compute simplified battle power from attributes and bonuses."""
    eq_atk = sum(getattr(e, 'attack_bonus', 0) for e in (equipments or []))
    eq_def = sum(getattr(e, 'defense_bonus', 0) for e in (equipments or []))
    eq_hp = sum(getattr(e, 'hp_bonus', 0) for e in (equipments or []))

    mn_atk = sum(getattr(m, 'attack_bonus', 0) for m in (mantras or []))
    mn_def = sum(getattr(m, 'defense_bonus', 0) for m in (mantras or []))
    mn_hp = sum(getattr(m, 'hp_bonus', 0) for m in (mantras or []))

    tr_atk = sum(getattr(t, 'attack_bonus', 0) for t in (treasures or []))
    tr_def = sum(getattr(t, 'defense_bonus', 0) for t in (treasures or []))
    tr_hp = sum(getattr(t, 'hp_bonus', 0) for t in (treasures or []))

    total_atk = (getattr(attr, 'attack', 0) or 0) + eq_atk + mn_atk + tr_atk
    total_def = (getattr(attr, 'defense', 0) or 0) + eq_def + mn_def + tr_def
    total_hp = (getattr(attr, 'hp', 0) or 0) + eq_hp + mn_hp + tr_hp

    power = (total_atk * atk_weight) + (total_def * def_weight) + (total_hp * hp_weight)
    return int(power)


def apply_level_up(character, attributes, realm_coeff: float):
    """Apply level-up increments to character attributes in-place."""
    character.level = (character.level or 1) + 1

    # 增量设计：基础增长 + 境界系数放大
    atk_inc = int(10 + realm_coeff * 2)
    def_inc = int(10 + realm_coeff * 2)
    hp_inc = int(100 + realm_coeff * 20)
    spd_inc = int(5 + realm_coeff)

    attributes.attack = (getattr(attributes, 'attack', 0) or 0) + atk_inc
    attributes.defense = (getattr(attributes, 'defense', 0) or 0) + def_inc
    attributes.hp = (getattr(attributes, 'hp', 0) or 0) + hp_inc
    attributes.speed = (getattr(attributes, 'speed', 0) or 0) + spd_inc

    return {
        'attack_inc': atk_inc,
        'defense_inc': def_inc,
        'hp_inc': hp_inc,
        'speed_inc': spd_inc,
    }


def calc_strengthen_success(strengthen_times: int, material_quality_factor: float = 1.0,
                            base_success: float = 0.9, success_floor: float = 0.05, success_cap: float = 0.95):
    """Calculate strengthen success rate based on times and material quality."""
    decay = 0.9
    success = base_success * (decay ** strengthen_times) * material_quality_factor
    if success < success_floor:
        success = success_floor
    if success > success_cap:
        success = success_cap
    return float(success)


def calc_forge_success(material_quality_factor: float = 1.0, luck_factor: float = 1.0,
                       base_success: float = 0.6, success_cap: float = 0.95, success_floor: float = 0.01):
    """Calculate forge/recast success probability."""
    final = base_success * material_quality_factor * luck_factor
    final = max(min(final, success_cap), success_floor)
    return float(final)


def slots_for_quality(quality: str, kind: str = 'treasure') -> int:
    """Return number of rune slots according to quality and kind."""
    if kind == 'treasure':
        mapping = {
            '普通': 1,
            '精良': 2,
            '稀有': 3,
            '史诗': 4,
            '传说': 5
        }
    else:
        mapping = {
            '黄阶': 1,
            '玄阶': 2,
            '地阶': 3,
            '天阶': 4
        }
    return int(mapping.get(quality, 1))


import random


def roll_treasure_quality(material_quality_factor: float = 1.0) -> str:
    """Randomly roll treasure quality, material factor increases rare chance."""
    base = {
        '普通': 0.60,
        '精良': 0.25,
        '稀有': 0.10,
        '史诗': 0.04,
        '传说': 0.01
    }
    # 调整权重
    weights = {}
    for k, v in base.items():
        # 简单模型：material_quality_factor 乘以稀有权重的提升
        if k in ('史诗', '传说'):
            weights[k] = v * material_quality_factor
        elif k == '稀有':
            weights[k] = v * (1 + (material_quality_factor - 1) * 0.5)
        else:
            weights[k] = v

    total = sum(weights.values())
    probs = [weights[k] / total for k in ['普通', '精良', '稀有', '史诗', '传说']]
    choices = ['普通', '精良', '稀有', '史诗', '传说']
    return random.choices(choices, probs, k=1)[0]


def generate_treasure_stats(quality: str):
    """Generate base stats for treasure by quality."""
    base_map = {
        '普通': {'attack': (5, 15), 'defense': (0, 5), 'hp': (20, 60), 'slots': 1},
        '精良': {'attack': (15, 35), 'defense': (5, 10), 'hp': (60, 150), 'slots': 2},
        '稀有': {'attack': (35, 70), 'defense': (10, 20), 'hp': (150, 350), 'slots': 3},
        '史诗': {'attack': (70, 140), 'defense': (20, 40), 'hp': (350, 800), 'slots': 4},
        '传说': {'attack': (140, 300), 'defense': (40, 80), 'hp': (800, 2000), 'slots': 5}
    }
    cfg = base_map.get(quality, base_map['普通'])
    atk = random.randint(*cfg['attack'])
    df = random.randint(*cfg['defense'])
    hp = random.randint(*cfg['hp'])
    return {
        'attack_bonus': atk,
        'defense_bonus': df,
        'hp_bonus': hp,
        'rune_slots': cfg['slots']
    }


def awaken_success_rate(quality: str, material_quality_factor: float = 1.0, base: float = 0.25) -> float:
    """Calculate awaken success rate according to quality and materials."""
    quality_factor = {
        '普通': 1.0,
        '精良': 0.9,
        '稀有': 0.8,
        '史诗': 0.6,
        '传说': 0.4
    }.get(quality, 1.0)
    rate = base * material_quality_factor * quality_factor
    return max(0.01, min(rate, 0.95))


# 功法和神通相关函数
def mantra_exp_for_level(level: int, quality: str) -> int:
    """Calculate experience required for mantra level up."""
    base_exp = 100
    quality_multipliers = {
        '黄阶': 1.0,
        '玄阶': 1.5,
        '地阶': 2.0,
        '天阶': 3.0
    }
    multiplier = quality_multipliers.get(quality, 1.0)
    return int(base_exp * level * multiplier)


def mantra_upgrade_cost(level: int, quality: str, wuxing: int, weather_bonus: float = 1.0) -> dict:
    """Calculate mantra upgrade costs including experience and spirit stones."""
    quality_multipliers = {
        '黄阶': 1.0,
        '玄阶': 1.5,
        '地阶': 2.0,
        '天阶': 3.0
    }
    multiplier = quality_multipliers.get(quality, 1.0)

    # 基础经验消耗
    exp_cost = int(200 * level * multiplier)

    # 灵石消耗（考虑悟性系数和天气系数）
    wuxing_factor = max(0.5, min(2.0, wuxing / 50.0))  # 悟性50为基准
    lingshi_cost = int(exp_cost * 0.8 * wuxing_factor * weather_bonus)

    return {
        'experience': exp_cost,
        'lingshi': lingshi_cost,
        'wuxing_factor': wuxing_factor,
        'weather_bonus': weather_bonus
    }


def cultivate_mantra_exp_gain(base_exp: int = 10, wuxing: int = 50, weather_bonus: float = 1.0, time_spent: int = 1) -> int:
    """Calculate experience gain from mantra cultivation."""
    wuxing_factor = max(0.5, min(3.0, wuxing / 50.0))  # 悟性越高修炼越快
    total_exp = int(base_exp * wuxing_factor * weather_bonus * time_spent)
    return total_exp


def shentong_exp_for_level(level: int) -> int:
    """Calculate experience required for shentong level up."""
    return int(150 * level * 1.2)  # 神通升级相对较难


def shentong_trigger_rate(proficiency: int) -> float:
    """Calculate shentong trigger rate based on proficiency."""
    # 熟练度0-100，对应触发概率10%-30%
    base_rate = 0.1
    proficiency_bonus = (proficiency / 100.0) * 0.2  # 最多增加20%
    return min(0.3, base_rate + proficiency_bonus)


def update_mantra_proficiency(proficiency: str, proficiency_exp: int, proficiency_max: int) -> str:
    """Update mantra proficiency level based on experience."""
    proficiency_levels = ['入门', '小成', '大成', '圆满']
    current_index = proficiency_levels.index(proficiency) if proficiency in proficiency_levels else 0

    # 检查是否可以晋升到下一级
    while current_index < len(proficiency_levels) - 1 and proficiency_exp >= proficiency_max:
        proficiency_exp -= proficiency_max
        current_index += 1
        proficiency_max = int(proficiency_max * 1.5)  # 下一级要求更高

    return proficiency_levels[current_index]
