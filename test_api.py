import os
import requests

api_key = os.getenv("TWELVEDATA_API_KEY")
print(f"API Key Status: {'✅ Set' if api_key else '❌ Missing'}")

if api_key:
    url = f"https://api.twelvedata.com/time_series?symbol=ARADEL.NGX&interval=1day&outputsize=5&apikey={api_key}"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()
        if "values" in data:
            print(f"✅ TwelveData Working! Latest price: ₦{data['values'][0]['close']}")
        else:
            print(f"❌ API Error: {data}")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
