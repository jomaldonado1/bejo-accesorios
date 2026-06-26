import server
try:
    df = server.cargar_datos_sheets()
    print("Columns in stock sheet:")
    print(df.columns.tolist())
    print("\nFirst row:")
    print(df.iloc[0].to_dict() if len(df) > 0 else "Empty")
except Exception as e:
    print(e)
