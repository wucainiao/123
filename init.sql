-- 修仙游戏数据库初始化脚本
-- 使用MySQL

CREATE DATABASE IF NOT EXISTS xianxia_game;
USE xianxia_game;

-- 用户表
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL
);

-- 人物表
CREATE TABLE characters (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    name VARCHAR(50) NOT NULL,
    level INT DEFAULT 1,
    experience BIGINT DEFAULT 0,
    realm VARCHAR(20) DEFAULT '凡人期',
    realm_level INT DEFAULT 1,
    linggen VARCHAR(10) DEFAULT '无',
    wuxing INT DEFAULT 0, -- 悟性
    qiyun INT DEFAULT 0, -- 气运
    lianxi INT DEFAULT 0, -- 历练
    reputation INT DEFAULT 0, -- 声望
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 人物属性表
CREATE TABLE character_attributes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    character_id INT NOT NULL,
    hp INT DEFAULT 100,
    attack INT DEFAULT 10,
    defense INT DEFAULT 10,
    speed INT DEFAULT 10,
    crit_rate FLOAT DEFAULT 0.05,
    dodge_rate FLOAT DEFAULT 0.05,
    hit_rate FLOAT DEFAULT 0.95,
    crit_damage FLOAT DEFAULT 1.5,
    vampiric_rate FLOAT DEFAULT 0.0,
    tenacity_rate FLOAT DEFAULT 0.0,
    counter_rate FLOAT DEFAULT 0.0,
    penetration_rate FLOAT DEFAULT 0.0,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE
);

-- 境界表（预定义数据）
CREATE TABLE realms (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(20) UNIQUE NOT NULL,
    stage INT NOT NULL,
    coefficient FLOAT NOT NULL
);

INSERT INTO realms (name, stage, coefficient) VALUES
('凡人期', 1, 0),
('炼气期', 2, 0.5),
('筑基期', 3, 1.2),
('金丹期', 4, 2.5),
('元婴期', 5, 4),
('化神期', 6, 7),
('炼虚期', 7, 10),
('合体期', 8, 14),
('大乘期', 9, 19),
('渡劫期', 10, 25),
('人仙', 11, 32),
('地仙', 11, 40),
('天仙', 11, 49),
('真仙', 11, 59),
('玄仙', 11, 70),
('金仙', 12, 82),
('太乙金仙', 12, 95),
('大罗金仙', 12, 109),
('混元金仙', 13, 124),
('混元大罗金仙', 13, 140),
('天道境', 14, 160),
('大道境', 14, 200);

-- 装备表
CREATE TABLE equipments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    character_id INT NOT NULL,
    type VARCHAR(20) NOT NULL, -- 武器、项链等
    name VARCHAR(50) NOT NULL,
    quality VARCHAR(10) DEFAULT '黄阶', -- 黄阶、玄阶、地阶、天阶
    level INT DEFAULT 1,
    max_level INT DEFAULT 10,
    experience BIGINT DEFAULT 0,
    attack_bonus INT DEFAULT 0,
    defense_bonus INT DEFAULT 0,
    hp_bonus INT DEFAULT 0,
    speed_bonus INT DEFAULT 0,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE
);

-- 法宝表
CREATE TABLE treasures (
    id INT PRIMARY KEY AUTO_INCREMENT,
    character_id INT NOT NULL,
    slot INT NOT NULL, -- 1-6
    name VARCHAR(50) NOT NULL,
    quality VARCHAR(10) DEFAULT '普通', -- 普通、精良、稀有、史诗、传说
    level INT DEFAULT 1,
    experience BIGINT DEFAULT 0,
    linggen VARCHAR(10) DEFAULT '无',
    attack_bonus INT DEFAULT 0,
    defense_bonus INT DEFAULT 0,
    hp_bonus INT DEFAULT 0,
    speed_bonus INT DEFAULT 0,
    crit_rate_bonus FLOAT DEFAULT 0,
    dodge_rate_bonus FLOAT DEFAULT 0,
    hit_rate_bonus FLOAT DEFAULT 0,
    crit_damage_bonus FLOAT DEFAULT 0,
    vampiric_rate_bonus FLOAT DEFAULT 0,
    tenacity_rate_bonus FLOAT DEFAULT 0,
    counter_rate_bonus FLOAT DEFAULT 0,
    penetration_rate_bonus FLOAT DEFAULT 0,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE
);

