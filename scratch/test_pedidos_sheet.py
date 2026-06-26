import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

def main():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name("claves.json", scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open("inventario_tienda")
        
        sheet = spreadsheet.worksheet("Pedidos")
        print(f"Pestaña Pedidos - Total rows: {len(sheet.get_all_values())}")
        rows = sheet.get_all_values()
        for i in range(min(5, len(rows))):
            print(f"Row {i+1}: {rows[i]}")
    except Exception as e:
        print("ERROR:", e)

if __name__ == "__main__":
    main()
