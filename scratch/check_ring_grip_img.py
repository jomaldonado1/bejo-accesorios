import gspread
from oauth2client.service_account import ServiceAccountCredentials

def main():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name("claves.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open("inventario_tienda").sheet1
        rows = sheet.get_all_values()
        headers = rows[3]
        
        nombre_idx = headers.index("Nombre del Artículo")
        modelo_idx = headers.index("Modelo Exacto")
        img_idx = headers.index("Imagen_URL")
        
        for i, row in enumerate(rows[4:], start=5):
            if "ring grip" in row[modelo_idx].lower():
                print(f"Fila {i}: {row[nombre_idx]} {row[modelo_idx]} -> URL Imagen: {repr(row[img_idx])}")
                
    except Exception as e:
        print("ERROR:", e)

if __name__ == "__main__":
    main()
