import os
import json
import random
import time
import urllib.parse
import base64
from io import BytesIO
from datetime import datetime, timedelta

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading

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
        gcp_env = gcp_env.strip()
        # Strip wrapping quotes if accidentally added by Render or user
        if gcp_env.startswith('"') and gcp_env.endswith('"'):
            gcp_env = gcp_env[1:-1]
        elif gcp_env.startswith("'") and gcp_env.endswith("'"):
            gcp_env = gcp_env[1:-1]
            
        try:
            creds_dict = json.loads(gcp_env)
        except Exception as first_err:
            print(f"Direct GCP_SERVICE_ACCOUNT JSON load failed: {first_err}. Attempting recovery...")
            try:
                import re
                # Replace any single backslash not followed by valid JSON escape character with \n
                repaired = re.sub(r'\\(?![nrtbf"\\/u])', r'\\n', gcp_env)
                creds_dict = json.loads(repaired)
            except Exception as recovery_err:
                print(f"GCP_SERVICE_ACCOUNT recovery parsing failed: {recovery_err}")
                creds_dict = None
                
        if creds_dict:
            try:
                # Robustness: replace escaped newlines in the private key
                if "private_key" in creds_dict:
                    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
                    
                return ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            except Exception as e:
                print(f"Error creating credentials from dict: {e}")
            
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
    headers = ["Fecha", "ID Pedido", "Cliente / Contacto", "Detalle Pedido WS", "Total", "Estado", "Nombre y Apellido", "Productos"]
    try:
        sheet = spreadsheet.worksheet("Pedidos")
        if sheet.col_count < 8:
            sheet.add_cols(8 - sheet.col_count)
        row1 = sheet.row_values(1)
        if not row1 or len(row1) == 0 or not row1[0].strip():
            # If sheet is empty, add headers to the first row
            sheet.update([headers], 'A1:H1')
        else:
            row1_clean = [r.strip() for r in row1]
            if len(row1_clean) < 7 or "Nombre y Apellido" not in row1_clean:
                sheet.update_cell(1, 7, "Nombre y Apellido")
            if len(row1_clean) < 8 or "Productos" not in row1_clean:
                sheet.update_cell(1, 8, "Productos")
    except Exception:
        sheet = spreadsheet.add_worksheet(title="Pedidos", rows=1000, cols=8)
        sheet.append_row(headers)
    return sheet

def get_compatibilidad_sheet():
    creds = get_creds()
    client = gspread.authorize(creds)
    spreadsheet = client.open("inventario_tienda")
    return spreadsheet.worksheet("Compatibilidad")

def get_combo_config_sheet():
    creds = get_creds()
    client = gspread.authorize(creds)
    spreadsheet = client.open("inventario_tienda")
    try:
        return spreadsheet.worksheet("ComboConfig")
    except Exception:
        # Fallback create
        sheet = spreadsheet.add_worksheet(title="ComboConfig", rows=10, cols=2)
        sheet.append_row(["Precio", "Cantidad"])
        sheet.append_row([25000, 10])
        return sheet

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
        return int(val_float)
    except ValueError:
        s_clean = re.sub(r'[^\d.]', '', s)
        try:
            val_float = float(s_clean)
            return int(val_float)
        except ValueError:
            return 0

