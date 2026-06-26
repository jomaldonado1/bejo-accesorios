import server
import traceback

print("Testing resize/add_cols")
try:
    creds = server.get_creds()
    client = server.gspread.authorize(creds)
    spreadsheet = client.open("inventario_tienda")
    sheet = spreadsheet.worksheet("Pedidos")
    
    print("Initial col_count:", sheet.col_count)
    if sheet.col_count < 7:
        print("Adding columns...")
        sheet.add_cols(7 - sheet.col_count)
    
    print("New col_count:", sheet.col_count)
    headers = ["Fecha", "ID Pedido", "Cliente / Contacto", "Detalle Pedido WS", "Total", "Estado", "Nombre y Apellido"]
    sheet.update('A1:G1', [headers])
    print("Headers updated successfully!")
    
except Exception as e:
    traceback.print_exc()
