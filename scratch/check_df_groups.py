import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("claves.json", scope)
client = gspread.authorize(creds)
sheet = client.open("inventario_tienda").sheet1
data = sheet.get_all_records(head=4)
df = pd.DataFrame(data)
df.columns = df.columns.str.strip()

print("Grouped counts:")
group_keys = df[["Nombre del Artículo","Marca Principal","Modelo Exacto"]].drop_duplicates()
for _, gk in group_keys.iterrows():
    mask = (
        (df["Nombre del Artículo"] == gk["Nombre del Artículo"]) &
        (df["Marca Principal"]      == gk["Marca Principal"]) &
        (df["Modelo Exacto"]        == gk["Modelo Exacto"])
    )
    sub = df[mask]
    print(f"{gk['Nombre del Artículo']} {gk['Marca Principal']} {gk['Modelo Exacto']}: {len(sub)} variants")
    for v in sub["Color / Diseño (Variación)"]:
        print(f"  - {v}")
