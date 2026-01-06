import json
from app import app, db

# 使用 Flask 测试客户端进行简单的集成测试

def test_register_login_create_character():
    client = app.test_client()

    # 注册
    resp = client.post('/register', json={
        'username': 'testuser',
        'password': 'testpass',
        'email': 'test@example.com'
    })
    assert resp.status_code in (200, 201)

    # 登录
    resp = client.post('/login', json={'username': 'testuser', 'password': 'testpass'})
    assert resp.status_code == 200
    token = resp.get_json().get('token')
    assert token

    headers = {'Authorization': token}

    # 创建人物
    resp = client.post('/character', headers=headers, json={'name': '英雄', 'linggen': '金'})
    assert resp.status_code in (200, 201)

    # 获取人物
    resp = client.get('/character', headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get('name') == '英雄'