def cargar_datos_sheets():
    try:
        sheet = get_sheet()
        data  = sheet.get_all_records(head=4)
        df    = pd.DataFrame(data)
        df.columns = df.columns.str.strip()
        col_cantidad = "CANTIDAD" if "CANTIDAD" in df.columns else "Cantidad"
        df[col_cantidad] = pd.to_numeric(df[col_cantidad], errors="coerce").fillna(0).astype(int)
        
        col_precio = "PRECIO DE MERCADO" if "PRECIO DE MERCADO" in df.columns else "Precio Mercado"
        df[col_precio] = df[col_precio].apply(limpiar_precio_mercado)
        
        # Collect all possible images safely
        def get_all_images(row):
            imgs = []
            if "Imagen_URL" in df.columns:
                val = str(row.get("Imagen_URL", "")).strip()
                if val: imgs.append(val)
            for col in ["FOTO 1 OPCIONAL", "FOTO 2 OPCIONAL", "FOTO 3 OPCIONAL", "FOTO 4 OPCIONAL"]:
                if col in df.columns:
                    val = str(row.get(col, "")).strip()
                    if val: imgs.append(val)
            return ",".join(imgs)
            
        df["Imagen_URL"] = df.apply(get_all_images, axis=1)
        
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
        col_name = "CANTIDAD" if "CANTIDAD" in cols else "Cantidad"
        if col_name not in cols:
            return False
        col_cant = cols.index(col_name) + 1
        for df_idx, cant_vendida in carrito.items():
            fila_sheet   = df_idx + 5
            stock_actual = int(df_ref.loc[df_idx, col_name])
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
    parse_error = None
    parsed_dict_keys = None
    try:
        gcp_env = os.environ.get("GCP_SERVICE_ACCOUNT")
        if gcp_env:
            gcp_env = gcp_env.strip()
            if gcp_env.startswith('"') and gcp_env.endswith('"'):
                gcp_env = gcp_env[1:-1]
            elif gcp_env.startswith("'") and gcp_env.endswith("'"):
                gcp_env = gcp_env[1:-1]
            creds_dict = json.loads(gcp_env)
            parsed_dict_keys = list(creds_dict.keys())
    except Exception as parse_ex:
        parse_error = f"{type(parse_ex).__name__}: {str(parse_ex)}"
        
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
        gcp_val = os.environ.get("GCP_SERVICE_ACCOUNT", "")
        snippet = gcp_val[max(0, 1500):min(len(gcp_val), 1620)] if gcp_val else None
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "gcp_env_exists": "GCP_SERVICE_ACCOUNT" in os.environ,
            "gcp_env_len": len(gcp_val),
            "parse_error": parse_error,
            "parsed_dict_keys": parsed_dict_keys,
            "gcp_env_snippet_around_error": snippet
        })

@app.route('/api/productos', methods=['GET'])
def get_productos():
    df = cargar_datos_sheets_cached()
    productos = []
    for idx, row in df.iterrows():
        productos.append({
            "index": int(idx),
            "nombre": str(row.get("CATEGORIA", row.get("Nombre del Artículo", ""))),
            "marca": str(row.get("MARCA", row.get("Marca Principal", ""))),
            "modelo": str(row.get("PRODUCTO / MODELO", row.get("Modelo Exacto", ""))),
            "color": str(row.get("COLOR", row.get("Color / Diseño (Variación)", ""))),
            "precio": int(row.get("PRECIO DE MERCADO", row.get("Precio Mercado", 0))),
            "cantidad": int(row.get("CANTIDAD", row.get("Cantidad", 0))),
            "imagen_url": str(row.get("Imagen_URL", "")),
            "en_oferta": bool(row.get("En Oferta", False)),
            "compatibilidad": str(row.get("COMPATIBILIDAD", row.get("Compatibilidad", "")))
        })
    return jsonify(productos)

@app.route('/api/combo-config', methods=['GET'])
def get_combo_config():
    try:
        sheet = get_combo_config_sheet()
        records = sheet.get_all_records()
        if records:
            row = records[0]
            precio = row.get("Precio", 25000)
            cantidad = row.get("Cantidad", 10)
            return jsonify({"precio": precio, "cantidad": cantidad})
    except Exception as e:
        print(f"Error fetching combo config: {e}")
    # Default fallback if sheet doesn't exist or errors out
    return jsonify({"precio": 25000, "cantidad": 10})

