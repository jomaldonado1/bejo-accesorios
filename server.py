import os
import json
import random
import time
import urllib.parse
import base64
from io import BytesIO
from datetime import datetime

import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests

from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS

try:
    from PIL import Image
    PIL_OK = True
except ImportError:
    PIL_OK = False

app = Flask(__name__)
# Enable CORS for local development ports and standard origins
CORS(app, resources={r"/api/*": {"origins": "*"}})

CLAVE_ADMIN = "BEJO2024"
NUMERO_WS   = "5493816582851"

# Cache variables
_cache_productos = None
_cache_productos_time = 0

_cache_compatibilidad = None
_cache_compatibilidad_time = 0

# ── GOOGLE SHEETS HELPERS ───────────────────────────────────────────────────

def get_creds():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # 1. Look for env var GCP_SERVICE_ACCOUNT (helpful for Render/Railway)
    gcp_env = os.environ.get("GCP_SERVICE_ACCOUNT")
    if gcp_env:
        try:
            gcp_env = gcp_env.strip()
            # Strip wrapping quotes if accidentally added by Render or user
            if gcp_env.startswith('"') and gcp_env.endswith('"'):
                gcp_env = gcp_env[1:-1]
            elif gcp_env.startswith("'") and gcp_env.endswith("'"):
                gcp_env = gcp_env[1:-1]
                
            creds_dict = json.loads(gcp_env)
            # Robustness: replace escaped newlines in the private key
            if "private_key" in creds_dict:
                creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
                
            return ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        except Exception as e:
            print(f"Error parsing GCP_SERVICE_ACCOUNT env var: {e}")
            
    # 2. Look for local claves.json
    if os.path.exists("claves.json"):
        try:
            return ServiceAccountCredentials.from_json_keyfile_name("claves.json", scope)
        except Exception as e:
            print(f"Error loading claves.json: {e}")
            
    # 3. Fallback to Streamlit secrets structure if imported
    try:
        import streamlit as st
        if "gcp_service_account" in st.secrets:
            creds_dict = {k: v for k, v in st.secrets["gcp_service_account"].items()}
            return ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    except Exception:
        pass
        
    raise Exception("No Google Sheets credentials found. Please set GCP_SERVICE_ACCOUNT environment variable or create claves.json.")

def get_sheet():
    creds = get_creds()
    client = gspread.authorize(creds)
    return client.open("inventario_tienda").sheet1

def get_pedidos_sheet():
    creds = get_creds()
    client = gspread.authorize(creds)
    spreadsheet = client.open("inventario_tienda")
    try:
        sheet = spreadsheet.worksheet("Pedidos")
    except Exception:
        sheet = spreadsheet.add_worksheet(title="Pedidos", rows=1000, cols=6)
        sheet.append_row(["Fecha", "ID Pedido", "Cliente / Contacto", "Detalle Pedido WS", "Total", "Estado"])
    return sheet

def get_compatibilidad_sheet():
    creds = get_creds()
    client = gspread.authorize(creds)
    spreadsheet = client.open("inventario_tienda")
    return spreadsheet.worksheet("Compatibilidad")

# ── LOGIC FUNCTIONS ─────────────────────────────────────────────────────────

def limpiar_precio_mercado(val):
    import re
    if pd.isna(val):
        return 0
    s = str(val).strip().replace('$', '').replace(' ', '')
    if not s:
        return 0
    if ',' in s and '.' in s:
        comma_idx = s.rfind(',')
        dot_idx = s.rfind('.')
        if comma_idx > dot_idx:
            s = s.replace('.', '').replace(',', '.')
        else:
            s = s.replace(',', '')
    elif ',' in s:
        parts = s.split(',')
        if len(parts[-1]) == 3:
            s = s.replace(',', '')
        else:
            s = s.replace(',', '.')
    elif '.' in s:
        parts = s.split('.')
        if len(parts[-1]) == 3:
            s = s.replace('.', '')
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
            return 0

