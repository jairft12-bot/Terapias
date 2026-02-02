import pandas as pd
import requests
import io
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "https://viva1aips-my.sharepoint.com/:x:/g/personal/gsiguenas_viva1a_com_pe/IQDGPInn2jcyT6oJdUfzmJE8AdUWEyt9EHy9QBN2KqK8jYg?e=YsMUjL&download=1"

print(f"Connecting to {url}...")
try:
    response = requests.get(url, verify=False)
    response.raise_for_status()
    
    file_content = io.BytesIO(response.content)
    xl = pd.ExcelFile(file_content)
    
    print("\nAvailable Sheets:")
    for sheet in xl.sheet_names:
        print(f" - '{sheet}'")
        
except Exception as e:
    print(f"Error: {e}")
