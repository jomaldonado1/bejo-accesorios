import sys
import traceback
sys.path.append('.')
from server import cargar_datos_sheets

try:
    df = cargar_datos_sheets()
    print("DataFrame size:", len(df))
    print("Columns:", df.columns.tolist())
    print("First 3 rows:")
    print(df.head(3))
except Exception as e:
    print("Exception occurred:")
    traceback.print_exc()
