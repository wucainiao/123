import json
import urllib.request
import urllib.error

url = 'http://127.0.0.1:5000/register'
data = json.dumps({'username':'web_test_user','password':'pw','email':'web_test@example.com'}).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={'Content-Type':'application/json'})
try:
    with urllib.request.urlopen(req, timeout=5) as resp:
        print('STATUS', resp.status)
        print('HEADERS:', resp.getheaders())
        body = resp.read().decode('utf-8', errors='ignore')
        print('BODY:\n', body[:2000])
except urllib.error.HTTPError as e:
    print('HTTP ERROR', e.code)
    try:
        body = e.read().decode('utf-8', errors='ignore')
        print('BODY:\n', body[:5000])
    except Exception as ex:
        print('FAILED READ BODY:', ex)
except Exception as e:
    print('ERROR', type(e).__name__, e)