def cargar_datos_sheets():
    try:
        sheet = get_sheet()
        data  = sheet.get_all_records(head=4)
        df    = pd.DataFrame(data)
        df.columns = df.columns.str.strip()
        df["Cantidad"] = pd.to_numeric(df["Cantidad"], errors="coerce").fillna(0).astype(int)
        df["Precio Mercado"] = df["Precio Mercado"].apply(limpiar_precio_mercado)
        if "Imagen_URL" not in df.columns:
            df["Imagen_URL"] = ""
        col_oferta = None
        for c in df.columns:
            if "oferta" in str(c).lower():
                col_oferta = c
                break
        if col_oferta:
            df["En Oferta"] = df[col_oferta].astype(str).str.lower().apply(
                lambda val: any(x in val.strip() for x in ["oferta", "si", "yes", "1", "true", "x", "✓", "🔥"])
            )
        else:
            df["En Oferta"] = False
        return df
    except Exception as e:
        print(f"⚠️ Error al conectar con Google Sheets: {e}")
        # Return mock data as fallback
        mock_data = [
            {"Nombre del Artículo": "Funda de silicona", "Marca Principal": "Samsung",
             "Modelo Exacto": "Galaxy A54", "Color / Diseño (Variación)": "Negro Mate",
             "Precio Mercado": 15000, "Cantidad": 5,
             "Imagen_URL": "", "Oferta": "si"},
            {"Nombre del Artículo": "Funda de silicona", "Marca Principal": "Apple",
             "Modelo Exacto": "iPhone 14", "Color / Diseño (Variación)": "Transparente",
             "Precio Mercado": 18000, "Cantidad": 8,
             "Imagen_URL": "", "Oferta": ""},
            {"Nombre del Artículo": "Cargador Rápido 20W", "Marca Principal": "Apple",
             "Modelo Exacto": "iPhone 12 al 15", "Color / Diseño (Variación)": "Blanco",
             "Precio Mercado": 22000, "Cantidad": 3,
             "Imagen_URL": "", "Oferta": ""},
            {"Nombre del Artículo": "Hidrogel", "Marca Principal": "Samsung",
             "Modelo Exacto": "Galaxy S23", "Color / Diseño (Variación)": "Transparente mate",
             "Precio Mercado": 8000, "Cantidad": 0,
             "Imagen_URL": "", "Oferta": ""},
        ]
        df_mock = pd.DataFrame(mock_data)
        df_mock["En Oferta"] = df_mock["Oferta"].str.lower() == "si"
        return df_mock

def cargar_compatibilidad_sheets():
    try:
        sheet = get_compatibilidad_sheet()
        rows = sheet.get_all_values()
        if len(rows) < 5:
            return pd.DataFrame(columns=["tipo de producto", "marca", "modelo", "compatibilidad"])
        headers = [h.strip() for h in rows[3]]
        data = rows[4:]
        df = pd.DataFrame(data, columns=headers)
        df = df.loc[:, df.columns != '']
        df.columns = df.columns.str.strip()
        for col in df.columns:
            df[col] = df[col].astype(str).str.strip()
        return df
    except Exception as e:
        print(f"⚠️ Error al conectar con la pestaña de Compatibilidad: {e}")
        return pd.DataFrame()

def cargar_pedidos_sheets():
    try:
        sheet = get_pedidos_sheet()
        data  = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        print(f"⚠️ Error al cargar historial de pedidos: {e}")
        return pd.DataFrame()

def actualizar_estado_pedido(id_ped, nuevo_estado, df_pedidos):
    try:
        sheet = get_pedidos_sheet()
        matching_idx = df_pedidos[df_pedidos["ID Pedido"] == id_ped].index
        if len(matching_idx) > 0:
            fila_sheet = int(matching_idx[0]) + 2
            sheet.update_cell(fila_sheet, 6, nuevo_estado)
            return True
        return False
    except Exception as e:
        print(f"Error al actualizar estado del pedido: {e}")
        return False

def descontar_stock(carrito: dict, df_ref: pd.DataFrame):
    try:
        sheet   = get_sheet()
        cols    = df_ref.columns.tolist()
        col_cant = cols.index("Cantidad") + 1
        for df_idx, cant_vendida in carrito.items():
            fila_sheet   = df_idx + 5
            stock_actual = int(df_ref.loc[df_idx, "Cantidad"])
            nuevo_stock  = max(0, stock_actual - cant_vendida)
            sheet.update_cell(fila_sheet, col_cant, str(nuevo_stock))
        return True
    except Exception as e:
        print(f"⚠️ No se pudo actualizar el stock en el Excel: {e}")
        return False

