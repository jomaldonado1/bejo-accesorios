import gspread
from oauth2client.service_account import ServiceAccountCredentials

def main():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name("claves.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open("inventario_tienda").sheet1
        
        # Leer todas las filas
        rows = sheet.get_all_values()
        headers = rows[3]  # Fila 4 son cabeceras
        precio_idx = headers.index("Precio Mercado")
        nombre_idx = headers.index("Nombre del Artículo")
        
        print("Precios leídos con get_all_values():")
        for i, row in enumerate(rows[4:], start=5):
            print(f"Fila {i}: {row[nombre_idx]} -> Precio: {repr(row[precio_idx])}")
            
    except Exception as e:
        print("ERROR:", e)

if __name__ == "__main__":
    main()