-- 符文表
CREATE TABLE runes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL,
    quality VARCHAR(10) DEFAULT '普通',
    attribute_type VARCHAR(20) NOT NULL, -- attack, defense等
    attribute_value INT DEFAULT 0
);

-- 功法表
CREATE TABLE mantras (
    id INT PRIMARY KEY AUTO_INCREMENT,
    character_id INT NOT NULL,
    name VARCHAR(50) NOT NULL,
    quality VARCHAR(10) DEFAULT '黄阶',
    level INT DEFAULT 1,
    max_level INT DEFAULT 10,
    experience BIGINT DEFAULT 0,
    proficiency VARCHAR(10) DEFAULT '入门', -- 入门、小成、大成、圆满
    proficiency_exp INT DEFAULT 0,
    linggen_required VARCHAR(10),
    attack_bonus INT DEFAULT 0,
    defense_bonus INT DEFAULT 0,
    hp_bonus INT DEFAULT 0,
    speed_bonus INT DEFAULT 0,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE
);

-- 神通表
CREATE TABLE shentong (
    id INT PRIMARY KEY AUTO_INCREMENT,
    character_id INT NOT NULL,
    name VARCHAR(50) NOT NULL,
    level INT DEFAULT 1,
    proficiency INT DEFAULT 0, -- 熟练度
    trigger_rate FLOAT DEFAULT 0.1,
    effect_description TEXT,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE
);

-- 经脉表
CREATE TABLE meridians (
    id INT PRIMARY KEY AUTO_INCREMENT,
    character_id INT NOT NULL,
    name VARCHAR(50) NOT NULL,
    type VARCHAR(20) DEFAULT '十二经脉', -- 十二经脉、任督二脉
    coefficient FLOAT DEFAULT 1.5,
    is_open BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE
);

-- 穴位表
CREATE TABLE acupoints (
    id INT PRIMARY KEY AUTO_INCREMENT,
    meridian_id INT NOT NULL,
    name VARCHAR(50) NOT NULL,
    level INT DEFAULT 0,
    max_level INT DEFAULT 10,
    attribute_bonus INT DEFAULT 0,
    FOREIGN KEY (meridian_id) REFERENCES meridians(id) ON DELETE CASCADE
);

-- 宠物表
CREATE TABLE pets (
    id INT PRIMARY KEY AUTO_INCREMENT,
    owner_id INT NOT NULL,
    name VARCHAR(50) NOT NULL,
    level INT DEFAULT 1,
    experience BIGINT DEFAULT 0,
    intimacy_level INT DEFAULT 1,
    intimacy_exp INT DEFAULT 0,
    skill_name VARCHAR(50),
    skill_trigger_rate FLOAT DEFAULT 0.1,
    attack_bonus INT DEFAULT 0,
    defense_bonus INT DEFAULT 0,
    hp_bonus INT DEFAULT 0,
    speed_bonus INT DEFAULT 0,
    FOREIGN KEY (owner_id) REFERENCES characters(id) ON DELETE CASCADE
);

-- 宗门表
CREATE TABLE sects (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) UNIQUE NOT NULL,
    level INT DEFAULT 1,
    prosperity INT DEFAULT 0,
    contribution INT DEFAULT 0,
    power INT DEFAULT 0,
    construction INT DEFAULT 0,
    prestige INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 宗门成员表
CREATE TABLE sect_members (
    id INT PRIMARY KEY AUTO_INCREMENT,
    sect_id INT NOT NULL,
    character_id INT NOT NULL,
    position VARCHAR(20) DEFAULT '弟子',
    contribution INT DEFAULT 0,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sect_id) REFERENCES sects(id) ON DELETE CASCADE,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE
);