def obtener_access_token_mp():
    # 1. Env Var
    tok = os.environ.get("MERCADOPAGO_ACCESS_TOKEN")
    if tok:
        return tok
    # 2. Look inside claves.json
    if os.path.exists("claves.json"):
        try:
            with open("claves.json", "r") as f:
                data = json.load(f)
                for key in ["mercadopago_access_token", "MERCADOPAGO_ACCESS_TOKEN"]:
                    if key in data:
                        return data[key]
        except Exception:
            pass
    # 3. Streamlit fallback
    try:
        import streamlit as st
        if "mercadopago" in st.secrets:
            tok = st.secrets["mercadopago"].get("access_token")
            if tok: return tok
        for key in ["MERCADOPAGO_ACCESS_TOKEN", "mercadopago_access_token"]:
            tok = st.secrets.get(key)
            if tok: return tok
    except Exception:
        pass
    return None

def crear_preferencia_mp(total_pedido, id_pedido, base_url):
    access_token = obtener_access_token_mp()
    if not access_token:
        print("No Mercado Pago token found. MP preference creation skipped.")
        return None
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    preference_data = {
        "items": [{
            "title": f"Pedido {id_pedido} - BEJO Accesorios",
            "quantity": 1,
            "unit_price": float(total_pedido),
            "currency_id": "ARS"
        }],
        "external_reference": id_pedido,
        "back_urls": {
            "success": base_url,
            "failure": base_url,
            "pending": base_url
        },
        "auto_return": "approved"
    }
    try:
        response = requests.post(
            "https://api.mercadopago.com/checkout/preferences",
            json=preference_data,
            headers=headers,
            timeout=10
        )
        if response.status_code in (200, 201):
            return response.json().get("init_point")
        else:
            print(f"MP Preference API error: Status {response.status_code}, Body: {response.text}")
            return None
    except Exception as e:
        print(f"Error creating MP preference: {e}")
        return None

def imagen_a_base64(archivo_bytes, max_size=(400,400), quality=72):
    if not PIL_OK:
        return None
    try:
        img = Image.open(archivo_bytes)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        if img.mode not in ("RGB","L"):
            img = img.convert("RGB")
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode()
        return f"data:image/jpeg;base64,{b64}"
    except Exception as e:
        print(f"Error al procesar imagen: {e}")
        return None

# ── CACHED FETCHING ──────────────────────────────────────────────────────────

def cargar_datos_sheets_cached(force=False):
    global _cache_productos, _cache_productos_time
    now = time.time()
    if force or _cache_productos is None or (now - _cache_productos_time) > 5:
        _cache_productos = cargar_datos_sheets()
        _cache_productos_time = now
    return _cache_productos

def cargar_compatibilidad_sheets_cached(force=False):
    global _cache_compatibilidad, _cache_compatibilidad_time
    now = time.time()
    if force or _cache_compatibilidad is None or (now - _cache_compatibilidad_time) > 5:
        _cache_compatibilidad = cargar_compatibilidad_sheets()
        _cache_compatibilidad_time = now
    return _cache_compatibilidad

# ── API ENDPOINTS ────────────────────────────────────────────────────────────

@app.route('/api/debug/sheets', methods=['GET'])
def debug_sheets():
    import traceback
    try:
        sheet = get_sheet()
        data  = sheet.get_all_records(head=4)
        df    = pd.DataFrame(data)
        return jsonify({
            "success": True,
            "row_count": len(df),
            "columns": df.columns.tolist()
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "gcp_env_exists": "GCP_SERVICE_ACCOUNT" in os.environ,
            "gcp_env_len": len(os.environ.get("GCP_SERVICE_ACCOUNT", ""))
        })

@app.route('/api/productos', methods=['GET'])
def get_productos():
    df = cargar_datos_sheets_cached()
    productos = []
    for idx, row in df.iterrows():
        productos.append({
            "index": int(idx),
            "nombre": str(row.get("Nombre del Artículo", "")),
            "marca": str(row.get("Marca Principal", "")),
            "modelo": str(row.get("Modelo Exacto", "")),
            "color": str(row.get("Color / Diseño (Variación)", "")),
            "precio": int(row.get("Precio Mercado", 0)),
            "cantidad": int(row.get("Cantidad", 0)),
            "imagen_url": str(row.get("Imagen_URL", "")),
            "en_oferta": bool(row.get("En Oferta", False))
        })
    return jsonify(productos)

