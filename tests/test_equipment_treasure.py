from app import app, db
from models import User, Character, CharacterAttribute, Equipment, Resource, Rune


def test_forge_rune_and_strengthen_equipment():
    client = app.test_client()

    # 注册并登录
    client.post('/register', json={'username': 'eq_test', 'password': 'pw', 'email': 'eq@example.com'})
    resp = client.post('/login', json={'username': 'eq_test', 'password': 'pw'})
    token = resp.get_json().get('token')
    headers = {'Authorization': token}

    # 创建人物
    client.post('/character', headers=headers, json={'name': '装备师', 'linggen': '土'})

    # 准备灵石资源
    with app.app_context():
        user = User.query.filter_by(username='eq_test').first()
        char = Character.query.filter_by(user_id=user.id).first()
        r = Resource(character_id=char.id, type='灵石', amount=10000)
        db.session.add(r)
        # 创建一件装备
        eq = Equipment(character_id=char.id, slot=1, type='武器', name='测试剑')
        db.session.add(eq)
        db.session.commit()
        equip_id = eq.id

    # 锻造符文
    resp = client.post('/rune/forge', headers=headers, json={'name': '烈攻', 'quality': '精良', 'attribute_type': 'attack', 'attribute_value': 15, 'material_quality_factor': 1.2})
    if resp.status_code == 201:
        rune_id = resp.get_json().get('rune_id')
        # 镶嵌到装备
        resp2 = client.post('/rune/equip/equipment', headers=headers, json={'rune_id': rune_id, 'equip_id': equip_id})
        assert resp2.status_code == 200

    # 强化装备多次，直到至少尝试一次成功或者几次失败
    success = False
    for i in range(3):
        resp = client.post(f'/equipment/strengthen/{equip_id}', headers=headers, json={'material_quality_factor': 1.0})
        if resp.status_code == 200:
            success = True
            break
    assert success or resp.status_code in (400,)
