from app import app, db
from models import User, Character

with app.app_context():
    # ensure clean DB
    db.drop_all()
    db.create_all()
    client = app.test_client()
    # register
    resp = client.post('/register', json={'username': 'char_test', 'password': 'pass123', 'email': 'ct@example.com'})
    print('register status', resp.status_code, resp.get_json())
    # login
    resp = client.post('/login', json={'username': 'char_test', 'password': 'pass123'})
    print('login status', resp.status_code, resp.get_json())
    token = resp.get_json().get('token')
    headers = {'Authorization': token}
    # create character
    resp = client.post('/character', headers=headers, json={'name': '测试角', 'linggen': '火'})
    print('create char', resp.status_code, resp.get_json())
    # list characters
    users = User.query.all()
    print('users:', [(u.id, u.username, u.email) for u in users])
    chars = Character.query.all()
    print('characters:', [(c.id, c.user_id, c.name, c.level, c.experience) for c in chars])