@app.route('/api/compatibilidad', methods=['GET'])
def get_compatibilidad():
    df = cargar_compatibilidad_sheets_cached()
    if df.empty:
        return jsonify([])
    result = []
    for _, row in df.iterrows():
        result.append({
            "tipo": str(row.get("tipo de producto", "")),
            "marca": str(row.get("marca", "")),
            "modelo": str(row.get("modelo", "")),
            "compatibilidad": str(row.get("compatibilidad", ""))
        })
    return jsonify(result)

@app.route('/api/checkout', methods=['POST'])
def post_checkout():
    data = request.json
    if not data:
        return jsonify({"success": False, "error": "Falta información del pedido"}), 400
        
    carrito_raw = data.get("carrito", {})
    entrega = data.get("entrega", {})
    pago = data.get("pago", {})
    
    if not carrito_raw:
        return jsonify({"success": False, "error": "El carrito está vacío"}), 400
        
    # Convert keys to integers since JSON keys are strings
    carrito = {}
    for k, v in carrito_raw.items():
        try:
            carrito[int(k)] = int(v)
        except ValueError:
            return jsonify({"success": False, "error": "Formato de carrito inválido"}), 400
            
    df_stock = cargar_datos_sheets_cached(force=True)
    
    # Validate stock
    total_pedido = 0
    resumen_productos = []
    for idx, qty in carrito.items():
        if idx not in df_stock.index:
            return jsonify({"success": False, "error": f"El producto con índice {idx} no existe en el inventario"}), 400
            
        row = df_stock.loc[idx]
        stock_actual = int(row["Cantidad"])
        if qty > stock_actual:
            return jsonify({
                "success": False, 
                "error": f"Límite de stock: {stock_actual} unidades disponibles de {row['Nombre del Artículo']}."
            }), 400
            
        nombre_prod = f"{row['Nombre del Artículo']} {row['Modelo Exacto']} ({row['Color / Diseño (Variación)']})"
        precio_unit = row["Precio Mercado"]
        subtotal = precio_unit * qty
        total_pedido += subtotal
        resumen_productos.append(f"- {nombre_prod} x{qty} (${subtotal:,.0f})")
        
    # Generate Order ID
    ahora = datetime.now()
    id_pedido = f"PED-{ahora.strftime('%d%m-%H%M')}-{random.randint(100,999)}"
    
    metodo_entrega = entrega.get("metodo", "")
    metodo_pago = pago.get("metodo", "")
    direccion = entrega.get("direccion", "")
    observacion = entrega.get("observacion", "")
    
    le = metodo_entrega.replace("🏪  ","").replace("🏠  ","").strip()
    lp = metodo_pago.replace("💵  ","").replace("🏦  ","").replace("💳  ","").strip()
    
    mitad = total_pedido // 2
    resto = total_pedido - mitad
    
    # Process MP preference if selected
    mp_url = None
    if "Mercado Pago" in metodo_pago:
        base_url = request.host_url.rstrip('/')
        mp_url = crear_preferencia_mp(total_pedido, id_pedido, base_url)
        
    # Generate WhatsApp message
    msg = (f"⚡ ¡Hola BEJO! Nuevo pedido 🔥\n\n🆔 *ID Pedido:* {id_pedido}\n"
           f"📦 *Productos:*\n" + "\n".join(resumen_productos) +
           f"\n\n💰 *Total:* ${total_pedido:,.0f}\n💳 *Pago:* {lp}\n")
    if "Transferencia" in metodo_pago:
        msg += f"   ↳ Seña (50%): ${mitad:,.0f} | Resto al recibir: ${resto:,.0f}\n"
    elif "Mercado Pago" in metodo_pago and mp_url:
        msg += f"   ↳ 🔗 *Link de Pago:* {mp_url}\n"
    msg += f"📍 *Entrega:* {le}\n"
    if "Envío" in metodo_entrega:
        msg += f"🏠 *Dirección:* {direccion}\n"
        if observacion: msg += f"📝 *Referencias:* {observacion}\n"
    if "Retiro" in metodo_entrega:
        msg += "\n⚠️ *Se coordinará con el local para el punto de entrega.*\n"
    msg += "\n✨ ¡Gracias por elegir BEJO! 🙌"
    
    ws_url = f"https://wa.me/{NUMERO_WS}?text={urllib.parse.quote(msg)}"
    
    # Write to Pedidos Worksheet
    try:
        p_sheet = get_pedidos_sheet()
        cliente_info = f"Pago: {lp} | Entrega: {le}"
        if "Envío" in metodo_entrega:
            cliente_info += f" | Dir: {direccion}"
        p_sheet.append_row([
            ahora.strftime('%Y-%m-%d %H:%M:%S'),
            id_pedido, cliente_info, msg,
            str(total_pedido), "Pendiente"
        ])
    except Exception as e:
        print(f"⚠️ Error appending row to Pedidos worksheet: {e}")
        
    # Decrement stock in sheet
    ok_stock = descontar_stock(carrito, df_stock)
    
    # Clear local cache to force reload on next call
    cargar_datos_sheets_cached(force=True)
    
    return jsonify({
        "success": True,
        "id_pedido": id_pedido,
        "total": int(total_pedido),
        "ws_url": ws_url,
        "mp_url": mp_url,
        "stock_updated": ok_stock
    })

