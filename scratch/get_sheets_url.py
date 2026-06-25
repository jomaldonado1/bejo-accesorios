import gspread
from oauth2client.service_account import ServiceAccountCredentials

def main():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name("claves.json", scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open("inventario_tienda")
        print("SPREADSHEET_URL:", spreadsheet.url)
    except Exception as e:
        print("ERROR:", e)

if __name__ == "__main__":
    main()
