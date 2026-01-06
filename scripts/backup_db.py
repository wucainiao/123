"""简单的数据库备份脚本（导出 SQL）。
需要在环境中安装 mysqldump 并配置数据库访问。
"""
import os
import subprocess

DB_URL = os.environ.get('DATABASE_URL', 'mysql://root:password@localhost/xianxia_game')

# 解析为mysqldump需要的参数 (简化解析，假设格式 mysql://user:pass@host/db)

def parse_url(url):
    assert url.startswith('mysql://')
    body = url[len('mysql://'):]
    userpass, hostdb = body.split('@')
    user, password = userpass.split(':')
    host, db = hostdb.split('/')
    return user, password, host, db


def backup(out_file='backup.sql'):
    user, password, host, db = parse_url(DB_URL)
    cmd = ['mysqldump', '-h', host, '-u', user, f'-p{password}', db]
    with open(out_file, 'w', encoding='utf-8') as f:
        subprocess.run(cmd, stdout=f)
    print(f'Backup saved to {out_file}')

if __name__ == '__main__':
    backup()
