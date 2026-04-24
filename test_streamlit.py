import streamlit as st
import os
import requests

st.title("🔍 TwelveData Connection Test")

# Check if API key exists
api_key = os.getenv("TWELVEDATA_API_KEY")
st.write(f"**API Key Status:** {'✅ Set' if api_key else '❌ Missing'}")

if api_key:
    # Test API call
    url = f"https://api.twelvedata.com/time_series?symbol=ARADEL.NGX&interval=1day&outputsize=5&apikey={api_key}"
    try:
        with st.spinner("Fetching data from TwelveData..."):
            res = requests.get(url, timeout=10)
            data = res.json()
            if "values" in 
                st.success("✅ TwelveData Working!")
                st.write(f"**Latest ARADEL Price:** ₦{data['values'][0]['close']}")
                st.json(data['values'][0])
            else:
                st.error(f"❌ API Error: {data}")
    except Exception as e:
        st.error(f"❌ Connection Failed: {e}")
else:
    st.warning("⚠️ Add TWELVEDATA_API_KEY to Streamlit secrets")
