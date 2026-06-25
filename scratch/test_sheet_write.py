import gspread
from oauth2client.service_account import ServiceAccountCredentials

def main():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name("claves.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open("inventario_tienda").sheet1
        
        fila = 234  # Fila de prueba que tiene "vidrio templado tablet"
        col_precio = 5  # Columna "Precio Mercado" (es la columna E, que es la 5)
        
        # 1. Leer el valor actual
        val_original = sheet.cell(fila, col_precio).value
        print(f"Valor original en fila {fila}, col {col_precio}: {repr(val_original)}")
        
        # 2. Escribir 11000 como string
        print("Escribiendo '11000'...")
        sheet.update_cell(fila, col_precio, "11000")
        
        # 3. Leer de nuevo el valor
        val_despues = sheet.cell(fila, col_precio).value
        print(f"Valor después de escribir '11000': {repr(val_despues)}")
        
        # 4. Restaurar el valor original para no alterar datos de producción
        sheet.update_cell(fila, col_precio, val_original)
        print("Valor original restaurado.")
        
    except Exception as e:
        print("ERROR:", e)

if __name__ == "__main__":
    main()
