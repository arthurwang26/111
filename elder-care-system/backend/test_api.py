import requests

r_login = requests.post('http://localhost:8000/auth/login', data={'username':'arthur', 'password':'arthur'})
token = r_login.json().get('access_token')

if not token:
    print("Login failed:", r_login.text)
else:
    r_res = requests.get('http://localhost:8000/api/residents', headers={'Authorization': f'Bearer {token}'})
    print("API Response:")
    print(r_res.text)
