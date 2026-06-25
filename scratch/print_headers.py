import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("claves.json", scope)
client = gspread.authorize(creds)
sheet = client.open("inventario_tienda").sheet1
headers = sheet.row_values(4)
print("Row 4 headers:", headers)
