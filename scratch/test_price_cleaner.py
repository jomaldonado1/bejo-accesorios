import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import re

def limpiar_precio(val_str):
    if pd.isna(val_str):
        return 0
    
    # Convertir a string y limpiar espacios
    s = str(val_str).strip().replace('$', '')
    
    if not s:
        return 0
        
    # Si tiene comas como separador de miles (ej: 4,500) y no tiene puntos, quitamos la coma
    if ',' in s and '.' not in s:
        s = s.replace(',', '')
    # Si tiene comas y puntos (ej: 4,500.00), quitamos la coma y dejamos el punto
    elif ',' in s and '.' in s:
        s = s.replace(',', '')
        
    try:
        # Intentar convertir a float
        val_float = float(s)
        # Si el valor es menor que 200 (como 4.5, 8.0, 11.0, 5, etc.), lo multiplicamos por 1000
        if val_float < 200:
            return int(val_float * 1000)
        return int(val_float)
    except ValueError:
        # Si falla (por ejemplo si el usuario puso "4.500" con punto y la conversión a float falló o dio otra cosa)
        # Intentamos quitar todos los caracteres no numéricos excepto el punto
        s_clean = re.sub(r'[^\d.]', '', s)
        try:
            val_float = float(s_clean)
            if val_float < 200:
                return int(val_float * 1000)
            return int(val_float)
        except ValueError:
            return 0

def main():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name("claves.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open("inventario_tienda").sheet1
        
        rows = sheet.get_all_values()
        headers = rows[3]
        precio_idx = headers.index("Precio Mercado")
        nombre_idx = headers.index("Nombre del Artículo")
        
        print("Precios limpiados con nueva función:")
        # Mostrar los primeros 30 y algunos específicos
        for i, row in enumerate(rows[4:], start=5):
            orig = row[precio_idx]
            cleaned = limpiar_precio(orig)
            # Solo mostrar si el precio original no está vacío o si queremos inspeccionar
            if orig.strip():
                print(f"Fila {i}: {row[nombre_idx][:25]} -> Original: {repr(orig)} -> Limpiado: {cleaned}")
                
    except Exception as e:
        print("ERROR:", e)

if __name__ == "__main__":
    main()
