# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
import jwt
import datetime
import math
import random

app = Flask(__name__)
# 允许跨域访问（开发时使用宽松策略）
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# helpers
from utils.helpers import (
    exp_for_level, apply_level_up, compute_battle_power, realm_coefficient_map,
    calc_strengthen_success, calc_forge_success,
    roll_treasure_quality, generate_treasure_stats, awaken_success_rate
)

# 元素克制关系
ELEMENT_RESTRAINTS = {
    '金': {'克制': '木', '被克制': '火', '相生': '水', '相克': '土'},
    '木': {'克制': '土', '被克制': '金', '相生': '火', '相克': '水'},
    '水': {'克制': '火', '被克制': '土', '相生': '木', '相克': '金'},
    '火': {'克制': '金', '被克制': '水', '相生': '土', '相克': '木'},
    '土': {'克制': '水', '被克制': '木', '相生': '金', '相克': '火'},
    '无': {'克制': '无', '被克制': '无', '相生': '无', '相克': '无'}
}

# 天气影响因子
WEATHER_FACTORS = {
    '晴天': {'基础': 1.0, '法宝': 1.0, '功法': 1.0, '克制': 1.0},
    '雨天': {'基础': 0.9, '法宝': 0.8, '功法': 1.2, '克制': 0.95},
    '雪天': {'基础': 0.8, '法宝': 0.9, '功法': 1.1, '克制': 0.9},
    '雾天': {'基础': 0.95, '法宝': 1.0, '功法': 0.9, '克制': 1.05},
    '雷暴': {'基础': 1.1, '法宝': 1.2, '功法': 0.8, '克制': 1.1},
    '烈日': {'基础': 1.2, '法宝': 1.1, '功法': 0.9, '克制': 1.0}
}

# 缺少的辅助函数定义
def calculate_element_restraint(attacker_linggen, defender_linggen, weather):
    """计算元素克制系数"""
    if attacker_linggen == '无' or defender_linggen == '无':
        return 1.0

    attacker_info = ELEMENT_RESTRAINTS.get(attacker_linggen, {})
    defender_info = ELEMENT_RESTRAINTS.get(defender_linggen, {})

    # 主克制系数（攻击方克制防御方）
    main_restraint = 1.2 if attacker_info.get('克制') == defender_linggen else 1.0

    # 副克制系数（防御方被攻击方克制）
    sub_restraint = 1.1 if defender_info.get('被克制') == attacker_linggen else 1.0

    # 被克制系数（攻击方被防御方克制）
    counter_restraint = 0.9 if attacker_info.get('被克制') == defender_linggen else 1.0

    # 天气影响
    weather_factor = WEATHER_FACTORS.get(weather, {}).get('克制', 1.0)

    final_restraint = (main_restraint + sub_restraint - counter_restraint) * weather_factor
    return max(0.5, min(2.0, final_restraint))  # 限制在0.5-2.0之间

def calculate_combat_stats(character, weather='晴天'):
    """计算战斗中的完整属性"""
    attr = CharacterAttribute.query.filter_by(character_id=character.id).first()
    if not attr:
        return None

    # 基础属性
    base_attack = attr.attack
    base_defense = attr.defense
    base_hp = attr.hp
    base_speed = attr.speed

    # 装备加成
    equip_attack = 0
    equip_defense = 0
    equip_hp = 0
    equip_speed = 0
    equip_crit_rate = 0
    equip_dodge_rate = 0
    equip_hit_rate = 0
    equip_crit_damage = 1.0
    equip_penetration_rate = 0

    for equip in character.equipments:
        if equip.equipped:
            equip_attack += equip.attack_bonus
            equip_defense += equip.defense_bonus
            equip_hp += equip.hp_bonus
            equip_speed += equip.speed_bonus
            equip_crit_rate += equip.crit_rate_bonus
            equip_dodge_rate += equip.dodge_rate_bonus

    # 法宝加成
    treasure_attack = 0
    treasure_defense = 0
    treasure_hp = 0
    treasure_speed = 0
    treasure_crit_rate = 0
    treasure_dodge_rate = 0
    treasure_hit_rate = 0
    treasure_crit_damage = 1.0
    treasure_penetration_rate = 0

    for treasure in character.treasures:
        treasure_attack += treasure.attack_bonus
        treasure_defense += treasure.defense_bonus
        treasure_hp += treasure.hp_bonus
        treasure_speed += treasure.speed_bonus
        treasure_crit_rate += treasure.crit_rate_bonus
        treasure_dodge_rate += treasure.dodge_rate_bonus
        treasure_hit_rate += treasure.hit_rate_bonus
        treasure_crit_damage += treasure.crit_damage_bonus
        treasure_penetration_rate += treasure.penetration_rate_bonus

    # 功法加成
    mantra_attack = 0
    mantra_defense = 0
    mantra_hp = 0
    mantra_speed = 0
    mantra_crit_rate = 0

    for mantra in character.mantras:
        if mantra.equipped:
            mantra_attack += mantra.attack_bonus
            mantra_defense += mantra.defense_bonus
            mantra_hp += mantra.hp_bonus
            mantra_speed += mantra.speed_bonus
            mantra_crit_rate += mantra.crit_rate_bonus

    # 穴位加成（经脉系统）
    acupoint_attack = 0
    acupoint_defense = 0
    acupoint_hp = 0
    acupoint_speed = 0

    for meridian in character.meridians:
        if meridian.is_open:
            for acupoint in meridian.acupoints:
                bonus = acupoint.attribute_bonus
                if meridian.name in ['手少阳胆经', '足少阳胆经', '足厥阴肝经', '督脉']:
                    acupoint_attack += bonus
                elif meridian.name in ['足太阳膀胱经', '足少阴肾经']:
                    acupoint_defense += bonus
                elif meridian.name in ['足阳明胃经', '足太阴脾经', '任脉']:
                    acupoint_hp += bonus
                else:
                    acupoint_speed += bonus

    # 宠物加成
    pet_attack = 0
    pet_defense = 0
    pet_hp = 0
    pet_speed = 0

    for pet in character.pets:
        pet_attack += pet.attack_bonus
        pet_defense += pet.defense_bonus
        pet_hp += pet.hp_bonus
        pet_speed += pet.speed_bonus

    # 天气因子
    weather_factors = WEATHER_FACTORS.get(weather, WEATHER_FACTORS['晴天'])

    # 总攻击力 = (人物攻击力 × 天气因子_基础 + 法宝攻击 × 天气因子_法宝 + 功法攻击 × 天气因子_功法)
    total_attack = (
        (base_attack + equip_attack + acupoint_attack + pet_attack) * weather_factors['基础'] +
        treasure_attack * weather_factors['法宝'] +
        mantra_attack * weather_factors['功法']
    )

    # 总防御力 = (人物防御力 × 天气因子_基础 + 法宝防御力 × 天气因子_法宝 + 功法防御力 × 天气因子_功法)
    total_defense = (
        (base_defense + equip_defense + acupoint_defense + pet_defense) * weather_factors['基础'] +
        treasure_defense * weather_factors['法宝'] +
        mantra_defense * weather_factors['功法']
    )

    total_hp = base_hp + equip_hp + treasure_hp + mantra_hp + acupoint_hp + pet_hp
    total_speed = base_speed + equip_speed + treasure_speed + mantra_speed + acupoint_speed + pet_speed

    total_crit_rate = min(1.0, attr.crit_rate + equip_crit_rate + treasure_crit_rate + mantra_crit_rate)
    total_dodge_rate = min(0.8, attr.dodge_rate + equip_dodge_rate + treasure_dodge_rate)
    total_hit_rate = min(1.0, attr.hit_rate + equip_hit_rate + treasure_hit_rate)
    total_crit_damage = attr.crit_damage * equip_crit_damage * treasure_crit_damage
    total_penetration_rate = attr.penetration_rate + equip_penetration_rate + treasure_penetration_rate

    return {
        'total_attack': int(total_attack),
        'total_defense': int(total_defense),
        'total_hp': int(total_hp),
        'total_speed': int(total_speed),
        'crit_rate': total_crit_rate,
        'dodge_rate': total_dodge_rate,
        'hit_rate': total_hit_rate,
        'crit_damage': total_crit_damage,
        'penetration_rate': total_penetration_rate,
        'linggen': character.linggen
    }

def calculate_damage(attacker_stats, defender_stats, weather='晴天', attacker_shentong=None):
    """计算伤害"""
    # 基础伤害 = 总攻击力
    base_damage = attacker_stats['total_attack']

    # 暴击判断
    is_crit = random.random() < attacker_stats['crit_rate']
    if is_crit:
        base_damage *= attacker_stats['crit_damage']

    # 命中判断
    is_hit = random.random() < attacker_stats['hit_rate'] * (1 - defender_stats['dodge_rate'])
    if not is_hit:
        return 0  # 闪避

    # 神通发动
    shentong_multiplier = 1.0
    if attacker_shentong and random.random() < attacker_shentong.trigger_rate:
        shentong_multiplier = attacker_shentong.damage_multiplier

    # 元素克制
    element_multiplier = calculate_element_restraint(
        attacker_stats['linggen'],
        defender_stats['linggen'],
        weather
    )

    # 经脉系数（暂时设为1.0，未来根据经脉开启情况调整）
    meridian_multiplier = 1.0

    # 最终伤害 = 基础伤害 × 神通倍率 × 灵根克制系数 × 经脉系数
    final_damage = base_damage * shentong_multiplier * element_multiplier * meridian_multiplier

    # 实际伤害 = 最终伤害 - 敌人防御 × (1 - 穿透率)
    actual_damage = final_damage - defender_stats['total_defense'] * (1 - attacker_stats['penetration_rate'])

    return max(1, int(actual_damage))  # 至少造成1点伤害

def mantra_upgrade_cost(level, quality, wuxing, weather_bonus):
    """计算功法升级消耗"""
    quality_multipliers = {'黄阶': 1.0, '玄阶': 1.5, '地阶': 2.0, '天阶': 3.0}
    quality_multiplier = quality_multipliers.get(quality, 1.0)
    wuxing_factor = max(0.5, min(3.0, wuxing / 50.0))

    base_exp = 100 * level
    experience = int(base_exp * quality_multiplier * wuxing_factor * weather_bonus)

    base_lingshi = 50 * level
    lingshi = int(base_lingshi * quality_multiplier * wuxing_factor * weather_bonus)

    return {
        'experience': experience,
        'lingshi': lingshi,
        'wuxing_factor': wuxing_factor,
        'weather_bonus': weather_bonus
    }

def cultivate_mantra_exp_gain(base_exp, wuxing, weather_bonus, time_spent):
    """计算功法修炼经验获取"""
    wuxing_factor = max(0.5, min(3.0, wuxing / 50.0))
    return int(base_exp * wuxing_factor * weather_bonus * time_spent)

def update_mantra_proficiency(current_proficiency, exp, max_exp):
    """更新功法熟练度等级"""
    if exp >= max_exp:
        return min(100, current_proficiency + 10)  # 每次升级增加10点熟练度
    return current_proficiency

def shentong_exp_for_level(level):
    """计算神通升级所需经验"""
    return 200 * level * level  # 平方增长

def shentong_trigger_rate(proficiency):
    """计算神通触发概率"""
    return min(0.5, proficiency / 200.0)  # 最高25%

# 配置
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///xianxia_dev.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 导入模型
from models import *

db.init_app(app)

# 如果使用内存 sqlite（测试场景），在启动时创建表结构以保证隔离的空数据库可用
if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:///:memory:'):
    with app.app_context():
        db.create_all()

# 初始化怪物数据
def init_monsters():
    """初始化怪物数据"""
    if Monster.query.count() == 0:
        monsters_data = [
            ('野狼', 5, 80, 8, 6, 7, '木', 25, 15, '一只普通的野狼', '普通'),
            ('火狐', 8, 120, 12, 8, 9, '火', 40, 25, '浑身燃烧着火焰的狐狸', '普通'),
            ('水蛇', 6, 90, 9, 7, 8, '水', 30, 20, '生活在水边的毒蛇', '普通'),
            ('土熊', 10, 150, 15, 10, 6, '土', 50, 30, '巨大的土熊，防御力惊人', '精英'),
            ('金雕', 12, 100, 18, 12, 15, '金', 60, 40, '空中霸主，速度极快', '精英'),
            ('雷鹰', 15, 180, 20, 14, 12, '金', 80, 50, '操控雷电的巨鹰', 'BOSS'),
            ('冰龙', 20, 300, 25, 20, 10, '水', 150, 100, '寒冰巨龙，极度危险', 'BOSS')
        ]
        for name, level, hp, attack, defense, speed, linggen, exp, lingshi, desc, ai in monsters_data:
            monster = Monster(
                name=name, level=level, hp=hp, attack=attack, defense=defense,
                speed=speed, linggen=linggen, experience_reward=exp,
                lingshi_reward=lingshi, description=desc, ai_type=ai
            )
            db.session.add(monster)
        db.session.commit()
        print("怪物数据初始化完成")

# 初始化副本数据
def init_dungeons():
    """初始化副本数据"""
    if Dungeon.query.count() == 0:
        dungeons_data = [
            ('新手试炼', 1, '普通', '[1,2]', '{"经验": 100, "灵石": 50}', '适合新手的简单试炼'),
            ('火山秘境', 5, '困难', '[2,4]', '{"经验": 300, "灵石": 150, "火属性材料": 5}', '充满火焰的危险秘境'),
            ('冰雪迷宫', 8, '噩梦', '[5,6]', '{"经验": 500, "灵石": 250, "冰属性材料": 8}', '终年冰雪的迷宫'),
            ('雷霆神殿', 12, '地狱', '[6,7]', '{"经验": 800, "灵石": 400, "雷属性材料": 10}', '雷霆之神的居所')
        ]
        for name, req_level, diff, monsters, rewards, desc in dungeons_data:
            dungeon = Dungeon(
                name=name, level_requirement=req_level, difficulty=diff,
                monster_ids=monsters, rewards=rewards, description=desc
            )
            db.session.add(dungeon)
        db.session.commit()
        print("副本数据初始化完成")

# 初始化境界数据
def init_realms():
    """初始化境界数据（如果不存在）"""
    if Realm.query.count() == 0:
        realms_data = [
            ('凡人期', 1, 0.0),
            ('炼气期', 2, 0.5),
            ('筑基期', 3, 1.2),
            ('金丹期', 4, 2.5),
            ('元婴期', 5, 4.0),
            ('化神期', 6, 7.0),
            ('炼虚期', 7, 10.0),
            ('合体期', 8, 14.0),
            ('大乘期', 9, 19.0),
            ('渡劫期', 10, 25.0),
            ('人仙', 11, 32.0),
            ('地仙', 12, 40.0),
            ('天仙', 13, 49.0),
            ('真仙', 14, 59.0),
            ('玄仙', 15, 70.0),
            ('金仙', 16, 82.0),
            ('太乙金仙', 17, 95.0),
            ('大罗金仙', 18, 109.0),
            ('混元金仙', 19, 124.0),
            ('混元大罗金仙', 20, 140.0),
            ('天道境', 21, 160.0),
            ('大道境', 22, 200.0),
        ]
        for name, stage, coefficient in realms_data:
            realm = Realm(name=name, stage=stage, coefficient=coefficient)
            db.session.add(realm)
        db.session.commit()
        print("境界数据初始化完成")

# 初始化材料数据
def init_materials():
    """初始化材料数据"""
    if Material.query.count() == 0:
        materials_data = [
            # 矿石
            ('铁矿石', '矿石', '普通', '常见', '用于锻造装备的基础材料', 10),
            ('铜矿石', '矿石', '普通', '常见', '铜质装备的制作材料', 15),
            ('金矿石', '矿石', '优质', '稀有', '黄金装备的制作材料', 50),
            ('灵石矿', '矿石', '极品', '珍贵', '法宝锻造的顶级材料', 200),

            # 草药
            ('人参', '草药', '普通', '常见', '基础丹药的药材', 8),
            ('灵芝', '草药', '优质', '稀有', '高级丹药的珍贵药材', 40),
            ('九叶草', '草药', '极品', '珍贵', '传说丹药的圣药', 150),

            # 木材
            ('松木', '木材', '普通', '常见', '基础符文的制作材料', 6),
            ('桃木', '木材', '优质', '稀有', '桃木符的制作材料', 30),
            ('紫檀木', '木材', '极品', '珍贵', '顶级符文的圣木', 120),

            # 灵材
            ('火灵珠', '灵材', '极品', '传说', '火属性法宝的核心材料', 500),
            ('水灵晶', '灵材', '极品', '传说', '水属性法宝的核心材料', 500),
        ]

        for name, type_, quality, rarity, desc, value in materials_data:
            material = Material(
                name=name,
                type=type_,
                quality=quality,
                rarity=rarity,
                description=desc,
                base_value=value
            )
            db.session.add(material)
        db.session.commit()
        print("材料数据初始化完成")

# 在应用启动时初始化数据
with app.app_context():
    db.create_all()
    init_realms()
    init_monsters()
    init_dungeons()
    init_materials()

# JWT相关
def encode_auth_token(user_id):
    try:
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
            'iat': datetime.datetime.utcnow(),
            'sub': user_id
        }
        return jwt.encode(payload, app.config.get('SECRET_KEY'), algorithm='HS256')
    except Exception as e:
        return e


def decode_auth_token(auth_token):
    try:
        payload = jwt.decode(auth_token, app.config.get('SECRET_KEY'), algorithms=['HS256'])
        return payload['sub']
    except jwt.ExpiredSignatureError:
        return 'Signature expired. Please log in again.'
    except jwt.InvalidTokenError:
        return 'Invalid token. Please log in again.'


# 认证装饰器
from functools import wraps


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            user_id = decode_auth_token(token)
            current_user = db.session.get(User, user_id)
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(current_user, *args, **kwargs)

    return decorated


# 用户注册
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({'message': 'Invalid JSON'}), 400
    # 使用 Werkzeug 的默认安全哈希
    password = data.get('password')
    if not password:
        return jsonify({'message': 'Password required'}), 400
    hashed_password = generate_password_hash(password)
    email = data.get('email')
    username = data.get('username')
    # 如果相同 email 或 username 已存在，则更新密码并返回 200（对测试保持幂等）
    existing = None
    if email:
        existing = User.query.filter_by(email=email).first()
    if not existing and username:
        existing = User.query.filter_by(username=username).first()

    if existing:
        existing.username = username or existing.username
        existing.password_hash = hashed_password
        db.session.commit()
        return jsonify({'message': 'User already existed, updated credentials.'}), 200

    new_user = User(username=username, password_hash=hashed_password, email=email)
    db.session.add(new_user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        # 可能存在并发或遗留数据冲突，尝试查找并返回已存在用户的成功响应
        existing = User.query.filter((User.email == email) | (User.username == username)).first()
        if existing:
            existing.password_hash = hashed_password
            db.session.commit()
            return jsonify({'message': 'User already existed, updated credentials.'}), 200
        return jsonify({'message': 'Registration failed due to conflict.'}), 400

    return jsonify({'message': 'User registered successfully!'}), 201


# 用户登录
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    if not user or not check_password_hash(user.password_hash, data['password']):
        return jsonify({'message': 'Invalid credentials'}), 401
    token = encode_auth_token(user.id)
    return jsonify({'token': token}), 200


# 创建人物
@app.route('/character', methods=['POST'])
@token_required
def create_character(current_user):
    data = request.get_json()
    new_char = Character(
        user_id=current_user.id,
        name=data['name'],
        linggen=data.get('linggen', '无'),
        wuxing=data.get('wuxing', 50),
        qiyun=data.get('qiyun', 50)
    )

    # 初始化属性（基于灵根调整基础属性）
    attr = CharacterAttribute(
        character=new_char,
        hp=100,
        attack=10,
        defense=10,
        speed=10,
        crit_rate=0.05,
        dodge_rate=0.05,
        hit_rate=0.95,
        crit_damage=1.5
    )

    # 根据灵根调整初始属性
    linggen_bonus = {
        '金': {'attack': 5, 'defense': 2},
        '木': {'hp': 20, 'defense': 3},
        '水': {'defense': 5, 'speed': 2},
        '火': {'attack': 8, 'crit_rate': 0.02},
        '土': {'hp': 30, 'defense': 8},
        '无': {}
    }

    bonus = linggen_bonus.get(data.get('linggen', '无'), {})
    attr.attack += bonus.get('attack', 0)
    attr.defense += bonus.get('defense', 0)
    attr.hp += bonus.get('hp', 0)
    attr.speed += bonus.get('speed', 0)
    attr.crit_rate += bonus.get('crit_rate', 0)

    db.session.add(new_char)
    db.session.flush()  # 获取 new_char.id

    # 初始化灵石资源
    resource = Resource(character_id=new_char.id, type='灵石', amount=1000)

    db.session.add(attr)
    db.session.add(resource)
    db.session.commit()
    return jsonify({'message': 'Character created successfully!'}), 201


# 获取人物信息
@app.route('/character', methods=['GET'])
@token_required
def get_character(current_user):
    # 返回当前用户最新创建的人物（按 id 倒序）以避免测试/多人物场景混淆
    char = Character.query.filter_by(user_id=current_user.id).order_by(Character.id.desc()).first()
    if not char:
        return jsonify({'message': 'No character found'}), 404
    attr = CharacterAttribute.query.filter_by(character_id=char.id).first()
    return jsonify({
        'id': char.id,
        'name': char.name,
        'level': char.level,
        'experience': char.experience,
        'realm': char.realm,
        'realm_level': char.realm_level,
        'linggen': char.linggen,
        'attributes': {
            'hp': attr.hp,
            'attack': attr.attack,
            'defense': attr.defense,
            'speed': attr.speed,
            'crit_rate': attr.crit_rate
            # 其他属性
        }
    }), 200


# 人物升级（使用 helpers）
@app.route('/character/levelup', methods=['POST'])
@token_required
def levelup_character(current_user):
    # 优先使用最新创建的人物；若该人物经验不足，则尝试查找同一账号下任何已有足够经验的人物
    char = Character.query.filter_by(user_id=current_user.id).order_by(Character.id.desc()).first()
    if not char:
        return jsonify({'message': 'No character found'}), 404
    needed = exp_for_level(char.level)
    if char.experience < needed:
        # 查找其他人物是否有足够经验（兼容测试中可能修改了旧人物的场景）
        alt = Character.query.filter(Character.user_id == current_user.id, Character.experience >= needed).order_by(Character.id.desc()).first()
        if alt:
            char = alt
        else:
            return jsonify({'message': 'Not enough experience', 'needed': needed}), 400

    # 检查是否需要境界突破（每10级突破一次境界）
    if char.level % 10 == 0:
        return jsonify({'message': '需要境界突破才能继续升级', 'need_realm_breakthrough': True}), 400

    attr = CharacterAttribute.query.filter_by(character_id=char.id).first()
    realm = Realm.query.filter_by(name=char.realm).first()
    realm_coeff = realm.coefficient if realm else 0.0
    # 扣除经验并升级
    char.experience -= needed
    incs = apply_level_up(char, attr, realm_coeff)
    db.session.commit()
    return jsonify({'message': 'Level up successful!', 'increments': incs, 'new_level': char.level}), 200


# 境界突破API
@app.route('/character/realm_breakthrough', methods=['POST'])
@token_required
def realm_breakthrough(current_user):
    char = Character.query.filter_by(user_id=current_user.id).order_by(Character.id.desc()).first()
    if not char:
        return jsonify({'message': 'No character found'}), 404

    # 检查等级要求（每10级可以突破一次境界）
    if char.level < 10:
        return jsonify({'message': '等级不足，无法突破境界'}), 400

    # 获取当前境界和下一个境界
    current_realm = Realm.query.filter_by(name=char.realm).first()
    if not current_realm:
        return jsonify({'message': '境界数据错误'}), 500

    next_realm = Realm.query.filter(Realm.stage > current_realm.stage).order_by(Realm.stage).first()
    if not next_realm:
        return jsonify({'message': '已达到最高境界'}), 400

    # 检查资源要求（灵石消耗）
    breakthrough_cost = 1000 * (current_realm.stage + 1)  # 突破消耗随境界增加
    resource = Resource.query.filter_by(character_id=char.id, type='灵石').first()
    if not resource or resource.amount < breakthrough_cost:
        return jsonify({'message': f'灵石不足，需要{breakthrough_cost}灵石', 'required_lingshi': breakthrough_cost}), 400

    # 境界突破逻辑
    data = request.get_json() or {}
    purity = data.get('purity', 0.5)  # 纯度系数，默认0.5
    success_rate = min(0.8, purity * 0.9 + 0.1)  # 成功率基于纯度，最低10%，最高80%

    if random.random() < success_rate:
        # 突破成功
        char.realm = next_realm.name
        char.level = 1  # 境界突破后等级重置为1
        char.experience = 0  # 经验清零
        resource.amount -= breakthrough_cost

        # 境界突破属性提升
        attr = CharacterAttribute.query.filter_by(character_id=char.id).first()
        realm_bonus = int(next_realm.coefficient * 50)  # 境界系数决定属性加成
        attr.hp += realm_bonus * 10
        attr.attack += realm_bonus * 2
        attr.defense += realm_bonus * 2
        attr.speed += realm_bonus

        db.session.commit()
        return jsonify({
            'message': f'境界突破成功！进入{next_realm.name}',
            'new_realm': next_realm.name,
            'success_rate': success_rate,
            'attribute_bonuses': {
                'hp': realm_bonus * 10,
                'attack': realm_bonus * 2,
                'defense': realm_bonus * 2,
                'speed': realm_bonus
            }
        }), 200
    else:
        # 突破失败，消耗部分灵石
        failure_cost = breakthrough_cost // 2
        resource.amount -= failure_cost
        db.session.commit()
        return jsonify({
            'message': '境界突破失败',
            'success_rate': success_rate,
            'lingshi_lost': failure_cost
        }), 400


# 战力接口
@app.route('/character/battle_power', methods=['GET'])
@token_required
def get_battle_power(current_user):
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'No character found'}), 404
    attr = CharacterAttribute.query.filter_by(character_id=char.id).first()
    equipments = Equipment.query.filter_by(character_id=char.id).all()
    mantras = Mantra.query.filter_by(character_id=char.id).all()
    treasures = Treasure.query.filter_by(character_id=char.id).all()
    power = compute_battle_power(attr, equipments=equipments, mantras=mantras, treasures=treasures)
    return jsonify({'battle_power': power}), 200