@app.route('/api/productos-combo', methods=['GET'])
def get_productos_combo():
    df = cargar_datos_sheets_cached()
    productos = []
    for idx, row in df.iterrows():
        apto = str(row.get("Apto_Combo", "")).strip().upper()
        cant = int(row.get("CANTIDAD", row.get("Cantidad", 0)))
        if apto == "SI" and cant > 0:
            productos.append({
                "index": int(idx),
                "nombre": str(row.get("CATEGORIA", row.get("Nombre del Artículo", ""))),
                "marca": str(row.get("MARCA", row.get("Marca Principal", ""))),
                "modelo": str(row.get("PRODUCTO / MODELO", row.get("Modelo Exacto", ""))),
                "color": str(row.get("COLOR", row.get("Color / Diseño (Variación)", ""))),
                "precio": int(row.get("PRECIO DE MERCADO", row.get("Precio Mercado", 0))),
                "cantidad": cant,
                "imagen_url": str(row.get("Imagen_URL", "")),
                "en_oferta": bool(row.get("En Oferta", False)),
                "compatibilidad": str(row.get("COMPATIBILIDAD", row.get("Compatibilidad", "")))
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
    combo_details = data.get("comboDetails", {})
    entrega = data.get("entrega", {})
    pago = data.get("pago", {})
    
    if not carrito_raw:
        return jsonify({"success": False, "error": "El carrito está vacío"}), 400
        
    # Convert keys to integers since JSON keys are strings (except combos)
    carrito = {}
    for k, v in carrito_raw.items():
        if str(k).startswith("combo_"):
            carrito[str(k)] = int(v)
        else:
            try:
                carrito[int(k)] = int(v)
            except ValueError:
                return jsonify({"success": False, "error": "Formato de carrito inválido"}), 400
            
    df_stock = cargar_datos_sheets_cached(force=True)
    
    # Validate stock
    total_pedido = 0
    resumen_productos = []
    stock_to_deduct = {} # idx -> qty
    
    for idx, qty in carrito.items():
        if str(idx).startswith("combo_"):
            cdetail = combo_details.get(str(idx), {})
            cprecio = cdetail.get("precio", 0)
            citems = cdetail.get("items", [])
            cnames = cdetail.get("itemNames", [])
            
            subtotal = cprecio * qty
            total_pedido += subtotal
            
            resumen_productos.append(f"- Combo Personalizado x{len(citems)} (Cantidad: {qty}) (${subtotal:,.0f})")
            for name in cnames:
                resumen_productos.append(f"  └ {name}")
                
            for item_id in citems:
                stock_to_deduct[item_id] = stock_to_deduct.get(item_id, 0) + qty
                if item_id not in df_stock.index:
                    return jsonify({"success": False, "error": f"El producto de combo con índice {item_id} no existe en el inventario"}), 400
        else:
            if idx not in df_stock.index:
                return jsonify({"success": False, "error": f"El producto con índice {idx} no existe en el inventario"}), 400
            
            row = df_stock.loc[idx]
            stock_to_deduct[idx] = stock_to_deduct.get(idx, 0) + qty
            
            nombre_prod = f"{row.get('CATEGORIA', row.get('Nombre del Artículo', ''))} {row.get('PRODUCTO / MODELO', row.get('Modelo Exacto', ''))} ({row.get('COLOR', row.get('Color / Diseño (Variación)', ''))})"
            precio_unit = row.get("PRECIO DE MERCADO", row.get("Precio Mercado", 0))
            subtotal = precio_unit * qty
            total_pedido += subtotal
            resumen_productos.append(f"- {nombre_prod} x{qty} (${subtotal:,.0f})")
            
    # Final stock validation
    for item_idx, req_qty in stock_to_deduct.items():
        row = df_stock.loc[item_idx]
        col_cantidad = "CANTIDAD" if "CANTIDAD" in df_stock.columns else "Cantidad"
        stock_actual = int(row[col_cantidad])
        if req_qty > stock_actual:
            return jsonify({
                "success": False, 
                "error": f"Límite de stock superado: {stock_actual} unidades disponibles de {row.get('Nombre del Artículo', 'producto')}."
            }), 400
        
    # Generate Order ID
    ahora = datetime.utcnow() - timedelta(hours=3)
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
    
    # Format products list for the new column using the already built resumen_productos
    productos_str = "\n".join(resumen_productos)

    # Write to Pedidos Worksheet
    try:
        p_sheet = get_pedidos_sheet()
        nombre_cliente = entrega.get("nombre", "").strip()
        cliente_info = f"Pago: {lp} | Entrega: {le}"
        if "Envío" in metodo_entrega:
            cliente_info += f" | Dir: {direccion}"
        p_sheet.append_row([
            ahora.strftime('%Y-%m-%d %H:%M:%S'),
            id_pedido, cliente_info, msg,
            str(total_pedido), "Pendiente", nombre_cliente, productos_str
        ])
    except Exception as e:
        print(f"⚠️ Error appending row to Pedidos worksheet: {e}")
        
    # Send email notification asynchronously
    enviar_email_confirmacion(id_pedido, nombre_cliente, le, lp, direccion, total_pedido, resumen_productos)

    # Decrement stock in sheet
    ok_stock = descontar_stock(stock_to_deduct, df_stock)
    
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
            "nombre_apellido": str(row.get("Nombre y Apellido", "")),
            "cliente_contacto": str(row.get("Cliente / Contacto", "")),
            "detalle_ws": str(row.get("Detalle Pedido WS", "")),
            "productos": str(row.get("Productos", "")),
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
            def update_col(nombre1, nombre2, val):
                if nombre1 in cols:
                    sheet.update_cell(fila_sheet, cols.index(nombre1) + 1, val)
                elif nombre2 in cols:
                    sheet.update_cell(fila_sheet, cols.index(nombre2) + 1, val)
            
            update_col("CATEGORIA", "Nombre del Artículo", nombre)
            update_col("MARCA", "Marca Principal", marca)
            update_col("PRODUCTO / MODELO", "Modelo Exacto", modelo)
            update_col("COLOR", "Color / Diseño (Variación)", color)
            update_col("PRECIO DE MERCADO", "Precio Mercado", str(precio))
            update_col("CANTIDAD", "Cantidad", str(cantidad))
            
            if urls_fotos:
                update_col("FOTO 1 OPCIONAL", "Imagen_URL", urls_fotos[0] if len(urls_fotos) > 0 else "")
                if "FOTO 2 OPCIONAL" in cols:
                    sheet.update_cell(fila_sheet, cols.index("FOTO 2 OPCIONAL") + 1, urls_fotos[1] if len(urls_fotos) > 1 else "")
                if "FOTO 3 OPCIONAL" in cols:
                    sheet.update_cell(fila_sheet, cols.index("FOTO 3 OPCIONAL") + 1, urls_fotos[2] if len(urls_fotos) > 2 else "")
            elif "FOTO 1 OPCIONAL" not in cols and "Imagen_URL" in cols:
                # Fallback if using old headers and no new photos
                sheet.update_cell(fila_sheet, cols.index("Imagen_URL") + 1, nueva_url_foto)
                
            msg_res = "Producto actualizado correctamente"
        else:
            # Create new product
            # Use current columns
            cols = df_stock.columns.tolist()
            new_row = [""] * len(cols)
            def set_col(nombre1, nombre2, val):
                if nombre1 in cols: new_row[cols.index(nombre1)] = val
                elif nombre2 in cols: new_row[cols.index(nombre2)] = val
            
            set_col("CATEGORIA", "Nombre del Artículo", nombre)
            set_col("MARCA", "Marca Principal", marca)
            set_col("PRODUCTO / MODELO", "Modelo Exacto", modelo)
            set_col("COLOR", "Color / Diseño (Variación)", color)
            set_col("PRECIO DE MERCADO", "Precio Mercado", str(precio))
            set_col("CANTIDAD", "Cantidad", str(cantidad))
            if urls_fotos:
                set_col("FOTO 1 OPCIONAL", "Imagen_URL", urls_fotos[0] if len(urls_fotos) > 0 else "")
                if len(urls_fotos) > 1: set_col("FOTO 2 OPCIONAL", "FOTO 2 OPCIONAL", urls_fotos[1])
                if len(urls_fotos) > 2: set_col("FOTO 3 OPCIONAL", "FOTO 3 OPCIONAL", urls_fotos[2])
                
            sheet.append_row(new_row)
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
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False, threaded=True)
