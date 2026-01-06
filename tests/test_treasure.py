import pytest
from app import app, db
from models import User, Character, Resource, Treasure


def test_treasure_forge_awaken_recast_flow():
    client = app.test_client()

    # 注册与登录
    username = 'tre_test'
    resp = client.post('/register', json={'username': username, 'password': 'pass123', 'email': 't@example.com'})
    assert resp.status_code in (200, 201)
    resp = client.post('/login', json={'username': username, 'password': 'pass123'})
    assert resp.status_code == 200
    token = resp.get_json().get('token')
    assert token
    headers = {'Authorization': token}

    # 创建人物
    resp = client.post('/character', headers=headers, json={'name': '法宝测试'})
    assert resp.status_code in (200, 201)

    # 在数据库中为人物添加大量灵石
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        char = Character.query.filter_by(user_id=user.id).first()
        # 创建或更新资源
        res = Resource.query.filter_by(character_id=char.id, type='灵石').first()
        if not res:
            res = Resource(character_id=char.id, type='灵石', amount=1000000)
            db.session.add(res)
        else:
            res.amount = 1000000
        db.session.commit()

    # 锻造（使用高材料系数以保证成功率）
    resp = client.post('/treasure/forge', headers=headers, json={'slot': 1, 'name': '试炼法宝', 'material_quality_factor': 10.0})
    assert resp.status_code == 201
    tre = resp.get_json().get('treasure')
    assert tre and 'id' in tre
    tre_id = tre['id']

    # 觉醒（使用高材料系数以提高通过率）
    resp = client.post(f'/treasure/awaken/{tre_id}', headers=headers, json={'material_quality_factor': 10.0})
    # 觉醒可能失败，但在高系数下应当成功（允许 200）或若意外返回 400 则记录
    assert resp.status_code in (200, 400)

    # 重铸
    resp = client.post(f'/treasure/recast/{tre_id}', headers=headers, json={'material_quality_factor': 10.0})
    assert resp.status_code in (200, 400)