-- 丹药表
CREATE TABLE pills (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL,
    effect_type VARCHAR(20), -- 属性提升、突破境界等
    effect_value INT DEFAULT 0
);

-- 灵植表
CREATE TABLE lingzhi (
    id INT PRIMARY KEY AUTO_INCREMENT,
    owner_id INT NOT NULL,
    name VARCHAR(50) NOT NULL,
    quality VARCHAR(10) DEFAULT '凡品',
    level INT DEFAULT 1,
    growth_time INT DEFAULT 0,
    mutation_rate FLOAT DEFAULT 0.01,
    attribute_type VARCHAR(10) DEFAULT '无',
    FOREIGN KEY (owner_id) REFERENCES characters(id) ON DELETE CASCADE
);

-- 战斗记录表
CREATE TABLE battles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    character_id INT NOT NULL,
    opponent_type VARCHAR(20), -- 怪物、玩家
    result VARCHAR(10), -- 胜利、失败
    experience_gained BIGINT DEFAULT 0,
    items_gained TEXT,
    battle_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE
);

-- 世界地图表
CREATE TABLE world_maps (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL,
    type VARCHAR(20), -- 山脉、森林等
    resources TEXT,
    weather VARCHAR(20) DEFAULT '晴天'
);

-- 资源表
CREATE TABLE resources (
    id INT PRIMARY KEY AUTO_INCREMENT,
    character_id INT NOT NULL,
    type VARCHAR(20), -- 灵石、经验等
    amount BIGINT DEFAULT 0,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE
);

-- 任务表
CREATE TABLE quests (
    id INT PRIMARY KEY AUTO_INCREMENT,
    character_id INT NOT NULL,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    type VARCHAR(20), -- 主线、支线、日常
    status VARCHAR(20) DEFAULT '进行中',
    reward_experience BIGINT DEFAULT 0,
    reward_items TEXT,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE
);

-- 成就表
CREATE TABLE achievements (
    id INT PRIMARY KEY AUTO_INCREMENT,
    character_id INT NOT NULL,
    name VARCHAR(50) NOT NULL,
    description TEXT,
    unlocked BOOLEAN DEFAULT FALSE,
    unlocked_at TIMESTAMP NULL,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE
);

-- 好友表
CREATE TABLE friendships (
    id INT PRIMARY KEY AUTO_INCREMENT,
    character_id INT NOT NULL,
    friend_id INT NOT NULL,
    status VARCHAR(20) DEFAULT '好友',
    intimacy INT DEFAULT 0,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE,
    FOREIGN KEY (friend_id) REFERENCES characters(id) ON DELETE CASCADE
);

-- 邮件表
CREATE TABLE mails (
    id INT PRIMARY KEY AUTO_INCREMENT,
    sender_id INT NOT NULL,
    receiver_id INT NOT NULL,
    title VARCHAR(100) NOT NULL,
    content TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_status BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (sender_id) REFERENCES characters(id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES characters(id) ON DELETE CASCADE
);

-- 排行榜表
CREATE TABLE rankings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    character_id INT NOT NULL,
    type VARCHAR(20), -- 修为、战力、财富
    score BIGINT DEFAULT 0,
    rank INT DEFAULT 0,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE
);

-- 商城表
CREATE TABLE shops (
    id INT PRIMARY KEY AUTO_INCREMENT,
    item_type VARCHAR(20), -- 装备、法宝、道具
    item_id INT NOT NULL,
    price INT NOT NULL,
    discount FLOAT DEFAULT 1.0
);

-- 交易表
CREATE TABLE transactions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    buyer_id INT NOT NULL,
    seller_id INT NOT NULL,
    item_type VARCHAR(20),
    item_id INT NOT NULL,
    price INT NOT NULL,
    fee FLOAT DEFAULT 0.05,
    transaction_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (buyer_id) REFERENCES characters(id) ON DELETE CASCADE,
    FOREIGN KEY (seller_id) REFERENCES characters(id) ON DELETE CASCADE
);