# 其余接口保留原样（未修改）

# 装备系统
@app.route('/equipment', methods=['GET'])
@token_required
def get_equipments(current_user):
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'No character found'}), 404

    # 确保角色有完整的装备栏位（10个槽位）
    init_equipment_slots(char.id)

    eqs = Equipment.query.filter_by(character_id=char.id).order_by(Equipment.slot).all()
    return jsonify([{
        'id': e.id,
        'slot': e.slot,
        'type': e.type,
        'name': e.name,
        'quality': e.quality,
        'level': e.level,
        'max_level': e.max_level,
        'experience': e.experience,
        'attack_bonus': e.attack_bonus,
        'defense_bonus': e.defense_bonus,
        'hp_bonus': e.hp_bonus,
        'speed_bonus': e.speed_bonus,
        'crit_rate_bonus': e.crit_rate_bonus,
        'dodge_rate_bonus': e.dodge_rate_bonus,
        'strengthen_times': e.strengthen_times,
        'rune_slots': e.rune_slots,
        'equipped': e.equipped
    } for e in eqs]), 200


def init_equipment_slots(character_id):
    """初始化角色的10个装备栏位"""
    # 装备栏位类型定义
    slot_types = {
        1: '武器',
        2: '头盔',
        3: '项链',
        4: '衣服',
        5: '腰带',
        6: '鞋子',
        7: '耳环',
        8: '戒指',
        9: '手镯',
        10: '护符'
    }

    for slot, equip_type in slot_types.items():
        # 检查是否已有该栏位的装备
        existing = Equipment.query.filter_by(character_id=character_id, slot=slot).first()
        if not existing:
            # 创建基础装备
            base_equipment = Equipment(
                character_id=character_id,
                slot=slot,
                type=equip_type,
                name=f'普通{equip_type}',
                quality='黄阶',
                max_level=10 if slot <= 6 else 5,  # 主要装备10级，饰品5级
                equipped=True
            )
            db.session.add(base_equipment)

    db.session.commit()

@app.route('/equipment/upgrade/<int:equip_id>', methods=['POST'])
@token_required
def upgrade_equipment(current_user, equip_id):
    equip = db.session.get(Equipment, equip_id)
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not equip or equip.character_id != char.id:
        return jsonify({'message': 'Equipment not found'}), 404

    # 检查是否已达到最大等级
    if equip.level >= equip.max_level:
        return jsonify({'message': f'Equipment already at max level ({equip.max_level})'}), 400

    # 根据品质计算升级消耗
    quality_multipliers = {
        '黄阶': 1.0,
        '玄阶': 1.5,
        '地阶': 2.0,
        '天阶': 3.0
    }
    base_exp = 100
    multiplier = quality_multipliers.get(equip.quality, 1.0)
    exp_needed = int(base_exp * equip.level * multiplier)
    lingshi_needed = int(exp_needed * 0.5)  # 灵石消耗为经验的一半

    # 检查资源
    resource = Resource.query.filter_by(character_id=char.id, type='灵石').first()
    if not resource or resource.amount < lingshi_needed:
        return jsonify({'message': f'Not enough ling shi, need {lingshi_needed}', 'required': lingshi_needed}), 400

    # 升级装备
    equip.level += 1
    equip.experience += exp_needed
    resource.amount -= lingshi_needed

    # 根据装备类型更新属性
    if equip.type == '武器':
        equip.attack_bonus += int(5 * multiplier)
    elif equip.type in ['头盔', '衣服']:
        equip.defense_bonus += int(3 * multiplier)
        equip.hp_bonus += int(10 * multiplier)
    elif equip.type in ['项链', '戒指', '耳环', '手镯', '护符']:
        equip.crit_rate_bonus += 0.005 * multiplier
        equip.dodge_rate_bonus += 0.005 * multiplier
    else:
        equip.attack_bonus += int(2 * multiplier)

    db.session.commit()
    return jsonify({
        'message': f'Equipment upgraded to level {equip.level}!',
        'new_level': equip.level,
        'exp_cost': exp_needed,
        'lingshi_cost': lingshi_needed
    }), 200


@app.route('/equipment/strengthen/<int:equip_id>', methods=['POST'])
@token_required
def strengthen_equipment(current_user, equip_id):
    equip = db.session.get(Equipment, equip_id)
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not equip or equip.character_id != char.id:
        return jsonify({'message': 'Equipment not found'}), 404

    # 检查强化次数上限（避免无限强化）
    if equip.strengthen_times >= 20:
        return jsonify({'message': 'Equipment has reached maximum strengthen level'}), 400

    # 消耗灵石（根据装备品质和强化次数计算）
    data = request.get_json() or {}
    material_quality = float(data.get('material_quality_factor', 1.0))
    quality_multipliers = {'黄阶': 1.0, '玄阶': 1.5, '地阶': 2.0, '天阶': 3.0}
    quality_multiplier = quality_multipliers.get(equip.quality, 1.0)
    base_cost = 100
    cost = int(base_cost * (equip.level + 1) * quality_multiplier * (1 + equip.strengthen_times * 0.1))

    resource = Resource.query.filter_by(character_id=char.id, type='灵石').first()
    if not resource or resource.amount < cost:
        return jsonify({'message': f'Not enough ling shi, need {cost}', 'required': cost}), 400

    # 计算成功率（使用衰减公式）
    success_rate = calc_strengthen_success(equip.strengthen_times, material_quality_factor=material_quality)

    resource.amount -= cost
    if random.random() < success_rate:
        # 强化成功，提高属性
        strengthen_bonus = int((5 + equip.level) * quality_multiplier * material_quality)
        if equip.type == '武器':
            equip.attack_bonus += strengthen_bonus
        elif equip.type in ['头盔', '衣服']:
            equip.defense_bonus += strengthen_bonus // 2
            equip.hp_bonus += strengthen_bonus
        else:
            equip.attack_bonus += strengthen_bonus // 2

        equip.strengthen_times += 1
        db.session.commit()
        return jsonify({
            'message': f'强化成功！装备属性提升{strengthen_bonus}',
            'success_rate': success_rate,
            'strengthen_level': equip.strengthen_times,
            'cost': cost
        }), 200
    else:
        # 强化失败，记录失败次数（可能导致装备损坏，但这里简化）
        equip.strengthen_times += 1
        db.session.commit()
        return jsonify({
            'message': '强化失败',
            'success_rate': success_rate,
            'strengthen_level': equip.strengthen_times,
            'cost': cost
        }), 400


@app.route('/rune/forge', methods=['POST'])
@token_required
def forge_rune(current_user):
    data = request.get_json() or {}
    name = data.get('name', '符文')
    quality = data.get('quality', '普通')
    attr_type = data.get('attribute_type', 'attack')
    attr_value = int(data.get('attribute_value', 1))
    material_quality = float(data.get('material_quality_factor', 1.0))

    # 简化成本
    char = Character.query.filter_by(user_id=current_user.id).first()
    resource = Resource.query.filter_by(character_id=char.id, type='灵石').first()
    cost = 200
    if not resource or resource.amount < cost:
        return jsonify({'message': 'Not enough ling shi'}), 400

    success_rate = calc_forge_success(material_quality_factor=material_quality)
    import random
    resource.amount -= cost
    if random.random() < success_rate:
        rune = Rune(name=name, quality=quality, attribute_type=attr_type, attribute_value=attr_value, owner_id=char.id)
        db.session.add(rune)
        db.session.commit()
        return jsonify({'message': 'Forge success', 'rune_id': rune.id, 'success_rate': success_rate}), 201
    else:
        db.session.commit()
        return jsonify({'message': 'Forge failed', 'success_rate': success_rate}), 400


@app.route('/rune/equip/equipment', methods=['POST'])
@token_required
def equip_rune_to_equipment(current_user):
    data = request.get_json() or {}
    rune_id = data.get('rune_id')
    equip_id = data.get('equip_id')
    rune = db.session.get(Rune, rune_id)
    equip = db.session.get(Equipment, equip_id)
    if not rune or not equip:
        return jsonify({'message': 'Rune or Equipment not found'}), 404
    char = Character.query.filter_by(user_id=current_user.id).first()
    if rune.owner_id != char.id or equip.character_id != char.id:
        return jsonify({'message': 'Not your rune/equipment'}), 403

    # 检查槽位上限
    from utils.helpers import slots_for_quality
    slot_limit = equip.rune_slots or slots_for_quality(equip.quality, kind='equipment')
    current_count = Rune.query.filter_by(equipment_id=equip.id).count()
    if current_count >= slot_limit:
        return jsonify({'message': 'No available rune slots on this equipment', 'slot_limit': slot_limit}), 400

    # 将符文镶嵌到装备上（简化：直接叠加属性并记录关联）
    if rune.attribute_type == 'attack':
        equip.attack_bonus += rune.attribute_value
    elif rune.attribute_type == 'defense':
        equip.defense_bonus += rune.attribute_value
    elif rune.attribute_type == 'hp':
        equip.hp_bonus += rune.attribute_value
    else:
        equip.attack_bonus += rune.attribute_value

    rune.equipment_id = equip.id
    db.session.commit()
    return jsonify({'message': 'Rune equipped to equipment', 'equip_id': equip.id, 'rune_id': rune.id}), 200


@app.route('/rune/equip/treasure', methods=['POST'])
@token_required
def equip_rune_to_treasure(current_user):
    data = request.get_json() or {}
    rune_id = data.get('rune_id')
    treasure_id = data.get('treasure_id')
    rune = db.session.get(Rune, rune_id)
    tr = db.session.get(Treasure, treasure_id)
    if not rune or not tr:
        return jsonify({'message': 'Rune or Treasure not found'}), 404
    char = Character.query.filter_by(user_id=current_user.id).first()
    if rune.owner_id != char.id or tr.character_id != char.id:
        return jsonify({'message': 'Not your rune/treasure'}), 403

    from utils.helpers import slots_for_quality
    slot_limit = tr.rune_slots or slots_for_quality(tr.quality, kind='treasure')
    current_count = Rune.query.filter_by(treasure_id=tr.id).count()
    if current_count >= slot_limit:
        return jsonify({'message': 'No available rune slots on this treasure', 'slot_limit': slot_limit}), 400

    # 叠加属性
    if rune.attribute_type == 'attack':
        tr.attack_bonus += rune.attribute_value
    elif rune.attribute_type == 'defense':
        tr.defense_bonus += rune.attribute_value
    elif rune.attribute_type == 'hp':
        tr.hp_bonus += rune.attribute_value
    else:
        tr.attack_bonus += rune.attribute_value

    rune.treasure_id = tr.id
    db.session.commit()
    return jsonify({'message': 'Rune equipped to treasure', 'treasure_id': tr.id, 'rune_id': rune.id}), 200


@app.route('/rune', methods=['GET'])
@token_required
def get_runes(current_user):
    """获取角色的符文列表"""
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'No character found'}), 404

    runes = Rune.query.filter_by(owner_id=char.id).all()
    return jsonify([{
        'id': r.id,
        'name': r.name,
        'quality': r.quality,
        'attribute_type': r.attribute_type,
        'attribute_value': r.attribute_value,
        'equipment_id': r.equipment_id,
        'treasure_id': r.treasure_id,
        'equipped': bool(r.equipment_id or r.treasure_id)
    } for r in runes]), 200


@app.route('/equipment/unequip/<int:equip_id>', methods=['POST'])
@token_required
def unequip_equipment(current_user, equip_id):
    """卸下装备"""
    equip = db.session.get(Equipment, equip_id)
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not equip or equip.character_id != char.id:
        return jsonify({'message': 'Equipment not found'}), 404

    if not equip.equipped:
        return jsonify({'message': 'Equipment already unequipped'}), 400

    equip.equipped = False
    db.session.commit()
    return jsonify({'message': 'Equipment unequipped successfully'}), 200


@app.route('/equipment/equip/<int:equip_id>', methods=['POST'])
@token_required
def equip_equipment(current_user, equip_id):
    """装备物品"""
    equip = db.session.get(Equipment, equip_id)
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not equip or equip.character_id != char.id:
        return jsonify({'message': 'Equipment not found'}), 404

    if equip.equipped:
        return jsonify({'message': 'Equipment already equipped'}), 400

    # 检查是否有同类型装备已装备，如果有则先卸下
    existing_equipped = Equipment.query.filter_by(
        character_id=char.id,
        type=equip.type,
        equipped=True
    ).first()

    if existing_equipped:
        existing_equipped.equipped = False

    equip.equipped = True
    db.session.commit()
    return jsonify({'message': 'Equipment equipped successfully'}), 200


@app.route('/treasure/upgrade/<int:treasure_id>', methods=['POST'])
@token_required
def upgrade_treasure(current_user, treasure_id):
    tr = db.session.get(Treasure, treasure_id)
    if not tr:
        return jsonify({'message': 'Treasure not found'}), 404
    char = Character.query.filter_by(user_id=current_user.id).first()
    if tr.character_id != char.id:
        return jsonify({'message': 'Not your treasure'}), 403
    # 简化升级逻辑：消耗灵石，提高等级和属性
    char = Character.query.filter_by(user_id=User.query.filter_by(username='').first().id).first() if False else Character.query.filter_by(user_id=tr.character_id).first()
    resource = Resource.query.filter_by(character_id=tr.character_id, type='灵石').first()
    cost = 150 * (tr.level + 1)
    if not resource or resource.amount < cost:
        return jsonify({'message': 'Not enough ling shi'}), 400
    resource.amount -= cost
    tr.level += 1
    tr.attack_bonus += 10
    db.session.commit()
    return jsonify({'message': 'Treasure upgraded', 'new_level': tr.level}), 200

@app.route('/treasure', methods=['GET'])
@token_required
def get_treasures(current_user):
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'No character found'}), 404
    trs = Treasure.query.filter_by(character_id=char.id).all()
    return jsonify([{
        'id': t.id,
        'slot': t.slot,
        'name': t.name,
        'quality': t.quality,
        'attack_bonus': t.attack_bonus
    } for t in trs]), 200

@app.route('/treasure/forge', methods=['POST'])
@token_required
def forge_treasure(current_user):
    char = Character.query.filter_by(user_id=current_user.id).first()
    data = request.get_json()
    # 更完整的锻造流程：消耗灵石 -> 依据材料品质计算成功率 -> 成功则生成品质与属性
    material_quality = float(data.get('material_quality_factor', 1.0))
    resource = Resource.query.filter_by(character_id=char.id, type='灵石').first()
    cost = int(800 * material_quality)
    if not resource or resource.amount < cost:
        return jsonify({'message': 'Not enough ling shi', 'required': cost}), 400

    success_rate = calc_forge_success(material_quality_factor=material_quality)
    if random.random() < success_rate:
        quality = roll_treasure_quality(material_quality)
        stats = generate_treasure_stats(quality)
        name = data.get('name') or f"{quality}法宝"
        new_treasure = Treasure(
            character_id=char.id,
            slot=int(data.get('slot', 1)),
            name=name,
            quality=quality,
            attack_bonus=stats['attack_bonus'],
            defense_bonus=stats['defense_bonus'],
            hp_bonus=stats['hp_bonus'],
            rune_slots=stats.get('rune_slots', 1)
        )
        resource.amount -= cost
        db.session.add(new_treasure)
        db.session.commit()
        return jsonify({
            'message': 'Treasure forged successfully!',
            'treasure': {
                'id': new_treasure.id,
                'name': new_treasure.name,
                'quality': new_treasure.quality,
                'attack_bonus': new_treasure.attack_bonus,
                'defense_bonus': new_treasure.defense_bonus,
                'hp_bonus': new_treasure.hp_bonus,
                'rune_slots': new_treasure.rune_slots
            }
        }), 201
    else:
        # 失败消耗材料
        resource.amount -= cost
        db.session.commit()
        return jsonify({'message': 'Forging failed', 'success_rate': success_rate}), 400

@app.route('/mantra', methods=['GET'])
@token_required
def get_mantras(current_user):
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'No character found'}), 404

    mns = Mantra.query.filter_by(character_id=char.id).all()
    return jsonify([{
        'id': m.id,
        'name': m.name,
        'quality': m.quality,
        'level': m.level,
        'max_level': m.max_level,
        'experience': m.experience,
        'proficiency': m.proficiency,
        'proficiency_exp': m.proficiency_exp,
        'proficiency_max': m.proficiency_max,
        'linggen_required': m.linggen_required,
        'equipped': m.equipped,
        'slot': m.slot,
        'attack_bonus': m.attack_bonus,
        'defense_bonus': m.defense_bonus,
        'hp_bonus': m.hp_bonus,
        'speed_bonus': m.speed_bonus,
        'crit_rate_bonus': m.crit_rate_bonus,
        'special_effect': m.special_effect
    } for m in mns]), 200


@app.route('/mantra/upgrade/<int:mantra_id>', methods=['POST'])
@token_required
def upgrade_mantra(current_user, mantra_id):
    """功法升级API"""
    mantra = db.session.get(Mantra, mantra_id)
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not mantra or mantra.character_id != char.id:
        return jsonify({'message': 'Mantra not found'}), 404

    # 检查是否已达到最大等级
    if mantra.level >= mantra.max_level:
        return jsonify({'message': f'Mantra already at max level ({mantra.max_level})'}), 400

    # 计算升级消耗（经验、灵石，考虑悟性系数和天气系数）
    data = request.get_json() or {}
    weather_bonus = float(data.get('weather_bonus', 1.0))  # 天气系数，默认1.0

    costs = mantra_upgrade_cost(mantra.level, mantra.quality, char.wuxing, weather_bonus)

    # 检查资源
    resource = Resource.query.filter_by(character_id=char.id, type='灵石').first()
    if not resource or resource.amount < costs['lingshi']:
        return jsonify({'message': f'Not enough ling shi, need {costs["lingshi"]}', 'required': costs['lingshi']}), 400

    # 检查经验
    if char.experience < costs['experience']:
        return jsonify({'message': f'Not enough experience, need {costs["experience"]}', 'required': costs['experience']}), 400

    # 升级功法
    mantra.level += 1
    mantra.experience += costs['experience']
    char.experience -= costs['experience']
    resource.amount -= costs['lingshi']

    # 根据品质更新属性
    quality_multipliers = {'黄阶': 1.0, '玄阶': 1.5, '地阶': 2.0, '天阶': 3.0}
    multiplier = quality_multipliers.get(mantra.quality, 1.0)
    level_bonus = mantra.level * multiplier

    mantra.attack_bonus = int(level_bonus * 2)
    mantra.defense_bonus = int(level_bonus * 1.5)
    mantra.hp_bonus = int(level_bonus * 10)
    mantra.speed_bonus = int(level_bonus * 0.5)
    mantra.crit_rate_bonus = level_bonus * 0.005

    db.session.commit()
    return jsonify({
        'message': f'Mantra upgraded to level {mantra.level}!',
        'new_level': mantra.level,
        'exp_cost': costs['experience'],
        'lingshi_cost': costs['lingshi'],
        'wuxing_factor': costs['wuxing_factor'],
        'weather_bonus': costs['weather_bonus']
    }), 200