# ── ADMIN ENDPOINTS ──────────────────────────────────────────────────────────

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.json or {}
    if data.get("password") == CLAVE_ADMIN:
        return jsonify({"success": True, "token": "admin-session-token-bejo"})
    return jsonify({"success": False, "error": "Clave incorrecta"}), 401

@app.route('/api/admin/pedidos', methods=['GET'])
def get_admin_pedidos():
    auth_header = request.headers.get("Authorization")
    if auth_header != "admin-session-token-bejo":
        return jsonify({"success": False, "error": "No autorizado"}), 401
    df = cargar_pedidos_sheets()
    if df.empty:
        return jsonify([])
    pedidos = []
    for _, row in df.iterrows():
        pedidos.append({
            "fecha": str(row.get("Fecha", "")),
            "id_pedido": str(row.get("ID Pedido", "")),
            "cliente_contacto": str(row.get("Cliente / Contacto", "")),
            "detalle_ws": str(row.get("Detalle Pedido WS", "")),
            "total": str(row.get("Total", "0")),
            "estado": str(row.get("Estado", "Pendiente"))
        })
    return jsonify(pedidos)

@app.route('/api/admin/pedidos/estado', methods=['POST'])
def post_admin_pedido_estado():
    auth_header = request.headers.get("Authorization")
    if auth_header != "admin-session-token-bejo":
        return jsonify({"success": False, "error": "No autorizado"}), 401
        
    data = request.json or {}
    id_ped = data.get("id_pedido")
    nuevo_estado = data.get("estado")
    
    if not id_ped or not nuevo_estado:
        return jsonify({"success": False, "error": "Faltan parámetros"}), 400
        
    df = cargar_pedidos_sheets()
    if df.empty:
        return jsonify({"success": False, "error": "No se encontraron pedidos"}), 400
        
    ok = actualizar_estado_pedido(id_ped, nuevo_estado, df)
    return jsonify({"success": ok})

