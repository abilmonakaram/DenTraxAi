import urllib.request, urllib.parse, json, uuid
u = 'user_'+str(uuid.uuid4())[:8]
print('User:', u)

req1 = urllib.request.Request(
    'http://127.0.0.1:8002/api/register',
    data=json.dumps({'username':u,'password':'p'}).encode(),
    headers={'Content-Type':'application/json'}
)
try:
    res1 = urllib.request.urlopen(req1)
    print('Reg:', res1.read().decode()[:50])
except Exception as e:
    print('RegErr:', e, e.read().decode())

req2 = urllib.request.Request(
    'http://127.0.0.1:8002/api/login',
    data=urllib.parse.urlencode({'username':u, 'password':'p'}).encode()
)
try:
    res2 = urllib.request.urlopen(req2)
    t = json.loads(res2.read().decode())['access_token']
    print('Log:', t[:20])

    req3 = urllib.request.Request(
        'http://127.0.0.1:8002/api/analytics/trends',
        headers={'Authorization': 'Bearer '+t}
    )
    try:
        res3 = urllib.request.urlopen(req3)
        print('Trends:', len(res3.read()))
    except Exception as e:
        print('TrendsErr:', e, e.read().decode())
except Exception as e:
    print('LogErr:', e, e.read().decode())
