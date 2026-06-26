import server
import pandas as pd
import traceback

print("Testing Pedidos Sheet...")
try:
    sheet = server.get_pedidos_sheet()
    print("Sheet retrieved.")
    row1 = sheet.row_values(1)
    print("Row 1:", row1)
    try:
        data = sheet.get_all_records()
        print(f"Got {len(data)} records.")
        if len(data) > 0:
            print("First record:", data[0])
    except Exception as e:
        print("Error in get_all_records():")
        traceback.print_exc()
except Exception as e:
    print("Error in get_pedidos_sheet():")
    traceback.print_exc()
