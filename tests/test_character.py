import pytest
from app import app, db
from models import User, Character, CharacterAttribute
from utils.helpers import exp_for_level


def test_character_levelup_flow():
    client = app.test_client()

    # 注册用户
    resp = client.post('/register', json={'username': 'char_test', 'password': 'pass123', 'email': 'ct@example.com'})
    assert resp.status_code in (200, 201)

    # 登录
    resp = client.post('/login', json={'username': 'char_test', 'password': 'pass123'})
    assert resp.status_code == 200
    token = resp.get_json().get('token')
    assert token
    headers = {'Authorization': token}

    # 创建人物
    resp = client.post('/character', headers=headers, json={'name': '测试角', 'linggen': '火'})
    assert resp.status_code in (200, 201)

    # 获取人物，确认初始等级
    resp = client.get('/character', headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['level'] == 1

    # 给人物添加足够经验以升级
    from models import Character as C
    with app.app_context():
        user = User.query.filter_by(username='char_test').first()
        char = Character.query.filter_by(user_id=user.id).first()
        needed = exp_for_level(char.level)
        print(f"DEBUG: Character level before setting exp: {char.level}")
        print(f"DEBUG: Experience needed for level {char.level}: {needed}")
        char.experience = needed
        db.session.commit()

        # Double check the character state
        char_after = Character.query.filter_by(user_id=user.id).first()
        print(f"DEBUG: Character level after setting exp: {char_after.level}")
        print(f"DEBUG: Character experience after setting exp: {char_after.experience}")

    # 请求升级
    resp = client.post('/character/levelup', headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()
    print(f"DEBUG: Levelup response - new_level: {data['new_level']}")
    assert data['new_level'] == 2

    # 验证属性增加
    resp = client.get('/character', headers=headers)
    data = resp.get_json()
    print(f"DEBUG: Final character level: {data['level']}")
    assert data['level'] == 2
    assert data['attributes']['hp'] > 100
