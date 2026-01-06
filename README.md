# 修仙游戏

基于设计文档和实施计划开发的完整修仙游戏。

## 技术栈
- 后端：Python + Flask + SQLAlchemy + MySQL
- 前端：HTML + CSS + JavaScript + Bootstrap

## 安装和运行

### 后端
1. 安装依赖：
   ```
   pip install -r requirements.txt
   ```

2. 设置MySQL数据库，运行init.sql创建表。

3. 设置环境变量：
   - DATABASE_URL=mysql://username:password@localhost/xianxia_game
   - SECRET_KEY=your-secret-key

4. 运行：
   ```
   python app.py
   ```

### 前端
打开index.html在浏览器中。

## 功能模块
- 用户注册登录
- 人物创建和管理
- 装备、法宝、功法等系统
- 战斗、宗门等

## API文档
- POST /register: 注册
- POST /login: 登录
- GET /character: 获取人物信息
- POST /character/levelup: 升级人物
- 更多API见app.py

## 部署
使用Gunicorn或Docker部署后端。