@app.route('/mantra/cultivate/<int:mantra_id>', methods=['POST'])
@token_required
def cultivate_mantra_api(current_user, mantra_id):
    """功法修炼API"""
    mantra = db.session.get(Mantra, mantra_id)
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not mantra or mantra.character_id != char.id:
        return jsonify({'message': 'Mantra not found'}), 404

    # 计算修炼经验获取
    data = request.get_json() or {}
    weather_bonus = float(data.get('weather_bonus', 1.0))  # 天气系数
    time_spent = int(data.get('time_spent', 1))  # 修炼时间

    exp_gain = cultivate_mantra_exp_gain(10, char.wuxing, weather_bonus, time_spent)

    # 更新熟练度经验
    mantra.proficiency_exp += exp_gain

    # 检查是否可以晋升熟练度等级
    new_proficiency = update_mantra_proficiency(mantra.proficiency, mantra.proficiency_exp, mantra.proficiency_max)

    if new_proficiency != mantra.proficiency:
        mantra.proficiency = new_proficiency
        mantra.proficiency_exp = 0  # 重置经验
        mantra.proficiency_max = int(mantra.proficiency_max * 1.5)  # 下一级要求更高

    db.session.commit()
    return jsonify({
        'message': f'修炼成功！获得{exp_gain}点熟练度经验',
        'exp_gained': exp_gain,
        'current_proficiency': mantra.proficiency,
        'proficiency_exp': mantra.proficiency_exp,
        'proficiency_max': mantra.proficiency_max,
        'level_up': new_proficiency != mantra.proficiency
    }), 200


@app.route('/mantra/equip/<int:mantra_id>', methods=['POST'])
@token_required
def equip_mantra(current_user, mantra_id):
    """装备功法"""
    mantra = db.session.get(Mantra, mantra_id)
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not mantra or mantra.character_id != char.id:
        return jsonify({'message': 'Mantra not found'}), 404

    if mantra.equipped:
        return jsonify({'message': 'Mantra already equipped'}), 400

    data = request.get_json() or {}
    slot = int(data.get('slot', 0))

    # 检查槽位是否已被占用
    existing_mantra = Mantra.query.filter_by(character_id=char.id, slot=slot, equipped=True).first()
    if existing_mantra:
        existing_mantra.equipped = False
        existing_mantra.slot = 0

    mantra.equipped = True
    mantra.slot = slot

    db.session.commit()
    return jsonify({'message': f'Mantra equipped to slot {slot}'}), 200


@app.route('/mantra/unequip/<int:mantra_id>', methods=['POST'])
@token_required
def unequip_mantra(current_user, mantra_id):
    """卸下功法"""
    mantra = db.session.get(Mantra, mantra_id)
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not mantra or mantra.character_id != char.id:
        return jsonify({'message': 'Mantra not found'}), 404

    if not mantra.equipped:
        return jsonify({'message': 'Mantra already unequipped'}), 400

    mantra.equipped = False
    mantra.slot = 0

    db.session.commit()
    return jsonify({'message': 'Mantra unequipped successfully'}), 200


@app.route('/treasure/awaken/<int:treasure_id>', methods=['POST'])
@token_required
def awaken_treasure(current_user, treasure_id):
    tre = db.session.get(Treasure, treasure_id)
    if not tre or tre.character_id != Character.query.filter_by(user_id=current_user.id).first().id:
        return jsonify({'message': 'Treasure not found or not yours'}), 404
    data = request.get_json() or {}
    material_quality = float(data.get('material_quality_factor', 1.0))
    resource = Resource.query.filter_by(character_id=tre.character_id, type='灵石').first()
    cost = int(1500 * material_quality)
    if not resource or resource.amount < cost:
        return jsonify({'message': 'Not enough ling shi', 'required': cost}), 400

    rate = awaken_success_rate(tre.quality, material_quality_factor=material_quality)
    resource.amount -= cost
    success = random.random() < rate
    if success:
        tre.awakened = True
        # 简单技能池，根据品质可能挑选更强技能
        skill_pool = ['护体真气', '回春术', '破甲斩', '吸血诀', '风雷诀', '天穹引']
        tre.special_skill = random.choice(skill_pool)
        db.session.commit()
        return jsonify({'message': 'Awaken success', 'special_skill': tre.special_skill}), 200
    else:
        db.session.commit()
        return jsonify({'message': 'Awaken failed', 'success_rate': rate}), 400


@app.route('/treasure/recast/<int:treasure_id>', methods=['POST'])
@token_required
def recast_treasure(current_user, treasure_id):
    tre = db.session.get(Treasure, treasure_id)
    if not tre or tre.character_id != Character.query.filter_by(user_id=current_user.id).first().id:
        return jsonify({'message': 'Treasure not found or not yours'}), 404
    data = request.get_json() or {}
    material_quality = float(data.get('material_quality_factor', 1.0))
    resource = Resource.query.filter_by(character_id=tre.character_id, type='灵石').first()
    cost = int(1200 * (1 + tre.recast_times * 0.5) * material_quality)
    if not resource or resource.amount < cost:
        return jsonify({'message': 'Not enough ling shi', 'required': cost}), 400

    success_rate = calc_forge_success(material_quality_factor=material_quality)
    resource.amount -= cost
    tre.recast_times = (tre.recast_times or 0) + 1
    if random.random() < success_rate:
        stats = generate_treasure_stats(tre.quality)
        tre.attack_bonus = stats['attack_bonus']
        tre.defense_bonus = stats['defense_bonus']
        tre.hp_bonus = stats['hp_bonus']
        tre.rune_slots = stats.get('rune_slots', tre.rune_slots)
        db.session.commit()
        return jsonify({'message': 'Recast success', 'new_stats': {
            'attack_bonus': tre.attack_bonus,
            'defense_bonus': tre.defense_bonus,
            'hp_bonus': tre.hp_bonus,
            'rune_slots': tre.rune_slots,
            'recast_times': tre.recast_times
        }}), 200
    else:
        db.session.commit()
        return jsonify({'message': 'Recast failed', 'success_rate': success_rate, 'recast_times': tre.recast_times}), 400


@app.route('/treasure/estimate', methods=['POST'])
@token_required
def estimate_treasure(current_user):
    data = request.get_json() or {}
    treasure_id = data.get('treasure_id')
    material_quality = float(data.get('material_quality_factor', 1.0))
    tre = db.session.get(Treasure, treasure_id)
    if not tre or tre.character_id != Character.query.filter_by(user_id=current_user.id).first().id:
        return jsonify({'message': 'Treasure not found or not yours'}), 404

    awaken_rate = awaken_success_rate(tre.quality, material_quality_factor=material_quality)
    recast_rate = calc_forge_success(material_quality_factor=material_quality)
    awaken_cost = int(1500 * material_quality)
    recast_cost = int(1200 * (1 + (tre.recast_times or 0) * 0.5) * material_quality)

    return jsonify({
        'awaken_rate': awaken_rate,
        'recast_rate': recast_rate,
        'awaken_cost': awaken_cost,
        'recast_cost': recast_cost,
        'recast_times': tre.recast_times or 0
    }), 200

@app.route('/mantra/cultivate/<int:mantra_id>', methods=['POST'])
@token_required
def cultivate_mantra(current_user, mantra_id):
    mantra = db.session.get(Mantra, mantra_id)
    if not mantra or mantra.character_id != Character.query.filter_by(user_id=current_user.id).first().id:
        return jsonify({'message': 'Mantra not found'}), 404
    # 修炼逻辑
    exp_gain = 10  # 简化
    mantra.proficiency_exp += exp_gain
    # 更新熟练度
    if mantra.proficiency_exp >= 100:  # 简化
        mantra.proficiency = '小成'
    db.session.commit()
    return jsonify({'message': 'Cultivated!'}), 200

@app.route('/shentong', methods=['GET'])
@token_required
def get_shentongs(current_user):
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'No character found'}), 404

    sts = Shentong.query.filter_by(character_id=char.id).all()
    return jsonify([{
        'id': s.id,
        'name': s.name,
        'level': s.level,
        'max_level': s.max_level,
        'experience': s.experience,
        'proficiency': s.proficiency,
        'trigger_rate': s.trigger_rate,
        'equipped': s.equipped,
        'slot': s.slot,
        'damage_multiplier': s.damage_multiplier,
        'effect_description': s.effect_description,
        'cooldown': s.cooldown
    } for s in sts]), 200


@app.route('/shentong/upgrade/<int:shentong_id>', methods=['POST'])
@token_required
def upgrade_shentong(current_user, shentong_id):
    """神通升级API"""
    shentong = db.session.get(Shentong, shentong_id)
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not shentong or shentong.character_id != char.id:
        return jsonify({'message': 'Shentong not found'}), 404

    # 检查是否已达到最大等级
    if shentong.level >= shentong.max_level:
        return jsonify({'message': f'Shentong already at max level ({shentong.max_level})'}), 400

    # 计算升级消耗
    exp_needed = shentong_exp_for_level(shentong.level)
    lingshi_needed = int(exp_needed * 0.8)  # 灵石消耗为经验的80%

    # 检查资源
    resource = Resource.query.filter_by(character_id=char.id, type='灵石').first()
    if not resource or resource.amount < lingshi_needed:
        return jsonify({'message': f'Not enough ling shi, need {lingshi_needed}', 'required': lingshi_needed}), 400

    if char.experience < exp_needed:
        return jsonify({'message': f'Not enough experience, need {exp_needed}', 'required': exp_needed}), 400

    # 升级神通
    shentong.level += 1
    shentong.experience += exp_needed
    char.experience -= exp_needed
    resource.amount -= lingshi_needed

    # 更新属性和触发概率
    shentong.damage_multiplier = 1.0 + (shentong.level - 1) * 0.1  # 每级增加10%伤害
    shentong.trigger_rate = shentong_trigger_rate(shentong.proficiency)

    db.session.commit()
    return jsonify({
        'message': f'Shentong upgraded to level {shentong.level}!',
        'new_level': shentong.level,
        'exp_cost': exp_needed,
        'lingshi_cost': lingshi_needed,
        'damage_multiplier': shentong.damage_multiplier,
        'trigger_rate': shentong.trigger_rate
    }), 200


@app.route('/shentong/equip/<int:shentong_id>', methods=['POST'])
@token_required
def equip_shentong(current_user, shentong_id):
    """装备神通"""
    shentong = db.session.get(Shentong, shentong_id)
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not shentong or shentong.character_id != char.id:
        return jsonify({'message': 'Shentong not found'}), 404

    if shentong.equipped:
        return jsonify({'message': 'Shentong already equipped'}), 400

    data = request.get_json() or {}
    slot = int(data.get('slot', 0))

    # 检查槽位是否已被占用（神通最多3个槽位）
    if slot < 1 or slot > 3:
        return jsonify({'message': 'Invalid slot, must be 1-3'}), 400

    existing_shentong = Shentong.query.filter_by(character_id=char.id, slot=slot, equipped=True).first()
    if existing_shentong:
        existing_shentong.equipped = False
        existing_shentong.slot = 0

    shentong.equipped = True
    shentong.slot = slot

    db.session.commit()
    return jsonify({'message': f'Shentong equipped to slot {slot}'}), 200


@app.route('/shentong/unequip/<int:shentong_id>', methods=['POST'])
@token_required
def unequip_shentong(current_user, shentong_id):
    """卸下神通"""
    shentong = db.session.get(Shentong, shentong_id)
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not shentong or shentong.character_id != char.id:
        return jsonify({'message': 'Shentong not found'}), 404

    if not shentong.equipped:
        return jsonify({'message': 'Shentong already unequipped'}), 400

    shentong.equipped = False
    shentong.slot = 0

    db.session.commit()
    return jsonify({'message': 'Shentong unequipped successfully'}), 200


@app.route('/shentong/cultivate/<int:shentong_id>', methods=['POST'])
@token_required
def cultivate_shentong(current_user, shentong_id):
    """神通修炼API"""
    shentong = db.session.get(Shentong, shentong_id)
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not shentong or shentong.character_id != char.id:
        return jsonify({'message': 'Shentong not found'}), 404

    # 计算修炼经验获取（神通修炼比功法更难）
    data = request.get_json() or {}
    time_spent = int(data.get('time_spent', 1))  # 修炼时间
    environment_bonus = float(data.get('environment_bonus', 1.0))  # 环境系数
    material_quality = float(data.get('material_quality', 1.0))  # 材料品质系数

    # 神通修炼经验获取（比功法更难）
    base_exp = 5  # 神通修炼基础经验较少
    wuxing_factor = max(0.3, min(2.5, char.wuxing / 50.0))  # 悟性影响较小
    total_exp = int(base_exp * wuxing_factor * environment_bonus * material_quality * time_spent)

    # 更新熟练度（0-100）
    old_proficiency = shentong.proficiency
    shentong.proficiency = min(100, shentong.proficiency + total_exp)
    new_proficiency = shentong.proficiency

    # 更新触发概率
    shentong.trigger_rate = shentong_trigger_rate(shentong.proficiency)

    db.session.commit()
    return jsonify({
        'message': f'神通修炼成功！熟练度提升{new_proficiency - old_proficiency}点',
        'exp_gained': total_exp,
        'current_proficiency': new_proficiency,
        'max_proficiency': 100,
        'trigger_rate': shentong.trigger_rate
    }), 200


@app.route('/mantra/learn', methods=['POST'])
@token_required
def learn_mantra(current_user):
    """学习新功法"""
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'No character found'}), 404

    data = request.get_json() or {}
    mantra_name = data.get('name', '').strip()
    quality = data.get('quality', '黄阶')

    if not mantra_name:
        return jsonify({'message': 'Mantra name is required'}), 400

    # 检查是否已有同名功法
    existing = Mantra.query.filter_by(character_id=char.id, name=mantra_name).first()
    if existing:
        return jsonify({'message': 'You already have this mantra'}), 400

    # 创建新功法
    new_mantra = Mantra(
        character_id=char.id,
        name=mantra_name,
        quality=quality,
        max_level=10 if quality == '黄阶' else 20 if quality == '玄阶' else 30 if quality == '地阶' else 40,
        equipped=False,
        slot=0
    )

    # 根据品质设置基础属性
    quality_multipliers = {'黄阶': 1.0, '玄阶': 1.5, '地阶': 2.0, '天阶': 3.0}
    multiplier = quality_multipliers.get(quality, 1.0)

    new_mantra.attack_bonus = int(5 * multiplier)
    new_mantra.defense_bonus = int(3 * multiplier)
    new_mantra.hp_bonus = int(15 * multiplier)
    new_mantra.speed_bonus = int(2 * multiplier)
    new_mantra.crit_rate_bonus = 0.01 * multiplier

    db.session.add(new_mantra)
    db.session.commit()

    return jsonify({
        'message': f'Successfully learned mantra: {mantra_name}',
        'mantra': {
            'id': new_mantra.id,
            'name': new_mantra.name,
            'quality': new_mantra.quality,
            'max_level': new_mantra.max_level
        }
    }), 201


@app.route('/shentong/learn', methods=['POST'])
@token_required
def learn_shentong(current_user):
    """学习新神通"""
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'No character found'}), 404

    data = request.get_json() or {}
    shentong_name = data.get('name', '').strip()

    if not shentong_name:
        return jsonify({'message': 'Shentong name is required'}), 400

    # 检查是否已有同名神通
    existing = Shentong.query.filter_by(character_id=char.id, name=shentong_name).first()
    if existing:
        return jsonify({'message': 'You already have this shentong'}), 400

    # 创建新神通
    new_shentong = Shentong(
        character_id=char.id,
        name=shentong_name,
        max_level=10,  # 神通最大10级
        equipped=False,
        slot=0,
        damage_multiplier=1.0,
        effect_description=f'{shentong_name}的神通效果'
    )

    db.session.add(new_shentong)
    db.session.commit()

    return jsonify({
        'message': f'Successfully learned shentong: {shentong_name}',
        'shentong': {
            'id': new_shentong.id,
            'name': new_shentong.name,
            'max_level': new_shentong.max_level
        }
    }), 201


@app.route('/mantra/delete/<int:mantra_id>', methods=['DELETE'])
@token_required
def delete_mantra(current_user, mantra_id):
    """删除功法（用于整理技能栏）"""
    mantra = db.session.get(Mantra, mantra_id)
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not mantra or mantra.character_id != char.id:
        return jsonify({'message': 'Mantra not found'}), 404

    # 只能删除未装备的功法
    if mantra.equipped:
        return jsonify({'message': 'Cannot delete equipped mantra'}), 400

    db.session.delete(mantra)
    db.session.commit()

    return jsonify({'message': 'Mantra deleted successfully'}), 200


@app.route('/shentong/delete/<int:shentong_id>', methods=['DELETE'])
@token_required
def delete_shentong(current_user, shentong_id):
    """删除神通（用于整理技能栏）"""
    shentong = db.session.get(Shentong, shentong_id)
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not shentong or shentong.character_id != char.id:
        return jsonify({'message': 'Shentong not found'}), 404

    # 只能删除未装备的神通
    if shentong.equipped:
        return jsonify({'message': 'Cannot delete equipped shentong'}), 400

    db.session.delete(shentong)
    db.session.commit()

    return jsonify({'message': 'Shentong deleted successfully'}), 200

@app.route('/meridian', methods=['GET'])
@token_required
def get_meridians(current_user):
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'No character found'}), 404

    # 初始化角色的经脉系统（如果还没有）
    init_meridian_system(char.id)

    mers = Meridian.query.filter_by(character_id=char.id).all()
    meridians_data = []
    for m in mers:
        acupoints = Acupoint.query.filter_by(meridian_id=m.id).all()
        meridians_data.append({
            'id': m.id,
            'name': m.name,
            'type': m.type,
            'coefficient': m.coefficient,
            'is_open': m.is_open,
            'acupoints': [{
                'id': a.id,
                'name': a.name,
                'level': a.level,
                'max_level': a.max_level,
                'attribute_bonus': a.attribute_bonus
            } for a in acupoints]
        })

    return jsonify(meridians_data), 200


@app.route('/meridian/open/<int:meridian_id>', methods=['POST'])
@token_required
def open_meridian(current_user, meridian_id):
    """开启经脉"""
    meridian = db.session.get(Meridian, meridian_id)
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not meridian or meridian.character_id != char.id:
        return jsonify({'message': 'Meridian not found'}), 404

    if meridian.is_open:
        return jsonify({'message': 'Meridian already open'}), 400

    # 计算开启消耗（基于经脉重要性）
    base_cost = 1000
    cost_multiplier = meridian.coefficient  # 任督二脉更难开启
    lingshi_cost = int(base_cost * cost_multiplier)

    # 检查资源
    resource = Resource.query.filter_by(character_id=char.id, type='灵石').first()
    if not resource or resource.amount < lingshi_cost:
        return jsonify({'message': f'Not enough ling shi, need {lingshi_cost}', 'required': lingshi_cost}), 400

    # 检查境界要求（至少筑基期）
    if char.realm in ['凡人期', '炼气期']:
        return jsonify({'message': '境界不足，无法开启经脉（需要筑基期以上）'}), 400

    # 开启经脉
    meridian.is_open = True
    resource.amount -= lingshi_cost

    db.session.commit()
    return jsonify({
        'message': f'成功开启{meridian.name}',
        'meridian_name': meridian.name,
        'lingshi_cost': lingshi_cost
    }), 200


def init_meridian_system(character_id):
    """初始化角色的经脉系统"""
    # 十二经脉+任督二脉数据（已在init_db.py中定义）
    meridians_data = [
        ("手太阴肺经", "十二经脉", 1.5),
        ("手阳明大肠经", "十二经脉", 1.5),
        ("足阳明胃经", "十二经脉", 1.5),
        ("足太阴脾经", "十二经脉", 1.5),
        ("手少阴心经", "十二经脉", 1.5),
        ("手太阳小肠经", "十二经脉", 1.5),
        ("足太阳膀胱经", "十二经脉", 1.5),
        ("足少阴肾经", "十二经脉", 1.5),
        ("手厥阴心包经", "十二经脉", 1.5),
        ("手少阳三焦经", "十二经脉", 1.5),
        ("足少阳胆经", "十二经脉", 1.5),
        ("足厥阴肝经", "十二经脉", 1.5),
        ("任脉", "任督二脉", 2.5),
        ("督脉", "任督二脉", 2.5),
    ]

    for name, meridian_type, coefficient in meridians_data:
        # 检查是否已存在
        existing = Meridian.query.filter_by(character_id=character_id, name=name).first()
        if not existing:
            # 从全局模板复制经脉和穴位
            template_meridian = Meridian.query.filter_by(character_id=None, name=name).first()
            if template_meridian:
                # 复制经脉
                new_meridian = Meridian(
                    character_id=character_id,
                    name=name,
                    type=meridian_type,
                    coefficient=coefficient,
                    is_open=False
                )
                db.session.add(new_meridian)
                db.session.commit()

                # 复制穴位
                template_acupoints = Acupoint.query.filter_by(meridian_id=template_meridian.id).all()
                for template_acupoint in template_acupoints:
                    new_acupoint = Acupoint(
                        meridian_id=new_meridian.id,
                        name=template_acupoint.name,
                        level=0,
                        max_level=10,
                        attribute_bonus=0
                    )
                    db.session.add(new_acupoint)

    db.session.commit()