@app.route('/api/admin/productos', methods=['POST'])
def admin_save_producto():
    auth_header = request.headers.get("Authorization")
    if auth_header != "admin-session-token-bejo":
        return jsonify({"success": False, "error": "No autorizado"}), 401
        
    idx = request.form.get("index") # string or null
    nombre = request.form.get("nombre", "").strip()
    marca = request.form.get("marca", "").strip()
    modelo = request.form.get("modelo", "").strip()
    color = request.form.get("color", "").strip()
    precio = request.form.get("precio", "0")
    cantidad = request.form.get("cantidad", "0")
    
    url_imgur1 = request.form.get("url_imgur1", "").strip()
    url_imgur2 = request.form.get("url_imgur2", "").strip()
    url_imgur3 = request.form.get("url_imgur3", "").strip()
    
    file_photo1 = request.files.get("foto1")
    file_photo2 = request.files.get("foto2")
    file_photo3 = request.files.get("foto3")
    
    if not nombre or not marca or not modelo:
        return jsonify({"success": False, "error": "Campos nombre, marca y modelo son obligatorios"}), 400
        
    urls_fotos = []
    
    # Process Photo 1
    if file_photo1:
        try:
            b64 = imagen_a_base64(file_photo1)
            if b64: urls_fotos.append(b64)
        except Exception as e:
            return jsonify({"success": False, "error": f"Error al procesar imagen 1: {e}"}), 500
    elif url_imgur1:
        urls_fotos.append(url_imgur1)
        
    # Process Photo 2
    if file_photo2:
        try:
            b64 = imagen_a_base64(file_photo2)
            if b64: urls_fotos.append(b64)
        except Exception as e:
            return jsonify({"success": False, "error": f"Error al procesar imagen 2: {e}"}), 500
    elif url_imgur2:
        urls_fotos.append(url_imgur2)
        
    # Process Photo 3
    if file_photo3:
        try:
            b64 = imagen_a_base64(file_photo3)
            if b64: urls_fotos.append(b64)
        except Exception as e:
            return jsonify({"success": False, "error": f"Error al procesar imagen 3: {e}"}), 500
    elif url_imgur3:
        urls_fotos.append(url_imgur3)
        
    nueva_url_foto = ",".join(urls_fotos)
    
    df_stock = cargar_datos_sheets_cached(force=True)
    sheet = get_sheet()
    
    try:
        if idx is not None and idx != "" and idx != "null":
            # Update existing product
            df_idx = int(idx)
            fila_sheet = df_idx + 5
            row = df_stock.loc[df_idx]
            
            # If all image fields are empty, retain old image URL
            if not urls_fotos and not file_photo1 and not file_photo2 and not file_photo3 and not url_imgur1 and not url_imgur2 and not url_imgur3:
                nueva_url_foto = str(row.get("Imagen_URL", ""))
                
            cols = df_stock.columns.tolist()
            def col_num(nombre_col): return cols.index(nombre_col) + 1
            
            sheet.update_cell(fila_sheet, col_num("Nombre del Artículo"), nombre)
            sheet.update_cell(fila_sheet, col_num("Marca Principal"), marca)
            sheet.update_cell(fila_sheet, col_num("Modelo Exacto"), modelo)
            sheet.update_cell(fila_sheet, col_num("Color / Diseño (Variación)"), color)
            sheet.update_cell(fila_sheet, col_num("Precio Mercado"), str(precio))
            sheet.update_cell(fila_sheet, col_num("Cantidad"), str(cantidad))
            sheet.update_cell(fila_sheet, col_num("Imagen_URL"), nueva_url_foto)
            
            msg_res = "Producto actualizado correctamente"
        else:
            # Create new product
            # Column structure: Marca Principal, Nombre del Artículo, Modelo Exacto, Color / Diseño, Precio Mercado, Oferta (empty), Cantidad, Imagen_URL
            sheet.append_row([
                marca, nombre, modelo, color, str(precio), "", str(cantidad), nueva_url_foto
            ])
            msg_res = "Producto agregado correctamente"
            
        cargar_datos_sheets_cached(force=True)
        return jsonify({"success": True, "message": msg_res})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/admin/productos/<int:idx>', methods=['DELETE'])
def admin_delete_producto(idx):
    auth_header = request.headers.get("Authorization")
    if auth_header != "admin-session-token-bejo":
        return jsonify({"success": False, "error": "No autorizado"}), 401
        
    try:
        sheet = get_sheet()
        fila_s = idx + 5
        sheet.delete_rows(fila_s)
        cargar_datos_sheets_cached(force=True)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/admin/download/inventario', methods=['GET'])
def admin_download_inventario():
    auth_token = request.args.get("token")
    if auth_token != "admin-session-token-bejo":
        return "No autorizado", 401
    df = cargar_datos_sheets_cached(force=True)
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Inventario')
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"inventario_bejo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.route('/api/admin/download/pedidos', methods=['GET'])
def admin_download_pedidos():
    auth_token = request.args.get("token")
    if auth_token != "admin-session-token-bejo":
        return "No autorizado", 401
    df = cargar_pedidos_sheets()
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Pedidos')
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"pedidos_bejo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ── STATIC FILE SERVING ──────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    # If file doesn't exist, we send it from the static folder
    if os.path.exists(os.path.join('static', path)):
        return send_from_directory('static', path)
    # Default fallback to index.html for SPA router (if any) or not found
    return send_from_directory('static', 'index.html')

# Run the Flask app
if __name__ == '__main__':
    # Ensure static directory exists
    os.makedirs('static', exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
