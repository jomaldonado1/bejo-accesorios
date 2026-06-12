import streamlit as st
import pandas as pd
import gspread
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
    if "gcp_service_account" in st.secrets:
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
    if "gcp_service_account" in st.secrets:
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

@st.cache_data(ttl=5)
def cargar_datos_sheets():
    try:
        sheet = get_sheet()
        data  = sheet.get_all_records(head=4)
        df    = pd.DataFrame(data)
        df.columns = df.columns.str.strip()
        df["Cantidad"] = pd.to_numeric(df["Cantidad"], errors="coerce").fillna(0).astype(int)
        df["Precio Mercado"] = (
            df["Precio Mercado"].astype(str)
            .str.replace('$','',regex=False).str.replace('.','',regex=False)
            .str.replace(',','',regex=False).str.strip()
        )
        df["Precio Mercado"] = pd.to_numeric(df["Precio Mercado"], errors="coerce").fillna(0).astype(int)
        if "Imagen_URL" not in df.columns:
            df["Imagen_URL"] = ""
        return df
    except Exception as e:
        st.error(f"⚠️ Error al conectar con Google Sheets: {e}")
        return pd.DataFrame()

df_stock = cargar_datos_sheets()

# ── SESSION STATE ─────────────────────────────────────────────────────────────
for k, v in {
    "carrito": {}, "mostrar_banner_carrito": False,
    "admin_autenticado": False,
    "admin_modo": None,          # "editar" | "nuevo"
    "admin_idx_sel": None,       # índice del df del producto seleccionado
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── HEADER ───────────────────────────────────────────────────────────────────
st.markdown('<div class="bejo-header">⚡ BEJO ⚡</div>', unsafe_allow_html=True)
st.markdown('<div class="bejo-subtitle">ACCESORIOS PARA CELULARES · CALIDAD PREMIUM</div>', unsafe_allow_html=True)

# ── GRILLA DE INICIO (3 elementos) ───────────────────────────────────────────
imgs_grilla = [
    "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=400&q=80",
    "https://images.unsplash.com/photo-1592890288564-76628a30a657?w=400&q=80",
    "https://images.unsplash.com/photo-1585771724684-38269d6639fd?w=400&q=80",
]
grid_html = '<div class="welcome-grid">' + "".join(f'<img src="{u}" alt="acc" loading="lazy"/>' for u in imgs_grilla) + '</div>'
st.markdown(grid_html, unsafe_allow_html=True)
st.markdown("---")

# ── Banner carrito ────────────────────────────────────────────────────────────
if st.session_state.get("mostrar_banner_carrito"):
    st.markdown('<div class="carrito-banner">🛒 ¡PRODUCTO AGREGADO AL CARRITO EXITOSAMENTE! ✅</div>', unsafe_allow_html=True)
    st.session_state.mostrar_banner_carrito = False

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

    items = df_fil
    if items.empty:
        st.info("No hay productos disponibles para los filtros seleccionados.")
    else:
        items_per_page = 6
        total_items = len(items)
        total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)
        
        # Clamp page number just in case
        if st.session_state.get("catalog_page", 1) > total_pages:
            st.session_state.catalog_page = 1
            
        curr_page = st.session_state.get("catalog_page", 1)
        start_idx = (curr_page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        page_items = items.iloc[start_idx:end_idx]

        # Mostramos los elementos en una grilla de 3 columnas
        for idx_group in range(0, len(page_items), 3):
            cols = st.columns(3)
            for col_idx in range(3):
                item_idx = idx_group + col_idx
                if item_idx < len(items):
                    index = items.index[item_idx]
                    row = items.iloc[item_idx]
                    
                    nombre_c     = f"{row['Nombre del Artículo']} {row['Modelo Exacto']}"
                    variacion    = row["Color / Diseño (Variación)"]
                    precio       = row["Precio Mercado"]
                    stock_actual = row["Cantidad"]
                    url_foto     = row["Imagen_URL"]
                    if pd.isna(url_foto) or str(url_foto).strip() == "":
                        url_foto = "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500"
                    
                    with cols[col_idx]:
                        with st.container(border=True):
                            mostrar_imagen(url_foto, use_container_width=True)
                            st.markdown(f"**{nombre_c}**")
                            st.markdown(f"<div style='font-size:0.85rem; color:#a89cff; margin-top:-10px;'>🎨 {variacion}</div>", unsafe_allow_html=True)
                            st.markdown(f"### **${precio:,.0f}**")
                            
                            # Botón Popover para ver detalles y comprar sin hacer larga la lista
                            with st.popover("🔍 Ver / Comprar 🛒", use_container_width=True):
                                mostrar_imagen(url_foto, use_container_width=True)
                                st.markdown(f"### {nombre_c}")
                                st.markdown(f"🎨 **Color / Diseño:** {variacion}")
                                st.markdown(f"💳 **Precio:** ${precio:,.0f}")
                                
                                if stock_actual <= 0:
                                    st.error("🔴 SIN STOCK DISPONIBLE")
                                    st.button("Agotado ✖️", key=f"btn_ag_agotado_{index}", disabled=True, use_container_width=True)
                                else:
                                    st.success(f"🟢 Disponible: {stock_actual} unidades")
                                    qty = st.number_input("Cantidad:", min_value=1, max_value=min(stock_actual, 10),
                                                          value=1, step=1, key=f"qty_{index}")
                                    if st.button("Agregar al Carrito 🛒", key=f"btn_{index}", type="primary", use_container_width=True):
                                        en_carrito = st.session_state.carrito.get(index, 0)
                                        nueva_cant = en_carrito + qty
                                        if nueva_cant <= stock_actual:
                                            st.session_state.carrito[index]         = nueva_cant
                                            st.session_state.mostrar_banner_carrito = True
                                            st.rerun()
                                        else:
                                            st.error(f"⚠️ Solo hay {stock_actual} unidades disponibles.")

        # Controles de paginación
        if total_pages > 1:
            st.markdown("<br>", unsafe_allow_html=True)
            p_col1, p_col2, p_col3 = st.columns([1, 2, 1])
            with p_col1:
                if st.button("⬅️ Anterior", disabled=(curr_page == 1), use_container_width=True, key="cat_prev_page"):
                    st.session_state.catalog_page -= 1
                    st.rerun()
            with p_col2:
                st.markdown(f"<p style='text-align:center; font-weight:700; font-size:1.1rem; color:#fff;'>Página {curr_page} de {total_pages}</p>", unsafe_allow_html=True)
            with p_col3:
                if st.button("Siguiente ➡️", disabled=(curr_page == total_pages), use_container_width=True, key="cat_next_page"):
                    st.session_state.catalog_page += 1
                    st.rerun()

    # ── CARRITO ──────────────────────────────────────────────────────────────
    if st.session_state.carrito:
        st.markdown('<div class="carrito-titulo">🛒 Tu Carrito de Compras</div>', unsafe_allow_html=True)
        total_pedido      = 0
        resumen_productos = []

        for idx, cantidad in list(st.session_state.carrito.items()):
            row          = df_stock.loc[idx]
            nombre_prod  = f"{row['Nombre del Artículo']} {row['Modelo Exacto']} ({row['Color / Diseño (Variación)']})"
            precio_unit  = row["Precio Mercado"]
            stock_actual = row["Cantidad"]
            c1, c2, c3, c4 = st.columns([3, 1.2, 1.5, 0.8])
            c1.markdown(f"🔹 **{nombre_prod}**")
            nueva_cant = c2.number_input("", min_value=1, max_value=min(stock_actual,10),
                                         value=int(cantidad), step=1,
                                         key=f"cqty_{idx}", label_visibility="collapsed")
            if nueva_cant != cantidad:
                st.session_state.carrito[idx] = nueva_cant
                st.rerun()
            subtotal = precio_unit * nueva_cant
            total_pedido += subtotal
            resumen_productos.append(f"- {nombre_prod} x{nueva_cant} (${subtotal:,.0f})")
            c3.markdown(f"**${subtotal:,.0f}**")
            if c4.button("🗑️", key=f"del_{idx}"):
                del st.session_state.carrito[idx]; st.rerun()

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
            st.markdown("#### 📍 Tu dirección de entrega")
            direccion = st.text_input("🏠 Dirección completa (calle, número, barrio):",
                                      placeholder="Ej: San Martín 456, Yerba Buena, Tucumán", key="inp_dir")
            query_mapa = urllib.parse.quote(f"{direccion}, Tucumán, Argentina") if direccion.strip() else "Tucuman,Argentina"
            st.components.v1.iframe(f"https://maps.google.com/maps?q={query_mapa}&output=embed&z=15",
                                    height=280, scrolling=False)
            if not direccion.strip():
                st.caption("💡 Escribí tu dirección arriba para verla marcada en el mapa.")
            observacion = st.text_input("📝 Observaciones:", placeholder="Ej: Portón blanco, timbre 2")
            horario = st.selectbox("🕐 Horario preferible:", [
                "Sin preferencia (cualquier hora)", "Mañana (8:00 a 12:00)",
                "Mediodía (12:00 a 15:00)", "Tarde (15:00 a 18:00)", "Noche (18:00 a 21:00)"
            ])

        # ── PAGO ─────────────────────────────────────────────────────────────
        st.markdown('<div class="seccion-titulo">💳 Método de Pago</div>', unsafe_allow_html=True)
        metodo_pago = st.radio("pago_r", ["💵  Efectivo","🏦  Transferencia Bancaria"],
                               index=None, label_visibility="collapsed")
        mitad = total_pedido // 2
        resto = total_pedido - mitad
        if metodo_pago == "🏦  Transferencia Bancaria":
            st.markdown(f"""<div class="info-transfer">🏦 <b>PAGO POR TRANSFERENCIA</b><br><br>
            ✅ Transferí <b>la mitad ahora: ${mitad:,.0f}</b><br>
            📦 El resto (<b>${resto:,.0f}</b>) lo abonás al recibir el producto.<br><br>
            💬 Los datos bancarios te los mandamos por WhatsApp. 🤝</div>""", unsafe_allow_html=True)

        st.markdown("")
        if st.button("🚀 CONFIRMAR PEDIDO Y ENVIAR A WHATSAPP", type="primary", use_container_width=True):
            errores = []
            if metodo_entrega is None: errores.append("⚠️ Seleccioná cómo querés recibir tu pedido.")
            if metodo_pago    is None: errores.append("⚠️ Seleccioná el método de pago.")
            if metodo_entrega == "🏠  Envío a domicilio" and not direccion.strip():
                errores.append("⚠️ Ingresá tu dirección de envío.")
            if errores:
                for e in errores: st.markdown(f'<div class="error-validacion">{e}</div>', unsafe_allow_html=True)
            else:
                ahora     = datetime.now()
                id_pedido = f"PED-{ahora.strftime('%d%m-%H%M')}-{random.randint(100,999)}"
                le = metodo_entrega.replace("🏪  ","").replace("🏠  ","")
                lp = metodo_pago.replace("💵  ","").replace("🏦  ","")
                msg = (f"⚡ ¡Hola BEJO! Nuevo pedido 🔥\n\n🆔 *ID Pedido:* {id_pedido}\n"
                       f"📦 *Productos:*\n" + "\n".join(resumen_productos) +
                       f"\n\n💰 *Total:* ${total_pedido:,.0f}\n💳 *Pago:* {lp}\n")
                if metodo_pago == "🏦  Transferencia Bancaria":
                    msg += f"   ↳ Seña (50%): ${mitad:,.0f} | Resto al recibir: ${resto:,.0f}\n"
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

                # ── Vaciar carrito ─────────────────────────────────────────
                st.session_state.carrito = {}

                st.balloons()
                if ok_stock:
                    st.success(f"✅ ¡Pedido **{id_pedido}** generado! Stock actualizado automáticamente.")
                else:
                    st.success(f"✅ ¡Pedido **{id_pedido}** generado! Revisá el stock manualmente.")

                st.markdown(f"""<a href="{ws_url}" target="_blank" style="display:block;text-align:center;
                    background:linear-gradient(135deg,#25D366,#128C7E);color:white;font-size:1.4rem;
                    font-weight:800;padding:1.1rem 2rem;border-radius:14px;text-decoration:none;
                    margin-top:1rem;box-shadow:0 4px 20px #25D36655;letter-spacing:1px;">
                    📲 ENVIAR PEDIDO POR WHATSAPP → {id_pedido}</a>
                    <script>window.open("{ws_url}","_blank");</script>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# PANEL ADMINISTRADOR
# ════════════════════════════════════════════════════════════════════════════
st.markdown("---")
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
                                n_nombre.strip(), n_marca.strip(), n_modelo.strip(),
                                n_color.strip(), str(n_precio), str(n_cantidad), url_foto_nueva
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