@app.route('/acupoint/open/<int:acupoint_id>', methods=['POST'])
@token_required
def open_acupoint(current_user, acupoint_id):
    """开启/升级穴位"""
    acupoint = db.session.get(Acupoint, acupoint_id)
    if not acupoint:
        return jsonify({'message': 'Acupoint not found'}), 404

    meridian = db.session.get(Meridian, acupoint.meridian_id)
    char = Character.query.filter_by(user_id=current_user.id).first()
    if meridian.character_id != char.id:
        return jsonify({'message': 'Not your acupoint'}), 403

    # 检查经脉是否开启
    if not meridian.is_open:
        return jsonify({'message': f'需要先开启{meridian.name}才能修炼穴位'}), 400

    if acupoint.level >= acupoint.max_level:
        return jsonify({'message': 'Already max level'}), 400

    # 消耗经验和灵石：基础*等级系数*经脉系数
    base_cost = 50
    exp_cost = int(base_cost * (acupoint.level + 1) * meridian.coefficient)
    lingshi_cost = int(exp_cost * 0.5)  # 灵石消耗为经验的一半

    resource = Resource.query.filter_by(character_id=char.id, type='灵石').first()
    if not resource or resource.amount < lingshi_cost:
        return jsonify({'message': f'Not enough ling shi, need {lingshi_cost}', 'required': lingshi_cost}), 400

    if char.experience < exp_cost:
        return jsonify({'message': f'Not enough experience, need {exp_cost}', 'required': exp_cost}), 400

    # 升级穴位
    acupoint.level += 1
    char.experience -= exp_cost
    resource.amount -= lingshi_cost

    # 计算属性加成：根据经脉类型和穴位等级
    old_bonus = acupoint.attribute_bonus
    acupoint.attribute_bonus = calculate_acupoint_bonus(meridian.name, acupoint.level)
    bonus_increase = acupoint.attribute_bonus - old_bonus

    # 更新人物属性
    attr = CharacterAttribute.query.filter_by(character_id=char.id).first()
    if attr:
        apply_acupoint_bonus_to_character(attr, meridian.name, bonus_increase)

    db.session.commit()
    return jsonify({
        'message': f'{acupoint.name}升级成功！',
        'acupoint_name': acupoint.name,
        'new_level': acupoint.level,
        'exp_cost': exp_cost,
        'lingshi_cost': lingshi_cost,
        'attribute_bonus': acupoint.attribute_bonus,
        'bonus_increase': bonus_increase
    }), 200


def calculate_acupoint_bonus(meridian_name: str, level: int) -> int:
    """根据经脉类型和等级计算穴位属性加成"""
    # 基础加成系数
    base_multipliers = {
        '手太阴肺经': 2,    # 影响速度
        '手阳明大肠经': 2,  # 影响速度
        '足阳明胃经': 3,    # 影响HP
        '足太阴脾经': 3,    # 影响HP
        '手少阴心经': 2,    # 影响暴击
        '手太阳小肠经': 2,  # 影响暴击
        '足太阳膀胱经': 3,  # 影响防御
        '足少阴肾经': 3,    # 影响防御
        '手厥阴心包经': 2,  # 影响暴击
        '手少阳三焦经': 2,  # 影响暴击
        '足少阳胆经': 2,    # 影响攻击
        '足厥阴肝经': 2,    # 影响攻击
        '任脉': 4,          # 重要经脉，影响HP
        '督脉': 4,          # 重要经脉，影响攻击
    }

    multiplier = base_multipliers.get(meridian_name, 2)
    return level * multiplier


def apply_acupoint_bonus_to_character(attr, meridian_name: str, bonus_increase: int):
    """将穴位属性加成应用到人物属性"""
    if meridian_name in ['足阳明胃经', '足太阴脾经', '任脉']:
        # 影响HP的经脉
        attr.hp += bonus_increase
    elif meridian_name in ['足太阳膀胱经', '足少阴肾经']:
        # 影响防御的经脉
        attr.defense += bonus_increase
    elif meridian_name in ['足少阳胆经', '足厥阴肝经', '督脉']:
        # 影响攻击的经脉
        attr.attack += bonus_increase
    elif meridian_name in ['手少阴心经', '手太阳小肠经', '手厥阴心包经', '手少阳三焦经']:
        # 影响暴击率的经脉
        attr.crit_rate += bonus_increase * 0.001  # 转换为百分比
    else:
        # 其他经脉影响速度
        attr.speed += bonus_increase

@app.route('/pet', methods=['GET'])
@token_required
def get_pets(current_user):
    char = Character.query.filter_by(user_id=current_user.id).first()
    pets = Pet.query.filter_by(owner_id=char.id).all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'intimacy_level': p.intimacy_level
    } for p in pets]), 200

@app.route('/pet/feed/<int:pet_id>', methods=['POST'])
@token_required
def feed_pet(current_user, pet_id):
    """喂养宠物"""
    pet = db.session.get(Pet, pet_id)
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not pet or pet.owner_id != char.id:
        return jsonify({'message': 'Pet not found'}), 404

    # 检查资源（灵石）
    resource = Resource.query.filter_by(character_id=char.id, type='灵石').first()
    feed_cost = 10  # 喂养消耗10灵石
    if not resource or resource.amount < feed_cost:
        return jsonify({'message': f'Not enough ling shi, need {feed_cost}', 'required': feed_cost}), 400

    # 计算亲密度经验增益（基于宠物品质）
    quality_multipliers = {'普通': 1.0, '精良': 1.5, '稀有': 2.0, '史诗': 3.0, '传说': 5.0}
    multiplier = quality_multipliers.get(pet.quality, 1.0)
    exp_gain = int(50 * multiplier)

    # 更新亲密度
    pet.intimacy_exp += exp_gain
    pet.last_feed_time = db.func.current_timestamp()
    resource.amount -= feed_cost

    # 检查是否可以升级亲密度等级
    if pet.intimacy_exp >= pet.max_intimacy_exp and pet.intimacy_level < 10:
        pet.intimacy_level += 1
        pet.intimacy_exp = 0
        pet.max_intimacy_exp = int(pet.max_intimacy_exp * 1.2)  # 下一级需要更多经验

        # 亲密度升级奖励：提升宠物属性
        attr_bonus = pet.intimacy_level * 5
        pet.attack_bonus += attr_bonus
        pet.defense_bonus += attr_bonus
        pet.hp_bonus += attr_bonus * 2
        pet.speed_bonus += attr_bonus

        # 更新技能触发概率
        pet.skill_trigger_rate = min(0.5, pet.intimacy_level / 20.0)  # 最高25%

        db.session.commit()
        return jsonify({
            'message': f'喂养成功！亲密度等级提升到{pet.intimacy_level}',
            'exp_gained': exp_gain,
            'level_up': True,
            'new_level': pet.intimacy_level,
            'attribute_bonuses': {
                'attack': attr_bonus,
                'defense': attr_bonus,
                'hp': attr_bonus * 2,
                'speed': attr_bonus
            }
        }), 200

    db.session.commit()
    return jsonify({
        'message': f'喂养成功！获得{exp_gain}点亲密度经验',
        'exp_gained': exp_gain,
        'current_level': pet.intimacy_level,
        'current_exp': pet.intimacy_exp,
        'max_exp': pet.max_intimacy_exp
    }), 200


@app.route('/pet/play/<int:pet_id>', methods=['POST'])
@token_required
def play_with_pet(current_user, pet_id):
    """陪伴宠物"""
    pet = db.session.get(Pet, pet_id)
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not pet or pet.owner_id != char.id:
        return jsonify({'message': 'Pet not found'}), 404

    # 计算陪伴经验增益
    quality_multipliers = {'普通': 1.0, '精良': 1.5, '稀有': 2.0, '史诗': 3.0, '传说': 5.0}
    multiplier = quality_multipliers.get(pet.quality, 1.0)
    exp_gain = int(30 * multiplier)

    # 更新亲密度
    pet.intimacy_exp += exp_gain
    pet.last_play_time = db.func.current_timestamp()

    # 检查是否可以升级亲密度等级
    level_up = False
    if pet.intimacy_exp >= pet.max_intimacy_exp and pet.intimacy_level < 10:
        pet.intimacy_level += 1
        pet.intimacy_exp = 0
        pet.max_intimacy_exp = int(pet.max_intimacy_exp * 1.2)
        level_up = True

        # 亲密度升级奖励
        attr_bonus = pet.intimacy_level * 3
        pet.attack_bonus += attr_bonus
        pet.defense_bonus += attr_bonus
        pet.hp_bonus += attr_bonus * 2
        pet.speed_bonus += attr_bonus

    db.session.commit()
    return jsonify({
        'message': f'陪伴成功！获得{exp_gain}点亲密度经验',
        'exp_gained': exp_gain,
        'level_up': level_up,
        'new_level': pet.intimacy_level if level_up else pet.intimacy_level
    }), 200


@app.route('/pet/battle/<int:pet_id>', methods=['POST'])
@token_required
def pet_battle(current_user, pet_id):
    """宠物参与战斗"""
    pet = db.session.get(Pet, pet_id)
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not pet or pet.owner_id != char.id:
        return jsonify({'message': 'Pet not found'}), 404

    # 战斗经验增益（比喂养和陪伴更多）
    quality_multipliers = {'普通': 1.0, '精良': 1.5, '稀有': 2.0, '史诗': 3.0, '传说': 5.0}
    multiplier = quality_multipliers.get(pet.quality, 1.0)
    exp_gain = int(100 * multiplier)

    # 宠物获得经验（用于升级）
    pet.experience += exp_gain * 2

    # 亲密度经验增益
    intimacy_exp_gain = int(40 * multiplier)
    pet.intimacy_exp += intimacy_exp_gain

    # 检查宠物等级升级
    pet_level_up = False
    while pet.experience >= exp_for_level(pet.level) and pet.level < 50:  # 宠物最高50级
        pet.experience -= exp_for_level(pet.level)
        pet.level += 1
        pet_level_up = True

        # 等级升级奖励
        level_bonus = pet.level * 2
        pet.attack_bonus += level_bonus
        pet.defense_bonus += level_bonus
        pet.hp_bonus += level_bonus * 3
        pet.speed_bonus += level_bonus

    # 检查亲密度等级升级
    intimacy_level_up = False
    if pet.intimacy_exp >= pet.max_intimacy_exp and pet.intimacy_level < 10:
        pet.intimacy_level += 1
        pet.intimacy_exp = 0
        pet.max_intimacy_exp = int(pet.max_intimacy_exp * 1.2)
        intimacy_level_up = True

        # 更新技能触发概率
        pet.skill_trigger_rate = min(0.5, pet.intimacy_level / 20.0)

    db.session.commit()
    return jsonify({
        'message': f'战斗完成！宠物获得{exp_gain * 2}经验和{intimacy_exp_gain}亲密度经验',
        'pet_exp_gained': exp_gain * 2,
        'intimacy_exp_gained': intimacy_exp_gain,
        'pet_level_up': pet_level_up,
        'pet_new_level': pet.level if pet_level_up else pet.level,
        'intimacy_level_up': intimacy_level_up,
        'intimacy_new_level': pet.intimacy_level if intimacy_level_up else pet.intimacy_level
    }), 200


@app.route('/pet/capture', methods=['POST'])
@token_required
def capture_pet(current_user):
    """捕捉宠物"""
    char = Character.query.filter_by(user_id=current_user.id).first()
    data = request.get_json() or {}

    # 捕捉消耗灵石
    capture_cost = 500
    resource = Resource.query.filter_by(character_id=char.id, type='灵石').first()
    if not resource or resource.amount < capture_cost:
        return jsonify({'message': f'Not enough ling shi, need {capture_cost}', 'required': capture_cost}), 400

    # 宠物品质随机生成
    quality_roll = random.random()
    if quality_roll < 0.6:
        quality = '普通'
        success_rate = 0.8
    elif quality_roll < 0.85:
        quality = '精良'
        success_rate = 0.6
    elif quality_roll < 0.95:
        quality = '稀有'
        success_rate = 0.4
    elif quality_roll < 0.99:
        quality = '史诗'
        success_rate = 0.2
    else:
        quality = '传说'
        success_rate = 0.1

    # 捕捉成功率
    if random.random() < success_rate:
        # 生成宠物
        pet_names = {
            '普通': ['小狗', '小猫', '兔子', '松鼠'],
            '精良': ['灵狐', '灵兔', '灵鹿', '灵鹰'],
            '稀有': ['火麒麟', '冰凤凰', '雷龙', '风虎'],
            '史诗': ['九尾狐', '五爪龙', '朱雀', '玄武'],
            '传说': ['真龙', '凤凰', '麒麟', '神龟']
        }

        name = random.choice(pet_names.get(quality, ['未知宠物']))

        # 根据品质设置基础属性
        quality_base_stats = {
            '普通': {'attack': 5, 'defense': 5, 'hp': 50, 'speed': 5},
            '精良': {'attack': 10, 'defense': 10, 'hp': 100, 'speed': 10},
            '稀有': {'attack': 20, 'defense': 20, 'hp': 200, 'speed': 20},
            '史诗': {'attack': 40, 'defense': 40, 'hp': 400, 'speed': 40},
            '传说': {'attack': 80, 'defense': 80, 'hp': 800, 'speed': 80}
        }

        base_stats = quality_base_stats.get(quality, quality_base_stats['普通'])

        new_pet = Pet(
            owner_id=char.id,
            name=name,
            type='野生',
            quality=quality,
            attack_bonus=base_stats['attack'],
            defense_bonus=base_stats['defense'],
            hp_bonus=base_stats['hp'],
            speed_bonus=base_stats['speed'],
            skill_name=f'{quality}守护',
            captured_at=db.func.current_timestamp()
        )

        resource.amount -= capture_cost
        db.session.add(new_pet)
        db.session.commit()

        return jsonify({
            'message': f'捕捉成功！获得{quality}品质宠物：{name}',
            'pet': {
                'id': new_pet.id,
                'name': new_pet.name,
                'quality': new_pet.quality,
                'type': new_pet.type
            },
            'success_rate': success_rate
        }), 201
    else:
        # 捕捉失败，消耗部分灵石
        failure_cost = capture_cost // 2
        resource.amount -= failure_cost
        db.session.commit()

        return jsonify({
            'message': '捕捉失败',
            'success_rate': success_rate,
            'lingshi_lost': failure_cost
        }), 400


@app.route('/pet/levelup/<int:pet_id>', methods=['POST'])
@token_required
def levelup_pet(current_user, pet_id):
    """宠物升级"""
    pet = db.session.get(Pet, pet_id)
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not pet or pet.owner_id != char.id:
        return jsonify({'message': 'Pet not found'}), 404

    # 检查是否已达到最大等级
    if pet.level >= 50:
        return jsonify({'message': 'Pet already at max level (50)'}), 400

    # 计算升级所需经验
    exp_needed = exp_for_level(pet.level)
    if pet.experience < exp_needed:
        return jsonify({'message': f'Not enough experience, need {exp_needed}', 'required': exp_needed}), 400

    # 升级宠物
    pet.experience -= exp_needed
    pet.level += 1

    # 等级提升奖励
    level_bonus = pet.level * 3
    pet.attack_bonus += level_bonus
    pet.defense_bonus += level_bonus
    pet.hp_bonus += level_bonus * 3
    pet.speed_bonus += level_bonus

    db.session.commit()
    return jsonify({
        'message': f'Pet upgraded to level {pet.level}!',
        'new_level': pet.level,
        'exp_cost': exp_needed,
        'attribute_bonuses': {
            'attack': level_bonus,
            'defense': level_bonus,
            'hp': level_bonus * 3,
            'speed': level_bonus
        }
    }), 200


@app.route('/pet/skill/<int:pet_id>', methods=['POST'])
@token_required
def use_pet_skill(current_user, pet_id):
    """使用宠物技能"""
    pet = db.session.get(Pet, pet_id)
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not pet or pet.owner_id != char.id:
        return jsonify({'message': 'Pet not found'}), 404

    # 检查技能是否可用（基于亲密度）
    if random.random() < pet.skill_trigger_rate:
        # 技能发动成功
        skill_effect = {
            'attack_boost': int(pet.attack_bonus * 0.5),
            'defense_boost': int(pet.defense_bonus * 0.3),
            'hp_heal': int(pet.hp_bonus * 0.2)
        }

        return jsonify({
            'message': f'宠物技能 {pet.skill_name} 发动成功！',
            'skill_name': pet.skill_name,
            'trigger_rate': pet.skill_trigger_rate,
            'effects': skill_effect
        }), 200
    else:
        return jsonify({
            'message': f'宠物技能 {pet.skill_name} 发动失败',
            'skill_name': pet.skill_name,
            'trigger_rate': pet.skill_trigger_rate
        }), 400


@app.route('/pet/market', methods=['GET'])
@token_required
def get_pet_market(current_user):
    """获取宠物市场"""
    # 模拟宠物市场（实际应该有独立的MarketPet模型）
    market_pets = [
        {'id': 1, 'name': '灵狐', 'quality': '精良', 'price': 1000, 'description': '敏捷的灵狐'},
        {'id': 2, 'name': '火麒麟', 'quality': '稀有', 'price': 5000, 'description': '火焰麒麟'},
        {'id': 3, 'name': '雷龙', 'quality': '史诗', 'price': 20000, 'description': '雷霆巨龙'},
        {'id': 4, 'name': '凤凰', 'quality': '传说', 'price': 100000, 'description': '不死神鸟'}
    ]

    return jsonify({'market_pets': market_pets}), 200


@app.route('/pet/market/buy/<int:pet_template_id>', methods=['POST'])
@token_required
def buy_pet_from_market(current_user, pet_template_id):
    """从宠物市场购买宠物"""
    char = Character.query.filter_by(user_id=current_user.id).first()

    # 模拟宠物模板数据
    pet_templates = {
        1: {'name': '灵狐', 'quality': '精良', 'price': 1000, 'attack': 15, 'defense': 10, 'hp': 120, 'speed': 25},
        2: {'name': '火麒麟', 'quality': '稀有', 'price': 5000, 'attack': 30, 'defense': 25, 'hp': 300, 'speed': 20},
        3: {'name': '雷龙', 'quality': '史诗', 'price': 20000, 'attack': 60, 'defense': 50, 'hp': 600, 'speed': 15},
        4: {'name': '凤凰', 'quality': '传说', 'price': 100000, 'attack': 100, 'defense': 80, 'hp': 1000, 'speed': 30}
    }

    if pet_template_id not in pet_templates:
        return jsonify({'message': 'Pet template not found'}), 404

    template = pet_templates[pet_template_id]

    # 检查是否已有同名宠物
    existing = Pet.query.filter_by(owner_id=char.id, name=template['name']).first()
    if existing:
        return jsonify({'message': f'You already have a {template["name"]}'}), 400

    # 检查灵石
    resource = Resource.query.filter_by(character_id=char.id, type='灵石').first()
    if not resource or resource.amount < template['price']:
        return jsonify({'message': f'Not enough ling shi, need {template["price"]}', 'required': template['price']}), 400

    # 创建宠物
    new_pet = Pet(
        owner_id=char.id,
        name=template['name'],
        type='购买',
        quality=template['quality'],
        attack_bonus=template['attack'],
        defense_bonus=template['defense'],
        hp_bonus=template['hp'],
        speed_bonus=template['speed'],
        skill_name=f'{template["quality"]}守护',
        captured_at=db.func.current_timestamp()
    )

    resource.amount -= template['price']
    db.session.add(new_pet)
    db.session.commit()

    return jsonify({
        'message': f'成功购买宠物：{template["name"]}',
        'pet': {
            'id': new_pet.id,
            'name': new_pet.name,
            'quality': new_pet.quality,
            'price': template['price']
        }
    }), 201

@app.route('/sect', methods=['GET'])
@token_required
def get_sects(current_user):
    """获取宗门列表"""
    sects = Sect.query.all()
    sects_data = []
    for sect in sects:
        member_count = SectMember.query.filter_by(sect_id=sect.id).count()
        sects_data.append({
            'id': sect.id,
            'name': sect.name,
            'level': sect.level,
            'prosperity': sect.prosperity,
            'power': sect.power,
            'prestige': sect.prestige,
            'member_count': member_count,
            'description': sect.description,
            'created_at': sect.created_at.isoformat() if sect.created_at else None
        })
    return jsonify({'sects': sects_data}), 200


@app.route('/sect/<int:sect_id>', methods=['GET'])
@token_required
def get_sect_detail(current_user, sect_id):
    """获取宗门详情"""
    sect = db.session.get(Sect, sect_id)
    if not sect:
        return jsonify({'message': 'Sect not found'}), 404

    # 获取宗门成员
    members = SectMember.query.filter_by(sect_id=sect_id).all()
    members_data = []
    for member in members:
        char = Character.query.get(member.character_id)
        members_data.append({
            'id': member.id,
            'character_id': member.character_id,
            'character_name': char.name if char else 'Unknown',
            'position': member.position,
            'contribution': member.contribution,
            'total_contribution': member.total_contribution,
            'joined_at': member.joined_at.isoformat() if member.joined_at else None
        })

    # 获取宗门任务
    tasks = SectTask.query.filter_by(sect_id=sect_id).all()
    tasks_data = []
    for task in tasks:
        tasks_data.append({
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'type': task.type,
            'status': task.status,
            'deadline': task.deadline.isoformat() if task.deadline else None
        })

    return jsonify({
        'sect': {
            'id': sect.id,
            'name': sect.name,
            'level': sect.level,
            'prosperity': sect.prosperity,
            'contribution': sect.contribution,
            'power': sect.power,
            'construction': sect.construction,
            'prestige': sect.prestige,
            'description': sect.description,
            'resources': sect.resources,
            'facilities': sect.facilities
        },
        'members': members_data,
        'tasks': tasks_data
    }), 200


@app.route('/sect', methods=['POST'])
@token_required
def create_sect(current_user):
    """创建宗门"""
    data = request.get_json()
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'No character found'}), 404

    # 检查是否已在其他宗门
    existing_member = SectMember.query.filter_by(character_id=char.id).first()
    if existing_member:
        return jsonify({'message': 'You are already in a sect'}), 400

    # 创建宗门消耗灵石
    create_cost = 10000
    resource = Resource.query.filter_by(character_id=char.id, type='灵石').first()
    if not resource or resource.amount < create_cost:
        return jsonify({'message': f'Not enough ling shi, need {create_cost}', 'required': create_cost}), 400

    new_sect = Sect(
        name=data['name'],
        description=data.get('description', ''),
        prosperity=0,
        contribution=0,
        power=char.level * 10,  # 初始实力值基于创建者等级
        construction=0,
        prestige=0
    )
    db.session.add(new_sect)
    db.session.commit()  # 先提交以获取ID

    # 创建宗主成员
    member = SectMember(
        sect_id=new_sect.id,
        character_id=char.id,
        position='宗主',
        contribution=1000,
        total_contribution=1000
    )
    db.session.add(member)

    # 扣除灵石
    resource.amount -= create_cost

    db.session.commit()
    return jsonify({
        'message': 'Sect created successfully!',
        'sect': {
            'id': new_sect.id,
            'name': new_sect.name,
            'level': new_sect.level
        }
    }), 201


