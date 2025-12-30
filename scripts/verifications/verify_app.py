import requests
import sys

try:
    response = requests.get('http://localhost:8501', timeout=5)
    print(f"✅ Status Code: {response.status_code}")
    
    if response.status_code == 200:
        html = response.text
        print(f"✅ Response received: {len(html)} bytes")
        
        # Check for Streamlit
        if 'streamlit' in html.lower():
            print("✅ Streamlit detected in response")
        
        # Check for errors
        if 'error' in html.lower() or 'exception' in html.lower():
            print("⚠️  Warning: 'error' or 'exception' found in HTML")
        else:
            print("✅ No errors detected in HTML")
            
        # Check for title
        if '<title>' in html:
            title = html.split('<title>')[1].split('</title>')[0]
            print(f"✅ Page title: {title}")
        
        print("\n🎉 AGStock application is running successfully!")
        sys.exit(0)
    else:
        print(f"❌ Unexpected status code: {response.status_code}")
        sys.exit(1)
        
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to http://localhost:8501")
    print("   Make sure Streamlit is running")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
