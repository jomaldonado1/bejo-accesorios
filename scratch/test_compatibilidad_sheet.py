import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

def main():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name("claves.json", scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open("inventario_tienda")
        
        # Intentar obtener la pestaña
        print("Worksheets:", [w.title for w in spreadsheet.worksheets()])
        
        # En la imagen se ve que dice "Tabla de compatibilidad" en la fila 2 y cabeceras en fila 4.
        # Vamos a ver qué worksheets tiene.
        for ws in spreadsheet.worksheets():
            if "compatibilidad" in ws.title.lower():
                sheet = ws
                print(f"Encontrada pestaña: {ws.title}")
                # Leer las primeras 10 filas para ver cómo vienen los datos
                rows = sheet.get_all_values()
                print("Total rows:", len(rows))
                for i in range(min(12, len(rows))):
                    print(f"Row {i+1}: {rows[i]}")
                break
    except Exception as e:
        print("ERROR:", e)

if __name__ == "__main__":
    main()