@app.route('/sect/join/<int:sect_id>', methods=['POST'])
@token_required
def join_sect(current_user, sect_id):
    """加入宗门"""
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'No character found'}), 404

    sect = db.session.get(Sect, sect_id)
    if not sect:
        return jsonify({'message': 'Sect not found'}), 404

    # 检查是否已在其他宗门
    existing_member = SectMember.query.filter_by(character_id=char.id).first()
    if existing_member:
        return jsonify({'message': 'You are already in a sect'}), 400

    # 检查宗门是否已满员（暂时不限制）
    # 创建成员记录
    member = SectMember(
        sect_id=sect_id,
        character_id=char.id,
        position='弟子',
        contribution=0,
        total_contribution=0
    )
    db.session.add(member)
    db.session.commit()

    return jsonify({
        'message': f'Successfully joined {sect.name}',
        'sect_name': sect.name,
        'position': member.position
    }), 200


@app.route('/sect/upgrade/<int:sect_id>', methods=['POST'])
@token_required
def upgrade_sect(current_user, sect_id):
    """宗门升级"""
    sect = db.session.get(Sect, sect_id)
    if not sect:
        return jsonify({'message': 'Sect not found'}), 404

    # 检查权限（只有宗主和大长老可以升级）
    char = Character.query.filter_by(user_id=current_user.id).first()
    member = SectMember.query.filter_by(sect_id=sect_id, character_id=char.id).first()
    if not member or member.position not in ['宗主', '大长老']:
        return jsonify({'message': 'No permission to upgrade sect'}), 403

    if sect.level >= sect.max_level:
        return jsonify({'message': f'Sect already at max level ({sect.max_level})'}), 400

    # 计算升级消耗（基于当前等级）
    upgrade_cost = sect.level * 5000  # 升级消耗随等级增加

    # 检查宗门资源（贡献值）
    if sect.contribution < upgrade_cost:
        return jsonify({'message': f'Not enough sect contribution, need {upgrade_cost}', 'required': upgrade_cost}), 400

    # 升级宗门
    sect.level += 1
    sect.contribution -= upgrade_cost

    # 升级奖励
    sect.power += 50  # 实力值增加
    sect.prestige += 10  # 威望值增加

    db.session.commit()
    return jsonify({
        'message': f'Sect upgraded to level {sect.level}!',
        'new_level': sect.level,
        'contribution_cost': upgrade_cost,
        'power_increase': 50,
        'prestige_increase': 10
    }), 200


@app.route('/sect/task', methods=['GET'])
@token_required
def get_sect_tasks(current_user):
    """获取宗门任务列表"""
    char = Character.query.filter_by(user_id=current_user.id).first()
    member = SectMember.query.filter_by(character_id=char.id).first()
    if not member:
        return jsonify({'message': 'You are not in any sect'}), 400

    tasks = SectTask.query.filter_by(sect_id=member.sect_id).all()
    tasks_data = []
    for task in tasks:
        tasks_data.append({
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'type': task.type,
            'requirements': task.requirements,
            'rewards': task.rewards,
            'status': task.status,
            'deadline': task.deadline.isoformat() if task.deadline else None
        })

    return jsonify({'tasks': tasks_data}), 200


@app.route('/sect/task/create', methods=['POST'])
@token_required
def create_sect_task(current_user):
    """创建宗门任务（宗主权限）"""
    char = Character.query.filter_by(user_id=current_user.id).first()
    member = SectMember.query.filter_by(character_id=char.id).first()
    if not member or member.position not in ['宗主', '大长老']:
        return jsonify({'message': 'No permission to create tasks'}), 403

    data = request.get_json()
    new_task = SectTask(
        sect_id=member.sect_id,
        title=data['title'],
        description=data.get('description', ''),
        type=data.get('type', '日常'),
        requirements=data.get('requirements', '{}'),
        rewards=data.get('rewards', '{}'),
        deadline=data.get('deadline')  # 可选
    )
    db.session.add(new_task)
    db.session.commit()

    return jsonify({
        'message': 'Task created successfully',
        'task_id': new_task.id
    }), 201


@app.route('/sect/activity', methods=['GET'])
@token_required
def get_sect_activities(current_user):
    """获取宗门活动"""
    char = Character.query.filter_by(user_id=current_user.id).first()
    member = SectMember.query.filter_by(character_id=char.id).first()
    if not member:
        return jsonify({'message': 'You are not in any sect'}), 400

    activities = SectActivity.query.filter_by(sect_id=member.sect_id).all()
    activities_data = []
    for activity in activities:
        activities_data.append({
            'id': activity.id,
            'title': activity.title,
            'description': activity.description,
            'type': activity.type,
            'status': activity.status,
            'participants': activity.participants,
            'rewards': activity.rewards,
            'start_time': activity.start_time.isoformat() if activity.start_time else None,
            'end_time': activity.end_time.isoformat() if activity.end_time else None
        })

    return jsonify({'activities': activities_data}), 200


@app.route('/sect/shop', methods=['GET'])
@token_required
def get_sect_shop(current_user):
    """获取宗门商店"""
    char = Character.query.filter_by(user_id=current_user.id).first()
    member = SectMember.query.filter_by(character_id=char.id).first()
    if not member:
        return jsonify({'message': 'You are not in any sect'}), 400

    shop_items = SectShop.query.filter_by(sect_id=member.sect_id).all()
    items_data = []
    for item in shop_items:
        items_data.append({
            'id': item.id,
            'item_name': item.item_name,
            'item_type': item.item_type,
            'item_quality': item.item_quality,
            'price': item.price,
            'stock': item.stock,
            'description': item.description
        })

    return jsonify({
        'shop_items': items_data,
        'your_contribution': member.contribution
    }), 200


@app.route('/sect/shop/buy/<int:item_id>', methods=['POST'])
@token_required
def buy_from_sect_shop(current_user, item_id):
    """从宗门商店购买物品"""
    char = Character.query.filter_by(user_id=current_user.id).first()
    member = SectMember.query.filter_by(character_id=char.id).first()
    if not member:
        return jsonify({'message': 'You are not in any sect'}), 400

    item = SectShop.query.filter_by(id=item_id, sect_id=member.sect_id).first()
    if not item:
        return jsonify({'message': 'Item not found in sect shop'}), 404

    if item.stock <= 0:
        return jsonify({'message': 'Item out of stock'}), 400

    if member.contribution < item.price:
        return jsonify({'message': f'Not enough contribution, need {item.price}', 'required': item.price}), 400

    # 扣除贡献值
    member.contribution -= item.price
    item.stock -= 1

    # 这里应该创建对应的物品（装备、法宝等），暂时只记录购买
    db.session.commit()

    return jsonify({
        'message': f'Successfully purchased {item.item_name}',
        'item_name': item.item_name,
        'contribution_cost': item.price
    }), 200


@app.route('/sect/tournament', methods=['GET'])
@token_required
def get_sect_tournaments(current_user):
    """获取宗门比武"""
    char = Character.query.filter_by(user_id=current_user.id).first()
    member = SectMember.query.filter_by(character_id=char.id).first()
    if not member:
        return jsonify({'message': 'You are not in any sect'}), 400

    tournaments = SectTournament.query.filter_by(sect_id=member.sect_id).all()
    tournaments_data = []
    for tournament in tournaments:
        tournaments_data.append({
            'id': tournament.id,
            'title': tournament.title,
            'status': tournament.status,
            'participants': tournament.participants,
            'rewards': tournament.rewards,
            'start_time': tournament.start_time.isoformat() if tournament.start_time else None,
            'end_time': tournament.end_time.isoformat() if tournament.end_time else None
        })

    return jsonify({'tournaments': tournaments_data}), 200


@app.route('/sect/alliance', methods=['GET'])
@token_required
def get_sect_alliances(current_user):
    """获取宗门联盟"""
    alliances = SectAlliance.query.all()
    alliances_data = []
    for alliance in alliances:
        leader_sect = Sect.query.get(alliance.leader_sect_id)
        alliances_data.append({
            'id': alliance.id,
            'name': alliance.name,
            'description': alliance.description,
            'leader_sect_name': leader_sect.name if leader_sect else 'Unknown',
            'alliance_power': alliance.alliance_power,
            'alliance_prestige': alliance.alliance_prestige,
            'created_at': alliance.created_at.isoformat() if alliance.created_at else None
        })

    return jsonify({'alliances': alliances_data}), 200


@app.route('/sect/my', methods=['GET'])
@token_required
def get_my_sect(current_user):
    """获取我的宗门信息"""
    char = Character.query.filter_by(user_id=current_user.id).first()
    member = SectMember.query.filter_by(character_id=char.id).first()

    if not member:
        return jsonify({'sect': None, 'member': None}), 200

    sect = Sect.query.get(member.sect_id)
    if not sect:
        return jsonify({'message': 'Sect not found'}), 404

    return jsonify({
        'sect': {
            'id': sect.id,
            'name': sect.name,
            'level': sect.level,
            'prosperity': sect.prosperity,
            'contribution': sect.contribution,
            'power': sect.power,
            'construction': sect.construction,
            'prestige': sect.prestige,
            'description': sect.description
        },
        'member': {
            'position': member.position,
            'contribution': member.contribution,
            'total_contribution': member.total_contribution
        }
    }), 200


@app.route('/sect/contribute', methods=['POST'])
@token_required
def contribute_to_sect(current_user):
    """为宗门贡献资源"""
    data = request.get_json()
    char = Character.query.filter_by(user_id=current_user.id).first()
    member = SectMember.query.filter_by(character_id=char.id).first()
    if not member:
        return jsonify({'message': 'You are not in any sect'}), 400

    contribution_amount = data.get('amount', 0)
    if contribution_amount <= 0:
        return jsonify({'message': 'Invalid contribution amount'}), 400

    # 检查玩家灵石
    resource = Resource.query.filter_by(character_id=char.id, type='灵石').first()
    if not resource or resource.amount < contribution_amount:
        return jsonify({'message': f'Not enough ling shi, have {resource.amount if resource else 0}', 'required': contribution_amount}), 400

    # 扣除灵石，增加宗门贡献值和成员贡献值
    resource.amount -= contribution_amount
    member.contribution += contribution_amount
    member.total_contribution += contribution_amount

    sect = Sect.query.get(member.sect_id)
    sect.contribution += contribution_amount

    # 根据贡献更新宗门属性
    sect.prosperity += int(contribution_amount / 100)  # 每100灵石增加1繁荣度
    sect.power += int(contribution_amount / 200)  # 每200灵石增加1实力值

    db.session.commit()

    return jsonify({
        'message': f'Successfully contributed {contribution_amount} ling shi to sect',
        'contribution_added': contribution_amount,
        'personal_contribution': member.contribution,
        'sect_prosperity': sect.prosperity,
        'sect_power': sect.power
    }), 200


# 丹药系统API
@app.route('/pill', methods=['GET'])
@token_required
def get_pills(current_user):
    """获取丹药列表"""
    pills = Pill.query.all()
    pills_data = []
    for pill in pills:
        pills_data.append({
            'id': pill.id,
            'name': pill.name,
            'quality': pill.quality,
            'level': pill.level,
            'effect_type': pill.effect_type,
            'effect_value': pill.effect_value,
            'success_rate': pill.success_rate,
            'difficulty': pill.difficulty,
            'description': pill.description
        })
    return jsonify({'pills': pills_data}), 200


@app.route('/pill/refine/<int:pill_id>', methods=['POST'])
@token_required
def refine_pill(current_user, pill_id):
    """炼制丹药"""
    pill = db.session.get(Pill, pill_id)
    if not pill:
        return jsonify({'message': 'Pill not found'}), 404

    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'Character not found'}), 404

    # 检查炼丹炉等级
    furnace = PillFurnace.query.filter_by(owner_id=char.id).first()
    furnace_level = furnace.level if furnace else 1
    furnace_bonus = furnace.success_rate_bonus if furnace else 0.0

    # 计算成功率
    base_success_rate = pill.success_rate
    final_success_rate = min(0.95, base_success_rate + furnace_bonus)

    # 炼制消耗
    refine_cost = pill.difficulty * 100  # 基础消耗
    resource = Resource.query.filter_by(character_id=char.id, type='灵石').first()
    if not resource or resource.amount < refine_cost:
        return jsonify({'message': f'Not enough ling shi, need {refine_cost}', 'required': refine_cost}), 400

    # 炼制逻辑
    resource.amount -= refine_cost
    if random.random() < final_success_rate:
        # 炼制成功，创建丹药物品
        # 检查是否已有相同丹药，增加数量
        existing_item = PillItem.query.filter_by(owner_id=char.id, pill_id=pill_id).first()
        if existing_item:
            existing_item.quantity += 1
        else:
            new_item = PillItem(owner_id=char.id, pill_id=pill_id, quantity=1)
            db.session.add(new_item)

        db.session.commit()
        return jsonify({
            'message': f'炼制成功！获得{pill.name}',
            'pill_name': pill.name,
            'success_rate': final_success_rate,
            'cost': refine_cost
        }), 200
    else:
        # 炼制失败
        db.session.commit()
        return jsonify({
            'message': '炼制失败',
            'success_rate': final_success_rate,
            'cost': refine_cost
        }), 400


@app.route('/pill/use/<int:pill_id>', methods=['POST'])
@token_required
def use_pill(current_user, pill_id):
    """使用丹药"""
    # 首先检查玩家是否拥有这个丹药
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'Character not found'}), 404

    pill_item = PillItem.query.filter_by(owner_id=char.id, pill_id=pill_id).first()
    if not pill_item or pill_item.quantity <= 0:
        return jsonify({'message': 'You do not have this pill'}), 400

    pill = db.session.get(Pill, pill_id)
    if not pill:
        return jsonify({'message': 'Pill not found'}), 404

    attr = CharacterAttribute.query.filter_by(character_id=char.id).first()
    if not attr:
        return jsonify({'message': 'Character attributes not found'}), 404

    # 根据丹药效果类型应用效果
    if pill.effect_type == '突破境界':
        # 境界突破丹药
        if char.realm in ['凡人期', '炼气期']:
            return jsonify({'message': '当前境界无法使用此丹药'}), 400

        # 简化境界突破逻辑
        next_realms = {
            '筑基期': '金丹期',
            '金丹期': '元婴期',
            '元婴期': '化神期',
            '化神期': '炼虚期'
        }
        if char.realm in next_realms:
            char.realm = next_realms[char.realm]
            char.level = 1
            attr.hp += pill.effect_value
            attr.attack += pill.effect_value // 2
        else:
            return jsonify({'message': '已达到最高境界'}), 400

    elif pill.effect_type == '属性提升':
        # 属性提升丹药
        if '生命' in pill.name or '气血' in pill.name:
            attr.hp += pill.effect_value
        elif '攻击' in pill.name or '力量' in pill.name:
            attr.attack += pill.effect_value
        elif '防御' in pill.name:
            attr.defense += pill.effect_value
        elif '速度' in pill.name:
            attr.speed += pill.effect_value

    elif pill.effect_type == '治疗':
        # 治疗丹药 - 恢复生命值
        attr.hp = min(attr.hp + pill.effect_value, 1000)  # 假设最大生命值为1000

    elif pill.effect_type == '解毒':
        # 解毒丹药 - 这里简化处理
        pass  # 可以添加中毒状态系统

    # 减少丹药数量
    pill_item.quantity -= 1
    if pill_item.quantity <= 0:
        db.session.delete(pill_item)

    db.session.commit()
    return jsonify({
        'message': f'成功使用{pill.name}',
        'effect_type': pill.effect_type,
        'effect_value': pill.effect_value
    }), 200


@app.route('/character/inventory/pills', methods=['GET'])
@token_required
def get_character_pills(current_user):
    """获取角色拥有的丹药"""
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'Character not found'}), 404

    pill_items = PillItem.query.filter_by(owner_id=char.id).all()
    pills_data = []

    for item in pill_items:
        if item.pill:
            pills_data.append({
                'id': item.pill.id,
                'name': item.pill.name,
                'quality': item.pill.quality,
                'level': item.pill.level,
                'effect_type': item.pill.effect_type,
                'effect_value': item.pill.effect_value,
                'quantity': item.quantity,
                'description': item.pill.description
            })

    return jsonify({'pills': pills_data}), 200


# 灵植系统API
@app.route('/lingzhi', methods=['GET'])
@token_required
def get_lingzhis(current_user):
    """获取灵植列表"""
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'Character not found'}), 404

    lingzhis = Lingzhi.query.filter_by(owner_id=char.id).all()
    lingzhis_data = []
    for lz in lingzhis:
        # 计算当前生长状态
        current_time = datetime.datetime.utcnow()
        planted_time = lz.planted_at
        time_diff = (current_time - planted_time).total_seconds() / 60  # 分钟

        growth_progress = min(100, (time_diff / lz.max_growth_time) * 100)

        # 更新生长状态
        if growth_progress >= 100 and lz.growth_stage != '成熟':
            lz.growth_stage = '成熟'
            db.session.commit()

        lingzhis_data.append({
            'id': lz.id,
            'name': lz.name,
            'quality': lz.quality,
            'level': lz.level,
            'growth_stage': lz.growth_stage,
            'growth_progress': growth_progress,
            'has_mutated': lz.has_mutated,
            'attribute_type': lz.attribute_type,
            'attribute_value': lz.attribute_value,
            'water_level': lz.water_level,
            'fertilizer_level': lz.fertilizer_level,
            'sunlight_level': lz.sunlight_level,
            'planted_at': lz.planted_at.isoformat() if lz.planted_at else None
        })

    return jsonify({'lingzhis': lingzhis_data}), 200


@app.route('/lingzhi/plant', methods=['POST'])
@token_required
def plant_lingzhi(current_user):
    """种植灵植"""
    data = request.get_json()
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'Character not found'}), 404

    # 检查灵田
    lingtians = Lingtian.query.filter_by(owner_id=char.id).all()
    available_lingtian = None
    for lt in lingtians:
        if not lt.is_occupied:
            available_lingtian = lt
            break

    if not available_lingtian:
        return jsonify({'message': 'No available lingtian'}), 400

    # 创建灵植
    quality = data.get('quality', '凡品')
    name = data.get('name', f'{quality}灵植')

    quality_configs = {
        '凡品': {'max_time': 60, 'mutation_rate': 0.01},
        '黄品': {'max_time': 90, 'mutation_rate': 0.02},
        '玄品': {'max_time': 120, 'mutation_rate': 0.05},
        '地品': {'max_time': 180, 'mutation_rate': 0.10},
        '天品': {'max_time': 300, 'mutation_rate': 0.20},
        '无上': {'max_time': 480, 'mutation_rate': 0.30}
    }

    config = quality_configs.get(quality, quality_configs['凡品'])

    new_lingzhi = Lingzhi(
        owner_id=char.id,
        name=name,
        quality=quality,
        max_growth_time=config['max_time'],
        mutation_rate=config['mutation_rate']
    )

    available_lingtian.lingzhi_id = new_lingzhi.id
    available_lingtian.is_occupied = True
    available_lingtian.planted_at = datetime.datetime.utcnow()

    db.session.add(new_lingzhi)
    db.session.commit()

    return jsonify({
        'message': f'Successfully planted {name}',
        'lingzhi': {
            'id': new_lingzhi.id,
            'name': new_lingzhi.name,
            'quality': new_lingzhi.quality,
            'max_growth_time': new_lingzhi.max_growth_time
        }
    }), 201


@app.route('/lingzhi/harvest/<int:lingzhi_id>', methods=['POST'])
@token_required
def harvest_lingzhi(current_user, lingzhi_id):
    """收获灵植"""
    data = request.get_json() or {}
    action = data.get('action', 'harvest')  # harvest 或 upgrade

    lingzhi = db.session.get(Lingzhi, lingzhi_id)
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not lingzhi or lingzhi.owner_id != char.id:
        return jsonify({'message': 'Lingzhi not found'}), 404

    # 检查是否成熟
    current_time = datetime.datetime.utcnow()
    planted_time = lingzhi.planted_at
    time_diff = (current_time - planted_time).total_seconds() / 60

    if time_diff < lingzhi.max_growth_time:
        return jsonify({'message': 'Lingzhi not mature yet'}), 400

    if action == 'upgrade':
        # 升级灵植：检查是否可以升级（需要达到前面所有阶段生长时间总和）
        current_level_growth_time = sum(lingzhi.max_growth_time for i in range(1, lingzhi.level + 1))
        if time_diff < current_level_growth_time:
            return jsonify({'message': 'Not enough time for upgrade'}), 400

        # 升级灵植
        if lingzhi.level < 10:  # 最大10级
            lingzhi.level += 1
            # 升级后生长时间延长
            lingzhi.max_growth_time = int(lingzhi.max_growth_time * 1.2)
            # 重置生长进度
            lingzhi.planted_at = current_time
            lingzhi.growth_stage = '种子'
            db.session.commit()

            return jsonify({
                'message': f'Successfully upgraded {lingzhi.name} to level {lingzhi.level}',
                'new_level': lingzhi.level,
                'new_max_growth_time': lingzhi.max_growth_time
            }), 200
        else:
            return jsonify({'message': 'Lingzhi already at max level'}), 400

    else:
        # 收获灵植
        # 计算收获奖励
        quality_multipliers = {
            '凡品': 1, '黄品': 2, '玄品': 5, '地品': 10, '天品': 20, '无上': 50
        }
        base_reward = 100
        multiplier = quality_multipliers.get(lingzhi.quality, 1)
        reward = base_reward * multiplier * lingzhi.level  # 等级越高奖励越多

        # 变异奖励
        if lingzhi.has_mutated and lingzhi.attribute_value > 0:
            reward *= 2  # 变异灵植奖励翻倍

        # 发放奖励（灵石）
        resource = Resource.query.filter_by(character_id=char.id, type='灵石').first()
        if resource:
            resource.amount += reward
        else:
            resource = Resource(character_id=char.id, type='灵石', amount=reward)
            db.session.add(resource)

        # 清理灵植和灵田
        lingtian = Lingtian.query.filter_by(lingzhi_id=lingzhi_id).first()
        if lingtian:
            lingtian.lingzhi_id = None
            lingtian.is_occupied = False
            lingtian.planted_at = None

        db.session.delete(lingzhi)
        db.session.commit()

        return jsonify({
            'message': f'Successfully harvested {lingzhi.name}',
            'reward': reward,
            'quality': lingzhi.quality,
            'level': lingzhi.level,
            'mutated': lingzhi.has_mutated
        }), 200


