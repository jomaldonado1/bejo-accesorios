import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time

def limpiar_precio_mercado(val):
    import re
    if val is None:
        return None
    s = str(val).strip().replace('$', '')
    if not s:
        return None
    if ',' in s and '.' not in s:
        s = s.replace(',', '')
    elif ',' in s and '.' in s:
        s = s.replace(',', '')
    try:
        val_float = float(s)
        if val_float < 200:
            return int(val_float * 1000)
        return int(val_float)
    except ValueError:
        s_clean = re.sub(r'[^\d.]', '', s)
        try:
            val_float = float(s_clean)
            if val_float < 200:
                return int(val_float * 1000)
            return int(val_float)
        except ValueError:
            return None

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
        
        print("Iniciando corrección de precios en Google Sheets...")
        
        updates = []
        # Recorrer los datos desde la fila 5 (índice 4)
        for i, row in enumerate(rows[4:], start=5):
            orig_val = row[precio_idx]
            cleaned_val = limpiar_precio_mercado(orig_val)
            
            if cleaned_val is not None:
                # Comprobar si el valor original es diferente del limpiado convertido a string
                # (por ejemplo, si en Sheets dice "6.50" o "5" y el limpio es 6500 o 5000)
                if orig_val.strip() != str(cleaned_val) and orig_val.strip() != f"$ {cleaned_val}":
                    # Columna de precio es precio_idx + 1 (1-based en Sheets)
                    updates.append({
                        'range': gspread.utils.rowcol_to_a1(i, precio_idx + 1),
                        'values': [[cleaned_val]]
                    })
        
        if updates:
            print(f"Se encontraron {len(updates)} filas para corregir en el Excel.")
            # Ejecutar actualizaciones en lote para no exceder cuotas de API
            sheet.batch_update(updates)
            print("¡Precios actualizados con éxito en Google Sheets!")
        else:
            print("No se encontraron diferencias. Todos los precios están correctos.")
            
    except Exception as e:
        print("ERROR:", e)

if __name__ == "__main__":
    main()
