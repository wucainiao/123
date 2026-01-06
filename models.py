from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# 用户模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    last_login = db.Column(db.DateTime)
    characters = db.relationship('Character', backref='user', lazy=True)

# 人物模型
class Character(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.BigInteger, default=0)
    realm = db.Column(db.String(20), default='凡人期')
    realm_level = db.Column(db.Integer, default=1)
    linggen = db.Column(db.String(10), default='无')
    wuxing = db.Column(db.Integer, default=0)
    qiyun = db.Column(db.Integer, default=0)
    lianxi = db.Column(db.Integer, default=0)
    reputation = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    attributes = db.relationship('CharacterAttribute', backref='character', lazy=True, uselist=False)
    equipments = db.relationship('Equipment', backref='character', lazy=True)
    treasures = db.relationship('Treasure', backref='character', lazy=True)
    mantras = db.relationship('Mantra', backref='character', lazy=True)
    shentongs = db.relationship('Shentong', backref='character', lazy=True)
    meridians = db.relationship('Meridian', backref='character', lazy=True)
    pets = db.relationship('Pet', backref='owner', lazy=True)
    lingzhis = db.relationship('Lingzhi', backref='owner', lazy=True)

# 人物属性模型
class CharacterAttribute(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    hp = db.Column(db.Integer, default=100)
    attack = db.Column(db.Integer, default=10)
    defense = db.Column(db.Integer, default=10)
    speed = db.Column(db.Integer, default=10)
    crit_rate = db.Column(db.Float, default=0.05)
    dodge_rate = db.Column(db.Float, default=0.05)
    hit_rate = db.Column(db.Float, default=0.95)
    crit_damage = db.Column(db.Float, default=1.5)
    vampiric_rate = db.Column(db.Float, default=0.0)
    tenacity_rate = db.Column(db.Float, default=0.0)
    counter_rate = db.Column(db.Float, default=0.0)
    penetration_rate = db.Column(db.Float, default=0.0)

# 境界模型
class Realm(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    stage = db.Column(db.Integer, nullable=False)
    coefficient = db.Column(db.Float, nullable=False)

# 装备模型
class Equipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    slot = db.Column(db.Integer, nullable=False)  # 装备栏位 1-10
    type = db.Column(db.String(20), nullable=False)  # 武器、头盔、项链、衣服、腰带、鞋子、耳环、戒指、手镯、护符
    name = db.Column(db.String(50), nullable=False)
    quality = db.Column(db.String(10), default='黄阶')  # 黄阶、玄阶、地阶、天阶
    level = db.Column(db.Integer, default=1)
    max_level = db.Column(db.Integer, default=10)  # 根据品质决定：黄阶10，玄阶20，地阶30，天阶40
    experience = db.Column(db.BigInteger, default=0)
    attack_bonus = db.Column(db.Integer, default=0)
    defense_bonus = db.Column(db.Integer, default=0)
    hp_bonus = db.Column(db.Integer, default=0)
    speed_bonus = db.Column(db.Integer, default=0)
    crit_rate_bonus = db.Column(db.Float, default=0)
    dodge_rate_bonus = db.Column(db.Float, default=0)
    strengthen_times = db.Column(db.Integer, default=0)
    rune_slots = db.Column(db.Integer, default=1)
    equipped = db.Column(db.Boolean, default=True)  # 是否已装备

# 法宝模型
class Treasure(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    slot = db.Column(db.Integer, nullable=False)  # 1-6
    name = db.Column(db.String(50), nullable=False)
    quality = db.Column(db.String(10), default='普通')
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.BigInteger, default=0)
    linggen = db.Column(db.String(10), default='无')
    attack_bonus = db.Column(db.Integer, default=0)
    defense_bonus = db.Column(db.Integer, default=0)
    hp_bonus = db.Column(db.Integer, default=0)
    speed_bonus = db.Column(db.Integer, default=0)
    crit_rate_bonus = db.Column(db.Float, default=0)
    dodge_rate_bonus = db.Column(db.Float, default=0)
    hit_rate_bonus = db.Column(db.Float, default=0)
    crit_damage_bonus = db.Column(db.Float, default=0)
    vampiric_rate_bonus = db.Column(db.Float, default=0)
    tenacity_rate_bonus = db.Column(db.Float, default=0)
    counter_rate_bonus = db.Column(db.Float, default=0)
    penetration_rate_bonus = db.Column(db.Float, default=0)
    rune_slots = db.Column(db.Integer, default=1)
    awakened = db.Column(db.Boolean, default=False)
    special_skill = db.Column(db.String(100), nullable=True)
    recast_times = db.Column(db.Integer, default=0)

# 符文模型
class Rune(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    quality = db.Column(db.String(10), default='普通')
    attribute_type = db.Column(db.String(20), nullable=False)
    attribute_value = db.Column(db.Integer, default=0)
    owner_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=True)
    treasure_id = db.Column(db.Integer, db.ForeignKey('treasure.id'), nullable=True)

# 功法模型
class Mantra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    quality = db.Column(db.String(10), default='黄阶')  # 黄阶、玄阶、地阶、天阶
    level = db.Column(db.Integer, default=1)
    max_level = db.Column(db.Integer, default=10)  # 根据品质决定：黄阶10，玄阶20，地阶30，天阶40
    experience = db.Column(db.BigInteger, default=0)
    proficiency = db.Column(db.String(10), default='入门')  # 入门、小成、大成、圆满
    proficiency_exp = db.Column(db.Integer, default=0)
    proficiency_max = db.Column(db.Integer, default=100)  # 熟练度上限
    linggen_required = db.Column(db.String(10))  # 灵根要求
    equipped = db.Column(db.Boolean, default=False)  # 是否装备
    slot = db.Column(db.Integer, default=0)  # 装备槽位 0-5
    attack_bonus = db.Column(db.Integer, default=0)
    defense_bonus = db.Column(db.Integer, default=0)
    hp_bonus = db.Column(db.Integer, default=0)
    speed_bonus = db.Column(db.Integer, default=0)
    crit_rate_bonus = db.Column(db.Float, default=0)
    special_effect = db.Column(db.String(100))  # 特殊效果描述

# 神通模型
class Shentong(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    level = db.Column(db.Integer, default=1)
    max_level = db.Column(db.Integer, default=10)  # 神通最大10级
    experience = db.Column(db.BigInteger, default=0)
    proficiency = db.Column(db.Integer, default=0)  # 熟练度0-100
    trigger_rate = db.Column(db.Float, default=0.1)  # 触发概率，基于熟练度计算
    equipped = db.Column(db.Boolean, default=False)  # 是否装备
    slot = db.Column(db.Integer, default=0)  # 装备槽位 0-2
    damage_multiplier = db.Column(db.Float, default=1.0)  # 伤害倍率
    effect_description = db.Column(db.Text)  # 效果描述
    cooldown = db.Column(db.Integer, default=3)  # 冷却回合

# 经脉模型
class Meridian(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Allow character_id to be nullable for global/template meridians
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=True)
    name = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(20), default='十二经脉')
    coefficient = db.Column(db.Float, default=1.5)
    is_open = db.Column(db.Boolean, default=False)
    acupoints = db.relationship('Acupoint', backref='meridian', lazy=True)

# 穴位模型
class Acupoint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meridian_id = db.Column(db.Integer, db.ForeignKey('meridian.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    level = db.Column(db.Integer, default=0)
    max_level = db.Column(db.Integer, default=10)
    attribute_bonus = db.Column(db.Integer, default=0)

# 宠物模型
class Pet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(20), default='普通')  # 宠物类型：普通、稀有、传说、神兽
    quality = db.Column(db.String(10), default='普通')  # 品质：普通、精良、稀有、史诗、传说
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.BigInteger, default=0)
    intimacy_level = db.Column(db.Integer, default=1)  # 亲密度等级1-10
    intimacy_exp = db.Column(db.Integer, default=0)  # 亲密度经验
    max_intimacy_exp = db.Column(db.Integer, default=100)  # 亲密度经验上限
    skill_name = db.Column(db.String(50))  # 宠物技能名称
    skill_trigger_rate = db.Column(db.Float, default=0.1)  # 技能触发概率
    attack_bonus = db.Column(db.Integer, default=0)
    defense_bonus = db.Column(db.Integer, default=0)
    hp_bonus = db.Column(db.Integer, default=0)
    speed_bonus = db.Column(db.Integer, default=0)
    crit_rate_bonus = db.Column(db.Float, default=0)
    captured_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    last_feed_time = db.Column(db.DateTime)  # 最后喂养时间
    last_play_time = db.Column(db.DateTime)  # 最后陪伴时间

# 宗门模型
class Sect(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    level = db.Column(db.Integer, default=1)
    max_level = db.Column(db.Integer, default=100)
    prosperity = db.Column(db.Integer, default=0)  # 繁荣度
    contribution = db.Column(db.Integer, default=0)  # 贡献值
    power = db.Column(db.Integer, default=0)  # 实力值
    construction = db.Column(db.Integer, default=0)  # 建设度
    prestige = db.Column(db.Integer, default=0)  # 威望值
    description = db.Column(db.Text)  # 宗门简介
    resources = db.Column(db.Text)  # 宗门资源JSON
    facilities = db.Column(db.Text)  # 宗门设施JSON
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    last_activity = db.Column(db.DateTime, default=db.func.current_timestamp())
    members = db.relationship('SectMember', backref='sect', lazy=True)
    tasks = db.relationship('SectTask', backref='sect', lazy=True)
    alliances = db.relationship('SectAlliance', backref='sect', lazy=True)

# 宗门成员模型
class SectMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sect_id = db.Column(db.Integer, db.ForeignKey('sect.id'), nullable=False)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    position = db.Column(db.String(20), default='弟子')  # 宗主、大长老、长老、执事、弟子
    contribution = db.Column(db.Integer, default=0)  # 个人贡献值
    total_contribution = db.Column(db.Integer, default=0)  # 累计贡献值
    joined_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    last_active = db.Column(db.DateTime, default=db.func.current_timestamp())
    permissions = db.Column(db.Text)  # 权限JSON

# 宗门任务模型
class SectTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sect_id = db.Column(db.Integer, db.ForeignKey('sect.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    type = db.Column(db.String(20), default='日常')  # 日常、周常、活动
    requirements = db.Column(db.Text)  # 任务要求JSON
    rewards = db.Column(db.Text)  # 奖励JSON
    status = db.Column(db.String(20), default='进行中')  # 进行中、已完成、已过期
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    deadline = db.Column(db.DateTime)
    participants = db.Column(db.Text)  # 参与者JSON

# 宗门活动模型
class SectActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sect_id = db.Column(db.Integer, db.ForeignKey('sect.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    type = db.Column(db.String(20), default='修炼')  # 修炼、比武、建设、探索
    status = db.Column(db.String(20), default='准备中')  # 准备中、进行中、已结束
    participants = db.Column(db.Text)  # 参与者JSON
    rewards = db.Column(db.Text)  # 奖励JSON
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

# 宗门商店模型
class SectShop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sect_id = db.Column(db.Integer, db.ForeignKey('sect.id'), nullable=False)
    item_name = db.Column(db.String(50), nullable=False)
    item_type = db.Column(db.String(20), nullable=False)
    item_quality = db.Column(db.String(10), default='普通')
    price = db.Column(db.Integer, default=0)  # 贡献值价格
    stock = db.Column(db.Integer, default=1)  # 库存
    description = db.Column(db.Text)
    added_at = db.Column(db.DateTime, default=db.func.current_timestamp())

# 宗门比武模型
class SectTournament(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sect_id = db.Column(db.Integer, db.ForeignKey('sect.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='报名中')  # 报名中、进行中、已结束
    participants = db.Column(db.Text)  # 参赛者JSON
    brackets = db.Column(db.Text)  # 对阵表JSON
    winner_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=True)
    rewards = db.Column(db.Text)  # 奖励JSON
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

# 宗门联盟模型
class SectAlliance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    leader_sect_id = db.Column(db.Integer, db.ForeignKey('sect.id'), nullable=False)
    member_sects = db.Column(db.Text)  # 成员宗门JSON
    alliance_power = db.Column(db.Integer, default=0)  # 联盟实力值
    alliance_prestige = db.Column(db.Integer, default=0)  # 联盟威望值
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    # Relationship to leader sect
    leader_sect = db.relationship('Sect', foreign_keys=[leader_sect_id])

# 丹药模型
class Pill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    quality = db.Column(db.String(10), default='凡品')  # 凡品、黄品、玄品、地品、天品、无上
    level = db.Column(db.Integer, default=1)  # 丹药等级1-10
    effect_type = db.Column(db.String(20))  # 突破境界、属性提升、治疗、解毒等
    effect_value = db.Column(db.Integer, default=0)  # 效果数值
    success_rate = db.Column(db.Float, default=0.5)  # 炼制成功率
    materials_required = db.Column(db.Text)  # 所需材料JSON
    difficulty = db.Column(db.Integer, default=1)  # 炼制难度1-10
    description = db.Column(db.Text)  # 丹药描述
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

# 灵植模型
class Lingzhi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    quality = db.Column(db.String(10), default='凡品')  # 凡品、黄品、玄品、地品、天品、无上
    level = db.Column(db.Integer, default=1)  # 灵植等级1-10
    growth_stage = db.Column(db.String(20), default='种子')  # 种子、发芽、生长、开花、结果、成熟
    growth_time = db.Column(db.Integer, default=0)  # 当前生长时间（分钟）
    max_growth_time = db.Column(db.Integer, default=60)  # 成熟所需时间（分钟）
    mutation_rate = db.Column(db.Float, default=0.01)  # 变异概率
    has_mutated = db.Column(db.Boolean, default=False)  # 是否已变异
    attribute_type = db.Column(db.String(10), default='无')  # 变异属性：攻击、防御、生命、速度等
    attribute_value = db.Column(db.Integer, default=0)  # 属性加成值
    water_level = db.Column(db.Integer, default=50)  # 水分等级0-100
    fertilizer_level = db.Column(db.Integer, default=50)  # 肥料等级0-100
    sunlight_level = db.Column(db.Integer, default=50)  # 日照等级0-100
    planted_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    last_cared_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    description = db.Column(db.Text)  # 灵植描述

# 灵田模型（用于种植灵植）
class Lingtian(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    slot = db.Column(db.Integer, default=1)  # 灵田槽位1-6
    lingzhi_id = db.Column(db.Integer, db.ForeignKey('lingzhi.id'), nullable=True)
    soil_quality = db.Column(db.String(10), default='普通')  # 普通、优质、极品
    irrigation_level = db.Column(db.Integer, default=0)  # 灌溉等级
    fertilizer_level = db.Column(db.Integer, default=0)  # 施肥等级
    is_occupied = db.Column(db.Boolean, default=False)
    planted_at = db.Column(db.DateTime)
    # Relationships
    lingzhi = db.relationship('Lingzhi', backref='lingtian', uselist=False)

# 炼丹炉模型
class PillFurnace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    level = db.Column(db.Integer, default=1)  # 炼丹炉等级
    quality = db.Column(db.String(10), default='普通')  # 普通、优质、极品
    success_rate_bonus = db.Column(db.Float, default=0.0)  # 成功率加成
    pill_quality_bonus = db.Column(db.String(10), default='无')  # 丹药品质加成
    description = db.Column(db.Text)

# 丹药物品模型（玩家拥有的丹药）
class PillItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    pill_id = db.Column(db.Integer, db.ForeignKey('pill.id'), nullable=False)  # 丹药模板ID
    quantity = db.Column(db.Integer, default=1)  # 数量
    acquired_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    pill = db.relationship('Pill', backref='items', lazy=True)

# 战斗记录模型
class Battle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    opponent_type = db.Column(db.String(20))
    result = db.Column(db.String(10))
    experience_gained = db.Column(db.BigInteger, default=0)
    items_gained = db.Column(db.Text)
    battle_time = db.Column(db.DateTime, default=db.func.current_timestamp())

# 怪物模型
class Monster(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    level = db.Column(db.Integer, default=1)
    hp = db.Column(db.Integer, default=100)
    attack = db.Column(db.Integer, default=10)
    defense = db.Column(db.Integer, default=5)
    speed = db.Column(db.Integer, default=8)
    linggen = db.Column(db.String(10), default='无')  # 金、木、水、火、土
    experience_reward = db.Column(db.Integer, default=50)
    lingshi_reward = db.Column(db.Integer, default=20)
    drop_items = db.Column(db.Text)  # JSON格式的掉落物品
    description = db.Column(db.Text)
    ai_type = db.Column(db.String(20), default='普通')  # 普通、精英、BOSS

# 副本模型
class Dungeon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    level_requirement = db.Column(db.Integer, default=1)
    difficulty = db.Column(db.String(10), default='普通')  # 普通、困难、噩梦、地狱
    monster_ids = db.Column(db.Text)  # JSON格式的怪物ID列表
    rewards = db.Column(db.Text)  # JSON格式的奖励
    description = db.Column(db.Text)
    completion_time_limit = db.Column(db.Integer, default=1800)  # 完成时间限制（秒）

# 战斗状态模型
class CombatState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    monster_id = db.Column(db.Integer, db.ForeignKey('monster.id'), nullable=True)
    dungeon_id = db.Column(db.Integer, db.ForeignKey('dungeon.id'), nullable=True)
    current_turn = db.Column(db.Integer, default=0)
    weather = db.Column(db.String(20), default='晴天')
    character_hp = db.Column(db.Integer, default=100)
    monster_hp = db.Column(db.Integer, default=100)
    status_effects = db.Column(db.Text)  # JSON格式的状态效果
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

# 生活技能模型
class LifeSkill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    skill_type = db.Column(db.String(20), nullable=False)  # 锻造、炼丹、符文、鉴定、采集、种植
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.Integer, default=0)
    proficiency = db.Column(db.Integer, default=0)  # 熟练度0-100

# 鉴定结果模型
class Identification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    item_type = db.Column(db.String(20), nullable=False)  # 装备、法宝、符文等
    item_id = db.Column(db.Integer, nullable=False)
    identified_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    success = db.Column(db.Boolean, default=True)

# 材料模型
class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 矿石、草药、木材、灵材等
    quality = db.Column(db.String(10), default='普通')
    rarity = db.Column(db.String(10), default='常见')  # 常见、稀有、珍贵、传说
    description = db.Column(db.Text)
    base_value = db.Column(db.Integer, default=10)  # 基础价值

# 玩家材料库存模型
class MaterialInventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('material.id'), nullable=False)
    quantity = db.Column(db.Integer, default=0)

# 世界地图模型
class WorldMap(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(20))
    resources = db.Column(db.Text)
    weather = db.Column(db.String(20), default='晴天')
    coordinates_x = db.Column(db.Integer, default=0)
    coordinates_y = db.Column(db.Integer, default=0)
    discovered_by = db.Column(db.Text)  # JSON格式，发现者ID列表
    special_events = db.Column(db.Text)  # JSON格式的特殊事件

# 资源模型
class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    type = db.Column(db.String(20))
    amount = db.Column(db.BigInteger, default=0)

# 任务模型
class Quest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    type = db.Column(db.String(20))
    status = db.Column(db.String(20), default='进行中')
    reward_experience = db.Column(db.BigInteger, default=0)
    reward_items = db.Column(db.Text)

# 成就模型
class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    unlocked = db.Column(db.Boolean, default=False)
    unlocked_at = db.Column(db.DateTime)

# 好友模型
class Friendship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    status = db.Column(db.String(20), default='好友')
    intimacy = db.Column(db.Integer, default=0)

# 邮件模型
class Mail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text)
    sent_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    read_status = db.Column(db.Boolean, default=False)

# 排行榜模型
class Ranking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    type = db.Column(db.String(20))
    score = db.Column(db.BigInteger, default=0)
    rank = db.Column(db.Integer, default=0)

# 商城模型
class Shop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_type = db.Column(db.String(20))
    item_id = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    discount = db.Column(db.Float, default=1.0)

# 交易模型
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    item_type = db.Column(db.String(20))
    item_id = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    fee = db.Column(db.Float, default=0.05)
    transaction_time = db.Column(db.DateTime, default=db.func.current_timestamp())

# 竞技场模型
class Arena(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    rank = db.Column(db.Integer, default=0)
    rating = db.Column(db.Integer, default=1000)  # 天梯积分
    wins = db.Column(db.Integer, default=0)
    losses = db.Column(db.Integer, default=0)
    streak = db.Column(db.Integer, default=0)  # 连胜场次
    last_match = db.Column(db.DateTime)
    season_high = db.Column(db.Integer, default=1000)

# PVP战斗记录模型
class PVPMatch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    winner_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    loser_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    winner_rating_change = db.Column(db.Integer, default=0)
    loser_rating_change = db.Column(db.Integer, default=0)
    match_type = db.Column(db.String(20), default='ranked')  # ranked, casual
    match_time = db.Column(db.DateTime, default=db.func.current_timestamp())

# 图鉴模型
class Codex(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    entry_type = db.Column(db.String(20), nullable=False)  # monster, equipment, mantra, treasure
    entry_id = db.Column(db.Integer, nullable=False)
    discovered_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    discovery_count = db.Column(db.Integer, default=1)

# 师徒关系模型
class Mentorship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    master_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    apprentice_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    status = db.Column(db.String(20), default='进行中')  # 进行中、已完成、已终止
    started_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    completed_at = db.Column(db.DateTime)
    lessons_given = db.Column(db.Integer, default=0)
    mantras_taught = db.Column(db.Text)  # JSON格式的传授功法

# 历练任务模型
class TrialQuest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    trial_points = db.Column(db.Integer, default=0)  # 历练值奖励
    requirements = db.Column(db.Text)  # JSON格式的要求
    status = db.Column(db.String(20), default='未开始')  # 未开始、进行中、已完成
    progress = db.Column(db.Text)  # JSON格式的进度
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)

# 活动模型
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    type = db.Column(db.String(20), default='节日')  # 节日、限时、竞技
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    rewards = db.Column(db.Text)  # JSON格式的奖励
    requirements = db.Column(db.Text)  # JSON格式的参与要求
    status = db.Column(db.String(20), default='未开始')  # 未开始、进行中、已结束
    participants = db.Column(db.Text)  # JSON格式的参与者

# 背包模型
class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    item_type = db.Column(db.String(20), nullable=False)  # equipment, treasure, pill, material, rune
    item_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, default=1)
    acquired_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    is_equipped = db.Column(db.Boolean, default=False)
    slot = db.Column(db.Integer, default=0)  # 装备槽位

# 聊天消息模型
class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=True)  # 私聊时使用
    channel = db.Column(db.String(20), default='world')  # world, sect, private, system
    content = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    is_read = db.Column(db.Boolean, default=False)

# 组队模型
class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    leader_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    max_members = db.Column(db.Integer, default=5)
    min_level = db.Column(db.Integer, default=1)
    max_level = db.Column(db.Integer, default=100)
    activity_type = db.Column(db.String(20), default='dungeon')  # dungeon, exploration, pvp
    status = db.Column(db.String(20), default='recruiting')  # recruiting, full, active, disbanded
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    members = db.relationship('TeamMember', backref='team', lazy=True)

# 组队成员模型
class TeamMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    role = db.Column(db.String(20), default='member')  # leader, member
    joined_at = db.Column(db.DateTime, default=db.func.current_timestamp())

# 世界事件模型
class WorldEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    event_type = db.Column(db.String(20), nullable=False)  # natural_disaster, treasure_spawn, monster_surge, etc.
    severity = db.Column(db.String(10), default='normal')  # minor, normal, major, catastrophic
    affected_regions = db.Column(db.Text)  # JSON format regions
    effects = db.Column(db.Text)  # JSON format effects
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

# 灵根改变记录模型
class LinggenChange(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    old_linggen = db.Column(db.String(10), nullable=False)
    new_linggen = db.Column(db.String(10), nullable=False)
    change_method = db.Column(db.String(20), nullable=False)  # item, event, special_quest
    change_item = db.Column(db.String(50))  # 如果是通过道具改变
    changed_at = db.Column(db.DateTime, default=db.func.current_timestamp())

# 保底计数器模型
class GuaranteedDrop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    drop_type = db.Column(db.String(20), nullable=False)  # equipment, treasure, pet, etc.
    attempts = db.Column(db.Integer, default=0)
    guaranteed = db.Column(db.Boolean, default=False)
    last_attempt = db.Column(db.DateTime, default=db.func.current_timestamp())

# 境界突破记录模型
class RealmBreakthroughRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    from_realm = db.Column(db.String(20), nullable=False)
    to_realm = db.Column(db.String(20), nullable=False)
    purity = db.Column(db.Float, nullable=False)  # 纯度系数
    pill_quality = db.Column(db.String(10))  # 丹药品质
    mantra_compat = db.Column(db.Float, default=1.0)  # 功法契合度
    success = db.Column(db.Boolean, nullable=False)
    attempted_at = db.Column(db.DateTime, default=db.func.current_timestamp())