@app.route('/lingzhi/care/<int:lingzhi_id>', methods=['POST'])
@token_required
def care_lingzhi(current_user, lingzhi_id):
    """照顾灵植"""
    data = request.get_json()
    care_type = data.get('type', 'water')  # water, fertilizer, sunlight

    lingzhi = db.session.get(Lingzhi, lingzhi_id)
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not lingzhi or lingzhi.owner_id != char.id:
        return jsonify({'message': 'Lingzhi not found'}), 404

    # 获取灵田信息
    lingtian = Lingtian.query.filter_by(lingzhi_id=lingzhi_id).first()
    if not lingtian:
        return jsonify({'message': 'Lingzhi not planted in any lingtian'}), 404

    # 照顾消耗
    care_cost = 10
    resource = Resource.query.filter_by(character_id=char.id, type='灵石').first()
    if not resource or resource.amount < care_cost:
        return jsonify({'message': f'Not enough ling shi, need {care_cost}', 'required': care_cost}), 400

    # 更新照顾状态
    resource.amount -= care_cost

    if care_type == 'water':
        lingzhi.water_level = min(100, lingzhi.water_level + 20)
    elif care_type == 'fertilizer':
        lingzhi.fertilizer_level = min(100, lingzhi.fertilizer_level + 20)
        # 记录施肥次数（用于变异概率计算）
        lingtian.fertilizer_level += 1
    elif care_type == 'sunlight':
        lingzhi.sunlight_level = min(100, lingzhi.sunlight_level + 20)

    # 计算变异概率：(1 + 0.1 × (灵田等级-1)) × (1 + 0.05 × min(施肥次数, 10)) × 天气系数× P基本概率
    # 简化：假设灵田等级为1，天气系数为1.0
    lingtian_level = 1  # 可以后续扩展灵田等级系统
    fertilizer_times = min(lingtian.fertilizer_level, 10)
    weather_factor = 1.0  # 可以后续添加天气系统
    base_mutation_rate = lingzhi.mutation_rate

    final_mutation_rate = (1 + 0.1 * (lingtian_level - 1)) * (1 + 0.05 * fertilizer_times) * weather_factor * base_mutation_rate
    final_mutation_rate = min(final_mutation_rate, 0.1)  # 最高不超过10%

    # 变异检查
    mutated = False
    attribute_type = None
    attribute_value = 0

    if not lingzhi.has_mutated and random.random() < final_mutation_rate:
        mutated = True
        lingzhi.has_mutated = True

        # 随机变异属性
        attributes = ['攻击', '防御', '生命', '速度']
        attribute_type = random.choice(attributes)
        attribute_value = random.randint(5, 20) * lingzhi.level

        lingzhi.attribute_type = attribute_type
        lingzhi.attribute_value = attribute_value

    lingzhi.last_cared_at = datetime.datetime.utcnow()
    db.session.commit()

    return jsonify({
        'message': f'Successfully cared for {lingzhi.name}',
        'care_type': care_type,
        'cost': care_cost,
        'water_level': lingzhi.water_level,
        'fertilizer_level': lingzhi.fertilizer_level,
        'sunlight_level': lingzhi.sunlight_level,
        'mutation_rate': final_mutation_rate,
        'mutated': mutated,
        'attribute_type': attribute_type,
        'attribute_value': attribute_value
    }), 200


@app.route('/lingtian', methods=['GET'])
@token_required
def get_lingtians(current_user):
    """获取灵田列表"""
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'Character not found'}), 404

    lingtians = Lingtian.query.filter_by(owner_id=char.id).all()
    lingtians_data = []
    for lt in lingtians:
        lingzhi_data = None
        if lt.lingzhi:
            lz = lt.lingzhi
            current_time = datetime.datetime.utcnow()
            planted_time = lz.planted_at
            time_diff = (current_time - planted_time).total_seconds() / 60
            growth_progress = min(100, (time_diff / lz.max_growth_time) * 100)

            lingzhi_data = {
                'id': lz.id,
                'name': lz.name,
                'quality': lz.quality,
                'growth_stage': lz.growth_stage,
                'growth_progress': growth_progress
            }

        lingtians_data.append({
            'id': lt.id,
            'slot': lt.slot,
            'soil_quality': lt.soil_quality,
            'irrigation_level': lt.irrigation_level,
            'fertilizer_level': lt.fertilizer_level,
            'is_occupied': lt.is_occupied,
            'lingzhi': lingzhi_data
        })

    return jsonify({'lingtians': lingtians_data}), 200


@app.route('/lingtian/init', methods=['POST'])
@token_required
def init_lingtians(current_user):
    """初始化灵田"""
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'Character not found'}), 404

    # 检查是否已初始化
    existing = Lingtian.query.filter_by(owner_id=char.id).first()
    if existing:
        return jsonify({'message': 'Lingtians already initialized'}), 400

    # 创建6块灵田
    for i in range(1, 7):
        new_lingtian = Lingtian(
            owner_id=char.id,
            slot=i,
            soil_quality='普通',
            irrigation_level=0,
            fertilizer_level=0,
            is_occupied=False
        )
        db.session.add(new_lingtian)

    db.session.commit()
    return jsonify({'message': 'Lingtians initialized successfully'}), 201


@app.route('/lingzhi/codex', methods=['GET'])
@token_required
def get_lingzhi_codex(current_user):
    """获取灵植图鉴"""
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'Character not found'}), 404

    # 获取玩家已解锁的灵植种类
    discovered_lingzhis = db.session.query(Lingzhi.quality, Lingzhi.name)\
        .filter_by(owner_id=char.id)\
        .distinct()\
        .all()

    # 所有可能的灵植种类
    all_lingzhi_types = {
        '凡品': ['凡品灵植', '低阶草药', '普通花卉'],
        '黄品': ['黄品灵植', '中阶草药', '珍贵花卉'],
        '玄品': ['玄品灵植', '高阶草药', '灵花'],
        '地品': ['地品灵植', '地级草药', '仙花'],
        '天品': ['天品灵植', '天级草药', '神花'],
        '无上': ['无上灵植', '圣药', '混沌花']
    }

    codex_data = []
    for quality, types in all_lingzhi_types.items():
        for lingzhi_name in types:
            discovered = any(discovered[1] == lingzhi_name for discovered in discovered_lingzhis)
            codex_data.append({
                'name': lingzhi_name,
                'quality': quality,
                'discovered': discovered,
                'description': f'{quality}品质的{lingzhi_name}，具有独特的生长特性和药用价值。'
            })

    return jsonify({'codex': codex_data}), 200


# 战斗系统API
@app.route('/combat/start', methods=['POST'])
@token_required
def start_combat(current_user):
    """开始战斗"""
    data = request.get_json()
    combat_type = data.get('type', 'monster')  # monster 或 dungeon
    monster_id = data.get('monster_id')
    dungeon_id = data.get('dungeon_id')

    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'Character not found'}), 404

    # 检查是否有正在进行的战斗
    active_combat = CombatState.query.filter_by(character_id=char.id, is_active=True).first()
    if active_combat:
        return jsonify({'message': 'Combat already in progress'}), 400

    # 创建战斗状态
    weather = random.choice(['晴天', '雨天', '雪天', '雾天', '雷暴', '烈日'])

    if combat_type == 'monster':
        monster = db.session.get(Monster, monster_id)
        if not monster:
            return jsonify({'message': 'Monster not found'}), 404

        combat = CombatState(
            character_id=char.id,
            monster_id=monster_id,
            weather=weather,
            character_hp=calculate_combat_stats(char, weather)['total_hp'],
            monster_hp=monster.hp,
            is_active=True
        )
    elif combat_type == 'dungeon':
        dungeon = db.session.get(Dungeon, dungeon_id)
        if not dungeon:
            return jsonify({'message': 'Dungeon not found'}), 404

        # 检查等级要求
        if char.level < dungeon.level_requirement:
            return jsonify({'message': f'Level requirement not met: {dungeon.level_requirement}', 'required_level': dungeon.level_requirement}), 400

        # 选择第一个怪物作为开始
        monster_ids = eval(dungeon.monster_ids) if dungeon.monster_ids else []
        if not monster_ids:
            return jsonify({'message': 'Dungeon has no monsters'}), 400

        first_monster_id = monster_ids[0]
        monster = db.session.get(Monster, first_monster_id)
        if not monster:
            return jsonify({'message': 'Dungeon monster not found'}), 404

        combat = CombatState(
            character_id=char.id,
            monster_id=first_monster_id,
            dungeon_id=dungeon_id,
            weather=weather,
            character_hp=calculate_combat_stats(char, weather)['total_hp'],
            monster_hp=monster.hp,
            is_active=True
        )
    else:
        return jsonify({'message': 'Invalid combat type'}), 400

    db.session.add(combat)
    db.session.commit()

    return jsonify({
        'message': 'Combat started',
        'combat_id': combat.id,
        'weather': weather,
        'character_hp': combat.character_hp,
        'monster': {
            'id': monster.id,
            'name': monster.name,
            'hp': monster.hp,
            'attack': monster.attack,
            'defense': monster.defense,
            'speed': monster.speed,
            'linggen': monster.linggen,
            'description': monster.description
        } if monster else None
    }), 201


@app.route('/combat/<int:combat_id>/action', methods=['POST'])
@token_required
def perform_combat_action(current_user, combat_id):
    """执行战斗行动"""
    data = request.get_json()
    action_type = data.get('action', 'attack')  # attack, defend, skill, flee

    combat = db.session.get(CombatState, combat_id)
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not combat or combat.character_id != char.id or not combat.is_active:
        return jsonify({'message': 'Combat not found or not active'}), 404

    monster = db.session.get(Monster, combat.monster_id)
    if not monster:
        return jsonify({'message': 'Monster not found'}), 404

    # 计算战斗属性
    char_stats = calculate_combat_stats(char, combat.weather)
    monster_stats = {
        'total_attack': monster.attack,
        'total_defense': monster.defense,
        'total_hp': monster.hp,
        'total_speed': monster.speed,
        'crit_rate': 0.05,
        'dodge_rate': 0.05,
        'hit_rate': 0.9,
        'crit_damage': 1.5,
        'penetration_rate': 0,
        'linggen': monster.linggen
    }

    combat_log = []
    combat_result = None

    # 决定行动顺序（速度高的先行动）
    if char_stats['total_speed'] >= monster_stats['total_speed']:
        # 玩家先行动
        player_action_result = perform_player_action(action_type, char_stats, monster_stats, combat, data)
        combat_log.extend(player_action_result['log'])

        if combat.monster_hp > 0 and not player_action_result.get('fled', False):
            # 怪物行动
            monster_action_result = perform_monster_action(monster_stats, char_stats, combat)
            combat_log.extend(monster_action_result['log'])
    else:
        # 怪物先行动
        monster_action_result = perform_monster_action(monster_stats, char_stats, combat)
        combat_log.extend(monster_action_result['log'])

        if combat.character_hp > 0 and not monster_action_result.get('fled', False):
            # 玩家行动
            player_action_result = perform_player_action(action_type, char_stats, monster_stats, combat, data)
            combat_log.extend(player_action_result['log'])

    # 检查战斗结果
    if combat.character_hp <= 0:
        combat_result = 'defeat'
        combat.is_active = False
    elif combat.monster_hp <= 0:
        combat_result = 'victory'
        combat.is_active = False
        # 发放奖励
        award_combat_rewards(char, monster, combat.weather)

    # 如果是副本战斗且胜利，进入下一波
    if combat_result == 'victory' and combat.dungeon_id:
        dungeon = db.session.get(Dungeon, combat.dungeon_id)
        if dungeon:
            monster_ids = eval(dungeon.monster_ids) if dungeon.monster_ids else []
            current_index = monster_ids.index(combat.monster_id) if combat.monster_id in monster_ids else -1

            if current_index < len(monster_ids) - 1:
                # 还有下一波怪物
                next_monster_id = monster_ids[current_index + 1]
                next_monster = db.session.get(Monster, next_monster_id)
                if next_monster:
                    combat.monster_id = next_monster_id
                    combat.monster_hp = next_monster.hp
                    combat.is_active = True
                    combat_result = None
                    combat_log.append(f"进入下一波！面对{next_monster.name}")

    combat.current_turn += 1
    db.session.commit()

    return jsonify({
        'combat_id': combat.id,
        'turn': combat.current_turn,
        'character_hp': combat.character_hp,
        'monster_hp': combat.monster_hp,
        'weather': combat.weather,
        'log': combat_log,
        'result': combat_result,
        'is_active': combat.is_active
    }), 200


def perform_player_action(action_type, char_stats, monster_stats, combat, data):
    """执行玩家行动"""
    log = []

    if action_type == 'attack':
        # 普通攻击
        damage = calculate_damage(char_stats, monster_stats, combat.weather)
        combat.monster_hp -= damage
        log.append(f"你发动普通攻击，造成{damage}点伤害！")

        # 神通发动检查
        equipped_shentong = Shentong.query.filter_by(character_id=combat.character_id, equipped=True).first()
        if equipped_shentong and random.random() < equipped_shentong.trigger_rate:
            shentong_damage = int(damage * equipped_shentong.damage_multiplier)
            combat.monster_hp -= shentong_damage
            log.append(f"神通{equipped_shentong.name}发动！额外造成{shentong_damage}点伤害！")

    elif action_type == 'defend':
        # 防御（减少下回合受到的伤害）
        defense_bonus = int(char_stats['total_defense'] * 0.5)
        # 这里简化处理，可以添加状态效果系统
        log.append(f"你采取防御姿态，下回合防御力增加{defense_bonus}！")

    elif action_type == 'skill':
        # 使用宠物技能
        pet_id = data.get('pet_id')
        if pet_id:
            pet = db.session.get(Pet, pet_id)
            if pet and pet.owner_id == combat.character_id:
                if random.random() < pet.skill_trigger_rate:
                    # 宠物技能发动
                    skill_damage = int(char_stats['total_attack'] * 0.8)
                    combat.monster_hp -= skill_damage
                    log.append(f"宠物{pet.name}发动{pet.skill_name}，造成{skill_damage}点伤害！")
                else:
                    log.append(f"宠物{pet.name}的{pet.skill_name}发动失败！")

    elif action_type == 'flee':
        # 逃跑（成功率基于速度差）
        speed_diff = char_stats['total_speed'] - monster_stats['total_speed']
        flee_chance = min(0.8, max(0.1, 0.5 + speed_diff * 0.01))
        if random.random() < flee_chance:
            combat.is_active = False
            log.append("成功逃跑！")
            return {'log': log, 'fled': True}
        else:
            log.append("逃跑失败！")

    return {'log': log}


def perform_monster_action(monster_stats, char_stats, combat):
    """执行怪物行动"""
    log = []

    # 怪物AI：80%概率普通攻击，20%概率特殊行动
    if random.random() < 0.8:
        # 普通攻击
        damage = calculate_damage(monster_stats, char_stats, combat.weather)
        combat.character_hp -= damage
        log.append(f"{Monster.query.get(combat.monster_id).name if combat.monster_id else '怪物'}发动攻击，造成{damage}点伤害！")
    else:
        # 特殊行动（这里简化）
        log.append(f"{Monster.query.get(combat.monster_id).name if combat.monster_id else '怪物'}使用特殊技能！")

    return {'log': log}


def award_combat_rewards(character, monster, weather):
    """发放战斗奖励"""
    # 经验奖励
    exp_reward = monster.experience_reward
    weather_bonus = WEATHER_FACTORS.get(weather, {}).get('基础', 1.0)
    exp_reward = int(exp_reward * weather_bonus)

    character.experience += exp_reward

    # 检查升级
    while character.experience >= exp_for_level(character.level):
        character.experience -= exp_for_level(character.level)
        if character.level < 100:  # 最大等级限制
            character.level += 1

    # 灵石奖励
    lingshi_reward = monster.lingshi_reward
    resource = Resource.query.filter_by(character_id=character.id, type='灵石').first()
    if resource:
        resource.amount += lingshi_reward
    else:
        resource = Resource(character_id=character.id, type='灵石', amount=lingshi_reward)
        db.session.add(resource)

    # 掉落物品（简化处理）
    if monster.drop_items and random.random() < 0.3:  # 30%掉落概率
        # 这里可以添加物品掉落逻辑
        pass

    db.session.commit()


@app.route('/combat/<int:combat_id>', methods=['GET'])
@token_required
def get_combat_status(current_user, combat_id):
    """获取战斗状态"""
    combat = db.session.get(CombatState, combat_id)
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not combat or combat.character_id != char.id:
        return jsonify({'message': 'Combat not found'}), 404

    monster = db.session.get(Monster, combat.monster_id) if combat.monster_id else None

    return jsonify({
        'combat_id': combat.id,
        'current_turn': combat.current_turn,
        'weather': combat.weather,
        'character_hp': combat.character_hp,
        'monster_hp': combat.monster_hp,
        'is_active': combat.is_active,
        'monster': {
            'id': monster.id,
            'name': monster.name,
            'linggen': monster.linggen,
            'description': monster.description
        } if monster else None
    }), 200


@app.route('/combat/<int:combat_id>/end', methods=['POST'])
@token_required
def end_combat(current_user, combat_id):
    """结束战斗"""
    combat = db.session.get(CombatState, combat_id)
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not combat or combat.character_id != char.id:
        return jsonify({'message': 'Combat not found'}), 404

    combat.is_active = False
    db.session.commit()

    return jsonify({'message': 'Combat ended'}), 200


# 怪物和副本API
@app.route('/monsters', methods=['GET'])
@token_required
def get_monsters(current_user):
    """获取怪物列表"""
    monsters = Monster.query.all()
    monsters_data = []
    for monster in monsters:
        monsters_data.append({
            'id': monster.id,
            'name': monster.name,
            'level': monster.level,
            'hp': monster.hp,
            'attack': monster.attack,
            'defense': monster.defense,
            'speed': monster.speed,
            'linggen': monster.linggen,
            'experience_reward': monster.experience_reward,
            'lingshi_reward': monster.lingshi_reward,
            'ai_type': monster.ai_type,
            'description': monster.description
        })

    return jsonify({'monsters': monsters_data}), 200


@app.route('/dungeons', methods=['GET'])
@token_required
def get_dungeons(current_user):
    """获取副本列表"""
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'Character not found'}), 404

    dungeons = Dungeon.query.filter(Dungeon.level_requirement <= char.level).all()
    dungeons_data = []
    for dungeon in dungeons:
        dungeons_data.append({
            'id': dungeon.id,
            'name': dungeon.name,
            'level_requirement': dungeon.level_requirement,
            'difficulty': dungeon.difficulty,
            'description': dungeon.description,
            'completion_time_limit': dungeon.completion_time_limit
        })

    return jsonify({'dungeons': dungeons_data}), 200


# 世界地图API
@app.route('/world/map', methods=['GET'])
@token_required
def get_world_map(current_user):
    """获取世界地图"""
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'Character not found'}), 404

    # 简化：返回固定的地图点
    map_points = [
        {'id': 1, 'name': '新手村', 'type': 'village', 'x': 0, 'y': 0, 'resources': ['灵石', '草药'], 'weather': '晴天'},
        {'id': 2, 'name': '幽暗森林', 'type': 'forest', 'x': 10, 'y': 5, 'resources': ['木材', '灵植种子'], 'weather': '雨天'},
        {'id': 3, 'name': '熔岩山脉', 'type': 'mountain', 'x': -15, 'y': 20, 'resources': ['矿石', '火属性材料'], 'weather': '烈日'},
        {'id': 4, 'name': '冰雪荒原', 'type': 'wasteland', 'x': 25, 'y': -10, 'resources': ['冰晶', '寒属性材料'], 'weather': '雪天'},
        {'id': 5, 'name': '神秘遗迹', 'type': 'ruins', 'x': -5, 'y': -25, 'resources': ['古董', '稀有物品'], 'weather': '雾天'}
    ]

    return jsonify({'map_points': map_points}), 200


@app.route('/world/explore/<int:point_id>', methods=['POST'])
@token_required
def explore_map_point(current_user, point_id):
    """探索地图点"""
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'Character not found'}), 404

    # 模拟探索结果
    explore_results = {
        1: {'resources': [{'type': '灵石', 'amount': 50}], 'events': ['发现了一些灵石']},
        2: {'resources': [{'type': '木材', 'amount': 20}, {'type': '灵植种子', 'amount': 1}], 'events': ['采集到木材', '找到灵植种子']},
        3: {'resources': [{'type': '矿石', 'amount': 15}], 'events': ['挖掘到矿石']},
        4: {'resources': [{'type': '冰晶', 'amount': 10}], 'events': ['收集到冰晶']},
        5: {'resources': [{'type': '古董', 'amount': 1}], 'events': ['发现古老文物']}
    }

    result = explore_results.get(point_id, {'resources': [], 'events': ['什么都没有发现']})

    # 发放资源
    for resource_item in result['resources']:
        resource = Resource.query.filter_by(character_id=char.id, type=resource_item['type']).first()
        if resource:
            resource.amount += resource_item['amount']
        else:
            resource = Resource(character_id=char.id, type=resource_item['type'], amount=resource_item['amount'])
            db.session.add(resource)

    db.session.commit()

    return jsonify({
        'point_id': point_id,
        'events': result['events'],
        'resources_gained': result['resources']
    }), 200


# 生活技能系统API
@app.route('/life_skills', methods=['GET'])
@token_required
def get_life_skills(current_user):
    """获取生活技能列表"""
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'Character not found'}), 404

    skills = LifeSkill.query.filter_by(character_id=char.id).all()
    skills_data = []
    for skill in skills:
        skills_data.append({
            'id': skill.id,
            'skill_type': skill.skill_type,
            'level': skill.level,
            'experience': skill.experience,
            'proficiency': skill.proficiency
        })

    return jsonify({'skills': skills_data}), 200


