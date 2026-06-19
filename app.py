import streamlit as st
import pandas as pd
import gspread
import folium
from streamlit_folium import st_folium
from oauth2client.service_account import ServiceAccountCredentials
import random
from datetime import datetime
import urllib.parse
import base64
from io import BytesIO
import time

try:
    from PIL import Image
    PIL_OK = True
except ImportError:
    PIL_OK = False

# ── Configuración ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BEJO – Accesorios para Celulares",
    page_icon="🔥",
    layout="centered"
)

CLAVE_ADMIN = "BEJO2024"
NUMERO_WS   = "5493816582851"

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;900&display=swap');
html, body, [class*="css"] { font-family: 'Outfit', sans-serif; }

.stApp {
    background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    color: #ffffff;
}

/* ── HEADER ── */
.bejo-header {
    text-align: center; padding: 2rem 1rem 0.5rem;
    background: linear-gradient(135deg, #ff6b35, #f7c59f, #ff6b35);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; font-size: clamp(2rem, 10vw, 3.8rem);
    font-weight: 900; letter-spacing: 6px; text-transform: uppercase;
    filter: drop-shadow(0 0 20px #ff6b3588);
}
.bejo-subtitle {
    text-align: center; color: #a89cff;
    font-size: clamp(0.65rem, 2.5vw, 1rem);
    letter-spacing: 3px; margin-top: -0.5rem; margin-bottom: 1.5rem;
}

/* ── GRILLA ── */
.welcome-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 8px; margin: 1rem 0 2rem 0; }
.welcome-grid img { width:100%; aspect-ratio:1; object-fit:cover; border-radius:10px; border:2px solid #ff6b3566; transition:transform .3s,border-color .3s; }
.welcome-grid img:hover { transform:scale(1.04); border-color:#ff6b35; }

/* ── BANNER CARRITO ── */
.carrito-banner {
    background: linear-gradient(135deg, #00c851, #007e33); color:#fff;
    font-size: clamp(1rem,4vw,1.25rem); font-weight:800; text-align:center;
    padding:.9rem 1.5rem; border-radius:14px; border-left:6px solid #00ff6a;
    box-shadow:0 0 25px #00c85166; margin:.5rem 0; letter-spacing:1px;
    animation:pulse-green 1s ease-in-out;
}
@keyframes pulse-green {
    0%{box-shadow:0 0 0px #00c851;} 50%{box-shadow:0 0 30px #00c851;} 100%{box-shadow:0 0 10px #00c85155;}
}

/* ── CARRITO ── */
.carrito-titulo {
    background: linear-gradient(135deg, #667eea, #764ba2); padding:1rem 1.5rem;
    border-radius:14px; color:white; font-size:clamp(1.2rem,5vw,1.6rem);
    font-weight:800; margin-bottom:1rem;
}
.total-box {
    background: linear-gradient(135deg, #f7971e, #ffd200); color:#1a1a1a;
    padding:1.2rem 2rem; border-radius:14px; font-size:clamp(1.3rem,5vw,1.8rem);
    font-weight:900; text-align:center; margin:1.2rem 0; box-shadow:0 4px 20px #ffd20066;
}

/* ── SECCIÓN TITULO ── */
.seccion-titulo {
    background: linear-gradient(90deg, rgba(255,107,53,0.25), rgba(255,107,53,0.05));
    border-left:4px solid #ff6b35; padding:.7rem 1.2rem; border-radius:0 10px 10px 0;
    color:#fff; font-size:clamp(1rem,4vw,1.2rem); font-weight:800;
    margin:1.5rem 0 .8rem 0; letter-spacing:1px;
}

/* ── BOTÓN PRINCIPAL ── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #ff6b35, #ff3d00) !important; color:white !important;
    font-weight:700 !important; font-size:clamp(.9rem,3vw,1.1rem) !important;
    border:none !important; border-radius:12px !important; padding:.75rem 2rem !important;
    box-shadow:0 4px 20px #ff6b3566 !important; transition:transform .2s,box-shadow .2s !important; width:100% !important;
}
.stButton > button[kind="primary"]:hover { transform:translateY(-2px) !important; box-shadow:0 8px 30px #ff6b3599 !important; }

/* ── BOTONES SECUNDARIOS ── */
.stButton > button:not([kind="primary"]) {
    background:rgba(255,107,53,0.15) !important; color:#ff6b35 !important;
    border:1px solid #ff6b35 !important; border-radius:10px !important;
    font-weight:600 !important; transition:background .2s !important;
}
.stButton > button:not([kind="primary"]):hover { background:rgba(255,107,53,0.35) !important; }

/* ── RADIO ── */
div[data-testid="stRadio"] > label { color:#fff !important; font-size:1.1rem !important; font-weight:700 !important; }
div[data-testid="stRadio"] div[role="radiogroup"] {
    background:rgba(255,255,255,0.05); border-radius:14px;
    padding:.8rem 1rem; border:1px solid rgba(255,107,53,0.4);
    display:flex; flex-direction:column; gap:.4rem;
}
div[data-testid="stRadio"] label[data-baseweb="radio"] {
    background:rgba(255,255,255,0.07); border-radius:10px;
    padding:.7rem 1rem; border:1px solid rgba(255,107,53,0.2); transition:all .2s; cursor:pointer;
}
div[data-testid="stRadio"] label[data-baseweb="radio"]:hover { background:rgba(255,107,53,0.2); border-color:#ff6b35; }
div[data-testid="stRadio"] label[data-baseweb="radio"] > div:last-child { color:#fff !important; font-size:1rem !important; font-weight:600 !important; }

/* ── INPUTS ── */
.stSelectbox > div > div,
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stTextArea textarea {
    background:rgba(40,30,70,0.85) !important; border-radius:10px !important;
    border:1.5px solid rgba(255,107,53,0.5) !important; color:#ffffff !important;
    font-size:1rem !important; font-weight:500 !important;
}
.stTextInput > div > div > input::placeholder, .stTextArea textarea::placeholder { color:#a89cff !important; opacity:.7 !important; }
.stTextInput > div > div > input:focus, .stTextArea textarea:focus { border-color:#ff6b35 !important; box-shadow:0 0 0 2px rgba(255,107,53,0.3) !important; }
[data-baseweb="select"] li, [data-baseweb="popover"] li { background:#1e1a3a !important; color:#fff !important; }

/* ── LABELS ── */
label, .stSelectbox label, .stTextInput label, .stNumberInput label, .stTextArea label {
    color:#e0d7ff !important; font-weight:600 !important; font-size:.95rem !important;
}

/* ── FILE UPLOADER ── */
div[data-testid="stFileUploader"] {
    background:rgba(40,30,70,0.6) !important; border:2px dashed rgba(255,107,53,0.5) !important;
    border-radius:14px !important; padding:.5rem !important;
}
div[data-testid="stFileUploader"] label { color:#e0d7ff !important; }
div[data-testid="stFileUploader"] button { color:#ff6b35 !important; border-color:#ff6b35 !important; }

/* ── INFO BOXES ── */
.info-ws { background:rgba(0,168,107,0.18); border:1px solid #00a86b; border-radius:12px; padding:1rem 1.5rem; color:#a8ffdb; margin:.5rem 0; }
.info-transfer { background:rgba(255,200,0,0.12); border:2px solid #ffd200; border-radius:12px; padding:1.2rem 1.5rem; color:#ffe94d; margin:.5rem 0; font-weight:600; }
.info-transfer b { font-size:1.3rem; color:#ffd200; }
.error-validacion { background:rgba(255,50,50,0.18); border:2px solid #ff4444; border-radius:12px; padding:.9rem 1.5rem; color:#ff9999; font-weight:700; margin:.5rem 0; text-align:center; }

/* ── ADMIN ── */
.admin-filtros { background:rgba(255,107,53,0.07); border:1px solid rgba(255,107,53,0.25); border-radius:14px; padding:1rem 1.2rem; margin-bottom:1rem; }
.prod-card { background:rgba(255,255,255,0.06); border:1.5px solid rgba(255,107,53,0.4); border-radius:14px; padding:1.2rem 1.5rem; margin:.8rem 0; }
.prod-card-titulo { color:#ff6b35; font-size:1.1rem; font-weight:800; margin-bottom:.5rem; }
.nuevo-prod-banner { background:linear-gradient(90deg,rgba(102,126,234,0.3),rgba(118,75,162,0.15)); border:1px solid #667eea; border-radius:14px; padding:1rem 1.5rem; margin:.8rem 0; color:#c8bfff; }
.tag-stock { display:inline-block; background:rgba(0,200,81,0.2); border:1px solid #00c851; border-radius:20px; padding:.2rem .7rem; color:#00ff6a; font-size:.85rem; font-weight:700; }
.tag-sin-stock { display:inline-block; background:rgba(255,68,68,0.2); border:1px solid #ff4444; border-radius:20px; padding:.2rem .7rem; color:#ff9999; font-size:.85rem; font-weight:700; }

/* ── DIVISOR ── */
hr { border-color:rgba(255,107,53,0.2) !important; }
iframe { border-radius:14px; border:2px solid rgba(255,107,53,0.4); }



/* ── RESPONSIVE ── */
@media (max-width:600px) {
    .welcome-grid { gap:5px; } .welcome-grid img { border-radius:7px; }
    .total-box { padding:.8rem 1rem; }
}
</style>
""", unsafe_allow_html=True)

# ── HELPERS ──────────────────────────────────────────────────────────────────
def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # ── Streamlit Cloud: usa st.secrets ──────────────────────────────────────
    has_secrets = False
    try:
        has_secrets = "gcp_service_account" in st.secrets
    except Exception:
        pass
    if has_secrets:
        import json
        creds_dict = {k: v for k, v in st.secrets["gcp_service_account"].items()}
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        # ── Local: usa claves.json ────────────────────────────────────────────
        creds = ServiceAccountCredentials.from_json_keyfile_name("claves.json", scope)
    client = gspread.authorize(creds)
    return client.open("inventario_tienda").sheet1

def get_pedidos_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    has_secrets = False
    try:
        has_secrets = "gcp_service_account" in st.secrets
    except Exception:
        pass
    if has_secrets:
        creds_dict = {k: v for k, v in st.secrets["gcp_service_account"].items()}
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name("claves.json", scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open("inventario_tienda")
    try:
        sheet = spreadsheet.worksheet("Pedidos")
    except Exception:
        # Si no existe la solapa de Pedidos, la creamos
        sheet = spreadsheet.add_worksheet(title="Pedidos", rows=1000, cols=6)
        sheet.append_row(["Fecha", "ID Pedido", "Cliente / Contacto", "Detalle Pedido WS", "Total", "Estado"])
    return sheet

def cargar_pedidos_sheets():
    try:
        sheet = get_pedidos_sheet()
        data  = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"⚠️ Error al cargar historial de pedidos: {e}")
        return pd.DataFrame()

def actualizar_estado_pedido(id_ped, nuevo_estado, df_pedidos):
    try:
        sheet = get_pedidos_sheet()
        matching_idx = df_pedidos[df_pedidos["ID Pedido"] == id_ped].index
        if len(matching_idx) > 0:
            fila_sheet = int(matching_idx[0]) + 2  # fila 1 son cabeceras, datos desde fila 2
            sheet.update_cell(fila_sheet, 6, nuevo_estado)  # Estado es col 6
            return True
        return False
    except Exception as e:
        st.error(f"Error al actualizar estado del pedido: {e}")
        return False

def get_compatibilidad_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    has_secrets = False
    try:
        has_secrets = "gcp_service_account" in st.secrets
    except Exception:
        pass
    if has_secrets:
        creds_dict = {k: v for k, v in st.secrets["gcp_service_account"].items()}
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name("claves.json", scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open("inventario_tienda")
    return spreadsheet.worksheet("Compatibilidad")

@st.cache_data(ttl=5)
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
        st.error(f"⚠️ Error al conectar con la pestaña de Compatibilidad: {e}")
        return pd.DataFrame()

def geocodificar_inversa_nominatim(lat, lon):
    import requests as _req
    url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
    headers = {
        'User-Agent': 'BEJO_Accesorios_App/1.0 (tienda_accesorios_agent)'
    }
    try:
        r = _req.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            address_parts = data.get("address", {})
            road = address_parts.get("road", "")
            house_number = address_parts.get("house_number", "")
            city = address_parts.get("city", address_parts.get("town", address_parts.get("suburb", "")))
            state = address_parts.get("state", "")
            
            clean_addr = ""
            if road:
                clean_addr += road
                if house_number:
                    clean_addr += f" {house_number}"
                if city:
                    clean_addr += f", {city}"
                if state:
                    clean_addr += f", {state}"
            else:
                clean_addr = data.get("display_name", "")
                
            return clean_addr
        return None
    except Exception:
        return None

def geocodificar_directa_nominatim(query):
    import requests as _req
    import urllib.parse
    query_clean = query.strip()
    if not query_clean:
        return None
    search_q = query_clean
    if "tucuman" not in query_clean.lower():
        search_q += ", San Miguel de Tucumán, Tucumán, Argentina"
    else:
        if "argentina" not in query_clean.lower():
            search_q += ", Argentina"
            
    url = f"https://nominatim.openstreetmap.org/search?format=json&q={urllib.parse.quote(search_q)}&limit=1"
    headers = {
        'User-Agent': 'BEJO_Accesorios_App/1.0 (tienda_accesorios_agent)'
    }
    try:
        r = _req.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data:
                lat = float(data[0]["lat"])
                lon = float(data[0]["lon"])
                address_parts = data[0].get("display_name", "")
                partes = [p.strip() for p in address_parts.split(",")]
                if len(partes) > 4:
                    clean_display = ", ".join(partes[:4])
                else:
                    clean_display = ", ".join(partes)
                return lat, lon, clean_display
        return None
    except Exception:
        return None




def descontar_stock(carrito: dict, df_ref: pd.DataFrame):
    """Resta del Excel las cantidades vendidas de cada producto del carrito."""
    try:
        sheet   = get_sheet()
        cols    = df_ref.columns.tolist()
        col_cant = cols.index("Cantidad") + 1   # columna 1-based en Sheets
        for df_idx, cant_vendida in carrito.items():
            fila_sheet   = df_idx + 5            # head=4 → datos desde fila 5
            stock_actual = int(df_ref.loc[df_idx, "Cantidad"])
            nuevo_stock  = max(0, stock_actual - cant_vendida)
            sheet.update_cell(fila_sheet, col_cant, str(nuevo_stock))
        return True
    except Exception as e:
        st.warning(f"⚠️ No se pudo actualizar el stock en el Excel: {e}")
        return False

def obtener_access_token_mp():
    """Obtiene de forma segura el access token de Mercado Pago desde st.secrets."""
    try:
        if "mercadopago" in st.secrets:
            try:
                tok = st.secrets["mercadopago"].get("access_token", None)
                if tok: return tok
            except Exception:
                pass
        for key in ["MERCADOPAGO_ACCESS_TOKEN", "mercadopago_access_token"]:
            tok = st.secrets.get(key, None)
            if tok: return tok
            try:
                tok = st.secrets[key]
                if tok: return tok
            except Exception:
                pass
        # Fallback en caso de que haya quedado dentro del bloque [gcp_service_account] por formato TOML
        if "gcp_service_account" in st.secrets:
            try:
                gcp = st.secrets["gcp_service_account"]
                for key in ["MERCADOPAGO_ACCESS_TOKEN", "mercadopago_access_token"]:
                    tok = gcp.get(key, None)
                    if tok: return tok
            except Exception:
                pass
    except Exception:
        pass
    return None

def crear_preferencia_mp(total_pedido, id_pedido):
    """Crea una preferencia de pago en Mercado Pago y devuelve la URL de checkout (init_point)."""
    access_token = obtener_access_token_mp()
    if not access_token:
        return None
        
    import requests
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    preference_data = {
        "items": [
            {
                "title": f"Pedido {id_pedido} - BEJO Accesorios",
                "quantity": 1,
                "unit_price": float(total_pedido),
                "currency_id": "ARS"
            }
        ],
        "external_reference": id_pedido,
        "back_urls": {
            "success": "https://bejo-accesorios.streamlit.app",
            "failure": "https://bejo-accesorios.streamlit.app",
            "pending": "https://bejo-accesorios.streamlit.app"
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
        return None
    except Exception:
        return None

def imagen_a_base64(archivo_subido, max_size=(400,400), quality=72):
    """Comprime una imagen subida y la convierte a data-URL base64."""
    if not PIL_OK:
        return None
    try:
        img = Image.open(archivo_subido)
        img.thumbnail(max_size, Image.LANCZOS)
        if img.mode not in ("RGB","L"):
            img = img.convert("RGB")
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode()
        return f"data:image/jpeg;base64,{b64}"
    except Exception as e:
        st.error(f"Error al procesar imagen: {e}")
        return None

def mostrar_imagen(src, **kwargs):
    """Muestra imagen ya sea URL o data-URL base64."""
    if isinstance(src, str) and src.startswith("data:image"):
        try:
            b64_data = src.split(",", 1)[1]
            st.image(base64.b64decode(b64_data), **kwargs)
        except Exception:
            st.image("https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500", **kwargs)
    elif src and str(src).strip():
        st.image(src, **kwargs)
    else:
        st.image("https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500", **kwargs)

def limpiar_precio_mercado(val):
    import re
    if pd.isna(val):
        return 0
    s = str(val).strip().replace('$', '')
    if not s:
        return 0
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
            return 0

@st.cache_data(ttl=5)
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
        return df
    except Exception as e:
        st.error(f"⚠️ Error al conectar con Google Sheets: {e}")
        # Fallback de datos de prueba para desarrollo local
        mock_data = [
            {
                "Nombre del Artículo": "Funda Silicona",
                "Marca Principal": "Samsung",
                "Modelo Exacto": "Galaxy A54",
                "Color / Diseño (Variación)": "Negro Mate",
                "Precio Mercado": 15000,
                "Cantidad": 5,
                "Imagen_URL": "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500"
            },
            {
                "Nombre del Artículo": "Funda Transparente",
                "Marca Principal": "Apple",
                "Modelo Exacto": "iPhone 14",
                "Color / Diseño (Variación)": "Transparente",
                "Precio Mercado": 18000,
                "Cantidad": 8,
                "Imagen_URL": "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500"
            }
        ]
        return pd.DataFrame(mock_data)

df_stock = cargar_datos_sheets()

# ── SESSION STATE ─────────────────────────────────────────────────────────────
for k, v in {
    "carrito": {}, "mostrar_banner_carrito": False,
    "admin_autenticado": False,
    "admin_modo": None,          # "editar" | "nuevo"
    "admin_idx_sel": None,       # índice del df del producto seleccionado
    "vista": "catalogo",         # "catalogo" | "carrito"
    "_georef_query": "",          # texto de búsqueda del autocomplete
    "_georef_sugerencias": [],    # sugerencias devueltas por Georef
    "_georef_elegida": None,      # calle elegida del autocomplete
    "map_coords": [-26.8306, -65.2201], # Centro de San Miguel de Tucumán
    "last_clicked_tracked": None,
    "inp_dir": "",
    "geo_error": None,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── PROCESAR AGREGAR AL CARRITO DESDE QUERY PARAMS ──
_add_idx = st.query_params.get("add_cart", "")
if _add_idx:
    try:
        _idx = int(_add_idx)
        if _idx in df_stock.index:
            _row = df_stock.loc[_idx]
            _stock = int(_row["Cantidad"])
            _en_carrito = st.session_state.carrito.get(_idx, 0)
            if _en_carrito + 1 <= _stock:
                st.session_state.carrito[_idx] = _en_carrito + 1
                st.session_state.mostrar_banner_carrito = True
            else:
                st.toast(f"⚠️ Solo hay {_stock} unidades disponibles de {_row['Nombre del Artículo']} ({_row['Color / Diseño (Variación)']}).", icon="⚠️")
    except Exception:
        pass
    # Limpiar parámetro
    _qp = dict(st.query_params)
    _qp.pop("add_cart", None)
    st.query_params.from_dict(_qp)
    st.rerun()

# ── CONDITIONAL CSS FOR ADMIN PANEL HOVER ──
if not st.session_state.admin_autenticado:
    st.markdown("""
    <style>
    div[data-testid="stExpander"] {
        opacity: 0.0 !important;
        transition: opacity 0.3s ease-in-out !important;
    }
    div[data-testid="stExpander"]:hover,
    div[data-testid="stExpander"]:focus-within {
        opacity: 1.0 !important;
    }
    div[data-testid="stExpander"] div[data-testid="stExpander"] {
        opacity: 1.0 !important;
    }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
    div[data-testid="stExpander"] {
        opacity: 1.0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ── DETECTAR RETORNO DE MERCADO PAGO ──
qp = st.query_params
if "external_reference" in qp:
    id_pedido = qp["external_reference"]
    status = qp.get("status", "unknown")
    payment_id = qp.get("payment_id", "")
    
    # Intentar actualizar el estado a "Pagado" en Google Sheets si fue aprobado
    if status == "approved":
        try:
            df_ped = cargar_pedidos_sheets()
            if not df_ped.empty:
                actualizar_estado_pedido(id_pedido, "Pagado", df_ped)
        except Exception:
            pass

    st.balloons()
    
    # Cabecera especial de confirmación
    st.markdown('<div class="bejo-header">⚡ BEJO ⚡</div>', unsafe_allow_html=True)
    st.markdown('<div class="bejo-subtitle">PEDIDO RECONFIRMADO</div>', unsafe_allow_html=True)
    
    status_text = "APROBADO ✅" if status == "approved" else "PENDIENTE ⏳" if status == "pending" else "RECHAZADO ❌" if status == "rejected" else status.upper()
    box_color = "linear-gradient(135deg, #00c851, #007e33)" if status == "approved" else "linear-gradient(135deg, #f7971e, #ffd200)" if status == "pending" else "linear-gradient(135deg, #ff4444, #cc0000)"
    text_color = "#1a1a1a" if status == "pending" else "#ffffff"

    # Mensaje automático a WS con datos del pedido
    msg_re = f"⚡ Hola BEJO! Acabo de pagar mi pedido 🔥\n\n🆔 *ID Pedido:* {id_pedido}\n💳 *Estado del pago:* {status_text}\n🧾 *ID Transacción MP:* {payment_id}\n\n¿Desean hacer alguna verificación o tengo alguna otra consulta? 🙌"
    ws_url_re = f"https://wa.me/{NUMERO_WS}?text={urllib.parse.quote(msg_re)}"

    st.markdown(f"""
<div style="background: {box_color}; color:{text_color}; border-radius:18px; padding:2rem; text-align:center; box-shadow:0 10px 30px rgba(0,0,0,0.25); margin: 1.5rem 0;">
<h1 style="color:{text_color}; margin:0 0 10px 0; font-size:2.2rem;">¡PEDIDO RECONFIRMADO! 🎉</h1>
<h3 style="color:{text_color}; opacity: 0.9; margin:0 0 20px 0; font-size:1.15rem;">Tu pago ha sido registrado de manera segura.</h3>
<div style="background:rgba(255,255,255,0.15); border-radius:12px; padding:1.2rem; margin-bottom:1.5rem; text-align:left;">
<p style="margin:5px 0; font-size:1.1rem; color:{text_color};">🆔 <b>ID de Pedido:</b> <span style="font-weight:700;">{id_pedido}</span></p>
<p style="margin:5px 0; font-size:1.1rem; color:{text_color};">💳 <b>Estado del Pago:</b> <span style="font-weight:700;">{status_text}</span></p>
<p style="margin:5px 0; font-size:1.1rem; color:{text_color};">🧾 <b>ID Transacción MP:</b> <span style="font-weight:700;">{payment_id}</span></p>
</div>
<p style="font-size:0.95rem; color:{text_color}; opacity: 0.85; margin:0 0 8px 0;">
📸 <b>¡Sacale captura a esta pantalla!</b> Así tenés tu comprobante listo.
</p>
<p style="font-size:0.9rem; color:{text_color}; opacity:0.75; margin:0;">
📲 En unos segundos te abriremos WhatsApp automáticamente para confirmar con el vendedor...
</p>
</div>
<script>
setTimeout(function() {{
    window.location.href = "{ws_url_re}";
}}, 4000);
</script>
""", unsafe_allow_html=True)

    if st.button("🛍️ Volver al Catálogo / Hacer otra compra", use_container_width=True, type="primary", key="btn_volver_mp"):
        st.query_params.clear()
        st.session_state.vista = "catalogo"
        st.rerun()
        
    st.stop()

# ── HEADER (Logo y Nombre) ───────────────────────────────────────────────────
logo_col1, logo_col2, logo_col3 = st.columns([1.3, 1, 1.3])
with logo_col2:
    try:
        st.image("logo.png", use_container_width=True)
    except Exception:
        pass

st.markdown('<div class="bejo-header">⚡ BEJO ⚡</div>', unsafe_allow_html=True)
st.markdown('<div class="bejo-subtitle">ACCESORIOS PARA CELULARES · CALIDAD PREMIUM</div>', unsafe_allow_html=True)

# ── MENÚ DE NAVEGACIÓN PRINCIPAL ──────────────────────────────────────────────
nav_c1, nav_c2 = st.columns(2)
with nav_c1:
    btn_cat_type = "primary" if st.session_state.vista == "catalogo" else "secondary"
    if st.button("🏠 INICIO / CATÁLOGO", use_container_width=True, key="nav_home", type=btn_cat_type):
        st.session_state.vista = "catalogo"
        st.rerun()
with nav_c2:
    num_items = sum(st.session_state.carrito.values())
    btn_car_type = "primary" if st.session_state.vista == "carrito" else "secondary"
    if st.button(f"🛒 MI CARRITO ({num_items} items)", use_container_width=True, key="nav_cart", type=btn_car_type):
        st.session_state.vista = "carrito"
        st.rerun()
st.markdown("---")

# ── VISTA DE COMPATIBILIDAD ───────────────────────────────────────────────────
if st.session_state.vista == "compatibilidad":
    st.markdown('<div class="carrito-titulo">🔍 Comprobador de Compatibilidad</div>', unsafe_allow_html=True)
    if st.button("⬅️ Volver al Catálogo / Inicio", use_container_width=True, key="btn_volver_cat_comp"):
        st.session_state.vista = "catalogo"
        st.rerun()
    st.markdown("")

    # Cargar datos de la pestaña Compatibilidad
    df_comp = cargar_compatibilidad_sheets()
    
    if df_comp.empty:
        st.warning("⚠️ No se pudieron cargar los datos de compatibilidad en este momento. Por favor intentá más tarde.")
    else:
        st.markdown("""
        <div style="background: rgba(255, 107, 53, 0.12); border-left: 4px solid #ff6b35; padding: 15px; border-radius: 0 10px 10px 0; margin-bottom: 20px;">
            <span style="color: #fff; font-weight: 600; font-size: 1rem;">📱 Averiguá qué accesorios son compatibles con otros modelos</span><br>
            <span style="color: #c8bfff; font-size: 0.9rem;">Elegí el tipo de artículo, la marca y el modelo de tu teléfono para ver las compatibilidades en nuestro stock.</span>
        </div>
        """, unsafe_allow_html=True)

        # Filtros en cascada
        col_comp1, col_comp2, col_comp3 = st.columns(3)
        
        # 1. Tipo de producto
        col_tipos = sorted(df_comp["tipo de producto"].dropna().unique())
        if not col_tipos:
            st.info("No hay tipos de producto cargados en la hoja de compatibilidad.")
        else:
            with col_comp1:
                tipo_sel = st.selectbox("1. Seleccioná el tipo de artículo:", col_tipos, key="comp_tipo_sel")
            
            df_filtered = df_comp[df_comp["tipo de producto"] == tipo_sel]
            
            # 2. Marca
            col_marcas = sorted(df_filtered["marca"].dropna().unique())
            if not col_marcas:
                st.info("No hay marcas cargadas para este tipo de producto.")
            else:
                with col_comp2:
                    marca_sel = st.selectbox("2. Seleccioná la marca de tu celu:", col_marcas, key="comp_marca_sel")
                    
                df_filtered = df_filtered[df_filtered["marca"] == marca_sel]
                
                # 3. Modelo
                col_modelos = sorted(df_filtered["modelo"].dropna().unique())
                if not col_modelos:
                    st.info("No hay modelos cargados para esta marca.")
                else:
                    with col_comp3:
                        modelo_sel = st.selectbox("3. Seleccioná el modelo exacto:", col_modelos, key="comp_modelo_sel")
                        
                    df_final = df_filtered[df_filtered["modelo"] == modelo_sel]
                    
                    st.markdown("---")
                    
                    if not df_final.empty:
                        # Mostrar compatibilidad
                        compat_value = df_final.iloc[0]["compatibilidad"]
                        if compat_value and str(compat_value).strip():
                            # Formatear la lista de compatibles de forma premium
                            lista_compat = [item.strip() for item in str(compat_value).split(",") if item.strip()]
                            
                            st.markdown(f"""
                            <div class="prod-card" style="border-color: #ff6b35; background: rgba(255, 107, 53, 0.05);">
                                <div style="color: #ff6b35; font-size: 1.25rem; font-weight: 900; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
                                    <span>✅ COMPATIBILIDADES ENCONTRADAS</span>
                                </div>
                                <p style="font-size: 1.05rem; color: #fff; margin-bottom: 12px;">
                                    Para tu <b>{tipo_sel}</b> de <b>{marca_sel} {modelo_sel}</b>, también podés usar las de estos modelos:
                                </p>
                                <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px;">
                                    {"".join(f'<span style="background: rgba(255,107,53,0.15); border: 1.5px solid #ff6b35; border-radius: 20px; padding: 6px 16px; color: #fff; font-size: 0.95rem; font-weight: 700; box-shadow: 0 2px 8px rgba(255,107,53,0.2);">{item}</span>' for item in lista_compat)}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.info("ℹ️ No hay información de compatibilidad cargada en el Excel para este modelo específico.")
                    else:
                        st.info("ℹ️ No se encontró ningún registro para la combinación seleccionada en la planilla de compatibilidades.")

    st.stop()

# ── VISTA DEL CARRITO Y CHECKOUT ──────────────────────────────────────────────
if st.session_state.vista == "carrito":
    st.markdown('<div class="carrito-titulo">🛒 Tu Carrito de Compras</div>', unsafe_allow_html=True)
    if st.button("⬅️ Volver a ver el catálogo", use_container_width=True, key="btn_volver_cat"):
        st.session_state.vista = "catalogo"
        st.rerun()
    st.markdown("")

    if not st.session_state.carrito:
        st.info("Tu carrito está vacío. ¡Volvé al catálogo para elegir productos!")
    else:
        total_pedido      = 0
        resumen_productos = []

        for idx, cantidad in list(st.session_state.carrito.items()):
            row          = df_stock.loc[idx]
            nombre_prod  = f"{row['Nombre del Artículo']} {row['Modelo Exacto']} ({row['Color / Diseño (Variación)']})"
            precio_unit  = row["Precio Mercado"]
            stock_actual = row["Cantidad"]
            c1, c2, c3, c4 = st.columns([2.5, 1.8, 1.2, 0.5])
            c1.markdown(f"🔹 **{nombre_prod}**")
            
            # Selector de cantidad con botones - / +
            qty_col1, qty_col2, qty_col3 = c2.columns([1, 1, 1])
            with qty_col1:
                if st.button("➖", key=f"qty_dec_{idx}", use_container_width=True):
                    if cantidad > 1:
                        st.session_state.carrito[idx] = cantidad - 1
                        st.rerun()
            with qty_col2:
                st.markdown(f"<p style='text-align:center; font-weight:700; font-size:1.1rem; line-height:2.2; margin:0;'>{cantidad}</p>", unsafe_allow_html=True)
            with qty_col3:
                if st.button("➕", key=f"qty_inc_{idx}", use_container_width=True):
                    if cantidad < stock_actual:
                        if cantidad < 10:
                            st.session_state.carrito[idx] = cantidad + 1
                            st.rerun()
                        else:
                            st.toast("⚠️ Límite de compra de 10 unidades por persona alcanzado.", icon="⚠️")
                    else:
                        st.session_state[f"msg_error_stock_{idx}"] = True
                        st.rerun()
                        
            subtotal = precio_unit * cantidad
            total_pedido += subtotal
            resumen_productos.append(f"- {nombre_prod} x{cantidad} (${subtotal:,.0f})")
            c3.markdown(f"**${subtotal:,.0f}**")
            if c4.button("🗑️", key=f"del_{idx}"):
                del st.session_state.carrito[idx]; st.rerun()

            # Mostrar advertencia si el cliente intenta superar el stock
            if st.session_state.get(f"msg_error_stock_{idx}"):
                st.warning(
                    f"😔 **¡No hay más stock disponible de este producto!**\n\n"
                    f"Ya agregaste las **{stock_actual}** unidades que tenemos en stock de: **{nombre_prod}**.\n\n"
                    f"Si necesitás más unidades, podés elegir otra variante (otro color o modelo de celular) desde el catálogo."
                )
                if st.button("Entendido 👍", key=f"clear_stock_msg_{idx}"):
                    st.session_state[f"msg_error_stock_{idx}"] = False
                    st.rerun()

        st.markdown(f'<div class="total-box">💰 Total a Pagar: ${total_pedido:,.0f}</div>', unsafe_allow_html=True)

        # ── ENTREGA ──────────────────────────────────────────────────────────
        st.markdown('<div class="seccion-titulo">📦 ¿Cómo querés recibirlo?</div>', unsafe_allow_html=True)
        metodo_entrega = st.radio("entrega_r", ["🏪  Retiro en punto de venta","🏠  Envío a domicilio"],
                                  index=None, label_visibility="collapsed")
        direccion = observacion = horario = ""

        if metodo_entrega == "🏪  Retiro en punto de venta":
            st.markdown("""<div class="info-ws">📍 <b>Retiro en local BEJO</b><br>
            Una vez confirmado el pedido, coordiná el retiro directamente con el vendedor por WhatsApp. 😊</div>""",
            unsafe_allow_html=True)

        elif metodo_entrega == "🏠  Envío a domicilio":
            st.markdown(f"""
            <div style="background: rgba(255, 107, 53, 0.12); border-left: 4px solid #ff6b35; padding: 12px; border-radius: 0 10px 10px 0; margin-bottom: 15px; font-size: 0.9rem; color: #fff;">
                🛵 <b>Información sobre Envíos:</b><br>
                • Realizamos envíos en <b>San Miguel de Tucumán</b> (consultar por envíos fuera de S.M.T.).<br>
                • <b>Envío GRATIS</b> dentro de las 4 Avenidas.<br>
                • Fuera de las 4 Avenidas, se coordinará el costo por WhatsApp de acuerdo a tu dirección.
            </div>
            """, unsafe_allow_html=True)
            st.markdown("#### 📍 Tu dirección de entrega")

            # Buscador y campo de dirección única
            addr_col1, addr_col2 = st.columns([3, 1])
            with addr_col1:
                direccion = st.text_input(
                    "Dirección de entrega (calle y número):",
                    value=st.session_state.inp_dir,
                    placeholder="Ej: Marcos Paz 987, San Miguel de Tucumán",
                )
                st.session_state.inp_dir = direccion
            with addr_col2:
                st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                buscar_btn = st.button("Buscar 🔍", use_container_width=True, help="Busca esta dirección en el mapa y mueve el pin")

            if buscar_btn and direccion.strip():
                res_geo = geocodificar_directa_nominatim(direccion)
                if res_geo:
                    lat, lon, display_addr = res_geo
                    st.session_state.map_coords = [lat, lon]
                    st.session_state.inp_dir = display_addr
                    st.session_state.geo_error = None
                    st.rerun()
                else:
                    st.session_state.geo_error = f"⚠️ No se encontró la dirección '{direccion}' en San Miguel de Tucumán. Verificá que esté bien escrita o hacé clic directamente en el mapa."
            
            if st.session_state.get("geo_error"):
                st.warning(st.session_state.geo_error)
            
            st.markdown("<p style='font-size:0.85rem; color:#a89cff; margin-bottom:8px;'>📍 También podés hacer clic o tocar directamente en el mapa para mover el pin a tu ubicación exacta:</p>", unsafe_allow_html=True)
            
            map_coords = st.session_state.map_coords
            m = folium.Map(location=map_coords, zoom_start=16, control_scale=True)
            folium.Marker(
                map_coords,
                popup="Tu ubicación seleccionada",
                tooltip="Hacé clic en el mapa para mover este pin",
                icon=folium.Icon(color="red", icon="info-sign")
            ).add_to(m)
            
            map_data = st_folium(
                m,
                height=280,
                use_container_width=True,
                key="direccion_map_picker",
                returned_objects=["last_clicked"]
            )
            
            if map_data and map_data.get("last_clicked"):
                last_clicked = map_data["last_clicked"]
                last_clicked_tracked = st.session_state.get("last_clicked_tracked")
                if last_clicked != last_clicked_tracked:
                    st.session_state.last_clicked_tracked = last_clicked
                    lat, lon = last_clicked["lat"], last_clicked["lng"]
                    st.session_state.map_coords = [lat, lon]
                    st.session_state.geo_error = None  # Limpiar error
                    with st.spinner("Buscando dirección..."):
                        dir_geocodificada = geocodificar_inversa_nominatim(lat, lon)
                        if dir_geocodificada:
                            st.session_state.inp_dir = dir_geocodificada
                    st.rerun()

        st.markdown('<div class="seccion-titulo">💳 Método de Pago</div>', unsafe_allow_html=True)
        metodo_pago = st.radio("pago_r", ["💵  Efectivo", "🏦  Transferencia Bancaria", "💳  Mercado Pago (Tarjeta, Dinero en cuenta)"],
                               index=None, label_visibility="collapsed")
        mitad = total_pedido // 2
        resto = total_pedido - mitad
        if metodo_pago == "🏦  Transferencia Bancaria":
            st.markdown(f"""<div class="info-transfer">🏦 <b>PAGO POR TRANSFERENCIA</b><br><br>
            ✅ Transferí <b>la mitad ahora: ${mitad:,.0f}</b><br>
            📦 El resto (<b>${resto:,.0f}</b>) lo abonás al recibir el producto.<br><br>
            💬 Los datos bancarios te los mandamos por WhatsApp. 🤝</div>""", unsafe_allow_html=True)
        elif metodo_pago == "💳  Mercado Pago (Tarjeta, Dinero en cuenta)":
            access_token = obtener_access_token_mp()
            if not access_token:
                st.warning("⚠️ El vendedor aún no configuró las credenciales de Mercado Pago en Streamlit. Seleccioná otro método o coordiná por WhatsApp.")
            else:
                st.markdown(f"""<div class="info-ws">💳 <b>PAGO CON MERCADO PAGO</b><br><br>
                Al confirmar el pedido, generaremos un link de pago oficial de Mercado Pago para que abones el total de <b>${total_pedido:,.0f}</b>.<br><br>
                Podrás abonar con tarjeta de crédito/débito, transferencia bancaria o dinero en cuenta. 🤝</div>""", unsafe_allow_html=True)

        st.markdown("")
        if st.button("🚀 CONFIRMAR PEDIDO Y ENVIAR A WHATSAPP", type="primary", use_container_width=True):
            errores = []
            if metodo_entrega is None: errores.append("⚠️ Seleccioná cómo querés recibir tu pedido.")
            if metodo_pago    is None: errores.append("⚠️ Seleccioná el método de pago.")
            if metodo_entrega == "🏠  Envío a domicilio" and not direccion.strip():
                errores.append("⚠️ Ingresá tu dirección de envío.")
            if metodo_pago == "💳  Mercado Pago (Tarjeta, Dinero en cuenta)":
                access_token = obtener_access_token_mp()
                if not access_token:
                    errores.append("⚠️ El vendedor aún no configuró las credenciales de Mercado Pago en Streamlit. Seleccioná otro método de pago.")
            if errores:
                for e in errores: st.markdown(f'<div class="error-validacion">{e}</div>', unsafe_allow_html=True)
            else:
                ahora     = datetime.now()
                id_pedido = f"PED-{ahora.strftime('%d%m-%H%M')}-{random.randint(100,999)}"
                le = metodo_entrega.replace("🏪  ","").replace("🏠  ","")
                lp = metodo_pago.replace("💵  ","").replace("🏦  ","").replace("💳  ","")
                
                # Generar link de pago si es Mercado Pago
                mp_url = None
                if metodo_pago == "💳  Mercado Pago (Tarjeta, Dinero en cuenta)":
                    with st.spinner("Generando link de pago de Mercado Pago..."):
                        mp_url = crear_preferencia_mp(total_pedido, id_pedido)
                
                msg = (f"⚡ ¡Hola BEJO! Nuevo pedido 🔥\n\n🆔 *ID Pedido:* {id_pedido}\n"
                       f"📦 *Productos:*\n" + "\n".join(resumen_productos) +
                       f"\n\n💰 *Total:* ${total_pedido:,.0f}\n💳 *Pago:* {lp}\n")
                if metodo_pago == "🏦  Transferencia Bancaria":
                    msg += f"   ↳ Seña (50%): ${mitad:,.0f} | Resto al recibir: ${resto:,.0f}\n"
                elif metodo_pago == "💳  Mercado Pago (Tarjeta, Dinero en cuenta)" and mp_url:
                    msg += f"   ↳ 🔗 *Link de Pago:* {mp_url}\n"
                msg += f"📍 *Entrega:* {le}\n"
                if metodo_entrega == "🏠  Envío a domicilio":
                    msg += f"🏠 *Dirección:* {direccion}\n"
                    if observacion.strip(): msg += f"📝 *Observación:* {observacion}\n"
                    msg += f"🕐 *Horario preferible:* {horario}\n"
                if metodo_entrega == "🏪  Retiro en punto de venta":
                    msg += "\n🤝 ¡Coordino el retiro con ustedes por WhatsApp!\n"
                msg += "\n✨ ¡Gracias por elegir BEJO! 🙌"
                ws_url = f"https://wa.me/{NUMERO_WS}?text={urllib.parse.quote(msg)}"

                # ── Guardar pedido en el Excel (solapa Pedidos) ─────────────
                try:
                    p_sheet = get_pedidos_sheet()
                    cliente_info = f"Pago: {lp} | Entrega: {le}"
                    if metodo_entrega == "🏠  Envío a domicilio":
                        cliente_info += f" | Dir: {direccion}"
                    p_sheet.append_row([
                        ahora.strftime('%Y-%m-%d %H:%M:%S'),
                        id_pedido,
                        cliente_info,
                        msg,
                        str(total_pedido),
                        "Pendiente"
                    ])
                except Exception as e:
                    st.warning(f"⚠️ No se pudo guardar el pedido en el historial de Sheets: {e}")

                # ── Descontar stock del Excel ──────────────────────────────
                with st.spinner("Actualizando stock en el catálogo..."):
                    ok_stock = descontar_stock(st.session_state.carrito, df_stock)
                st.cache_data.clear()   # fuerza recarga del catálogo

                # ── Vaciar carrito y regresar a la vista catálogo ─────────────
                st.session_state.carrito = {}
                st.session_state.vista = "catalogo"

                st.balloons()
                if ok_stock:
                    st.success(f"✅ ¡Pedido **{id_pedido}** generado con éxito!")
                else:
                    st.success(f"✅ ¡Pedido **{id_pedido}** generado! Revisá el stock manualmente.")

                # Redirección automática / Botones finales
                if mp_url:
                    st.markdown(f"""
                        <div style="background: rgba(37, 211, 102, 0.15); border: 1px solid #25D366; border-radius: 12px; padding: 20px; text-align: center; margin-top: 1.5rem;">
                            <h3 style="color: #a8ffdb; margin: 0 0 15px 0;">🎉 ¡Pedido {id_pedido} confirmado!</h3>
                            <p style="color: #fff; margin-bottom: 20px; font-size: 1.05rem;">
                                Por favor, realizá el pago en Mercado Pago y enviá el pedido por WhatsApp.
                            </p>
                            <div style="display: flex; flex-direction: column; gap: 12px; align-items: center; justify-content: center;">
                                <a href="{mp_url}" target="_blank" style="display: inline-block; background: #009EE3; color: white; font-weight: 800; padding: 12px 24px; border-radius: 10px; text-decoration: none; font-size: 1.1rem; box-shadow: 0 4px 15px rgba(0,158,227,0.4); border: none; width: 80%; max-width: 320px;">
                                    💳 PAGAR CON MERCADO PAGO
                                </a>
                                <a href="{ws_url}" target="_self" style="display: inline-block; background: #25D366; color: white; font-weight: 800; padding: 12px 24px; border-radius: 10px; text-decoration: none; font-size: 1.1rem; box-shadow: 0 4px 15px rgba(37,211,102,0.4); border: none; width: 80%; max-width: 320px;">
                                    📲 ENVIAR POR WHATSAPP
                                </a>
                            </div>
                            <p style="color: #a89cff; font-size: 0.85rem; margin-top: 20px;">
                                En 5 segundos te redirigiremos automáticamente a WhatsApp para que envíes el detalle y el link al vendedor.
                            </p>
                        </div>
                        <script>
                            setTimeout(function() {{
                                window.location.href = "{ws_url}";
                            }}, 5000);
                        </script>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                        <div style="background: rgba(37, 211, 102, 0.15); border: 1px solid #25D366; border-radius: 12px; padding: 15px; text-align: center; margin-top: 1.5rem;">
                            <h3 style="color: #a8ffdb; margin: 0 0 10px 0;">📲 Redirigiendo a WhatsApp...</h3>
                            <p style="color: #fff; margin: 0; font-size: 1rem;">Estamos abriendo tu chat para enviar los detalles del pedido <b>{id_pedido}</b>.</p>
                            <p style="color: #a89cff; font-size: 0.85rem; margin: 10px 0 0 0;">Si la aplicación no se abre automáticamente, <a href="{ws_url}" target="_self" style="color: #ffd200; font-weight: 700; text-decoration: underline;">hacé clic acá para enviar</a>.</p>
                        </div>
                        <script>
                            setTimeout(function() {{
                                window.location.href = "{ws_url}";
                            }}, 2000);
                        </script>
                    """, unsafe_allow_html=True)
    st.stop()

# ── VISTA CATÁLOGO (Default) ──────────────────────────────────────────────────
# ── GRILLA DE INICIO (3 elementos) ───────────────────────────────────────────
imgs_grilla = [
    "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=400&q=80",
    "https://images.unsplash.com/photo-1592890288564-76628a30a657?w=400&q=80",
    "https://images.unsplash.com/photo-1585771724684-38269d6639fd?w=400&q=80",
]
grid_html = '<div class="welcome-grid">' + "".join(f'<img src="{u}" alt="acc" loading="lazy"/>' for u in imgs_grilla) + '</div>'
st.markdown(grid_html, unsafe_allow_html=True)
st.markdown("---")

# ── Comprobador de Compatibilidad (Acceso Rápido) ──────────────────────────────
st.markdown(
    """
    <div style="text-align: center; margin-bottom: 0.5rem;">
        <span style="color: #c8bfff; font-size: 0.95rem; font-weight: 600;">📱 ¿Querés saber qué fundas o vidrios templados son compatibles con tu celu?</span>
    </div>
    """,
    unsafe_allow_html=True
)
if st.button("🔍 COMPROBÁ LA COMPATIBILIDAD (FUNDA, VIDRIO TEMPLADO, ACCESORIO)", type="primary", use_container_width=True, key="btn_go_compatibilidad"):
    st.session_state.vista = "compatibilidad"
    st.rerun()
st.markdown("---")

# ── Consulta por WhatsApp ─────────────────────────────────────────────────────
st.markdown(
    f"""
    <div style="background: rgba(37, 211, 102, 0.12); border: 1px solid rgba(37,211,102,0.4); border-radius: 12px; padding: 12px; text-align: center; margin-bottom: 1.5rem;">
        <span style="color: #a8ffdb; font-weight: 600; font-size: 0.95rem;">💬 ¿Tenés alguna duda o consulta antes de elegir tus productos?</span><br>
        <a href="https://wa.me/{NUMERO_WS}?text=Hola%20BEJO!%20Tengo%20una%20consulta%20antes%20de%20comprar..." target="_blank" 
           style="display: inline-block; background: #25D366; color: white; font-weight: 800; padding: 8px 16px; border-radius: 8px; text-decoration: none; margin-top: 8px; font-size: 0.9rem; box-shadow: 0 4px 10px rgba(37,211,102,0.3);">
           Consultar por WhatsApp 📲
        </a>
    </div>
    """,
    unsafe_allow_html=True
)

# ── Banner carrito ────────────────────────────────────────────────────────────
if st.session_state.get("mostrar_banner_carrito"):
    st.markdown('<div class="carrito-banner">🛒 ¡PRODUCTO AGREGADO AL CARRITO EXITOSAMENTE! ✅</div>', unsafe_allow_html=True)
    st.session_state.mostrar_banner_carrito = False

# ── Botón de acceso directo al carrito (arriba) ───────────────────────────────
if st.session_state.carrito:
    num_items = sum(st.session_state.carrito.values())
    if st.button(f"🛒 VER CARRITO DE COMPRAS ({num_items} items) ➔", type="primary", use_container_width=True, key="btn_go_cart_top"):
        st.session_state.vista = "carrito"
        st.rerun()
    st.markdown("")

# ════════════════════════════════════════════════════════════════════════════
# CATÁLOGO
# ════════════════════════════════════════════════════════════════════════════
if df_stock.empty:
    st.warning("No se pudieron cargar los datos de Google Sheets.")
else:
    st.markdown("### 🔍 Buscar Accesorios")
    cf1, cf2, cf3, cf4 = st.columns(4)
    with cf1:
        tipos = ["Todos"] + sorted([t for t in df_stock["Nombre del Artículo"].dropna().unique() if str(t).strip()])
        tipo_sel = st.selectbox("Tipo de Producto:", tipos)
    df_fil = df_stock if tipo_sel == "Todos" else df_stock[df_stock["Nombre del Artículo"] == tipo_sel]
    
    with cf2:
        marcas = ["Todas"] + sorted([m for m in df_fil["Marca Principal"].dropna().unique() if str(m).strip()])
        marca_sel = st.selectbox("Marca:", marcas)
    df_fil = df_fil if marca_sel == "Todas" else df_fil[df_fil["Marca Principal"] == marca_sel]
    
    with cf3:
        modelos = ["Todos"] + sorted([m for m in df_fil["Modelo Exacto"].dropna().unique() if str(m).strip()])
        modelo_sel = st.selectbox("Modelo:", modelos)
    df_fil = df_fil if modelo_sel == "Todos" else df_fil[df_fil["Modelo Exacto"] == modelo_sel]
    
    with cf4:
        disenos = ["Todos"] + sorted([d for d in df_fil["Color / Diseño (Variación)"].dropna().unique() if str(d).strip()])
        diseno_sel = st.selectbox("Color / Diseño:", disenos)
    df_fil = df_fil if diseno_sel == "Todos" else df_fil[df_fil["Color / Diseño (Variación)"] == diseno_sel]
    
    st.markdown("---")

    # HASH / FILTERS TRACKING TO RESET PAGE TO 1
    filter_key = f"{tipo_sel}_{marca_sel}_{modelo_sel}_{diseno_sel}"
    if st.session_state.get("last_filter_key") != filter_key:
        st.session_state.catalog_page = 1
        st.session_state.last_filter_key = filter_key

    if df_fil.empty:
        st.info("No hay productos disponibles para los filtros seleccionados.")
    else:
        PLACEHOLDER_IMG = "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500"

        def safe_img(url):
            if pd.isna(url) or str(url).strip() == "":
                return PLACEHOLDER_IMG
            return str(url).strip()

        # Grupos únicos por Tipo + Marca + Modelo
        group_keys = df_fil[["Nombre del Artículo","Marca Principal","Modelo Exacto"]].drop_duplicates()
        grouped_list = []
        for _, gk in group_keys.iterrows():
            mask = (
                (df_fil["Nombre del Artículo"] == gk["Nombre del Artículo"]) &
                (df_fil["Marca Principal"]      == gk["Marca Principal"]) &
                (df_fil["Modelo Exacto"]        == gk["Modelo Exacto"])
            )
            grouped_list.append(df_fil[mask])

        items_per_page = 6
        total_pages    = max(1, (len(grouped_list) + items_per_page - 1) // items_per_page)
        if st.session_state.get("catalog_page", 1) > total_pages:
            st.session_state.catalog_page = 1
        curr_page   = st.session_state.get("catalog_page", 1)
        start_idx   = (curr_page - 1) * items_per_page
        page_groups = grouped_list[start_idx:start_idx + items_per_page]

        # ── CSS GLOBAL (carrusel CSS puro + lightbox) ───────────────────────
        st.markdown("""
<style>
/* ── Card ── */
.bejo-card { background:rgba(255,255,255,0.05); border:1.5px solid rgba(255,107,53,0.35);
    border-radius:16px; overflow:hidden; transition:box-shadow .3s; margin-bottom:6px; }
.bejo-card:hover { box-shadow:0 0 22px rgba(255,107,53,0.35); }
/* ── Título del producto (cabecera de la card) ── */
.card-header { padding:10px 14px 7px; background:rgba(255,107,53,0.12);
    border-bottom:1px solid rgba(255,107,53,0.25); }
.card-title { font-weight:900; font-size:0.97rem; color:#fff; margin:0; line-height:1.3;
    letter-spacing:0.01em; text-shadow:0 1px 6px rgba(0,0,0,0.4); }
/* ── Ocultar radios y checkboxes de zoom ── */
.bejo-card input[type=radio],
.bejo-card input.zoom-cb { position:absolute; opacity:0; width:0; height:0; pointer-events:none; }
/* ── Slides ── */
.cslides { list-style:none; margin:0 !important; padding:0 !important; position:relative; background:#0f0c29; width:100% !important; }
.cslides > li {
    position: absolute;
    top: 0;
    left: 0;
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    visibility: hidden;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.2s ease-in-out;
}
/* ── Imagen: zoom al hacer click ── */
.img-lbl { display:block !important; width:100% !important; cursor:zoom-in; position:relative; overflow:hidden; margin:0 !important; padding:0 !important; }
.img-lbl img { width:100% !important; max-width:100% !important; height:auto !important; aspect-ratio:1/1 !important; object-fit:cover !important; display:block !important;
    transition:transform .3s; }
.img-lbl:hover img { transform:scale(1.03); }
.zoom-hint { position:absolute; top:8px; right:8px; background:rgba(0,0,0,0.55);
    border-radius:50%; width:30px; height:30px; display:flex; align-items:center;
    justify-content:center; font-size:0.9rem; pointer-events:none; opacity:0.8; }
/* ── Lightbox overlay ── */
.zoom-ov { display:none; position:fixed; inset:0; z-index:99999;
    background:rgba(0,0,0,0.93); align-items:center; justify-content:center;
    cursor:zoom-out; flex-direction:column; gap:10px; }
.zoom-ov > img { max-width:92vw; max-height:86vh; object-fit:contain; border-radius:12px;
    box-shadow:0 0 60px rgba(255,107,53,0.25); }
.zoom-close { color:rgba(255,255,255,0.55); font-size:0.8rem; user-select:none; }
/* ── Flechas ── */
.cprev,.cnext { position:absolute; top:42%; transform:translateY(-50%);
    background:rgba(0,0,0,0.55); color:#fff; cursor:pointer; border-radius:50%;
    width:32px; height:32px; visibility:hidden; opacity:0; pointer-events:none;
    display:flex; align-items:center; justify-content:center;
    font-size:1.5rem; z-index:10; user-select:none; text-decoration:none; transition:background .2s, opacity .2s; }
.cprev:hover,.cnext:hover { background:rgba(255,107,53,0.9); }
.cprev { left:6px; } .cnext { right:6px; }
/* ── Descripción del slide ── */
.slide-info { padding:7px 12px 9px; background:rgba(15,12,41,0.9); width:100% !important; box-sizing:border-box !important; }
.slide-color { color:#c8bfff; font-size:0.83rem; font-weight:700; margin-bottom:2px; }
.slide-price { color:#ffd200; font-size:1.05rem; font-weight:900; }
/* ── Botones Agregar al Carrito en Slide ── */
.slide-cta {
    display: block !important;
    width: 100% !important;
    box-sizing: border-box !important;
    text-align: center;
    background: linear-gradient(135deg, #ff6b35, #ff3d00);
    color: #ffffff !important;
    font-weight: 700;
    text-decoration: none;
    padding: 8px 12px;
    margin-top: 8px;
    border-radius: 8px;
    font-size: 0.9rem;
    box-shadow: 0 4px 12px rgba(255,107,53,0.3);
    transition: transform 0.2s, box-shadow 0.2s, background 0.2s;
}
.slide-cta:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 16px rgba(255,107,53,0.5);
    background: linear-gradient(135deg, #ff7b4b, #ff4d1a);
    color: #ffffff !important;
}
.slide-cta-agotado {
    display: block !important;
    width: 100% !important;
    box-sizing: border-box !important;
    text-align: center;
    background: rgba(255,255,255,0.06);
    color: rgba(255,255,255,0.4) !important;
    padding: 8px 12px;
    margin-top: 8px;
    border-radius: 8px;
    font-size: 0.85rem;
    font-weight: 600;
    border: 1px solid rgba(255,255,255,0.1);
}
/* ── Dots ── */
.cdots { display:flex; justify-content:center; gap:6px; padding:5px 0 3px; list-style:none; margin:0; }
.cdots > li > label { display:block; width:9px; height:9px; border-radius:50%;
    background:rgba(255,255,255,0.25); cursor:pointer; transition:background .2s; }
</style>
""", unsafe_allow_html=True)

        # ── RENDERIZADO DE CARDS ────────────────────────────────────────────────
        for g_idx in range(0, len(page_groups), 3):
            cols = st.columns(3)
            for col_idx in range(3):
                gi = g_idx + col_idx
                if gi >= len(page_groups):
                    break
                grupo_df = page_groups[gi]
                first    = grupo_df.iloc[0]
                nombre_c = f"{first['Nombre del Artículo']} {first['Modelo Exacto']}"
                # ID único corto para este carrusel
                cid = f"c{start_idx + gi}"

                variantes = []
                for vi_idx, (vi_row_i, vi_row) in enumerate(grupo_df.iterrows()):
                    variantes.append({
                        "idx":    vi_row_i,
                        "color":  vi_row["Color / Diseño (Variación)"],
                        "precio": vi_row["Precio Mercado"],
                        "stock":  vi_row["Cantidad"],
                        "img":    safe_img(vi_row["Imagen_URL"]),
                        "vi":     vi_idx,
                    })

                n_var = len(variantes)

                # ── Radios del carrusel ──────────────────────────────────────────────
                radios = "".join(
                    f'<input type="radio" name="{cid}" id="{cid}s{i}" {"checked" if i == 0 else ""}>'
                    for i in range(n_var)
                )

                # ── Checkboxes de zoom (ocultos, uno por variante) ────────────────
                zoom_cbs = "".join(
                    f'<input type="checkbox" id="z{cid}s{i}" class="zoom-cb">'
                    for i in range(n_var)
                )

                # ── Slides: foto + lupa + flechas + descripción propia ───────────
                slides_items = []
                for i, v in enumerate(variantes):
                    prev_i = (i - 1 + n_var) % n_var
                    next_i = (i + 1) % n_var
                    nav = (
                        f'<label class="cprev" for="{cid}s{prev_i}">&#8249;</label>'
                        f'<label class="cnext" for="{cid}s{next_i}">&#8250;</label>'
                    ) if n_var > 1 else ""
                    # Imagen envuelta en label → click = activa checkbox de zoom
                    img_wrap = (
                        f'<label for="z{cid}s{i}" class="img-lbl">'
                        f'<img src="{v["img"]}" alt="{v["color"]}" loading="lazy">'
                        f'<span class="zoom-hint">🔍</span>'
                        f'</label>'
                    )
                    if v["stock"] <= 0:
                        cta_html = '<div class="slide-cta-agotado">🔴 Agotado</div>'
                    else:
                        cta_html = f'<a class="slide-cta" href="?add_cart={v["idx"]}" target="_self">🛒 Agregar al carrito</a>'

                    info = (
                        f'<div class="slide-info">'
                        f'<div class="slide-color">🎨 {v["color"]}</div>'
                        f'<div class="slide-price">${v["precio"]:,.0f}</div>'
                        f'{cta_html}'
                        f'</div>'
                    )
                    slides_items.append(f'<li>{img_wrap}{nav}{info}</li>')
                slides_ul = f'<ul class="cslides">{"".join(slides_items)}</ul>'

                # ── Dots ───────────────────────────────────────────────────────
                if n_var > 1:
                    dots_ol = '<ol class="cdots">' + "".join(
                        f'<li><label for="{cid}s{i}"></label></li>' for i in range(n_var)
                    ) + '</ol>'
                else:
                    dots_ol = ""

                # ── Overlays de zoom (uno por variante, hermanos de los checkboxes) ──
                zoom_ovs = "".join(
                    f'<label for="z{cid}s{i}" class="zoom-ov" id="zo{cid}s{i}">'
                    f'<img src="{v["img"]}" alt="{v["color"]}">'
                    f'<span class="zoom-close">✕ Tocá para cerrar</span>'
                    f'</label>'
                    for i, v in enumerate(variantes)
                )

                # ── CSS per-carrusel ──────────────────────────────────────────────
                show_rules = "".join(
                    f'#{cid}s{i}:checked~.cslides>li:nth-child({i+1}){{position:relative !important;width:100% !important;visibility:visible !important;opacity:1 !important;pointer-events:auto !important}}'
                    f'#{cid}s{i}:checked~.cslides>li:nth-child({i+1}) .cprev{{visibility:visible !important;opacity:1 !important;pointer-events:auto !important}}'
                    f'#{cid}s{i}:checked~.cslides>li:nth-child({i+1}) .cnext{{visibility:visible !important;opacity:1 !important;pointer-events:auto !important}}'
                    f'#{cid}s{i}:checked~.cdots>li:nth-child({i+1})>label{{background:#ff6b35 !important}}'
                    for i in range(n_var)
                )
                # Zoom: cuando checkbox i está checked, mostrar su overlay hermano
                zoom_rules = "".join(
                    f'#z{cid}s{i}:checked~#zo{cid}s{i}{{display:flex}}'
                    for i in range(n_var)
                )

                card_html = f"""<div class="bejo-card" onclick="event.stopPropagation()">
<style>{show_rules}{zoom_rules}</style>
<div class="card-header"><div class="card-title">{nombre_c}</div></div>
{radios}{zoom_cbs}
{slides_ul}
{dots_ol}
{zoom_ovs}
</div>"""

                with cols[col_idx]:
                    st.markdown(card_html, unsafe_allow_html=True)

        # ── Controles de paginación ──────────────────────────────────────────────
        if total_pages > 1:
            st.markdown("<br>", unsafe_allow_html=True)
            p_col1, p_col2, p_col3 = st.columns([1, 2, 1])
            with p_col1:
                if st.button("⬅️ Anterior", disabled=(curr_page == 1),
                             use_container_width=True, key="cat_prev_page"):
                    st.session_state.catalog_page -= 1
                    st.rerun()
            with p_col2:
                st.markdown(f"<p style='text-align:center;font-weight:700;font-size:1.1rem;color:#fff;'>"
                            f"Página {curr_page} de {total_pages}</p>", unsafe_allow_html=True)
            with p_col3:
                if st.button("Siguiente ➡️", disabled=(curr_page == total_pages),
                             use_container_width=True, key="cat_next_page"):
                    st.session_state.catalog_page += 1
                    st.rerun()


    # ── BOTÓN DE CHECKOUT AL FINAL DEL CATÁLOGO ───────────────────────────────
    if st.session_state.carrito:
        st.markdown("---")
        num_items = sum(st.session_state.carrito.values())
        if st.button(f"🛒 FINALIZAR COMPRA ({num_items} items) ➔", type="primary", use_container_width=True, key="btn_go_cart_bottom"):
            st.session_state.vista = "carrito"
            st.rerun()

# ════════════════════════════════════════════════════════════════════════════
# PANEL ADMINISTRADOR
# ════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown('<div class="admin-trigger"></div>', unsafe_allow_html=True)
with st.expander("⚙️ Panel de Control – Solo Administrador"):

    if not st.session_state.admin_autenticado:
        st.markdown("🔐 **Ingresá la clave de administrador:**")
        kc, kb = st.columns([3, 1])
        clave_ing = kc.text_input("Clave:", type="password", placeholder="Contraseña...", label_visibility="collapsed")
        if kb.button("Entrar 🔓"):
            if clave_ing == CLAVE_ADMIN:
                st.session_state.admin_autenticado = True; st.rerun()
            else:
                st.markdown('<div class="error-validacion">❌ Clave incorrecta.</div>', unsafe_allow_html=True)

    else:
        # ── cabecera admin ────────────────────────────────────────────────
        col_tit, col_out = st.columns([4, 1])
        col_tit.markdown("### 🛠️ Panel BEJO · Administración")
        
        # Diagnóstico de Mercado Pago
        has_mp = obtener_access_token_mp() is not None
        if has_mp:
            st.success("🟢 **Mercado Pago:** Configurado correctamente y listo para recibir cobros.")
        else:
            st.error("🔴 **Mercado Pago:** No se detectó tu Access Token. Asegurá que agregaste `MERCADOPAGO_ACCESS_TOKEN` en los Secretos de Streamlit Cloud y presionaste el botón **Save**.")

        if col_out.button("Salir 🔒"):
            st.session_state.admin_autenticado = False
            st.session_state.admin_modo = None
            st.session_state.admin_idx_sel = None
            st.rerun()

        if df_stock.empty:
            st.warning("No hay datos cargados de Google Sheets.")
        else:
            # ── Descargar reportes ──────────────────────────────
            dc1, dc2 = st.columns(2)
            with dc1:
                # Descargar inventario
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_stock.to_excel(writer, index=False, sheet_name='Inventario')
                buffer.seek(0)
                st.download_button(
                    label="📥 Descargar Inventario (Excel)",
                    data=buffer,
                    file_name=f"inventario_bejo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            with dc2:
                # Descargar pedidos
                df_pedidos_all = cargar_pedidos_sheets()
                if not df_pedidos_all.empty:
                    buffer_ped = BytesIO()
                    with pd.ExcelWriter(buffer_ped, engine='openpyxl') as writer:
                        df_pedidos_all.to_excel(writer, index=False, sheet_name='Pedidos')
                    buffer_ped.seek(0)
                    st.download_button(
                        label="📥 Descargar Pedidos (Excel)",
                        data=buffer_ped,
                        file_name=f"pedidos_bejo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                else:
                    st.button("📥 No hay pedidos registrados", disabled=True, use_container_width=True)

            st.markdown("")

            # ── Control de Estados de Pedidos ──────────────────────────────
            if not df_pedidos_all.empty:
                with st.expander("📦 Gestionar Estados de Pedidos"):
                    pedidos_list = df_pedidos_all["ID Pedido"].tolist()[::-1] # más recientes primero
                    ped_sel = st.selectbox("Seleccioná un Pedido para gestionar:", pedidos_list, key="adm_ped_sel")
                    
                    if ped_sel:
                        ped_row = df_pedidos_all[df_pedidos_all["ID Pedido"] == ped_sel].iloc[0]
                        
                        st.markdown(f"📅 **Fecha:** {ped_row['Fecha']}")
                        st.markdown(f"💰 **Total:** ${float(ped_row['Total']):,.0f}")
                        st.markdown(f"👤 **Cliente/Contacto:** {ped_row['Cliente / Contacto']}")
                        st.markdown(f"📌 **Estado actual:** `{ped_row['Estado']}`")
                        
                        with st.expander("📝 Ver Mensaje Completo enviado a WS"):
                            st.text(ped_row["Detalle Pedido WS"])
                            
                        estados_posibles = ["Pendiente", "Entregado", "Rechazado", "Cancelado"]
                        idx_est_actual = estados_posibles.index(ped_row["Estado"]) if ped_row["Estado"] in estados_posibles else 0
                        nuevo_est = st.selectbox("Cambiar Estado a:", estados_posibles, index=idx_est_actual, key="adm_nuevo_est")
                        
                        if st.button("💾 Actualizar Estado de Pedido", type="primary", use_container_width=True):
                            if actualizar_estado_pedido(ped_sel, nuevo_est, df_pedidos_all):
                                st.success(f"✅ Estado del pedido {ped_sel} actualizado a '{nuevo_est}' con éxito.")
                                time.sleep(1)
                                st.rerun()

            st.markdown("---")
            # ════════════════════════════════════════════════════════════════
            # FILTROS EN CASCADA
            # ════════════════════════════════════════════════════════════════
            st.markdown('<div class="admin-filtros">', unsafe_allow_html=True)
            st.markdown("#### 🔍 Buscá el producto por filtros")
            af1, af2, af3, af4 = st.columns(4)
            with af1:
                tipos_a = ["(Todos)"] + sorted([t for t in df_stock["Nombre del Artículo"].dropna().unique() if str(t).strip()])
                t_a = st.selectbox("Tipo:", tipos_a, key="adm_tipo")
            df_a = df_stock if t_a == "(Todos)" else df_stock[df_stock["Nombre del Artículo"] == t_a]
            
            with af2:
                marcas_a = ["(Todas)"] + sorted([m for m in df_a["Marca Principal"].dropna().unique() if str(m).strip()])
                m_a = st.selectbox("Marca:", marcas_a, key="adm_marca")
            df_a = df_a if m_a == "(Todas)" else df_a[df_a["Marca Principal"] == m_a]
            
            with af3:
                modelos_a = ["(Todos)"] + sorted([m for m in df_a["Modelo Exacto"].dropna().unique() if str(m).strip()])
                mo_a = st.selectbox("Modelo:", modelos_a, key="adm_modelo")
            df_a = df_a if mo_a == "(Todos)" else df_a[df_a["Modelo Exacto"] == mo_a]
            
            with af4:
                colores_a = ["(Todos)"] + sorted([d for d in df_a["Color / Diseño (Variación)"].dropna().unique() if str(d).strip()])
                co_a = st.selectbox("Color / Diseño:", colores_a, key="adm_color")
            df_a = df_a if co_a == "(Todos)" else df_a[df_a["Color / Diseño (Variación)"] == co_a]
            st.markdown('</div>', unsafe_allow_html=True)

            # ── Resultado de búsqueda ─────────────────────────────────────
            filtros_activos = (t_a != "(Todos)" or m_a != "(Todas)" or mo_a != "(Todos)" or co_a != "(Todos)")

            if not filtros_activos:
                st.info("👆 Seleccioná al menos un filtro para buscar un producto, o usá el botón para agregar uno nuevo.")

            elif df_a.empty:
                # ── NO ENCONTRADO → opción de crear ──────────────────────
                st.markdown("""<div class="nuevo-prod-banner">
                    🔎 <b>No se encontró ningún producto con esos filtros.</b><br>
                    ¿Querés agregarlo al catálogo?
                </div>""", unsafe_allow_html=True)
                if st.button("➕ Sí, agregar este producto nuevo", type="primary", key="btn_ir_nuevo"):
                    st.session_state.admin_modo = "nuevo"

            else:
                # ── ENCONTRADO: lista de resultados ──────────────────────
                st.markdown(f"✅ **{len(df_a)} producto(s) encontrado(s):**")
                for i_row, r_row in df_a.iterrows():
                    tag = (f'<span class="tag-stock">Stock: {r_row["Cantidad"]}</span>'
                           if r_row["Cantidad"] > 0
                           else '<span class="tag-sin-stock">Sin stock</span>')
                    col_info_p, col_sel_p = st.columns([4, 1])
                    col_info_p.markdown(
                        f'**{r_row["Nombre del Artículo"]} {r_row["Modelo Exacto"]}** – '
                        f'{r_row["Color / Diseño (Variación)"]} &nbsp; {tag} &nbsp; '
                        f'**${r_row["Precio Mercado"]:,.0f}**',
                        unsafe_allow_html=True
                    )
                    if col_sel_p.button("✏️ Editar", key=f"adm_edit_{i_row}"):
                        st.session_state.admin_modo    = "editar"
                        st.session_state.admin_idx_sel = i_row
                        st.rerun()

            # Botón siempre visible para agregar nuevo
            st.markdown("")
            if st.button("➕ Agregar producto nuevo", key="btn_nuevo_siempre"):
                st.session_state.admin_modo    = "nuevo"
                st.session_state.admin_idx_sel = None

            st.markdown("---")

            # ════════════════════════════════════════════════════════════════
            # MODO EDITAR PRODUCTO EXISTENTE
            # ════════════════════════════════════════════════════════════════
            if st.session_state.admin_modo == "editar" and st.session_state.admin_idx_sel is not None:
                idx_e = st.session_state.admin_idx_sel
                prod  = df_stock.loc[idx_e]

                st.markdown(f"""<div class="prod-card">
                    <div class="prod-card-titulo">✏️ Editando: {prod['Nombre del Artículo']} {prod['Modelo Exacto']} – {prod['Color / Diseño (Variación)']}</div>
                </div>""", unsafe_allow_html=True)

                # Foto actual
                col_foto_act, col_info_act = st.columns([1, 2])
                with col_foto_act:
                    mostrar_imagen(prod["Imagen_URL"], caption="Foto actual", use_container_width=True)
                with col_info_act:
                    st.markdown(f"**Marca:** {prod['Marca Principal']}")
                    st.markdown(f"**Modelo:** {prod['Modelo Exacto']}")
                    st.markdown(f"**Color:** {prod['Color / Diseño (Variación)']}")
                    tag_s = (f'<span class="tag-stock">Stock actual: {prod["Cantidad"]}</span>'
                             if prod["Cantidad"] > 0
                             else '<span class="tag-sin-stock">Sin stock</span>')
                    st.markdown(tag_s, unsafe_allow_html=True)
                    st.markdown(f"**Precio actual:** ${prod['Precio Mercado']:,.0f}")

                st.markdown("#### 📝 Modificar datos")
                ec1, ec2 = st.columns(2)
                with ec1:
                    e_precio = st.number_input("Nuevo precio ($):", min_value=0, step=100,
                                               value=int(prod["Precio Mercado"]), key="e_precio")
                with ec2:
                    e_sumar  = st.number_input("Sumar unidades al stock:", min_value=0, step=1,
                                               value=0, key="e_sumar")
                e_nombre = st.text_input("Nombre del Artículo:", value=str(prod["Nombre del Artículo"]), key="e_nombre")
                e_color  = st.text_input("Color / Diseño:", value=str(prod["Color / Diseño (Variación)"]), key="e_color")

                st.markdown("#### 🖼️ Cambiar foto")
                st.caption("Podés subir una foto desde tu compu o celular, o pegar un link de Imgur.")
                foto_col1, foto_col2 = st.columns([1, 1])
                with foto_col1:
                    archivo_foto = st.file_uploader(
                        "📷 Subir imagen (jpg, png, webp):",
                        type=["jpg","jpeg","png","webp"],
                        key="e_foto_file",
                        help="Se comprime automáticamente. Funciona desde celular también."
                    )
                with foto_col2:
                    e_url_imgur = st.text_input("O pegá link de Imgur:", placeholder="https://i.imgur.com/...",
                                                value="", key="e_url_imgur")

                # Preview nueva foto
                nueva_foto_preview = None
                if archivo_foto is not None:
                    st.markdown("**Vista previa de la nueva foto:**")
                    st.image(archivo_foto, width=200)
                    nueva_foto_preview = "archivo"
                elif e_url_imgur.strip():
                    nueva_foto_preview = "url"

                be1, be2 = st.columns([3, 1])
                if be1.button("💾 Guardar todos los cambios", key="btn_guardar_editar", type="primary"):
                    try:
                        sheet      = get_sheet()
                        fila_sheet = idx_e + 5  # head=4 → datos desde fila 5

                        # Determinar nueva foto
                        nueva_url_foto = str(prod["Imagen_URL"])
                        if archivo_foto is not None:
                            data_url = imagen_a_base64(archivo_foto)
                            if data_url:
                                nueva_url_foto = data_url
                            else:
                                st.warning("⚠️ Instalá Pillow para procesar imágenes: `pip install Pillow`")
                        elif e_url_imgur.strip():
                            nueva_url_foto = e_url_imgur.strip()

                        nuevo_stock = int(prod["Cantidad"]) + int(e_sumar)

                        # Actualizar en sheets columna a columna
                        cols = df_stock.columns.tolist()
                        def col_num(nombre): return cols.index(nombre) + 1

                        sheet.update_cell(fila_sheet, col_num("Nombre del Artículo"),      e_nombre.strip())
                        sheet.update_cell(fila_sheet, col_num("Color / Diseño (Variación)"), e_color.strip())
                        sheet.update_cell(fila_sheet, col_num("Precio Mercado"),            str(e_precio))
                        sheet.update_cell(fila_sheet, col_num("Cantidad"),                  str(nuevo_stock))
                        sheet.update_cell(fila_sheet, col_num("Imagen_URL"),                nueva_url_foto)

                        st.success(f"✅ Producto actualizado. Stock: {nuevo_stock} | Precio: ${e_precio:,.0f}")
                        st.cache_data.clear()
                        st.session_state.admin_modo = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")

                if be2.button("❌ Cancelar", key="btn_cancel_editar"):
                    st.session_state.admin_modo = None
                    st.rerun()

            # ════════════════════════════════════════════════════════════════
            # MODO AGREGAR PRODUCTO NUEVO
            # ════════════════════════════════════════════════════════════════
            elif st.session_state.admin_modo == "nuevo":
                st.markdown("""<div class="nuevo-prod-banner">
                    ➕ <b>Nuevo Producto</b> – Completá todos los campos marcados con *
                </div>""", unsafe_allow_html=True)

                with st.form("form_nuevo_prod"):
                    nc1, nc2 = st.columns(2)
                    with nc1:
                        n_nombre   = st.text_input("Nombre del Artículo *", placeholder="Ej: Funda Silicona")
                        n_marca    = st.text_input("Marca Principal *",      placeholder="Ej: Samsung")
                        n_modelo   = st.text_input("Modelo Exacto *",        placeholder="Ej: Galaxy A54")
                    with nc2:
                        n_color    = st.text_input("Color / Diseño *",       placeholder="Ej: Negro Mate")
                        n_precio   = st.number_input("Precio ($) *",         min_value=0, step=100)
                        n_cantidad = st.number_input("Cantidad inicial *",    min_value=0, step=1)

                    st.markdown("#### 🖼️ Foto del producto")
                    fn1, fn2 = st.columns([1, 1])
                    with fn1:
                        n_foto_file = st.file_uploader(
                            "📷 Subir imagen desde tu compu/celu (jpg, png, webp):",
                            type=["jpg","jpeg","png","webp"], key="n_foto_file"
                        )
                    with fn2:
                        n_url_imgur = st.text_input("O pegá link de Imgur:", placeholder="https://i.imgur.com/...")

                    enviado = st.form_submit_button("💾 Guardar Nuevo Producto", type="primary", use_container_width=True)

                if enviado:
                    errores_n = []
                    if not n_nombre.strip(): errores_n.append("Falta el Nombre del Artículo.")
                    if not n_marca.strip():  errores_n.append("Falta la Marca Principal.")
                    if not n_modelo.strip(): errores_n.append("Falta el Modelo Exacto.")
                    if not n_color.strip():  errores_n.append("Falta el Color / Diseño.")
                    if errores_n:
                        for e in errores_n: st.error(f"⚠️ {e}")
                    else:
                        try:
                            # Procesar foto
                            url_foto_nueva = ""
                            if n_foto_file is not None:
                                data_url = imagen_a_base64(n_foto_file)
                                url_foto_nueva = data_url or ""
                                if not data_url:
                                    st.warning("⚠️ Instalá Pillow: `pip install Pillow`")
                            elif n_url_imgur.strip():
                                url_foto_nueva = n_url_imgur.strip()

                            sheet = get_sheet()
                            sheet.append_row([
                                n_marca.strip(),
                                n_nombre.strip(),
                                n_modelo.strip(),
                                n_color.strip(),
                                str(n_precio),
                                "",  # Tu Precio Competitivo
                                str(n_cantidad),
                                url_foto_nueva
                            ])
                            st.success(f"✅ ¡Producto **{n_nombre}** agregado al catálogo!")
                            st.cache_data.clear()
                            st.session_state.admin_modo = None
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al guardar: {e}")

                if st.button("❌ Cancelar", key="btn_cancel_nuevo"):
                    st.session_state.admin_modo = None
                    st.rerun()

            # ════════════════════════════════════════════════════════════════
            # ELIMINAR PRODUCTO (siempre visible al fondo)
            # ════════════════════════════════════════════════════════════════
            with st.expander("🗑️ Eliminar producto del catálogo"):
                st.warning("⚠️ Esta acción elimina la fila del producto de Google Sheets. No se puede deshacer.")
                lista_elim = [
                    f"{i} | {r['Nombre del Artículo']} {r['Modelo Exacto']} – {r['Color / Diseño (Variación)']}"
                    for i, r in df_stock.iterrows()
                ]
                sel_elim = st.selectbox("Seleccioná el producto:", lista_elim, key="sel_elim")
                idx_elim  = int(sel_elim.split("|")[0].strip())
                prod_elim = df_stock.loc[idx_elim]
                st.markdown(f"🗑️ Vas a eliminar: **{prod_elim['Nombre del Artículo']} "
                            f"{prod_elim['Modelo Exacto']}** – {prod_elim['Color / Diseño (Variación)']}")
                confirmar_elim = st.checkbox("Confirmo que quiero eliminar este producto.", key="chk_elim")
                if st.button("🗑️ Eliminar definitivamente", key="btn_elim_final", type="primary"):
                    if not confirmar_elim:
                        st.error("Marcá el check de confirmación primero.")
                    else:
                        try:
                            sheet    = get_sheet()
                            fila_s   = idx_elim + 5
                            sheet.delete_rows(fila_s)
                            st.success("✅ Producto eliminado.")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"No se pudo eliminar: {e}")


