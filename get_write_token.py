import base64
import requests

app_id = "1592488"
app_secret = "1e05bd0433b2f88ff3329fb916db0f3905b206e0"
redirect_uri = "http://localhost/"
scopes = "boards:read,boards:write,pins:read,pins:write"

url = f"https://www.pinterest.com/oauth/?client_id={app_id}&redirect_uri={redirect_uri}&response_type=code&scope={scopes}"

print("\n--- PINTEREST OAUTH FLOW ---")
print(f"1. Open this link in your browser and click 'Give Access':\n\n{url}\n")
print("2. After authorizing, your browser will redirect to a page that won't load (http://localhost/...).")
print("3. Look at your browser address bar and copy the string after '?code='")

code = input("\n4. Paste the code here: ").strip()

print("\nExchanging code for token...")

auth_str = f"{app_id}:{app_secret}"
b64_auth = base64.b64encode(auth_str.encode()).decode()

token_url = "https://api.pinterest.com/v5/oauth/token"
headers = {
    "Authorization": f"Basic {b64_auth}",
    "Content-Type": "application/x-www-form-urlencoded"
}
data = {
    "grant_type": "authorization_code",
    "code": code,
    "redirect_uri": redirect_uri
}

response = requests.post(token_url, headers=headers, data=data)
res_data = response.json()

if "access_token" in res_data:
    print("\n✅ SUCCESS! Here is your write-enabled token:\n")
    print(res_data["access_token"])
else:
    print("\n❌ Failed to get token:")
    print(res_data)