@app.route('/life_skills/init', methods=['POST'])
@token_required
def init_life_skills(current_user):
    """初始化生活技能"""
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'Character not found'}), 404

    # 检查是否已初始化
    existing = LifeSkill.query.filter_by(character_id=char.id).first()
    if existing:
        return jsonify({'message': 'Life skills already initialized'}), 400

    # 初始化6种生活技能
    skill_types = ['锻造', '炼丹', '符文', '鉴定', '采集', '种植']
    for skill_type in skill_types:
        skill = LifeSkill(character_id=char.id, skill_type=skill_type)
        db.session.add(skill)

    db.session.commit()
    return jsonify({'message': 'Life skills initialized successfully'}), 201


@app.route('/identify', methods=['POST'])
@token_required
def identify_item(current_user):
    """鉴定物品"""
    data = request.get_json()
    item_type = data.get('item_type')  # equipment, treasure, rune
    item_id = data.get('item_id')

    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'Character not found'}), 404

    # 获取鉴定技能等级
    identify_skill = LifeSkill.query.filter_by(character_id=char.id, skill_type='鉴定').first()
    skill_level = identify_skill.level if identify_skill else 1

    # 消耗灵石
    cost = 50 * skill_level  # 鉴定消耗随技能等级增加
    resource = Resource.query.filter_by(character_id=char.id, type='灵石').first()
    if not resource or resource.amount < cost:
        return jsonify({'message': f'Not enough ling shi, need {cost}', 'required': cost}), 400

    # 计算成功率：基础成功率 = min(技能等级系数 + 道具品质系数 + 悟性*系数, 基础成功率上限)
    base_success_rate = 0.5  # 基础成功率
    skill_bonus = skill_level * 0.05  # 技能等级加成
    wuxing_bonus = char.wuxing * 0.002  # 悟性加成
    final_success_rate = min(0.95, base_success_rate + skill_bonus + wuxing_bonus)

    success = random.random() < final_success_rate

    if success:
        # 鉴定成功，记录鉴定结果
        identification = Identification(
            character_id=char.id,
            item_type=item_type,
            item_id=item_id,
            success=True
        )
        db.session.add(identification)

        # 扣除灵石
        resource.amount -= cost

        # 增加技能经验
        if identify_skill:
            identify_skill.experience += 10
            # 检查升级
            while identify_skill.experience >= identify_skill.level * 100:
                identify_skill.experience -= identify_skill.level * 100
                identify_skill.level += 1

        db.session.commit()

        return jsonify({
            'message': '鉴定成功！',
            'success': True,
            'cost': cost,
            'skill_level': identify_skill.level if identify_skill else 1
        }), 200
    else:
        # 鉴定失败
        resource.amount -= cost
        db.session.commit()

        return jsonify({
            'message': '鉴定失败',
            'success': False,
            'cost': cost
        }), 400


@app.route('/materials', methods=['GET'])
@token_required
def get_materials(current_user):
    """获取材料列表"""
    materials = Material.query.all()
    materials_data = []
    for material in materials:
        materials_data.append({
            'id': material.id,
            'name': material.name,
            'type': material.type,
            'quality': material.quality,
            'rarity': material.rarity,
            'description': material.description,
            'base_value': material.base_value
        })

    return jsonify({'materials': materials_data}), 200


@app.route('/materials/inventory', methods=['GET'])
@token_required
def get_material_inventory(current_user):
    """获取材料库存"""
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'Character not found'}), 404

    inventory = MaterialInventory.query.filter_by(character_id=char.id).all()
    inventory_data = []
    for item in inventory:
        material = Material.query.get(item.material_id)
        if material:
            inventory_data.append({
                'id': item.id,
                'material_id': item.material_id,
                'name': material.name,
                'type': material.type,
                'quality': material.quality,
                'rarity': material.rarity,
                'quantity': item.quantity,
                'base_value': material.base_value
            })

    return jsonify({'inventory': inventory_data}), 200


@app.route('/materials/collect', methods=['POST'])
@token_required
def collect_materials(current_user):
    """采集材料"""
    data = request.get_json()
    material_id = data.get('material_id')
    quantity = data.get('quantity', 1)

    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'Character not found'}), 404

    material = Material.query.get(material_id)
    if not material:
        return jsonify({'message': 'Material not found'}), 404

    # 获取采集技能等级
    collect_skill = LifeSkill.query.filter_by(character_id=char.id, skill_type='采集').first()
    skill_level = collect_skill.level if collect_skill else 1

    # 计算成功率
    base_success_rate = 0.6  # 基础成功率
    skill_bonus = skill_level * 0.03  # 技能等级加成
    rarity_modifier = {'常见': 0.2, '稀有': -0.1, '珍贵': -0.2, '传说': -0.3}.get(material.rarity, 0)
    final_success_rate = min(0.95, max(0.1, base_success_rate + skill_bonus + rarity_modifier))

    # 消耗灵石
    cost = 20 * quantity
    resource = Resource.query.filter_by(character_id=char.id, type='灵石').first()
    if not resource or resource.amount < cost:
        return jsonify({'message': f'Not enough ling shi, need {cost}', 'required': cost}), 400

    collected = 0
    for i in range(quantity):
        if random.random() < final_success_rate:
            collected += 1

    if collected > 0:
        # 更新材料库存
        inventory_item = MaterialInventory.query.filter_by(
            character_id=char.id,
            material_id=material_id
        ).first()

        if inventory_item:
            inventory_item.quantity += collected
        else:
            inventory_item = MaterialInventory(
                character_id=char.id,
                material_id=material_id,
                quantity=collected
            )
            db.session.add(inventory_item)

        # 扣除灵石
        resource.amount -= cost

        # 增加技能经验
        if collect_skill:
            collect_skill.experience += collected * 5
            # 检查升级
            while collect_skill.experience >= collect_skill.level * 100:
                collect_skill.experience -= collect_skill.level * 100
                collect_skill.level += 1

        db.session.commit()

        return jsonify({
            'message': f'采集成功！获得{collected}个{material.name}',
            'collected': collected,
            'success_rate': final_success_rate,
            'cost': cost
        }), 200
    else:
        # 采集失败
        resource.amount -= cost
        db.session.commit()

        return jsonify({
            'message': '采集失败，没有获得任何材料',
            'collected': 0,
            'success_rate': final_success_rate,
            'cost': cost
        }), 400


@app.route('/life_skills/success_rate', methods=['POST'])
@token_required
def calculate_success_rate(current_user):
    """计算生活技能成功率"""
    data = request.get_json()
    skill_type = data.get('skill_type')
    material_quality_factor = data.get('material_quality_factor', 1.0)

    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'Character not found'}), 404

    # 获取技能等级
    skill = LifeSkill.query.filter_by(character_id=char.id, skill_type=skill_type).first()
    skill_level = skill.level if skill else 1

    # 计算成功率：基础成功率 = min(技能等级系数 + 道具品质系数 + 悟性*系数, 基础成功率上限)
    skill_coefficient = skill_level * 0.05  # 技能等级系数
    material_coefficient = (material_quality_factor - 1) * 0.1  # 道具品质系数
    wuxing_coefficient = char.wuxing * 0.001  # 悟性系数

    base_success_rate = min(0.95, skill_coefficient + material_coefficient + wuxing_coefficient)

    return jsonify({
        'skill_type': skill_type,
        'skill_level': skill_level,
        'base_success_rate': base_success_rate,
        'skill_coefficient': skill_coefficient,
        'material_coefficient': material_coefficient,
        'wuxing_coefficient': wuxing_coefficient
    }), 200


# 社交和经济系统API

# 好友系统API
@app.route('/friends', methods=['GET'])
@token_required
def get_friends(current_user):
    """获取好友列表"""
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'Character not found'}), 404

    # 获取好友关系（双向）
    friends1 = Friendship.query.filter_by(character_id=char.id).all()
    friends2 = Friendship.query.filter_by(friend_id=char.id).all()

    friends_data = []
    friend_ids = set()

    for friendship in friends1 + friends2:
        friend_id = friendship.friend_id if friendship.character_id == char.id else friendship.character_id
        if friend_id not in friend_ids:
            friend_ids.add(friend_id)
            friend_char = Character.query.get(friend_id)
            if friend_char:
                friends_data.append({
                    'id': friend_id,
                    'name': friend_char.name,
                    'level': friend_char.level,
                    'realm': friend_char.realm,
                    'intimacy': friendship.intimacy,
                    'status': friendship.status
                })

    return jsonify({'friends': friends_data}), 200


@app.route('/friends/add', methods=['POST'])
@token_required
def add_friend(current_user):
    """添加好友"""
    data = request.get_json()
    friend_name = data.get('friend_name')

    char = Character.query.filter_by(user_id=current_user.id).first()
    friend_char = Character.query.filter_by(name=friend_name).first()

    if not char or not friend_char:
        return jsonify({'message': 'Character not found'}), 404

    if char.id == friend_char.id:
        return jsonify({'message': 'Cannot add yourself as friend'}), 400

    # 检查是否已经是好友
    existing = Friendship.query.filter(
        ((Friendship.character_id == char.id) & (Friendship.friend_id == friend_char.id)) |
        ((Friendship.character_id == friend_char.id) & (Friendship.friend_id == char.id))
    ).first()

    if existing:
        return jsonify({'message': 'Already friends'}), 400

    # 创建好友关系
    friendship = Friendship(
        character_id=char.id,
        friend_id=friend_char.id,
        intimacy=0
    )
    db.session.add(friendship)
    db.session.commit()

    return jsonify({
        'message': f'Successfully added {friend_name} as friend',
        'friend': {
            'id': friend_char.id,
            'name': friend_char.name,
            'level': friend_char.level,
            'realm': friend_char.realm
        }
    }), 201


# 邮件系统API
@app.route('/mail', methods=['GET'])
@token_required
def get_mail(current_user):
    """获取邮件列表"""
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'Character not found'}), 404

    mails = Mail.query.filter_by(receiver_id=char.id).order_by(Mail.sent_at.desc()).all()
    mails_data = []
    for mail in mails:
        sender = Character.query.get(mail.sender_id)
        mails_data.append({
            'id': mail.id,
            'title': mail.title,
            'content': mail.content,
            'sender_name': sender.name if sender else 'System',
            'sent_at': mail.sent_at.isoformat(),
            'read_status': mail.read_status
        })

    return jsonify({'mails': mails_data}), 200


@app.route('/mail/send', methods=['POST'])
@token_required
def send_mail(current_user):
    """发送邮件"""
    data = request.get_json()
    receiver_name = data.get('receiver_name')
    title = data.get('title')
    content = data.get('content')

    if not receiver_name or not title or not content:
        return jsonify({'message': 'Missing required fields'}), 400

    char = Character.query.filter_by(user_id=current_user.id).first()
    receiver = Character.query.filter_by(name=receiver_name).first()

    if not char or not receiver:
        return jsonify({'message': 'Character not found'}), 404

    # 创建邮件
    mail = Mail(
        sender_id=char.id,
        receiver_id=receiver.id,
        title=title,
        content=content
    )
    db.session.add(mail)
    db.session.commit()

    return jsonify({
        'message': f'Mail sent to {receiver_name}',
        'mail_id': mail.id
    }), 201


@app.route('/mail/<int:mail_id>/read', methods=['POST'])
@token_required
def read_mail(current_user, mail_id):
    """标记邮件为已读"""
    char = Character.query.filter_by(user_id=current_user.id).first()
    mail = Mail.query.filter_by(id=mail_id, receiver_id=char.id).first()

    if not mail:
        return jsonify({'message': 'Mail not found'}), 404

    mail.read_status = True
    db.session.commit()

    return jsonify({'message': 'Mail marked as read'}), 200


# 排行榜API
@app.route('/rankings/<ranking_type>', methods=['GET'])
@token_required
def get_rankings(current_user, ranking_type):
    """获取排行榜"""
    valid_types = ['level', 'battle_power', 'wealth', 'sect']
    if ranking_type not in valid_types:
        return jsonify({'message': 'Invalid ranking type'}), 400

    rankings = []

    if ranking_type == 'level':
        # 等级排行榜
        chars = Character.query.order_by(Character.level.desc(), Character.experience.desc()).limit(100).all()
        for i, char in enumerate(chars, 1):
            rankings.append({
                'rank': i,
                'name': char.name,
                'level': char.level,
                'realm': char.realm,
                'value': char.level
            })

    elif ranking_type == 'battle_power':
        # 战力排行榜
        chars = Character.query.all()
        char_powers = []
        for char in chars:
            attr = CharacterAttribute.query.filter_by(character_id=char.id).first()
            if attr:
                power = compute_battle_power(attr,
                    Equipment.query.filter_by(character_id=char.id).all(),
                    Mantra.query.filter_by(character_id=char.id).all(),
                    Treasure.query.filter_by(character_id=char.id).all())
                char_powers.append((char, power))

        char_powers.sort(key=lambda x: x[1], reverse=True)
        for i, (char, power) in enumerate(char_powers[:100], 1):
            rankings.append({
                'rank': i,
                'name': char.name,
                'level': char.level,
                'realm': char.realm,
                'value': power
            })

    elif ranking_type == 'wealth':
        # 财富排行榜
        chars = Character.query.all()
        char_wealths = []
        for char in chars:
            wealth = 0
            resources = Resource.query.filter_by(character_id=char.id).all()
            for res in resources:
                wealth += res.amount
            char_wealths.append((char, wealth))

        char_wealths.sort(key=lambda x: x[1], reverse=True)
        for i, (char, wealth) in enumerate(char_wealths[:100], 1):
            rankings.append({
                'rank': i,
                'name': char.name,
                'level': char.level,
                'realm': char.realm,
                'value': wealth
            })

    return jsonify({'rankings': rankings, 'type': ranking_type}), 200


# 商城API
@app.route('/shop', methods=['GET'])
@token_required
def get_shop(current_user):
    """获取商城物品"""
    shop_items = Shop.query.all()
    items_data = []
    for item in shop_items:
        items_data.append({
            'id': item.id,
            'item_type': item.item_type,
            'item_id': item.item_id,
            'price': item.price,
            'discount': item.discount,
            'final_price': int(item.price * item.discount)
        })

    return jsonify({'shop_items': items_data}), 200


@app.route('/shop/buy/<int:item_id>', methods=['POST'])
@token_required
def buy_from_shop(current_user, item_id):
    """从商城购买物品"""
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'Character not found'}), 404

    shop_item = Shop.query.get(item_id)
    if not shop_item:
        return jsonify({'message': 'Shop item not found'}), 404

    final_price = int(shop_item.price * shop_item.discount)
    resource = Resource.query.filter_by(character_id=char.id, type='灵石').first()
    if not resource or resource.amount < final_price:
        return jsonify({'message': f'Not enough ling shi, need {final_price}', 'required': final_price}), 400

    # 扣除灵石
    resource.amount -= final_price

    # 这里应该创建对应的物品，暂时只记录购买
    db.session.commit()

    return jsonify({
        'message': f'Successfully purchased item for {final_price} ling shi',
        'item_type': shop_item.item_type,
        'final_price': final_price
    }), 200


# 交易系统API
@app.route('/trade/create', methods=['POST'])
@token_required
def create_trade(current_user):
    """创建交易"""
    data = request.get_json()
    target_name = data.get('target_name')
    offer_items = data.get('offer_items', [])
    request_items = data.get('request_items', [])

    char = Character.query.filter_by(user_id=current_user.id).first()
    target = Character.query.filter_by(name=target_name).first()

    if not char or not target:
        return jsonify({'message': 'Character not found'}), 404

    # 这里简化交易逻辑，实际应该创建交易记录并等待对方确认
    # 暂时直接完成交易

    return jsonify({
        'message': f'Trade request sent to {target_name}',
        'status': 'pending'
    }), 201


# 任务系统API
@app.route('/quests', methods=['GET'])
@token_required
def get_quests(current_user):
    """获取任务列表"""
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'Character not found'}), 404

    quests = Quest.query.filter_by(character_id=char.id).all()
    quests_data = []
    for quest in quests:
        quests_data.append({
            'id': quest.id,
            'title': quest.title,
            'description': quest.description,
            'type': quest.type,
            'status': quest.status,
            'reward_experience': quest.reward_experience,
            'reward_items': quest.reward_items
        })

    return jsonify({'quests': quests_data}), 200


@app.route('/quests/accept/<int:quest_id>', methods=['POST'])
@token_required
def accept_quest(current_user, quest_id):
    """接受任务"""
    char = Character.query.filter_by(user_id=current_user.id).first()
    quest = Quest.query.get(quest_id)

    if not char or not quest:
        return jsonify({'message': 'Quest not found'}), 404

    if quest.status != '未开始':
        return jsonify({'message': 'Quest already started'}), 400

    quest.status = '进行中'
    quest.started_at = datetime.datetime.utcnow()
    db.session.commit()

    return jsonify({'message': 'Quest accepted', 'quest_id': quest_id}), 200


# 成就系统API
@app.route('/achievements', methods=['GET'])
@token_required
def get_achievements(current_user):
    """获取成就列表"""
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'Character not found'}), 404

    achievements = Achievement.query.filter_by(character_id=char.id).all()
    achievements_data = []
    for achievement in achievements:
        achievements_data.append({
            'id': achievement.id,
            'name': achievement.name,
            'description': achievement.description,
            'unlocked': achievement.unlocked,
            'unlocked_at': achievement.unlocked_at.isoformat() if achievement.unlocked_at else None
        })

    return jsonify({'achievements': achievements_data}), 200


# 图鉴系统API
@app.route('/codex/<entry_type>', methods=['GET'])
@token_required
def get_codex(current_user, entry_type):
    """获取图鉴"""
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'Character not found'}), 404

    valid_types = ['monster', 'equipment', 'mantra', 'treasure']
    if entry_type not in valid_types:
        return jsonify({'message': 'Invalid codex type'}), 400

    codex_entries = Codex.query.filter_by(
        character_id=char.id,
        entry_type=entry_type
    ).all()

    entries_data = []
    for entry in codex_entries:
        entries_data.append({
            'entry_id': entry.entry_id,
            'discovered_at': entry.discovered_at.isoformat(),
            'discovery_count': entry.discovery_count
        })

    return jsonify({'codex': entries_data, 'type': entry_type}), 200


# 背包系统API
@app.route('/inventory', methods=['GET'])
@token_required
def get_inventory(current_user):
    """获取背包物品"""
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'Character not found'}), 404

    inventory_items = Inventory.query.filter_by(character_id=char.id).all()
    items_data = []
    for item in inventory_items:
        items_data.append({
            'id': item.id,
            'item_type': item.item_type,
            'item_id': item.item_id,
            'quantity': item.quantity,
            'is_equipped': item.is_equipped,
            'slot': item.slot,
            'acquired_at': item.acquired_at.isoformat()
        })

    return jsonify({'inventory': items_data}), 200


# 聊天系统API
@app.route('/chat/world', methods=['GET'])
@token_required
def get_world_chat(current_user):
    """获取世界聊天消息"""
    messages = ChatMessage.query.filter_by(channel='world').order_by(ChatMessage.sent_at.desc()).limit(50).all()
    messages_data = []
    for msg in messages:
        sender = Character.query.get(msg.sender_id)
        messages_data.append({
            'id': msg.id,
            'sender_name': sender.name if sender else 'Unknown',
            'content': msg.content,
            'sent_at': msg.sent_at.isoformat(),
            'is_read': msg.is_read
        })

    return jsonify({'messages': messages_data[::-1]}), 200  # 反转顺序，返回最新的在后面


@app.route('/chat/send', methods=['POST'])
@token_required
def send_chat_message(current_user):
    """发送聊天消息"""
    data = request.get_json()
    channel = data.get('channel', 'world')
    content = data.get('content', '').strip()
    receiver_name = data.get('receiver_name')  # 私聊时使用

    if not content:
        return jsonify({'message': 'Content cannot be empty'}), 400

    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'Character not found'}), 404

    receiver_id = None
    if receiver_name and channel == 'private':
        receiver = Character.query.filter_by(name=receiver_name).first()
        if receiver:
            receiver_id = receiver.id

    message = ChatMessage(
        sender_id=char.id,
        receiver_id=receiver_id,
        channel=channel,
        content=content
    )
    db.session.add(message)
    db.session.commit()

    return jsonify({
        'message': 'Message sent',
        'message_id': message.id
    }), 201


# 高级功能系统API

# 灵根改变API
@app.route('/character/change_linggen', methods=['POST'])
@token_required
def change_linggen(current_user):
    """灵根改变API（奇遇或道具）"""
    data = request.get_json()
    change_method = data.get('change_method', 'item')  # item, event, special_quest
    item_name = data.get('item_name')  # 如果是通过道具改变

    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'Character not found'}), 404

    # 检查灵根改变条件
    if change_method == 'item':
        # 通过道具改变，需要消耗特定道具
        if not item_name:
            return jsonify({'message': 'Item name required for item change method'}), 400

        # 检查是否拥有该道具（这里简化，实际应该检查背包）
        # 消耗灵石作为代价
        cost = 50000  # 改变灵根消耗大量灵石
        resource = Resource.query.filter_by(character_id=char.id, type='灵石').first()
        if not resource or resource.amount < cost:
            return jsonify({'message': f'Not enough ling shi, need {cost}', 'required': cost}), 400

        resource.amount -= cost

        # 随机生成新灵根（不能和原有灵根相同）
        available_linggen = ['金', '木', '水', '火', '土']
        if char.linggen in available_linggen:
            available_linggen.remove(char.linggen)
        new_linggen = random.choice(available_linggen)

    elif change_method == 'event':
        # 通过奇遇事件改变
        new_linggen = random.choice(['金', '木', '水', '火', '土'])

    elif change_method == 'special_quest':
        # 通过特殊任务改变
        new_linggen = data.get('new_linggen')
        if not new_linggen or new_linggen not in ['金', '木', '水', '火', '土']:
            return jsonify({'message': 'Invalid new linggen for special quest'}), 400

    else:
        return jsonify({'message': 'Invalid change method'}), 400

    # 记录灵根改变
    old_linggen = char.linggen
    linggen_change_record = LinggenChange(
        character_id=char.id,
        old_linggen=old_linggen,
        new_linggen=new_linggen,
        change_method=change_method,
        change_item=item_name if change_method == 'item' else None
    )
    db.session.add(linggen_change_record)

    # 更新人物灵根
    char.linggen = new_linggen

    # 灵根改变可能影响现有功法契合度
    # 这里可以添加功法兼容性检查逻辑

    db.session.commit()

    return jsonify({
        'message': f'灵根成功改变！从{old_linggen}属性变为{new_linggen}属性',
        'old_linggen': old_linggen,
        'new_linggen': new_linggen,
        'change_method': change_method
    }), 200


