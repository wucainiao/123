# API 文档（概要）

后端使用 Flask 实现，常用接口包括：

- POST /register: 注册，body: {username, password, email}
- POST /login: 登录，body: {username, password}
- GET /character: 获取人物信息，需在 Header 中传 `Authorization: <token>`
- POST /character: 创建人物，body: {name, linggen, wuxing, qiyun}
- POST /character/levelup: 人物升级
- GET /equipment: 获取装备
- POST /equipment/upgrade/<equip_id>: 装备升级
- GET /treasure: 获取法宝
- POST /treasure/forge: 锻造法宝

更多接口详见 docs/openapi.yaml
