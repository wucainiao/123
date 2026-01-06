import json
import urllib.request
import urllib.error

urls = ['http://127.0.0.1:5000/register', 'http://localhost:5000/register']
for u in urls:
    data = json.dumps({'username':'cors_test_py','password':'pw','email':'cors_py@example.com'}).encode('utf-8')
    req = urllib.request.Request(u, data=data, headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            print(u, 'STATUS', resp.status)
            for k in ['Access-Control-Allow-Origin', 'Content-Type']:
                print('  hdr', k, ':', resp.getheader(k))
            body = resp.read(500).decode('utf-8', errors='ignore')
            print('  body:', body[:200])
    except urllib.error.HTTPError as e:
        print(u, 'HTTPError', e.code)
        print('  hdr:', e.headers.get('Access-Control-Allow-Origin'))
        try:
            print('  body:', e.read(500).decode('utf-8', errors='ignore'))
        except Exception:
            pass
    except Exception as e:
        print(u, 'ERR', type(e).__name__, str(e))