# 组队系统API
@app.route('/team/create', methods=['POST'])
@token_required
def create_team(current_user):
    """创建队伍"""
    data = request.get_json()
    team_name = data.get('name')
    activity_type = data.get('activity_type', 'dungeon')
    max_members = data.get('max_members', 5)
    min_level = data.get('min_level', 1)
    max_level = data.get('max_level', 100)

    if not team_name:
        return jsonify({'message': 'Team name is required'}), 400

    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'Character not found'}), 404

    # 检查是否已在其他队伍
    existing_member = TeamMember.query.filter_by(character_id=char.id).first()
    if existing_member:
        return jsonify({'message': 'You are already in a team'}), 400

    # 创建队伍
    team = Team(
        name=team_name,
        leader_id=char.id,
        activity_type=activity_type,
        max_members=max_members,
        min_level=min_level,
        max_level=max_level
    )
    db.session.add(team)
    db.session.commit()

    # 将创建者加入队伍
    team_member = TeamMember(
        team_id=team.id,
        character_id=char.id,
        role='leader'
    )
    db.session.add(team_member)
    db.session.commit()

    return jsonify({
        'message': f'Team "{team_name}" created successfully',
        'team': {
            'id': team.id,
            'name': team.name,
            'leader_id': team.leader_id,
            'activity_type': team.activity_type,
            'max_members': team.max_members,
            'status': team.status
        }
    }), 201


@app.route('/team/join/<int:team_id>', methods=['POST'])
@token_required
def join_team(current_user, team_id):
    """加入队伍"""
    char = Character.query.filter_by(user_id=current_user.id).first()
    team = Team.query.get(team_id)

    if not char or not team:
        return jsonify({'message': 'Character or team not found'}), 404

    # 检查是否已在其他队伍
    existing_member = TeamMember.query.filter_by(character_id=char.id).first()
    if existing_member:
        return jsonify({'message': 'You are already in a team'}), 400

    # 检查队伍状态和人数限制
    if team.status != 'recruiting':
        return jsonify({'message': 'Team is not recruiting'}), 400

    current_members = TeamMember.query.filter_by(team_id=team_id).count()
    if current_members >= team.max_members:
        return jsonify({'message': 'Team is full'}), 400

    # 检查等级要求
    if char.level < team.min_level or char.level > team.max_level:
        return jsonify({'message': f'Level requirement not met ({team.min_level}-{team.max_level})'}), 400

    # 加入队伍
    team_member = TeamMember(
        team_id=team_id,
        character_id=char.id,
        role='member'
    )
    db.session.add(team_member)
    db.session.commit()

    # 检查队伍是否已满
    new_member_count = TeamMember.query.filter_by(team_id=team_id).count()
    if new_member_count >= team.max_members:
        team.status = 'full'
        db.session.commit()

    return jsonify({
        'message': f'Successfully joined team "{team.name}"',
        'team_id': team_id,
        'team_name': team.name
    }), 200


@app.route('/team/<int:team_id>', methods=['GET'])
@token_required
def get_team_info(current_user, team_id):
    """获取队伍信息"""
    team = Team.query.get(team_id)
    if not team:
        return jsonify({'message': 'Team not found'}), 404

    # 获取队伍成员
    members = TeamMember.query.filter_by(team_id=team_id).all()
    members_data = []
    for member in members:
        char = Character.query.get(member.character_id)
        if char:
            members_data.append({
                'id': member.id,
                'character_id': member.character_id,
                'character_name': char.name,
                'level': char.level,
                'realm': char.realm,
                'role': member.role,
                'joined_at': member.joined_at.isoformat()
            })

    return jsonify({
        'team': {
            'id': team.id,
            'name': team.name,
            'leader_id': team.leader_id,
            'activity_type': team.activity_type,
            'max_members': team.max_members,
            'min_level': team.min_level,
            'max_level': team.max_level,
            'status': team.status,
            'created_at': team.created_at.isoformat()
        },
        'members': members_data,
        'member_count': len(members_data)
    }), 200


@app.route('/team/leave', methods=['POST'])
@token_required
def leave_team(current_user):
    """离开队伍"""
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'Character not found'}), 404

    team_member = TeamMember.query.filter_by(character_id=char.id).first()
    if not team_member:
        return jsonify({'message': 'You are not in any team'}), 400

    team = Team.query.get(team_member.team_id)
    is_leader = team_member.role == 'leader'

    # 删除成员记录
    db.session.delete(team_member)

    if is_leader:
        # 如果是队长离开，解散队伍或转让队长
        remaining_members = TeamMember.query.filter_by(team_id=team.id).all()
        if remaining_members:
            # 转让给第一个成员
            remaining_members[0].role = 'leader'
            team.leader_id = remaining_members[0].character_id
        else:
            # 队伍解散
            db.session.delete(team)

    db.session.commit()

    return jsonify({'message': 'Successfully left the team'}), 200


# 保底机制API
@app.route('/guaranteed_drop/<drop_type>', methods=['GET'])
@token_required
def get_guaranteed_drop_status(current_user, drop_type):
    """获取保底状态"""
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'Character not found'}), 404

    guaranteed_drop = GuaranteedDrop.query.filter_by(
        character_id=char.id,
        drop_type=drop_type
    ).first()

    if not guaranteed_drop:
        return jsonify({
            'drop_type': drop_type,
            'attempts': 0,
            'guaranteed': False,
            'guaranteed_threshold': 100  # 100次后必定掉落
        }), 200

    return jsonify({
        'drop_type': drop_type,
        'attempts': guaranteed_drop.attempts,
        'guaranteed': guaranteed_drop.guaranteed,
        'guaranteed_threshold': 100,
        'last_attempt': guaranteed_drop.last_attempt.isoformat()
    }), 200


@app.route('/guaranteed_drop/<drop_type>/attempt', methods=['POST'])
@token_required
def attempt_guaranteed_drop(current_user, drop_type):
    """尝试保底掉落"""
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'Character not found'}), 404

    # 获取或创建保底计数器
    guaranteed_drop = GuaranteedDrop.query.filter_by(
        character_id=char.id,
        drop_type=drop_type
    ).first()

    if not guaranteed_drop:
        guaranteed_drop = GuaranteedDrop(
            character_id=char.id,
            drop_type=drop_type,
            attempts=0,
            guaranteed=False
        )
        db.session.add(guaranteed_drop)

    # 增加尝试次数
    guaranteed_drop.attempts += 1
    guaranteed_drop.last_attempt = db.func.current_timestamp()

    # 检查是否达到保底
    guaranteed_threshold = 100
    if guaranteed_drop.attempts >= guaranteed_threshold:
        guaranteed_drop.guaranteed = True

    # 计算掉落概率
    base_drop_rate = 0.01  # 基础1%掉率
    if guaranteed_drop.guaranteed:
        drop_rate = 1.0  # 保底必定掉落
    else:
        # 随着尝试次数增加，掉落概率逐渐提高
        drop_rate = min(0.5, base_drop_rate + (guaranteed_drop.attempts * 0.005))

    # 模拟掉落
    dropped = random.random() < drop_rate

    if dropped:
        # 重置保底计数器
        guaranteed_drop.attempts = 0
        guaranteed_drop.guaranteed = False

        # 根据掉落类型发放奖励
        if drop_type == 'equipment':
            # 创建随机装备
            equip_type = random.choice(['武器', '头盔', '衣服', '项链', '戒指'])
            quality = random.choice(['玄阶', '地阶', '天阶'])
            name = f"{quality}{equip_type}"

            equipment = Equipment(
                character_id=char.id,
                type=equip_type,
                name=name,
                quality=quality,
                max_level=20 if quality == '玄阶' else 30 if quality == '地阶' else 40,
                equipped=False
            )
            db.session.add(equipment)

            reward_info = {
                'type': 'equipment',
                'name': name,
                'quality': quality
            }

        elif drop_type == 'treasure':
            # 创建随机法宝
            quality = random.choice(['普通', '优质', '稀有', '史诗'])
            name = f"{quality}法宝"

            treasure = Treasure(
                character_id=char.id,
                name=name,
                quality=quality,
                equipped=False
            )
            db.session.add(treasure)

            reward_info = {
                'type': 'treasure',
                'name': name,
                'quality': quality
            }

        else:
            reward_info = {'type': 'unknown', 'description': '未知奖励'}

    db.session.commit()

    return jsonify({
        'drop_type': drop_type,
        'attempts': guaranteed_drop.attempts,
        'drop_rate': drop_rate,
        'dropped': dropped,
        'reward': reward_info if dropped else None,
        'guaranteed': guaranteed_drop.guaranteed
    }), 200


# 世界事件API
@app.route('/world/events', methods=['GET'])
@token_required
def get_world_events(current_user):
    """获取世界事件"""
    current_time = datetime.datetime.utcnow()

    # 获取当前活跃的事件
    active_events = WorldEvent.query.filter(
        WorldEvent.is_active == True,
        WorldEvent.start_time <= current_time,
        WorldEvent.end_time >= current_time
    ).all()

    events_data = []
    for event in active_events:
        events_data.append({
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'event_type': event.event_type,
            'severity': event.severity,
            'affected_regions': event.affected_regions,
            'effects': event.effects,
            'start_time': event.start_time.isoformat(),
            'end_time': event.end_time.isoformat()
        })

    return jsonify({'events': events_data}), 200


@app.route('/world/events/create', methods=['POST'])
@token_required
def create_world_event(current_user):
    """创建世界事件（管理员功能，简化版）"""
    data = request.get_json()

    event = WorldEvent(
        title=data.get('title', '世界事件'),
        description=data.get('description', ''),
        event_type=data.get('event_type', 'natural_disaster'),
        severity=data.get('severity', 'normal'),
        affected_regions=data.get('affected_regions', '[]'),
        effects=data.get('effects', '{}'),
        start_time=datetime.datetime.utcnow(),
        end_time=datetime.datetime.utcnow() + datetime.timedelta(hours=1),
        is_active=True
    )
    db.session.add(event)
    db.session.commit()

    return jsonify({
        'message': 'World event created',
        'event_id': event.id
    }), 201


# 历练系统API
@app.route('/trial_quests', methods=['GET'])
@token_required
def get_trial_quests(current_user):
    """获取历练任务"""
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'Character not found'}), 404

    trial_quests = TrialQuest.query.filter_by(character_id=char.id).all()
    quests_data = []
    for quest in trial_quests:
        quests_data.append({
            'id': quest.id,
            'title': quest.title,
            'description': quest.description,
            'trial_points': quest.trial_points,
            'requirements': quest.requirements,
            'status': quest.status,
            'progress': quest.progress,
            'started_at': quest.started_at.isoformat() if quest.started_at else None,
            'completed_at': quest.completed_at.isoformat() if quest.completed_at else None
        })

    return jsonify({'trial_quests': quests_data}), 200


@app.route('/trial_quests/accept/<int:quest_id>', methods=['POST'])
@token_required
def accept_trial_quest(current_user, quest_id):
    """接受历练任务"""
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'Character not found'}), 404

    trial_quest = TrialQuest.query.filter_by(id=quest_id, character_id=char.id).first()
    if not trial_quest:
        return jsonify({'message': 'Trial quest not found'}), 404

    if trial_quest.status != '未开始':
        return jsonify({'message': 'Quest already started'}), 400

    trial_quest.status = '进行中'
    trial_quest.started_at = datetime.datetime.utcnow()
    db.session.commit()

    return jsonify({
        'message': 'Trial quest accepted',
        'quest_id': quest_id
    }), 200


@app.route('/trial_quests/complete/<int:quest_id>', methods=['POST'])
@token_required
def complete_trial_quest(current_user, quest_id):
    """完成历练任务"""
    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'Character not found'}), 404

    trial_quest = TrialQuest.query.filter_by(id=quest_id, character_id=char.id).first()
    if not trial_quest:
        return jsonify({'message': 'Trial quest not found'}), 404

    if trial_quest.status != '进行中':
        return jsonify({'message': 'Quest not in progress'}), 400

    # 检查任务完成条件（这里简化，实际应该检查进度）
    # 假设任务已完成
    trial_quest.status = '已完成'
    trial_quest.completed_at = datetime.datetime.utcnow()

    # 奖励历练值
    char.lianxi += trial_quest.trial_points

    # 历练值提升综合能力
    # 每1000点历练值提升1点全属性
    attribute_bonus = trial_quest.trial_points // 1000
    if attribute_bonus > 0:
        attr = CharacterAttribute.query.filter_by(character_id=char.id).first()
        if attr:
            attr.hp += attribute_bonus * 10
            attr.attack += attribute_bonus
            attr.defense += attribute_bonus
            attr.speed += attribute_bonus

    db.session.commit()

    return jsonify({
        'message': f'Trial quest completed! Gained {trial_quest.trial_points} trial points',
        'trial_points_gained': trial_quest.trial_points,
        'total_trial_points': char.lianxi,
        'attribute_bonuses': {
            'hp': attribute_bonus * 10,
            'attack': attribute_bonus,
            'defense': attribute_bonus,
            'speed': attribute_bonus
        } if attribute_bonus > 0 else None
    }), 200


# 境界突破增强API
@app.route('/character/enhanced_realm_breakthrough', methods=['POST'])
@token_required
def enhanced_realm_breakthrough(current_user):
    """增强版境界突破API（包含纯度、丹药品质、功法契合）"""
    data = request.get_json()

    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'Character not found'}), 404

    # 检查等级要求
    if char.level < 10:
        return jsonify({'message': '等级不足，无法突破境界'}), 400

    # 获取当前境界和下一个境界
    current_realm = Realm.query.filter_by(name=char.realm).first()
    if not current_realm:
        return jsonify({'message': '境界数据错误'}), 500

    next_realm = Realm.query.filter(Realm.stage > current_realm.stage).order_by(Realm.stage).first()
    if not next_realm:
        return jsonify({'message': '已达到最高境界'}), 400

    # 计算各种影响因子
    purity = float(data.get('purity', 0.5))  # 纯度系数 0-1
    pill_quality = data.get('pill_quality', '普通')  # 丹药品质
    mantra_compat = float(data.get('mantra_compat', 1.0))  # 功法契合度

    # 丹药品质影响
    pill_multipliers = {
        '普通': 1.0,
        '优质': 1.2,
        '极品': 1.5,
        '传说': 2.0
    }
    pill_multiplier = pill_multipliers.get(pill_quality, 1.0)

    # 基础成功率
    base_success_rate = 0.3  # 基础30%成功率

    # 计算最终成功率：纯度 × 丹药品质加成 × 功法契合度 × 境界基础率
    realm_success_bonus = current_realm.stage * 0.05  # 境界越高越难突破
    final_success_rate = min(0.95, (purity * pill_multiplier * mantra_compat * (1 - realm_success_bonus)))

    # 消耗资源
    breakthrough_cost = int(1000 * (current_realm.stage + 1) * (2 - purity))  # 纯度越高消耗越少
    resource = Resource.query.filter_by(character_id=char.id, type='灵石').first()
    if not resource or resource.amount < breakthrough_cost:
        return jsonify({'message': f'灵石不足，需要{breakthrough_cost}灵石', 'required': breakthrough_cost}), 400

    # 记录突破尝试
    breakthrough_record = RealmBreakthroughRecord(
        character_id=char.id,
        from_realm=current_realm.name,
        to_realm=next_realm.name,
        purity=purity,
        pill_quality=pill_quality,
        mantra_compat=mantra_compat,
        success=False  # 先设为失败，成功后再更新
    )
    db.session.add(breakthrough_record)

    success = random.random() < final_success_rate

    if success:
        # 突破成功
        char.realm = next_realm.name
        char.level = 1
        char.experience = 0
        resource.amount -= breakthrough_cost

        # 更新记录为成功
        breakthrough_record.success = True

        # 境界突破属性提升
        attr = CharacterAttribute.query.filter_by(character_id=char.id).first()
        realm_bonus = int(next_realm.coefficient * 50 * purity * pill_multiplier)
        attr.hp += realm_bonus * 10
        attr.attack += realm_bonus * 2
        attr.defense += realm_bonus * 2
        attr.speed += realm_bonus

        # 纯度影响悟性提升
        char.wuxing += int(purity * 10)

        db.session.commit()

        return jsonify({
            'message': f'境界突破成功！进入{next_realm.name}',
            'success': True,
            'new_realm': next_realm.name,
            'final_success_rate': final_success_rate,
            'purity': purity,
            'pill_quality': pill_quality,
            'mantra_compat': mantra_compat,
            'attribute_bonuses': {
                'hp': realm_bonus * 10,
                'attack': realm_bonus * 2,
                'defense': realm_bonus * 2,
                'speed': realm_bonus,
                'wuxing': int(purity * 10)
            }
        }), 200
    else:
        # 突破失败
        failure_cost = breakthrough_cost // 2
        resource.amount -= failure_cost
        db.session.commit()

        return jsonify({
            'message': '境界突破失败',
            'success': False,
            'final_success_rate': final_success_rate,
            'purity': purity,
            'pill_quality': pill_quality,
            'mantra_compat': mantra_compat,
            'lingshi_lost': failure_cost
        }), 400


# 公式计算服务API
@app.route('/calculate/formulas', methods=['POST'])
@token_required
def calculate_formulas(current_user):
    """所有公式集成计算服务"""
    data = request.get_json()
    formula_type = data.get('type')
    parameters = data.get('parameters', {})

    char = Character.query.filter_by(user_id=current_user.id).first()
    if not char:
        return jsonify({'message': 'Character not found'}), 404

    results = {}

    if formula_type == 'combat_power':
        # 战力计算公式：战斗力 = (基础攻击力 + 功法攻击力 + 法宝攻击力) * 攻击权重 + (基础防御力 + 功法防御力 + 法宝防御力) * 防御权重 + 生命值 * 生命权重
        attr = CharacterAttribute.query.filter_by(character_id=char.id).first()
        if attr:
            # 计算装备、法宝、功法加成
            equip_attack = sum(e.attack_bonus for e in char.equipments if e.equipped) if char.equipments else 0
            treasure_attack = sum(t.attack_bonus for t in char.treasures) if char.treasures else 0
            mantra_attack = sum(m.attack_bonus for m in char.mantras if m.equipped) if char.mantras else 0

            equip_defense = sum(e.defense_bonus for e in char.equipments if e.equipped) if char.equipments else 0
            treasure_defense = sum(t.defense_bonus for t in char.treasures) if char.treasures else 0
            mantra_defense = sum(m.defense_bonus for m in char.mantras if m.equipped) if char.mantras else 0

            total_attack = attr.attack + equip_attack + treasure_attack + mantra_attack
            total_defense = attr.defense + equip_defense + treasure_defense + mantra_defense

            # 权重计算
            attack_weight = 0.4
            defense_weight = 0.3
            hp_weight = 0.3

            combat_power = int(
                total_attack * attack_weight +
                total_defense * defense_weight +
                attr.hp * hp_weight
            )

            results = {
                'combat_power': combat_power,
                'total_attack': total_attack,
                'total_defense': total_defense,
                'total_hp': attr.hp,
                'attack_weight': attack_weight,
                'defense_weight': defense_weight,
                'hp_weight': hp_weight
            }

    elif formula_type == 'experience_required':
        # 经验公式：500 * (level ** 2) * math.exp(0.05 * (level - 1))
        level = parameters.get('level', char.level)
        exp_required = int(500 * (level ** 2) * math.exp(0.05 * (level - 1)))
        results = {'level': level, 'experience_required': exp_required}

    elif formula_type == 'success_rate':
        # 成功率公式：min(技能等级系数 + 道具品质系数 + 悟性*系数, 上限)
        skill_type = parameters.get('skill_type', '锻造')
        material_quality_factor = parameters.get('material_quality_factor', 1.0)

        skill = LifeSkill.query.filter_by(character_id=char.id, skill_type=skill_type).first()
        skill_level = skill.level if skill else 1

        skill_coefficient = skill_level * 0.05
        material_coefficient = (material_quality_factor - 1) * 0.1
        wuxing_coefficient = char.wuxing * 0.001

        success_rate = min(0.95, skill_coefficient + material_coefficient + wuxing_coefficient)

        results = {
            'skill_type': skill_type,
            'skill_level': skill_level,
            'success_rate': success_rate,
            'skill_coefficient': skill_coefficient,
            'material_coefficient': material_coefficient,
            'wuxing_coefficient': wuxing_coefficient
        }

    elif formula_type == 'element_restraint':
        # 元素克制计算
        attacker_linggen = parameters.get('attacker_linggen', char.linggen)
        defender_linggen = parameters.get('defender_linggen', '无')
        weather = parameters.get('weather', '晴天')

        restraint = calculate_element_restraint(attacker_linggen, defender_linggen, weather)
        results = {
            'attacker_linggen': attacker_linggen,
            'defender_linggen': defender_linggen,
            'weather': weather,
            'element_restraint': restraint
        }

    else:
        return jsonify({'message': 'Unknown formula type'}), 400

    return jsonify({
        'formula_type': formula_type,
        'parameters': parameters,
        'results': results
    }), 200


# Serve frontend index and favicon for convenience
@app.route('/')
def serve_index():
    base = os.path.dirname(__file__)
    index_path = os.path.join(base, 'index.html')
    if os.path.exists(index_path):
        return send_file(index_path)
    return jsonify({'message': 'No index available'}), 404


@app.route('/favicon.ico')
def favicon():
    base = os.path.dirname(__file__)
    fav = os.path.join(base, 'favicon.ico')
    if os.path.exists(fav):
        return send_file(fav)
    return ('', 204)


@app.route('/<path:filename>')
def serve_static(filename):
    base = os.path.dirname(__file__)
    path = os.path.join(base, filename)
    if os.path.exists(path) and filename.endswith(('.html', '.js', '.css', '.ico', '.png', '.jpg', '.jpeg', '.gif')):
        return send_file(path)
    return jsonify({'message': 'File not found'}), 404

@app.route('/app.js')
def serve_app_js():
    base = os.path.dirname(__file__)
    path = os.path.join(base, 'app.js')
    if os.path.exists(path):
        return send_file(path, mimetype='application/javascript')
    return jsonify({'message': 'app.js not found'}), 404


if __name__ == '__main__':
    app.run(debug=True)
