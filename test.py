import urllib.request, json
req = urllib.request.Request('http://localhost:8000/api/register', data=b'{"username":"test3","password":"123"}', headers={'Content-Type': 'application/json'}, method='POST')
try:
    urllib.request.urlopen(req)
except Exception as e:
    if hasattr(e, 'read'):
        print(e.read().decode('utf-8'))
    else:
        print(e)
