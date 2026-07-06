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
import streamlit.components.v1 as st_components

try:
    from PIL import Image
    PIL_OK = True
except ImportError:
    PIL_OK = False

# ── Configuración ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BEJO – Accesorios para Celulares",
    page_icon="⚡",
    layout="wide"
)

CLAVE_ADMIN = "BEJO2024"
NUMERO_WS   = "5493816582851"

# ══════════════════════════════════════════════════════════════════════════════
# DESIGN SYSTEM — Apple / Samsung Store Style
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ── RESET & ROOT VARIABLES ── */
:root {
    --bg:          #F5F5F7;
    --surface:     #FFFFFF;
    --surface2:    #FBFBFD;
    --text:        #1D1D1F;
    --text2:       #6E6E73;
    --text3:       #86868B;
    --accent:      #0066CC;
    --accent-dark: #0055a8;
    --accent-light:#E8F0FB;
    --offer:       #FF3B30;
    --success:     #34C759;
    --warning:     #FF9F0A;
    --danger:      #FF3B30;
    --border:      rgba(0,0,0,0.08);
    --border2:     rgba(0,0,0,0.04);
    --shadow-sm:   0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
    --shadow-md:   0 4px 16px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04);
    --shadow-lg:   0 12px 40px rgba(0,0,0,0.12), 0 4px 12px rgba(0,0,0,0.06);
    --shadow-xl:   0 24px 64px rgba(0,0,0,0.16);
    --radius-sm:   10px;
    --radius-md:   16px;
    --radius-lg:   20px;
    --radius-xl:   28px;
    --transition:  all 0.25s cubic-bezier(0.4,0,0.2,1);
}

/* ── BASE ── */
*, *::before, *::after { box-sizing: border-box; }

html, body,
.stApp,
[data-testid="stApp"],
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > .main,
.main {
    background: var(--bg) !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    color: var(--text) !important;
}

/* Remove Streamlit chrome */
[data-testid="stHeader"] { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
footer { display: none !important; }
#MainMenu { display: none !important; }

/* Layout */
[data-testid="stAppViewContainer"] > section,
[data-testid="stMain"],
section.main { padding: 0 !important; max-width: 100% !important; }

.block-container {
    max-width: 100% !important;
    padding: 6.5rem 2rem 4rem 2rem !important;
    margin: 0 !important;
}
@media (max-width: 900px) {
    .block-container { padding: 6rem 1rem 3rem 1rem !important; }
}
@media (max-width: 600px) {
    .block-container { padding: 5.5rem 0.75rem 3rem 0.75rem !important; }
}

/* ── GLASSMORPHISM HEADER ── */
.bejo-topbar {
    position: fixed;
    top: 0; left: 0; right: 0;
    z-index: 10000;
    background: rgba(255,255,255,0.82);
    backdrop-filter: blur(20px) saturate(180%);
    -webkit-backdrop-filter: blur(20px) saturate(180%);
    border-bottom: 1px solid rgba(0,0,0,0.08);
    transition: var(--transition);
}
.bejo-topbar-inner {
    max-width: 1440px;
    margin: 0 auto;
    padding: 0 2rem;
    height: 60px;
    display: flex;
    align-items: center;
    gap: 2rem;
}
.bejo-brand {
    display: flex;
    align-items: center;
    gap: 10px;
    text-decoration: none;
    flex-shrink: 0;
}
.bejo-brand img {
    width: 36px;
    height: 36px;
    border-radius: 8px;
    object-fit: contain;
}
.bejo-brand-name {
    font-size: 1.25rem;
    font-weight: 800;
    color: var(--text) !important;
    letter-spacing: 2px;
    text-transform: uppercase;
}
.bejo-nav-pills {
    display: flex;
    align-items: center;
    gap: 4px;
    flex: 1;
    overflow-x: auto;
    scrollbar-width: none;
}
.bejo-nav-pills::-webkit-scrollbar { display: none; }
.bejo-nav-pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--text2) !important;
    text-decoration: none;
    white-space: nowrap;
    transition: var(--transition);
    cursor: pointer;
    border: none;
    background: transparent;
    letter-spacing: 0.2px;
}
.bejo-nav-pill:hover {
    background: rgba(0,0,0,0.05);
    color: var(--text) !important;
}
.bejo-nav-pill.active {
    background: var(--accent-light);
    color: var(--accent) !important;
    font-weight: 700;
}
.bejo-nav-pill.pill-ws {
    background: #25D366;
    color: white !important;
    font-weight: 700;
}
.bejo-nav-pill.pill-ws:hover { background: #20bf5e; }
.bejo-nav-pill.pill-offer {
    background: #FFF2F1;
    color: var(--offer) !important;
    font-weight: 700;
}
.bejo-topbar-actions {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-shrink: 0;
}
.cart-icon-btn {
    position: relative;
    display: inline-flex;
    align-items: center;
    gap: 7px;
    background: var(--accent);
    color: white !important;
    border: none;
    border-radius: 24px;
    padding: 8px 18px 8px 14px;
    font-size: 0.85rem;
    font-weight: 700;
    cursor: pointer;
    transition: var(--transition);
    text-decoration: none;
    letter-spacing: 0.2px;
    box-shadow: 0 4px 12px rgba(0,102,204,0.3);
}
.cart-icon-btn:hover {
    background: var(--accent-dark);
    box-shadow: 0 6px 20px rgba(0,102,204,0.4);
    transform: translateY(-1px);
}
.cart-badge {
    background: white;
    color: var(--accent);
    border-radius: 50%;
    width: 20px; height: 20px;
    font-size: 0.7rem;
    font-weight: 800;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 1px 4px rgba(0,0,0,0.15);
}

/* ── HIDDEN NAV TRIGGERS ── */
.bejo-nav-triggers,
.bejo-nav-triggers * {
    position: absolute !important;
    top: -9999px !important;
    left: -9999px !important;
    width: 1px !important;
    height: 1px !important;
    overflow: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
}

/* ── HERO SECTION ── */
.bejo-hero {
    background: linear-gradient(135deg, #0066CC 0%, #004d99 40%, #003380 100%);
    padding: 3.5rem 2rem;
    text-align: center;
    position: relative;
    overflow: hidden;
    margin: 0 0 2.5rem 0;
    border-radius: var(--radius-lg);
}
.bejo-hero::before {
    content: '';
    position: absolute;
    inset: 0;
    background: radial-gradient(ellipse 60% 80% at 20% 50%, rgba(255,255,255,0.08), transparent),
                radial-gradient(ellipse 40% 60% at 80% 30%, rgba(255,255,255,0.06), transparent);
    pointer-events: none;
}
.hero-eyebrow {
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: rgba(255,255,255,0.7);
    margin-bottom: 0.75rem;
}
.hero-title {
    font-size: clamp(2rem, 6vw, 3.5rem);
    font-weight: 900;
    color: white;
    letter-spacing: -0.5px;
    line-height: 1.1;
    margin-bottom: 0.75rem;
}
.hero-subtitle {
    font-size: clamp(0.9rem, 2vw, 1.1rem);
    color: rgba(255,255,255,0.75);
    font-weight: 400;
    margin-bottom: 2rem;
    max-width: 480px;
    margin-left: auto;
    margin-right: auto;
    line-height: 1.6;
}
.hero-cta-group {
    display: flex;
    gap: 12px;
    justify-content: center;
    flex-wrap: wrap;
}
.hero-btn {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 13px 28px;
    border-radius: var(--radius-md);
    font-weight: 700;
    font-size: 0.95rem;
    text-decoration: none;
    transition: var(--transition);
    cursor: pointer;
    border: none;
    letter-spacing: 0.2px;
}
.hero-btn-primary {
    background: white;
    color: var(--accent) !important;
    box-shadow: 0 4px 16px rgba(0,0,0,0.2);
}
.hero-btn-primary:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.25); }
.hero-btn-secondary {
    background: rgba(255,255,255,0.15);
    color: white !important;
    border: 1.5px solid rgba(255,255,255,0.3);
}
.hero-btn-secondary:hover { background: rgba(255,255,255,0.25); }

/* ── SECTION TITLES ── */
.section-header {
    display: flex;
    align-items: baseline;
    gap: 12px;
    margin: 0 0 1.2rem 0;
}
.section-title {
    font-size: 1.5rem;
    font-weight: 800;
    color: var(--text);
    letter-spacing: -0.3px;
    margin: 0;
}
.section-subtitle {
    font-size: 0.9rem;
    color: var(--text3);
    font-weight: 400;
}

/* ── FILTER CHIPS ── */
.filter-wrap {
    background: var(--surface);
    border-radius: var(--radius-md);
    padding: 1.25rem 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--border);
}
.filter-label {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--text3);
    margin-bottom: 0.6rem;
}

/* ── PRODUCT CARDS ── */
.tech-card {
    background: var(--surface);
    border-radius: var(--radius-md);
    overflow: hidden;
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--border);
    transition: var(--transition);
    display: flex;
    flex-direction: column;
    height: 100%;
    margin-bottom: 8px;
}
.tech-card:hover {
    box-shadow: var(--shadow-lg);
    transform: translateY(-3px);
}

/* Carousel (CSS-only) */
.tech-card input[type=radio],
.tech-card input.zoom-cb {
    position: absolute; opacity: 0; width: 0; height: 0; pointer-events: none;
}
.card-slides { list-style: none; margin: 0 !important; padding: 0 !important; position: relative; }
.card-slides > li {
    position: absolute; top: 0; left: 0; width: 100% !important;
    margin: 0 !important; padding: 0 !important;
    visibility: hidden; opacity: 0; pointer-events: none;
    transition: opacity 0.2s ease;
}

/* Slide image area */
.slide-img-wrap {
    position: relative;
    aspect-ratio: 1/1;
    overflow: hidden;
    background: var(--surface2);
    cursor: zoom-in;
    display: block;
}
.slide-img-wrap img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.4s ease;
    display: block;
}
.slide-img-wrap:hover img { transform: scale(1.04); }
.zoom-hint {
    position: absolute; top: 8px; right: 8px;
    background: rgba(255,255,255,0.85);
    backdrop-filter: blur(8px);
    border-radius: 50%;
    width: 28px; height: 28px;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.8rem;
    opacity: 0;
    transition: opacity 0.2s;
    pointer-events: none;
}
.tech-card:hover .zoom-hint { opacity: 1; }

/* Slide info bar */
.slide-data {
    padding: 10px 14px 12px;
    background: var(--surface);
    flex-grow: 1;
    display: flex;
    flex-direction: column;
}

/* Card Header (product name) */
.card-topline {
    padding: 12px 14px 0;
    background: var(--surface);
}
.card-brand-tag {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 2px;
}
.card-name {
    font-size: 0.92rem;
    font-weight: 700;
    color: var(--text);
    line-height: 1.3;
    margin: 0;
}
.card-compat {
    font-size: 0.75rem;
    color: var(--text3);
    margin: 3px 0 0 0;
    font-weight: 400;
}

/* Stock badges */
.badge-stock {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 3px 9px;
    border-radius: 20px;
    margin-top: 6px;
    width: fit-content;
}
.badge-stock-ok {
    background: rgba(52,199,89,0.12);
    color: #248a3d;
    border: 1px solid rgba(52,199,89,0.25);
}
.badge-stock-low {
    background: rgba(255,159,10,0.12);
    color: #c17000;
    border: 1px solid rgba(255,159,10,0.3);
}
.badge-stock-out {
    background: rgba(255,59,48,0.08);
    color: #c0392b;
    border: 1px solid rgba(255,59,48,0.2);
}
.badge-offer {
    position: absolute;
    top: 10px; left: 10px;
    background: var(--offer);
    color: white;
    font-size: 0.65rem;
    font-weight: 800;
    padding: 3px 9px;
    border-radius: 20px;
    letter-spacing: 0.5px;
    z-index: 5;
    box-shadow: 0 2px 8px rgba(255,59,48,0.35);
}

/* Color variant chip */
.slide-variant {
    font-size: 0.78rem;
    color: var(--text2);
    font-weight: 500;
    margin-bottom: 2px;
}
/* Price */
.slide-price {
    font-size: 1.15rem;
    font-weight: 800;
    color: var(--text);
    margin: 2px 0;
    letter-spacing: -0.3px;
}

/* CTA button */
.btn-add-cart {
    display: block !important;
    width: 100% !important;
    box-sizing: border-box !important;
    text-align: center;
    background: var(--accent);
    color: white !important;
    font-weight: 700;
    font-size: 0.82rem;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    text-decoration: none;
    padding: 10px 12px;
    margin-top: 10px;
    border-radius: var(--radius-sm);
    transition: var(--transition);
    box-shadow: 0 2px 8px rgba(0,102,204,0.2);
}
.btn-add-cart:hover {
    background: var(--accent-dark);
    box-shadow: 0 4px 16px rgba(0,102,204,0.35);
    transform: translateY(-1px);
    color: white !important;
}
.btn-add-cart-disabled {
    display: block !important;
    width: 100% !important;
    box-sizing: border-box !important;
    text-align: center;
    background: rgba(0,0,0,0.06);
    color: var(--text3) !important;
    font-weight: 600;
    font-size: 0.82rem;
    padding: 10px 12px;
    margin-top: 10px;
    border-radius: var(--radius-sm);
    cursor: not-allowed;
    border: 1px solid var(--border);
}

/* Carousel arrows */
.cprev, .cnext {
    position: absolute; top: 50%; transform: translateY(-50%);
    background: rgba(255,255,255,0.9) !important;
    backdrop-filter: blur(8px);
    color: var(--text) !important;
    cursor: pointer; border-radius: 50%;
    width: 30px; height: 30px;
    visibility: hidden; opacity: 0; pointer-events: none;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem; z-index: 10; user-select: none;
    text-decoration: none;
    transition: var(--transition);
    border: 1px solid var(--border) !important;
    box-shadow: var(--shadow-sm);
}
.cprev:hover, .cnext:hover {
    background: var(--accent) !important;
    color: white !important;
    border-color: var(--accent) !important;
}
.cprev { left: 8px; } .cnext { right: 8px; }

/* Dots */
.cdots {
    display: flex; justify-content: center; gap: 5px;
    padding: 6px 0 4px; list-style: none; margin: 0;
}
.cdots > li > label {
    display: block; width: 6px; height: 6px; border-radius: 50%;
    background: rgba(0,0,0,0.15); cursor: pointer;
    transition: var(--transition);
}

/* Lightbox */
.zoom-ov {
    display: none; position: fixed; inset: 0; z-index: 99999;
    background: rgba(0,0,0,0.7);
    backdrop-filter: blur(16px);
    align-items: center; justify-content: center;
    cursor: zoom-out; flex-direction: column; gap: 12px;
}
.zoom-ov > img {
    max-width: 90vw; max-height: 85vh; object-fit: contain;
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-xl);
}
.zoom-close { color: white; font-size: 0.82rem; user-select: none; opacity: 0.75; }

/* ── CART SLIDE-OVER ── */
.cart-overlay {
    display: none;
    position: fixed; inset: 0; z-index: 20000;
    background: rgba(0,0,0,0.35);
    backdrop-filter: blur(4px);
    cursor: pointer;
}
.cart-drawer {
    position: fixed;
    top: 0; right: 0; bottom: 0;
    width: 420px;
    max-width: 100vw;
    background: var(--surface);
    z-index: 20001;
    box-shadow: -8px 0 40px rgba(0,0,0,0.15);
    transform: translateX(100%);
    transition: transform 0.35s cubic-bezier(0.4,0,0.2,1);
    display: flex; flex-direction: column;
    overflow: hidden;
}
.cart-open .cart-overlay { display: block; }
.cart-open .cart-drawer { transform: translateX(0); }

.cart-drawer-header {
    padding: 1.25rem 1.5rem;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-shrink: 0;
    background: var(--surface);
}
.cart-drawer-title {
    font-size: 1.1rem;
    font-weight: 800;
    color: var(--text);
    display: flex;
    align-items: center;
    gap: 8px;
}
.cart-close-btn {
    width: 30px; height: 30px;
    border-radius: 50%;
    background: var(--bg);
    border: none;
    cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem;
    color: var(--text2);
    transition: var(--transition);
}
.cart-close-btn:hover { background: rgba(0,0,0,0.1); color: var(--text); }

.cart-drawer-body {
    flex: 1;
    overflow-y: auto;
    padding: 1rem 1.5rem;
}
.cart-item-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 0;
    border-bottom: 1px solid var(--border2);
}
.cart-item-img {
    width: 60px; height: 60px;
    border-radius: var(--radius-sm);
    object-fit: cover;
    background: var(--bg);
    flex-shrink: 0;
    border: 1px solid var(--border);
}
.cart-item-info { flex: 1; min-width: 0; }
.cart-item-name {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text);
    line-height: 1.3;
    margin-bottom: 2px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.cart-item-color {
    font-size: 0.75rem;
    color: var(--text3);
    margin-bottom: 4px;
}
.cart-item-price {
    font-size: 0.9rem;
    font-weight: 700;
    color: var(--accent);
}
.qty-controls {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-shrink: 0;
}
.qty-btn {
    width: 26px; height: 26px;
    border-radius: 50%;
    background: var(--bg);
    border: 1px solid var(--border);
    cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem;
    color: var(--text2);
    text-decoration: none;
    font-weight: 700;
    transition: var(--transition);
    line-height: 1;
}
.qty-btn:hover { background: var(--accent); color: white; border-color: var(--accent); }
.qty-num { font-weight: 700; font-size: 0.9rem; color: var(--text); min-width: 16px; text-align: center; }
.qty-del {
    width: 26px; height: 26px;
    border-radius: 50%;
    background: transparent;
    border: 1px solid transparent;
    cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.85rem;
    color: var(--text3);
    text-decoration: none;
    transition: var(--transition);
}
.qty-del:hover { background: #FFF2F1; color: var(--offer); border-color: rgba(255,59,48,0.2); }

.cart-empty-msg {
    text-align: center;
    padding: 3rem 1rem;
    color: var(--text3);
}
.cart-empty-msg .cart-empty-icon { font-size: 3rem; margin-bottom: 1rem; display: block; }
.cart-empty-msg p { font-size: 0.9rem; }

.cart-drawer-footer {
    padding: 1.25rem 1.5rem;
    border-top: 1px solid var(--border);
    flex-shrink: 0;
    background: var(--surface);
}
.cart-total-row {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 1rem;
}
.cart-total-label { font-size: 0.85rem; color: var(--text2); font-weight: 500; }
.cart-total-amount { font-size: 1.4rem; font-weight: 800; color: var(--text); }
.btn-checkout {
    display: block;
    width: 100%;
    background: var(--accent);
    color: white !important;
    font-weight: 700;
    font-size: 0.95rem;
    letter-spacing: 0.5px;
    text-align: center;
    padding: 14px;
    border-radius: var(--radius-md);
    text-decoration: none;
    transition: var(--transition);
    border: none;
    cursor: pointer;
    box-shadow: 0 4px 16px rgba(0,102,204,0.3);
}
.btn-checkout:hover {
    background: var(--accent-dark);
    box-shadow: 0 6px 24px rgba(0,102,204,0.4);
    transform: translateY(-1px);
}
.btn-continue-shop {
    display: block;
    width: 100%;
    background: transparent;
    color: var(--accent) !important;
    font-weight: 600;
    font-size: 0.85rem;
    text-align: center;
    padding: 10px;
    border-radius: var(--radius-md);
    text-decoration: none;
    transition: var(--transition);
    border: none;
    cursor: pointer;
    margin-top: 8px;
}
.btn-continue-shop:hover { background: var(--accent-light); }

/* ── PAYMENT / CHECKOUT STYLES ── */
.checkout-section {
    background: var(--surface);
    border-radius: var(--radius-md);
    padding: 1.5rem;
    margin-bottom: 1.25rem;
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--border);
}
.checkout-section-title {
    font-size: 1rem;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 1rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 8px;
}
.payment-option {
    border: 2px solid var(--border);
    border-radius: var(--radius-md);
    padding: 1.25rem 1.5rem;
    margin-bottom: 0.75rem;
    transition: var(--transition);
    cursor: pointer;
}
.payment-option:hover { border-color: var(--accent); background: var(--accent-light); }
.payment-option-title { font-size: 1rem; font-weight: 700; color: var(--text); margin-bottom: 3px; }
.payment-option-sub { font-size: 0.82rem; color: var(--text3); }
.btn-pay-mp {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    width: 100%;
    background: #009EE3;
    color: white !important;
    font-weight: 800;
    font-size: 1rem;
    padding: 15px 20px;
    border-radius: var(--radius-md);
    text-decoration: none;
    transition: var(--transition);
    border: none;
    cursor: pointer;
    box-shadow: 0 4px 16px rgba(0,158,227,0.35);
    letter-spacing: 0.3px;
}
.btn-pay-mp:hover { background: #0086c5; box-shadow: 0 6px 24px rgba(0,158,227,0.5); transform: translateY(-1px); }
.btn-pay-ws {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    width: 100%;
    background: #25D366;
    color: white !important;
    font-weight: 800;
    font-size: 1rem;
    padding: 15px 20px;
    border-radius: var(--radius-md);
    text-decoration: none;
    transition: var(--transition);
    border: none;
    cursor: pointer;
    box-shadow: 0 4px 16px rgba(37,211,102,0.35);
    letter-spacing: 0.3px;
}
.btn-pay-ws:hover { background: #1aab50; box-shadow: 0 6px 24px rgba(37,211,102,0.5); transform: translateY(-1px); }
.total-summary-box {
    background: linear-gradient(135deg, var(--accent) 0%, var(--accent-dark) 100%);
    color: white;
    padding: 1.5rem;
    border-radius: var(--radius-md);
    text-align: center;
    margin: 1.25rem 0;
    box-shadow: var(--shadow-md);
}
.total-summary-label { font-size: 0.85rem; opacity: 0.85; margin-bottom: 4px; font-weight: 500; }
.total-summary-amount { font-size: 2rem; font-weight: 900; letter-spacing: -0.5px; }
.info-box {
    border-radius: var(--radius-md);
    padding: 1rem 1.25rem;
    margin: 0.75rem 0;
    font-size: 0.88rem;
    font-weight: 500;
    line-height: 1.6;
}
.info-box-blue { background: var(--accent-light); border: 1px solid rgba(0,102,204,0.2); color: var(--accent-dark); }
.info-box-green { background: rgba(52,199,89,0.1); border: 1px solid rgba(52,199,89,0.25); color: #1a7a33; }
.info-box-orange { background: rgba(255,159,10,0.1); border: 1px solid rgba(255,159,10,0.25); color: #915c00; }
.info-box-yellow { background: rgba(255,214,10,0.1); border: 1px solid rgba(255,214,10,0.3); color: #7a5900; }
.error-box { background: rgba(255,59,48,0.08); border: 1.5px solid rgba(255,59,48,0.25); color: var(--offer); border-radius: var(--radius-md); padding: 0.75rem 1.25rem; font-weight: 700; text-align: center; margin: 0.5rem 0; }

/* ── RADIO OVERRIDES ── */
div[data-testid="stRadio"] > label { font-size: 0.9rem !important; font-weight: 700 !important; color: var(--text) !important; }
div[data-testid="stRadio"] div[role="radiogroup"] {
    display: flex; flex-direction: column; gap: 8px; padding: 4px 0;
}
div[data-testid="stRadio"] label[data-baseweb="radio"] {
    background: var(--surface);
    border: 1.5px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 12px 16px;
    cursor: pointer;
    transition: var(--transition);
}
div[data-testid="stRadio"] label[data-baseweb="radio"]:hover { border-color: var(--accent); background: var(--accent-light); }
div[data-testid="stRadio"] label[data-baseweb="radio"] > div:last-child { color: var(--text) !important; font-size: 0.92rem !important; font-weight: 600 !important; }

/* ── INPUT OVERRIDES ── */
.stSelectbox > div > div,
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stTextArea textarea {
    background: var(--surface) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text) !important;
    font-size: 0.95rem !important;
    font-family: 'Inter', sans-serif !important;
}
.stTextInput > div > div > input:focus,
.stTextArea textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(0,102,204,0.12) !important;
}
label, .stSelectbox label, .stTextInput label,
.stNumberInput label, .stTextArea label {
    color: var(--text2) !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    font-family: 'Inter', sans-serif !important;
}

/* ── BUTTON OVERRIDES ── */
.stButton > button {
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    transition: var(--transition) !important;
    border: 1.5px solid var(--border) !important;
    font-size: 0.88rem !important;
}
.stButton > button[kind="primary"] {
    background: var(--accent) !important;
    color: white !important;
    border-color: var(--accent) !important;
    box-shadow: 0 2px 8px rgba(0,102,204,0.25) !important;
}
.stButton > button[kind="primary"]:hover {
    background: var(--accent-dark) !important;
    border-color: var(--accent-dark) !important;
    box-shadow: 0 4px 16px rgba(0,102,204,0.35) !important;
    transform: translateY(-1px) !important;
}
.stButton > button:not([kind="primary"]) {
    background: var(--surface) !important;
    color: var(--text) !important;
}
.stButton > button:not([kind="primary"]):hover {
    background: var(--bg) !important;
    border-color: rgba(0,0,0,0.18) !important;
}

/* ── EXPANDER ── */
div[data-testid="stExpander"] {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    background: var(--surface) !important;
    box-shadow: var(--shadow-sm) !important;
    overflow: hidden;
}
div[data-testid="stExpander"] summary { font-weight: 600 !important; }

/* ── PAGINATION ── */
.pagination-wrap {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    margin: 1.5rem 0;
}
.page-info {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text2);
    padding: 0 12px;
}

/* ── OFFER BADGE in catalog banner ── */
.offer-home-card {
    background: var(--surface);
    border-radius: var(--radius-md);
    overflow: hidden;
    border: 1px solid var(--border);
    box-shadow: var(--shadow-sm);
    transition: var(--transition);
    margin-bottom: 8px;
}
.offer-home-card:hover {
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
}

/* ── CART BANNER (success toast) ── */
.cart-added-banner {
    background: linear-gradient(135deg, var(--success), #2aa44f);
    color: white;
    font-size: 0.95rem;
    font-weight: 700;
    text-align: center;
    padding: 0.85rem 1.5rem;
    border-radius: var(--radius-md);
    box-shadow: 0 4px 16px rgba(52,199,89,0.3);
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    animation: slideDown 0.3s ease;
}
@keyframes slideDown { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: none; } }

/* ── ADMIN PANEL ── */
.admin-panel {
    background: var(--surface);
    border-radius: var(--radius-lg);
    padding: 2rem;
    border: 1px solid var(--border);
    box-shadow: var(--shadow-sm);
}
.admin-badge-stock { display: inline-block; background: rgba(52,199,89,0.12); border: 1px solid rgba(52,199,89,0.3); border-radius: 20px; padding: 2px 10px; color: #248a3d; font-size: 0.78rem; font-weight: 700; }
.admin-badge-nostock { display: inline-block; background: rgba(255,59,48,0.08); border: 1px solid rgba(255,59,48,0.2); border-radius: 20px; padding: 2px 10px; color: var(--offer); font-size: 0.78rem; font-weight: 700; }

/* ── FOOTER / WA CTA ── */
.wa-cta-bar {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 1rem 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    flex-wrap: wrap;
    margin: 1.5rem 0 0 0;
}
.wa-cta-text { font-size: 0.9rem; color: var(--text2); font-weight: 500; }
.wa-btn {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    background: #25D366;
    color: white !important;
    font-weight: 700;
    font-size: 0.88rem;
    padding: 9px 20px;
    border-radius: 24px;
    text-decoration: none;
    transition: var(--transition);
    box-shadow: 0 3px 10px rgba(37,211,102,0.3);
    white-space: nowrap;
}
.wa-btn:hover { background: #1aab50; box-shadow: 0 5px 16px rgba(37,211,102,0.45); transform: translateY(-1px); }

/* ── PAGE VIEW HEADERS ── */
.view-header {
    background: var(--surface);
    border-radius: var(--radius-md);
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
    border: 1px solid var(--border);
    box-shadow: var(--shadow-sm);
}
.view-header-title {
    font-size: 1.6rem;
    font-weight: 800;
    color: var(--text);
    letter-spacing: -0.3px;
    margin-bottom: 4px;
}
.view-header-sub { font-size: 0.9rem; color: var(--text3); }

/* ── COMPATIBILITY ── */
.compat-chip {
    display: inline-block;
    background: var(--accent-light);
    border: 1.5px solid rgba(0,102,204,0.2);
    border-radius: 20px;
    padding: 6px 16px;
    color: var(--accent-dark);
    font-size: 0.88rem;
    font-weight: 700;
    margin: 4px;
}
.compat-result-box {
    background: var(--surface);
    border: 1.5px solid rgba(0,102,204,0.2);
    border-radius: var(--radius-md);
    padding: 1.5rem;
    margin-top: 1rem;
}

/* ── MAYOR VIEW ── */
.benefit-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 1.5rem;
    height: 100%;
    box-shadow: var(--shadow-sm);
}
.benefit-card-title { font-size: 1.05rem; font-weight: 800; color: var(--text); margin-bottom: 1rem; }

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.15); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(0,0,0,0.25); }

/* ── FILE UPLOADER ── */
div[data-testid="stFileUploader"] {
    background: var(--bg) !important;
    border: 2px dashed rgba(0,102,204,0.25) !important;
    border-radius: var(--radius-md) !important;
}
div[data-testid="stFileUploader"] label { color: var(--text2) !important; }

/* ── SEPARATOR ── */
hr { border-color: var(--border) !important; margin: 1.5rem 0 !important; }

/* ── INVISIBLE ADMIN EXPANDER for non-admin ── */
.admin-hidden div[data-testid="stExpander"] {
    opacity: 0.01 !important;
    transition: opacity 0.3s !important;
}
.admin-hidden div[data-testid="stExpander"]:hover,
.admin-hidden div[data-testid="stExpander"]:focus-within {
    opacity: 1 !important;
}
</style>
""", unsafe_allow_html=True)

# ── HELPERS ──────────────────────────────────────────────────────────────────
def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
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
            fila_sheet = int(matching_idx[0]) + 2
            sheet.update_cell(fila_sheet, 6, nuevo_estado)
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
    headers = {'User-Agent': 'BEJO_Accesorios_App/1.0 (tienda_accesorios_agent)'}
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
                if house_number: clean_addr += f" {house_number}"
                if city: clean_addr += f", {city}"
                if state: clean_addr += f", {state}"
            else:
                clean_addr = data.get("display_name", "")
            return clean_addr
        return None
    except Exception:
        return None

def geocodificar_directa_nominatim(query):
    import requests as _req
    import urllib.parse as _up
    import re as _re
    query_clean = query.strip()
    if not query_clean:
        return None
    headers_nom = {'User-Agent': 'BEJO_Accesorios_App/1.0'}
    m = _re.match(r'^([\D]+?)\s*(\d+)\s*$', query_clean)
    calle = m.group(1).strip() if m else query_clean
    altura = m.group(2).strip() if m else None
    try:
        municipios = ["San Miguel de Tucum%C3%A1n", "Yerba Buena", "Banda del R%C3%ADo Sal%C3%AD", "Alderetes", "Tucum%C3%A1n"]
        for municipio in municipios:
            params = f"nombre={_up.quote(calle)}&provincia=tucuman&max=1&campos=basico"
            if altura: params += f"&altura={altura}"
            georef_url = f"https://apis.datos.gob.ar/georef/api/direcciones?{params}&localidad_censal={municipio}"
            r = _req.get(georef_url, timeout=6)
            if r.status_code == 200:
                data = r.json()
                dirs = data.get("direcciones", [])
                if dirs:
                    d = dirs[0]
                    lat = d.get("ubicacion", {}).get("lat")
                    lon = d.get("ubicacion", {}).get("lon")
                    if lat and lon:
                        nombre_calle = d.get("nomenclatura", calle)
                        display = f"{nombre_calle}, Tucumán, Argentina"
                        return float(lat), float(lon), display
    except Exception:
        pass
    try:
        r2 = _req.get(
            f"https://apis.datos.gob.ar/georef/api/calles?nombre={_up.quote(calle)}&provincia=tucuman&max=1&campos=basico",
            timeout=6
        )
        if r2.status_code == 200:
            calles = r2.json().get("calles", [])
            if calles:
                nombre_georef = calles[0].get("nombre", calle)
                q_struct = f"{nombre_georef} {altura if altura else ''}, Tucumán, Argentina".strip()
                r3 = _req.get(
                    f"https://nominatim.openstreetmap.org/search?format=json&q={_up.quote(q_struct)}&limit=1&countrycodes=ar",
                    headers=headers_nom, timeout=6
                )
                if r3.status_code == 200 and r3.json():
                    d3 = r3.json()[0]
                    partes = [p.strip() for p in d3.get("display_name", "").split(",")]
                    display = ", ".join(partes[:4]) if len(partes) > 4 else ", ".join(partes)
                    return float(d3["lat"]), float(d3["lon"]), display
    except Exception:
        pass
    def _nominatim(q):
        try:
            url = f"https://nominatim.openstreetmap.org/search?format=json&q={_up.quote(q)}&limit=1&countrycodes=ar"
            r = _req.get(url, headers=headers_nom, timeout=6)
            if r.status_code == 200 and r.json():
                d = r.json()[0]
                partes = [p.strip() for p in d.get("display_name", "").split(",")]
                return float(d["lat"]), float(d["lon"]), ", ".join(partes[:4])
        except Exception:
            pass
        return None
    base = "San Miguel de Tucumán, Tucumán, Argentina"
    intentos = [
        f"{query_clean}, {base}",
        f"{calle} {altura or ''}, {base}".strip(),
        f"Calle {calle} {altura or ''}, {base}".strip(),
        f"{calle}, {base}",
    ]
    for intento in intentos:
        res = _nominatim(intento)
        if res:
            return res
    return None

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
        st.warning(f"⚠️ No se pudo actualizar el stock en el Excel: {e}")
        return False

def obtener_access_token_mp():
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
    access_token = obtener_access_token_mp()
    if not access_token:
        return None
    import requests
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
        st.error(f"⚠️ Error al conectar con Google Sheets: {e}")
        mock_data = [
            {"Nombre del Artículo": "Funda de silicona", "Marca Principal": "Samsung",
             "Modelo Exacto": "Galaxy A54", "Color / Diseño (Variación)": "Negro Mate",
             "Precio Mercado": 15000, "Cantidad": 5,
             "Imagen_URL": "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500", "Oferta": "si"},
            {"Nombre del Artículo": "Funda de silicona", "Marca Principal": "Apple",
             "Modelo Exacto": "iPhone 14", "Color / Diseño (Variación)": "Transparente",
             "Precio Mercado": 18000, "Cantidad": 8,
             "Imagen_URL": "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500", "Oferta": ""},
            {"Nombre del Artículo": "Cargador Rápido 20W", "Marca Principal": "Apple",
             "Modelo Exacto": "iPhone 12 al 15", "Color / Diseño (Variación)": "Blanco",
             "Precio Mercado": 22000, "Cantidad": 3,
             "Imagen_URL": "https://images.unsplash.com/photo-1585771724684-38269d6639fd?w=500", "Oferta": ""},
            {"Nombre del Artículo": "Hidrogel", "Marca Principal": "Samsung",
             "Modelo Exacto": "Galaxy S23", "Color / Diseño (Variación)": "Transparente mate",
             "Precio Mercado": 8000, "Cantidad": 0,
             "Imagen_URL": "https://images.unsplash.com/photo-1510557880182-3d4d3cba35a5?w=500", "Oferta": ""},
        ]
        df_mock = pd.DataFrame(mock_data)
        df_mock["En Oferta"] = df_mock["Oferta"].str.lower() == "si"
        return df_mock

# ── DATA ─────────────────────────────────────────────────────────────────────
df_stock = cargar_datos_sheets()

# ── SESSION STATE ─────────────────────────────────────────────────────────────
for k, v in {
    "carrito": {}, "mostrar_banner_carrito": False,
    "admin_autenticado": False,
    "admin_modo": None,
    "admin_idx_sel": None,
    "vista": "catalogo",
    "_georef_query": "",
    "_georef_sugerencias": [],
    "_georef_elegida": None,
    "map_coords": [-26.8306, -65.2201],
    "last_clicked_tracked": None,
    "inp_dir": "",
    "geo_error": None,
    "inp_dir_version": 0,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── PROCESS QUERY PARAMS ──────────────────────────────────────────────────────
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
                st.toast(f"⚠️ Solo hay {_stock} unidades disponibles de {_row['Nombre del Artículo']}.", icon="⚠️")
    except Exception:
        pass
    _qp = dict(st.query_params)
    _qp.pop("add_cart", None)
    st.query_params.from_dict(_qp)
    st.rerun()

_go_param = st.query_params.get("go", "")
if _go_param == "carrito":
    _qp2 = dict(st.query_params)
    _qp2.pop("go", None)
    st.query_params.from_dict(_qp2)
    if st.session_state.carrito:
        st.session_state.vista = "carrito"
    st.rerun()
elif _go_param in ["catalogo","ofertas","mayor","compatibilidad","productos"]:
    _qp3 = dict(st.query_params)
    _qp3.pop("go", None)
    st.query_params.from_dict(_qp3)
    st.session_state.vista = _go_param
    st.rerun()

# ── QUANTITY ADJUSTMENTS VIA URL ──────────────────────────────────────────────
_qty_inc = st.query_params.get("qty_inc", "")
if _qty_inc:
    try:
        _idx2 = int(_qty_inc)
        if _idx2 in df_stock.index:
            _stock2 = int(df_stock.loc[_idx2, "Cantidad"])
            _cur = st.session_state.carrito.get(_idx2, 0)
            if _cur < _stock2 and _cur < 10:
                st.session_state.carrito[_idx2] = _cur + 1
    except Exception:
        pass
    _qp4 = dict(st.query_params)
    _qp4.pop("qty_inc", None)
    st.query_params.from_dict(_qp4)
    st.rerun()

_qty_dec = st.query_params.get("qty_dec", "")
if _qty_dec:
    try:
        _idx3 = int(_qty_dec)
        _cur2 = st.session_state.carrito.get(_idx3, 0)
        if _cur2 > 1:
            st.session_state.carrito[_idx3] = _cur2 - 1
        elif _cur2 == 1:
            del st.session_state.carrito[_idx3]
    except Exception:
        pass
    _qp5 = dict(st.query_params)
    _qp5.pop("qty_dec", None)
    st.query_params.from_dict(_qp5)
    st.rerun()

_qty_del = st.query_params.get("qty_del", "")
if _qty_del:
    try:
        _idx4 = int(_qty_del)
        if _idx4 in st.session_state.carrito:
            del st.session_state.carrito[_idx4]
    except Exception:
        pass
    _qp6 = dict(st.query_params)
    _qp6.pop("qty_del", None)
    st.query_params.from_dict(_qp6)
    st.rerun()

# ── LOGO ──────────────────────────────────────────────────────────────────────
try:
    import base64 as _b64
    with open("logo.png", "rb") as _f:
        _logo_b64 = _b64.b64encode(_f.read()).decode()
    _logo_src = f"data:image/png;base64,{_logo_b64}"
except Exception:
    _logo_src = ""

# ── DETECT MP RETURN ──────────────────────────────────────────────────────────
qp = st.query_params
if "external_reference" in qp:
    id_pedido = qp["external_reference"]
    status = qp.get("status", "unknown")
    payment_id = qp.get("payment_id", "")
    if status == "approved":
        try:
            df_ped = cargar_pedidos_sheets()
            if not df_ped.empty:
                actualizar_estado_pedido(id_pedido, "Pagado", df_ped)
        except Exception:
            pass
    st.balloons()
    status_text = "APROBADO ✅" if status == "approved" else "PENDIENTE ⏳" if status == "pending" else "RECHAZADO ❌"
    box_bg = "linear-gradient(135deg,#34C759,#248a3d)" if status == "approved" else "linear-gradient(135deg,#FF9F0A,#c17000)" if status == "pending" else "linear-gradient(135deg,#FF3B30,#c0392b)"
    msg_re = f"⚡ Hola BEJO! Acabo de pagar mi pedido 🔥\n\n🆔 *ID Pedido:* {id_pedido}\n💳 *Estado del pago:* {status_text}\n🧾 *ID Transacción MP:* {payment_id}\n\n¡Gracias! 🙌"
    ws_url_re = f"https://wa.me/{NUMERO_WS}?text={urllib.parse.quote(msg_re)}"
    st.markdown(f"""
<div style="max-width:600px;margin:4rem auto;">
  <div style="background:{box_bg};color:white;border-radius:24px;padding:2.5rem;text-align:center;box-shadow:0 20px 60px rgba(0,0,0,0.15);">
    <div style="font-size:3rem;margin-bottom:1rem;">🎉</div>
    <h1 style="color:white;font-size:1.8rem;font-weight:900;margin:0 0 8px;">¡Pedido Confirmado!</h1>
    <p style="color:rgba(255,255,255,0.85);margin:0 0 1.5rem;font-size:1rem;">Tu pago fue registrado de manera segura.</p>
    <div style="background:rgba(255,255,255,0.15);border-radius:14px;padding:1.2rem;text-align:left;margin-bottom:1.5rem;">
      <p style="color:white;margin:4px 0;font-size:0.95rem;">🆔 <b>ID Pedido:</b> {id_pedido}</p>
      <p style="color:white;margin:4px 0;font-size:0.95rem;">💳 <b>Estado:</b> {status_text}</p>
      <p style="color:white;margin:4px 0;font-size:0.95rem;">🧾 <b>ID MP:</b> {payment_id}</p>
    </div>
    <p style="color:rgba(255,255,255,0.75);font-size:0.85rem;margin-bottom:1.5rem;">📸 Guardá captura como comprobante. En instantes abrimos WhatsApp...</p>
    <a href="{ws_url_re}" target="_blank"
       style="display:inline-block;background:white;color:#25D366!important;font-weight:800;padding:13px 28px;border-radius:14px;text-decoration:none;font-size:1rem;box-shadow:0 4px 16px rgba(0,0,0,0.15);">
      📲 Confirmar por WhatsApp
    </a>
  </div>
</div>
<script>
setTimeout(function(){{ window.location.href = "{ws_url_re}"; }}, 4500);
</script>
""", unsafe_allow_html=True)
    if st.button("🛍️ Volver al Catálogo", use_container_width=True, type="primary", key="btn_volver_mp"):
        st.query_params.clear()
        st.session_state.vista = "catalogo"
        st.rerun()
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# GLASSMORPHISM HEADER
# ══════════════════════════════════════════════════════════════════════════════
_vista_actual = st.session_state.vista
_num_items    = sum(st.session_state.carrito.values())
_logo_img_tag = f'<img src="{_logo_src}" alt="BEJO Logo">' if _logo_src else '⚡'

# Build cart total for drawer
_carrito_total = 0
_cart_items_html = ""
if st.session_state.carrito:
    for _ci, _cqty in st.session_state.carrito.items():
        if _ci in df_stock.index:
            _crow = df_stock.loc[_ci]
            _cname = f"{_crow['Nombre del Artículo']} {_crow['Modelo Exacto']}"
            _ccolor = _crow["Color / Diseño (Variación)"]
            _cprice = _crow["Precio Mercado"]
            _cimg = _crow["Imagen_URL"] if str(_crow["Imagen_URL"]).strip() else "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=300"
            _csubt = _cprice * _cqty
            _carrito_total += _csubt
            _cart_items_html += f"""
<div class="cart-item-row">
  <img class="cart-item-img" src="{_cimg}" alt="{_cname}" onerror="this.src='https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=300'">
  <div class="cart-item-info">
    <div class="cart-item-name">{_cname}</div>
    <div class="cart-item-color">🎨 {_ccolor}</div>
    <div class="cart-item-price">${_csubt:,.0f}</div>
  </div>
  <div class="qty-controls">
    <a class="qty-btn" href="?qty_dec={_ci}" title="Restar">−</a>
    <span class="qty-num">{_cqty}</span>
    <a class="qty-btn" href="?qty_inc={_ci}" title="Sumar">+</a>
    <a class="qty-del" href="?qty_del={_ci}" title="Eliminar">🗑</a>
  </div>
</div>"""
else:
    _cart_items_html = """
<div class="cart-empty-msg">
  <span class="cart-empty-icon">🛒</span>
  <p>Tu carrito está vacío.</p>
  <p style="margin-top:4px;">Explorá el catálogo y agregá productos.</p>
</div>"""

_cart_footer_html = ""
if st.session_state.carrito:
    _cart_footer_html = f"""
<div class="cart-drawer-footer">
  <div class="cart-total-row">
    <span class="cart-total-label">Total estimado</span>
    <span class="cart-total-amount">${_carrito_total:,.0f}</span>
  </div>
  <a href="?go=carrito" class="btn-checkout" target="_self">PROCEDER AL PAGO →</a>
  <button class="btn-continue-shop" onclick="closeCart()">Seguir comprando</button>
</div>"""
else:
    _cart_footer_html = """
<div class="cart-drawer-footer">
  <a href="?go=catalogo" class="btn-checkout" target="_self" style="background:var(--accent)">Ver Catálogo →</a>
</div>"""

_nav_items = [
    ("🏠 Inicio",      "catalogo",      ""),
    ("🔍 Compatibilidad","compatibilidad",""),
    ("🔥 Ofertas",     "ofertas",       "pill-offer"),
    ("📦 Mayor",       "mayor",         ""),
    ("📋 Productos",   "productos",     ""),
]
_nav_html = ""
for _nlabel, _nvista, _nextra in _nav_items:
    _nactive = "active" if _vista_actual == _nvista else ""
    _nav_html += f'<a class="bejo-nav-pill {_nactive} {_nextra}" href="?go={_nvista}" target="_self">{_nlabel}</a>'
_ws_nav_url = f"https://wa.me/{NUMERO_WS}?text={urllib.parse.quote('Hola BEJO! Tengo una consulta 😊')}"
_nav_html += f'<a class="bejo-nav-pill pill-ws" href="{_ws_nav_url}" target="_blank">💬 WhatsApp</a>'

_cart_btn_label = f"🛒 Carrito ({_num_items})" if _num_items > 0 else "🛒 Carrito"

st.markdown(f"""
<!-- HEADER GLASSMORPHISM -->
<div class="bejo-topbar">
  <div class="bejo-topbar-inner">
    <a class="bejo-brand" href="?go=catalogo" target="_self">
      {_logo_img_tag}
      <span class="bejo-brand-name">BEJO</span>
    </a>
    <nav class="bejo-nav-pills">
      {_nav_html}
    </nav>
    <div class="bejo-topbar-actions">
      <button class="cart-icon-btn" onclick="toggleCart()">
        🛒
        <span id="cartLabel">{"Carrito" if _num_items == 0 else f"Carrito"}</span>
        {"<span class='cart-badge'>" + str(_num_items) + "</span>" if _num_items > 0 else ""}
      </button>
    </div>
  </div>
</div>

<!-- CART SLIDE-OVER DRAWER -->
<div class="cart-overlay" id="cartOverlay" onclick="closeCart()"></div>
<aside class="cart-drawer" id="cartDrawer">
  <div class="cart-drawer-header">
    <div class="cart-drawer-title">🛒 Tu Carrito {f"<span class='cart-badge' style='background:var(--accent);color:white;margin-left:6px;'>{_num_items}</span>" if _num_items > 0 else ""}</div>
    <button class="cart-close-btn" onclick="closeCart()">✕</button>
  </div>
  <div class="cart-drawer-body">
    {_cart_items_html}
  </div>
  {_cart_footer_html}
</aside>

<script>
function toggleCart() {{
  document.body.classList.toggle('cart-open');
}}
function closeCart() {{
  document.body.classList.remove('cart-open');
}}
// Keep cart open after page reload if it was open
</script>
""", unsafe_allow_html=True)

# ── HIDDEN STREAMLIT NAV TRIGGERS ─────────────────────────────────────────────
st.markdown('<div class="bejo-nav-triggers">', unsafe_allow_html=True)
_nb1, _nb2, _nb3, _nb4, _nb5, _nb_cart = st.columns([1,1,1,1,1,1])
with _nb1:
    if st.button("Catálogo", key="nav_home_h"):
        st.session_state.vista = "catalogo"; st.rerun()
with _nb2:
    if st.button("Compatibilidad", key="nav_compat_h"):
        st.session_state.vista = "compatibilidad"; st.rerun()
with _nb3:
    if st.button("Ofertas", key="nav_ofertas_h"):
        st.session_state.vista = "ofertas"; st.rerun()
with _nb4:
    if st.button("Mayor", key="nav_mayor_h"):
        st.session_state.vista = "mayor"; st.rerun()
with _nb5:
    if st.button("Productos", key="nav_productos_h"):
        st.session_state.vista = "productos"; st.rerun()
with _nb_cart:
    if st.button("Carrito", key="nav_cart_h"):
        st.session_state.vista = "carrito"; st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# VISTA: PRODUCTOS (árbol de categorías)
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.vista == "productos":
    st.markdown("""
<div class="view-header">
  <div class="view-header-title">📋 Nuestros Productos</div>
  <div class="view-header-sub">Explorá el catálogo completo por categoría y marca</div>
</div>""", unsafe_allow_html=True)
    if df_stock.empty:
        st.info("No hay productos cargados en el catálogo.")
    else:
        tipos_unicos = sorted([t for t in df_stock["Nombre del Artículo"].dropna().unique() if str(t).strip()])
        for tipo in tipos_unicos:
            df_tipo = df_stock[df_stock["Nombre del Artículo"] == tipo]
            marcas_unicas = sorted([m for m in df_tipo["Marca Principal"].dropna().unique() if str(m).strip()])
            if not marcas_unicas:
                continue
            st.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;margin:1.5rem 0 0.75rem;">
  <span style="font-size:1rem;font-weight:800;color:var(--text);">📁 {tipo.upper()}</span>
  <span style="font-size:0.78rem;color:var(--text3);">{len(marcas_unicas)} marca(s)</span>
</div>""", unsafe_allow_html=True)
            cols_m = st.columns(max(2, min(6, len(marcas_unicas) + 1)))
            with cols_m[0]:
                if st.button(f"🔍 Ver todo", key=f"tree_all_{tipo}", use_container_width=True):
                    st.session_state.filtro_tipo_val = tipo
                    st.session_state.filtro_marca_val = "Todas"
                    st.session_state.vista = "catalogo"
                    st.rerun()
            for idx, marca in enumerate(marcas_unicas):
                col_target = cols_m[(idx + 1) % len(cols_m)]
                with col_target:
                    if st.button(f"📱 {marca}", key=f"tree_btn_{tipo}_{marca}", use_container_width=True):
                        st.session_state.filtro_tipo_val = tipo
                        st.session_state.filtro_marca_val = marca
                        st.session_state.vista = "catalogo"
                        st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("← Volver al Catálogo", use_container_width=True, key="btn_volver_cat_tree", type="primary"):
        st.session_state.vista = "catalogo"; st.rerun()
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# VISTA: OFERTAS
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.vista == "ofertas":
    st.markdown("""
<div class="view-header" style="border-left:4px solid var(--offer);background:linear-gradient(135deg,rgba(255,59,48,0.05),var(--surface));">
  <div class="view-header-title" style="color:var(--offer);">🔥 Ofertas Especiales</div>
  <div class="view-header-sub">Precios rebajados por tiempo limitado · No te las pierdas</div>
</div>""", unsafe_allow_html=True)
    df_of = df_stock[df_stock["En Oferta"] == True]
    if df_of.empty:
        st.markdown("""
<div style="background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-md);padding:3rem;text-align:center;box-shadow:var(--shadow-sm);">
  <div style="font-size:3rem;margin-bottom:1rem;">🔥</div>
  <div style="font-size:1.2rem;font-weight:700;color:var(--text);margin-bottom:8px;">No hay ofertas activas ahora</div>
  <div style="color:var(--text3);font-size:0.9rem;line-height:1.6;">
    Para activar ofertas, agregá una columna <b>"Oferta"</b> en tu planilla<br>
    y escribí <b>"si"</b> en los artículos que quieras promocionar.
  </div>
</div>""", unsafe_allow_html=True)
    else:
        of_items = df_of.reset_index().to_dict('records')
        for i in range(0, len(of_items), 3):
            cols = st.columns(3)
            for ci in range(3):
                item_idx = i + ci
                if item_idx >= len(of_items):
                    break
                item = of_items[item_idx]
                orig_idx = item.get('index', item_idx)
                img_url = item["Imagen_URL"] if str(item["Imagen_URL"]).strip() else "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500"
                if item["Cantidad"] <= 0:
                    cta_btn = '<span class="btn-add-cart-disabled">🔴 Sin Stock</span>'
                else:
                    cta_btn = f'<a class="btn-add-cart" href="?add_cart={orig_idx}" target="_self" style="background:var(--offer);">🛒 Agregar Oferta</a>'
                with cols[ci]:
                    st.markdown(f"""
<div class="offer-home-card">
  <div style="position:relative;aspect-ratio:4/3;overflow:hidden;background:var(--surface2);">
    <img src="{img_url}" style="width:100%;height:100%;object-fit:cover;" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500'">
    <span class="badge-offer">🔥 OFERTA</span>
  </div>
  <div style="padding:12px 14px 14px;">
    <div style="font-size:0.7rem;font-weight:700;letter-spacing:1.2px;text-transform:uppercase;color:var(--offer);margin-bottom:3px;">{item['Marca Principal']}</div>
    <div style="font-size:0.95rem;font-weight:700;color:var(--text);margin-bottom:3px;">{item['Nombre del Artículo']} {item['Modelo Exacto']}</div>
    <div style="font-size:0.78rem;color:var(--text3);margin-bottom:8px;">🎨 {item['Color / Diseño (Variación)']}</div>
    <div style="font-size:1.2rem;font-weight:900;color:var(--text);margin-bottom:8px;">${item['Precio Mercado']:,.0f}</div>
    {cta_btn}
  </div>
</div>""", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("← Volver al Catálogo", use_container_width=True, key="btn_volver_cat_ofertas", type="primary"):
        st.session_state.vista = "catalogo"; st.rerun()
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# VISTA: VENTA POR MAYOR
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.vista == "mayor":
    _ws_mayor = f"https://wa.me/{NUMERO_WS}?text={urllib.parse.quote('Hola BEJO! Quiero consultar sobre precios mayoristas y cantidades disponibles 📦')}"
    st.markdown("""
<div class="view-header" style="border-left:4px solid #FF9F0A;background:linear-gradient(135deg,rgba(255,159,10,0.06),var(--surface));">
  <div class="view-header-title" style="color:#c17000;">📦 Venta por Mayor</div>
  <div class="view-header-sub">Precios especiales para revendedores y comercios de Tucumán</div>
</div>""", unsafe_allow_html=True)
    mc1, mc2 = st.columns(2)
    with mc1:
        st.markdown("""
<div class="benefit-card">
  <div class="benefit-card-title" style="color:#c17000;">✅ Beneficios</div>
  <ul style="color:var(--text2);font-size:0.9rem;line-height:2;padding-left:1.2rem;margin:0;">
    <li>Precios mayoristas exclusivos</li>
    <li>Stock reservado para clientes frecuentes</li>
    <li>Envío sin cargo a partir de cierta cantidad</li>
    <li>Acceso anticipado a nuevos productos</li>
    <li>Atención personalizada por WhatsApp</li>
  </ul>
</div>""", unsafe_allow_html=True)
    with mc2:
        st.markdown("""
<div class="benefit-card">
  <div class="benefit-card-title" style="color:#c17000;">📋 ¿Cómo funciona?</div>
  <div style="color:var(--text2);font-size:0.9rem;line-height:1.9;">
    <p style="margin:0 0 10px;"><b>1.</b> Consultá por WhatsApp con la lista de productos que te interesan.</p>
    <p style="margin:0 0 10px;"><b>2.</b> Te enviamos una cotización mayorista en el día.</p>
    <p style="margin:0 0 10px;"><b>3.</b> Coordinamos pago y envío o retiro personal.</p>
    <p style="color:#c17000;font-weight:700;margin:0;">📍 San Miguel de Tucumán</p>
  </div>
</div>""", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
<div style="text-align:center;">
  <a href="{_ws_mayor}" target="_blank" class="btn-pay-ws" style="max-width:420px;margin:0 auto;display:flex;">
    💬 CONSULTAR PRECIO MAYORISTA POR WHATSAPP
  </a>
</div>""", unsafe_allow_html=True)
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# VISTA: COMPATIBILIDAD
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.vista == "compatibilidad":
    st.markdown("""
<div class="view-header" style="border-left:4px solid var(--accent);">
  <div class="view-header-title">🔍 Comprobador de Compatibilidad</div>
  <div class="view-header-sub">Descubrí qué accesorios son compatibles con tu modelo de celular</div>
</div>""", unsafe_allow_html=True)
    if st.button("← Volver al Catálogo", use_container_width=False, key="btn_volver_cat_comp"):
        st.session_state.vista = "catalogo"; st.rerun()
    st.markdown("")
    df_comp = cargar_compatibilidad_sheets()
    if df_comp.empty:
        st.warning("⚠️ No se pudieron cargar los datos de compatibilidad. Por favor intentá más tarde.")
    else:
        st.markdown("""
<div class="info-box info-box-blue" style="margin-bottom:1.25rem;">
  📱 Elegí el tipo de artículo, la marca y el modelo de tu teléfono para ver las compatibilidades en nuestro stock.
</div>""", unsafe_allow_html=True)
        col_comp1, col_comp2, col_comp3 = st.columns(3)
        col_tipos = sorted(df_comp["tipo de producto"].dropna().unique())
        if not col_tipos:
            st.info("No hay tipos de producto cargados.")
        else:
            with col_comp1:
                tipo_sel = st.selectbox("1. Tipo de artículo:", col_tipos, key="comp_tipo_sel")
            df_filtered = df_comp[df_comp["tipo de producto"] == tipo_sel]
            col_marcas = sorted(df_filtered["marca"].dropna().unique())
            if col_marcas:
                with col_comp2:
                    marca_sel = st.selectbox("2. Marca de tu celu:", col_marcas, key="comp_marca_sel")
                df_filtered = df_filtered[df_filtered["marca"] == marca_sel]
                col_modelos = sorted(df_filtered["modelo"].dropna().unique())
                if col_modelos:
                    with col_comp3:
                        modelo_sel = st.selectbox("3. Modelo exacto:", col_modelos, key="comp_modelo_sel")
                    df_final = df_filtered[df_filtered["modelo"] == modelo_sel]
                    st.markdown("---")
                    if not df_final.empty:
                        compat_value = df_final.iloc[0]["compatibilidad"]
                        if compat_value and str(compat_value).strip():
                            lista_compat = [c.strip() for c in str(compat_value).split(",") if c.strip()]
                            chips = "".join(f'<span class="compat-chip">{c}</span>' for c in lista_compat)
                            st.markdown(f"""
<div class="compat-result-box">
  <div style="font-size:1rem;font-weight:700;color:var(--accent);margin-bottom:12px;">✅ Compatibilidades encontradas</div>
  <p style="font-size:0.92rem;color:var(--text2);margin-bottom:12px;">
    Tu <b>{tipo_sel}</b> de <b>{marca_sel} {modelo_sel}</b> también es compatible con:
  </p>
  <div style="display:flex;flex-wrap:wrap;gap:4px;">{chips}</div>
</div>""", unsafe_allow_html=True)
                        else:
                            st.info("ℹ️ No hay información de compatibilidad cargada para este modelo.")
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# VISTA: CARRITO / CHECKOUT
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.vista == "carrito":
    st.markdown("""
<div class="view-header">
  <div class="view-header-title">🛒 Tu Carrito de Compras</div>
</div>""", unsafe_allow_html=True)
    if st.button("← Seguir comprando", use_container_width=False, key="btn_volver_cat"):
        st.session_state.vista = "catalogo"; st.rerun()
    st.markdown("")

    if not st.session_state.carrito:
        st.markdown("""
<div style="background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-md);padding:4rem 2rem;text-align:center;box-shadow:var(--shadow-sm);">
  <div style="font-size:4rem;margin-bottom:1rem;">🛒</div>
  <div style="font-size:1.25rem;font-weight:700;color:var(--text);margin-bottom:8px;">Tu carrito está vacío</div>
  <div style="color:var(--text3);font-size:0.9rem;">Explorá el catálogo y encontrá lo que buscás.</div>
</div>""", unsafe_allow_html=True)
    else:
        total_pedido      = 0
        resumen_productos = []

        # ── Cart item list ──
        for idx, cantidad in list(st.session_state.carrito.items()):
            row          = df_stock.loc[idx]
            nombre_prod  = f"{row['Nombre del Artículo']} {row['Modelo Exacto']} ({row['Color / Diseño (Variación)']})"
            precio_unit  = row["Precio Mercado"]
            stock_actual = row["Cantidad"]
            subtotal = precio_unit * cantidad
            total_pedido += subtotal
            resumen_productos.append(f"- {nombre_prod} x{cantidad} (${subtotal:,.0f})")

            c1, c2, c3, c4 = st.columns([2.8, 1.8, 1.4, 0.5])
            c1.markdown(f"**{nombre_prod}**")
            qty_col1, qty_col2, qty_col3 = c2.columns([1, 1, 1])
            with qty_col1:
                if st.button("−", key=f"qty_dec_{idx}", use_container_width=True):
                    if cantidad > 1:
                        st.session_state.carrito[idx] = cantidad - 1
                        st.rerun()
                    else:
                        del st.session_state.carrito[idx]; st.rerun()
            with qty_col2:
                st.markdown(f"<p style='text-align:center;font-weight:700;font-size:1.1rem;line-height:2.2;margin:0;'>{cantidad}</p>", unsafe_allow_html=True)
            with qty_col3:
                if st.button("+", key=f"qty_inc_{idx}", use_container_width=True):
                    if cantidad < stock_actual and cantidad < 10:
                        st.session_state.carrito[idx] = cantidad + 1
                        st.rerun()
                    else:
                        st.session_state[f"msg_error_stock_{idx}"] = True; st.rerun()
            c3.markdown(f"**${subtotal:,.0f}**")
            if c4.button("🗑", key=f"del_{idx}"):
                del st.session_state.carrito[idx]; st.rerun()

            if st.session_state.get(f"msg_error_stock_{idx}"):
                st.markdown(f'<div class="error-box">😔 Límite de stock: {stock_actual} unidades disponibles de {row["Nombre del Artículo"]}.</div>', unsafe_allow_html=True)
                if st.button("Entendido", key=f"clear_stock_{idx}"):
                    st.session_state[f"msg_error_stock_{idx}"] = False; st.rerun()

        # Total box
        st.markdown(f"""
<div class="total-summary-box">
  <div class="total-summary-label">Total a Pagar</div>
  <div class="total-summary-amount">${total_pedido:,.0f}</div>
</div>""", unsafe_allow_html=True)

        # ── ENTREGA ──
        st.markdown("""
<div class="checkout-section">
  <div class="checkout-section-title">📦 ¿Cómo querés recibirlo?</div>
</div>""", unsafe_allow_html=True)

        metodo_entrega = st.radio(
            "entrega_r",
            ["🏪  Retiro en punto de venta", "🏠  Envío a domicilio"],
            index=None, label_visibility="collapsed"
        )
        direccion = observacion = ""

        if metodo_entrega == "🏪  Retiro en punto de venta":
            st.markdown("""<div class="info-box info-box-blue">📍 <b>Retiro en local BEJO</b><br>
            Una vez confirmado el pedido, coordiná el retiro con el vendedor por WhatsApp. 😊</div>""", unsafe_allow_html=True)

        elif metodo_entrega == "🏠  Envío a domicilio":
            st.markdown("""<div class="info-box info-box-green">🛵 <b>Información sobre Envíos:</b><br>
            • Realizamos envíos en <b>San Miguel de Tucumán, Yerba Buena, Alderetes y zonas cercanas</b>.<br>
            • <b>Envío GRATIS</b> dentro de las 4 Avenidas de S.M.T.<br>
            • Fuera de las 4 Avenidas, coordinamos el costo por WhatsApp.<br>
            📞 En caso de dudas con la dirección, <b>el administrador se comunicará con vos</b>.</div>""", unsafe_allow_html=True)
            st.markdown("#### 📍 Datos de entrega")
            _dc1, _dc2 = st.columns([2, 1])
            with _dc1:
                dir_calle = st.text_input("🏠 Calle y número *", placeholder="Ej: Haiti 650", key="dir_calle")
            with _dc2:
                dir_barrio = st.text_input("🌿 Barrio", placeholder="Ej: Villa Carmela", key="dir_barrio")
            _dc3, _dc4 = st.columns([2, 1])
            with _dc3:
                dir_localidad = st.selectbox("📍 Localidad *",
                    ["— Seleccioná tu localidad —", "San Miguel de Tucumán", "Yerba Buena",
                     "Alderetes", "Banda del Río Salí", "Las Talitas", "El Manantial", "Otra localidad"],
                    key="dir_localidad")
            with _dc4:
                dir_telefono = st.text_input("📞 Teléfono *", placeholder="Ej: 381 4123456", key="dir_telefono")
            dir_observacion = st.text_area("📝 Referencias / Observaciones",
                placeholder="Ej: Casa azul, piso 3 dpto B, entre Av. Mate de Luna y Marcos Paz...",
                height=80, key="dir_observacion")
            _loc = dir_localidad if dir_localidad != "— Seleccioná tu localidad —" else ""
            direccion = " | ".join(filter(None, [
                dir_calle.strip(),
                f"Barrio {dir_barrio.strip()}" if dir_barrio.strip() else "",
                _loc,
                f"Tel: {dir_telefono.strip()}" if dir_telefono.strip() else "",
            ]))
            observacion = dir_observacion.strip()

        # ── MÉTODO DE PAGO ──
        st.markdown("""
<div class="checkout-section" style="margin-top:1rem;">
  <div class="checkout-section-title">💳 Método de Pago</div>
</div>""", unsafe_allow_html=True)

        metodo_pago = st.radio(
            "pago_r",
            ["💵  Efectivo", "🏦  Transferencia Bancaria", "💳  Mercado Pago (Tarjeta, Dinero en cuenta)"],
            index=None, label_visibility="collapsed"
        )
        mitad = total_pedido // 2
        resto = total_pedido - mitad

        if metodo_pago == "🏦  Transferencia Bancaria":
            st.markdown(f"""<div class="info-box info-box-yellow">🏦 <b>PAGO POR TRANSFERENCIA</b><br><br>
            ✅ Transferí la mitad ahora: <b>${mitad:,.0f}</b><br>
            📦 El resto (${resto:,.0f}) lo abonás al recibir el producto.<br><br>
            💬 Los datos bancarios te los enviamos por WhatsApp. 🤝</div>""", unsafe_allow_html=True)
        elif metodo_pago == "💳  Mercado Pago (Tarjeta, Dinero en cuenta)":
            access_token = obtener_access_token_mp()
            if not access_token:
                st.warning("⚠️ El vendedor aún no configuró las credenciales de Mercado Pago. Seleccioná otro método o coordiná por WhatsApp.")
            else:
                st.markdown(f"""<div class="info-box info-box-blue">💳 <b>PAGO CON MERCADO PAGO</b><br><br>
                Al confirmar el pedido, generamos un link de pago oficial de Mercado Pago para que abones el total de <b>${total_pedido:,.0f}</b>.<br><br>
                Podrás pagar con tarjeta de crédito/débito, transferencia o dinero en cuenta. 🤝</div>""", unsafe_allow_html=True)

        st.markdown("")
        if st.button("🚀 CONFIRMAR PEDIDO", type="primary", use_container_width=True, key="btn_confirmar"):
            errores = []
            if metodo_entrega is None: errores.append("⚠️ Seleccioná cómo querés recibir tu pedido.")
            if metodo_pago is None:    errores.append("⚠️ Seleccioná el método de pago.")
            if metodo_entrega == "🏠  Envío a domicilio" and not direccion.strip():
                errores.append("⚠️ Ingresá tu dirección de envío.")
            if metodo_pago == "💳  Mercado Pago (Tarjeta, Dinero en cuenta)":
                if not obtener_access_token_mp():
                    errores.append("⚠️ Mercado Pago no configurado. Seleccioná otro método.")
            if errores:
                for e in errores:
                    st.markdown(f'<div class="error-box">{e}</div>', unsafe_allow_html=True)
            else:
                ahora     = datetime.now()
                id_pedido = f"PED-{ahora.strftime('%d%m-%H%M')}-{random.randint(100,999)}"
                le = metodo_entrega.replace("🏪  ","").replace("🏠  ","")
                lp = metodo_pago.replace("💵  ","").replace("🏦  ","").replace("💳  ","")

                mp_url = None
                if metodo_pago == "💳  Mercado Pago (Tarjeta, Dinero en cuenta)":
                    with st.spinner("Generando link de pago..."):
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
                    if observacion: msg += f"📝 *Referencias:* {observacion}\n"
                if metodo_entrega == "🏪  Retiro en punto de venta":
                    msg += "\n🤝 ¡Coordino el retiro por WhatsApp!\n"
                msg += "\n✨ ¡Gracias por elegir BEJO! 🙌"
                ws_url = f"https://wa.me/{NUMERO_WS}?text={urllib.parse.quote(msg)}"

                try:
                    p_sheet = get_pedidos_sheet()
                    cliente_info = f"Pago: {lp} | Entrega: {le}"
                    if metodo_entrega == "🏠  Envío a domicilio":
                        cliente_info += f" | Dir: {direccion}"
                    p_sheet.append_row([
                        ahora.strftime('%Y-%m-%d %H:%M:%S'),
                        id_pedido, cliente_info, msg,
                        str(total_pedido), "Pendiente"
                    ])
                except Exception as e:
                    st.warning(f"⚠️ No se pudo guardar el pedido en el historial: {e}")

                with st.spinner("Actualizando stock..."):
                    ok_stock = descontar_stock(st.session_state.carrito, df_stock)
                st.cache_data.clear()
                st.session_state.carrito = {}
                st.session_state.vista = "catalogo"
                st.balloons()
                if ok_stock:
                    st.success(f"✅ ¡Pedido **{id_pedido}** generado!")
                else:
                    st.success(f"✅ ¡Pedido **{id_pedido}** generado! Revisá el stock manualmente.")

                if mp_url:
                    st.markdown(f"""
<div style="background:linear-gradient(135deg,rgba(0,158,227,0.08),rgba(0,102,204,0.05));border:2px solid rgba(0,158,227,0.25);border-radius:var(--radius-md);padding:1.5rem;text-align:center;margin-top:1.5rem;">
  <h3 style="color:var(--text);margin:0 0 8px;font-size:1.3rem;">🎉 Pedido {id_pedido} confirmado</h3>
  <p style="color:var(--text3);margin-bottom:1.5rem;font-size:0.9rem;">Tocá los botones para pagar y avisar al vendedor.</p>
  <div style="display:flex;flex-direction:column;gap:10px;align-items:center;">
    <a href="{mp_url}" target="_blank" class="btn-pay-mp" style="max-width:320px;width:100%;justify-content:center;">
      💳 PAGAR CON MERCADO PAGO
    </a>
    <a href="{ws_url}" target="_blank" class="btn-pay-ws" style="max-width:320px;width:100%;justify-content:center;">
      📲 AVISAR POR WHATSAPP
    </a>
  </div>
</div>""", unsafe_allow_html=True)
                    st_components.html(f"""<script>
setTimeout(function(){{ window.open('{ws_url}', '_blank'); }}, 1500);
</script>""", height=1)
                else:
                    st.markdown(f"""
<div style="background:rgba(37,211,102,0.08);border:2px solid #25D366;border-radius:var(--radius-md);padding:1.5rem;text-align:center;margin-top:1.5rem;">
  <h3 style="color:var(--text);margin:0 0 8px;font-size:1.3rem;">🎉 Pedido {id_pedido} confirmado</h3>
  <p style="color:var(--text3);margin-bottom:1.25rem;font-size:0.9rem;">Se está abriendo WhatsApp con los datos del pedido...</p>
  <a href="{ws_url}" target="_blank" class="btn-pay-ws" style="max-width:320px;margin:0 auto;justify-content:center;">
    📲 ENVIAR PEDIDO POR WHATSAPP
  </a>
</div>""", unsafe_allow_html=True)
                    st_components.html(f"""<!DOCTYPE html><html><body style="margin:0;background:transparent;">
<a href="{ws_url}" target="_top" id="wsauto" style="opacity:0;position:absolute;">WA</a>
<script>setTimeout(function(){{ document.getElementById('wsauto').click(); }}, 1500);</script>
</body></html>""", height=1)
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# VISTA CATÁLOGO (Default)
# ══════════════════════════════════════════════════════════════════════════════

# Cart added banner
if st.session_state.get("mostrar_banner_carrito"):
    st.markdown('<div class="cart-added-banner">✅ ¡Producto agregado al carrito!</div>', unsafe_allow_html=True)
    st.session_state.mostrar_banner_carrito = False

if df_stock.empty:
    st.warning("No se pudieron cargar los datos de Google Sheets.")
    st.stop()

# ── HERO ──────────────────────────────────────────────────────────────────────
_ws_hero = f"https://wa.me/{NUMERO_WS}?text={urllib.parse.quote('Hola BEJO! Tengo una consulta 😊')}"
st.markdown(f"""
<div class="bejo-hero">
  <div class="hero-eyebrow">⚡ San Miguel de Tucumán · Envíos</div>
  <div class="hero-title">Todo para tu celu: lo nuevo, lo clásico y lo que ya no encontrás.</div>
  <div class="hero-subtitle">Variedad en fundas, cargadores y accesorios alternativos de calidad para todos los modelos a precios increíbles. ¡Llevá más, pagá menos! Armá tu combo, comprá en un clic y coordiná el envío.</div>
  <div class="hero-cta-group">
    <a href="#catalogo" class="hero-btn hero-btn-primary">🛍️ Ver Catálogo</a>
    <a href="{_ws_hero}" target="_blank" class="hero-btn hero-btn-secondary">💬 Consultar</a>
  </div>
</div>""", unsafe_allow_html=True)

# ── FILTERS ───────────────────────────────────────────────────────────────────
if "filtro_tipo_val" not in st.session_state:
    st.session_state.filtro_tipo_val = "Todos"
if "filtro_marca_val" not in st.session_state:
    st.session_state.filtro_marca_val = "Todas"

# Sync from query params
if "tipo_filtro" in st.query_params:
    st.session_state.filtro_tipo_val = st.query_params["tipo_filtro"]
    del st.query_params["tipo_filtro"]
if "marca_filtro" in st.query_params:
    st.session_state.filtro_marca_val = st.query_params["marca_filtro"]
    del st.query_params["marca_filtro"]

st.markdown('<div id="catalogo">', unsafe_allow_html=True)
st.markdown("""
<div class="filter-wrap">
  <div class="filter-label">🔍 Buscá tu accesorio</div>
</div>""", unsafe_allow_html=True)

cf1, cf2, cf3, cf4 = st.columns(4)

with cf1:
    tipos = ["Todos"] + sorted([t for t in df_stock["Nombre del Artículo"].dropna().unique() if str(t).strip()])
    try:
        tipo_idx = tipos.index(st.session_state.filtro_tipo_val)
    except ValueError:
        tipo_idx = 0
        st.session_state.filtro_tipo_val = "Todos"
    tipo_sel = st.selectbox("Categoría:", tipos, index=tipo_idx, key="sel_tipo")
    st.session_state.filtro_tipo_val = tipo_sel

df_fil = df_stock if tipo_sel == "Todos" else df_stock[df_stock["Nombre del Artículo"] == tipo_sel]

with cf2:
    marcas = ["Todas"] + sorted([m for m in df_fil["Marca Principal"].dropna().unique() if str(m).strip()])
    if st.session_state.filtro_marca_val not in marcas:
        st.session_state.filtro_marca_val = "Todas"
    try:
        marca_idx = marcas.index(st.session_state.filtro_marca_val)
    except ValueError:
        marca_idx = 0
        st.session_state.filtro_marca_val = "Todas"
    marca_sel = st.selectbox("Marca:", marcas, index=marca_idx, key="sel_marca")
    st.session_state.filtro_marca_val = marca_sel

df_fil = df_fil if marca_sel == "Todas" else df_fil[df_fil["Marca Principal"] == marca_sel]

with cf3:
    modelos = ["Todos"] + sorted([m for m in df_fil["Modelo Exacto"].dropna().unique() if str(m).strip()])
    modelo_sel = st.selectbox("Modelo:", modelos, key="sel_modelo")
df_fil = df_fil if modelo_sel == "Todos" else df_fil[df_fil["Modelo Exacto"] == modelo_sel]

with cf4:
    disenos = ["Todos"] + sorted([d for d in df_fil["Color / Diseño (Variación)"].dropna().unique() if str(d).strip()])
    diseno_sel = st.selectbox("Color / Diseño:", disenos, key="sel_diseno")
df_fil = df_fil if diseno_sel == "Todos" else df_fil[df_fil["Color / Diseño (Variación)"] == diseno_sel]

st.markdown('</div>', unsafe_allow_html=True)

# ── OFERTAS DESTACADAS (solo en home sin filtros) ─────────────────────────────
if tipo_sel == "Todos" and marca_sel == "Todas" and modelo_sel == "Todos" and diseno_sel == "Todos":
    df_of_home = df_stock[df_stock["En Oferta"] == True]
    if not df_of_home.empty:
        st.markdown("""
<div class="section-header" style="margin-top:0;">
  <h2 class="section-title">🔥 Ofertas Destacadas</h2>
  <span class="section-subtitle">Precios especiales por tiempo limitado</span>
</div>""", unsafe_allow_html=True)
        of_home_items = df_of_home.reset_index().head(3).to_dict('records')
        cols_of = st.columns(3)
        for o_idx, o_item in enumerate(of_home_items):
            orig_o_idx = o_item.get('index', o_idx)
            o_img = o_item["Imagen_URL"] if str(o_item["Imagen_URL"]).strip() else "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500"
            if o_item["Cantidad"] <= 0:
                cta_home = '<span class="btn-add-cart-disabled">Sin Stock</span>'
            else:
                cta_home = f'<a class="btn-add-cart" href="?add_cart={orig_o_idx}" target="_self" style="background:var(--offer);">🛒 Agregar Oferta</a>'
            with cols_of[o_idx]:
                st.markdown(f"""
<div class="offer-home-card">
  <div style="position:relative;aspect-ratio:4/3;overflow:hidden;background:var(--surface2);">
    <img src="{o_img}" style="width:100%;height:100%;object-fit:cover;" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500'">
    <span class="badge-offer">🔥 OFERTA</span>
  </div>
  <div style="padding:12px 14px 14px;">
    <div style="font-size:0.7rem;font-weight:700;letter-spacing:1.2px;text-transform:uppercase;color:var(--offer);margin-bottom:3px;">{o_item['Marca Principal']}</div>
    <div style="font-size:0.9rem;font-weight:700;color:var(--text);">{o_item['Nombre del Artículo']} {o_item['Modelo Exacto']}</div>
    <div style="font-size:0.78rem;color:var(--text3);margin:3px 0 8px;">🎨 {o_item['Color / Diseño (Variación)']}</div>
    <div style="font-size:1.15rem;font-weight:900;color:var(--text);margin-bottom:8px;">${o_item['Precio Mercado']:,.0f}</div>
    {cta_home}
  </div>
</div>""", unsafe_allow_html=True)
        st.markdown("---")

# ── PRODUCT GRID ──────────────────────────────────────────────────────────────
filter_key = f"{tipo_sel}_{marca_sel}_{modelo_sel}_{diseno_sel}"
if st.session_state.get("last_filter_key") != filter_key:
    st.session_state.catalog_page = 1
    st.session_state.last_filter_key = filter_key

if df_fil.empty:
    st.markdown("""
<div style="background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-md);padding:3rem;text-align:center;box-shadow:var(--shadow-sm);">
  <div style="font-size:2.5rem;margin-bottom:1rem;">🔍</div>
  <div style="font-size:1rem;font-weight:600;color:var(--text2);">No hay productos para los filtros seleccionados.</div>
</div>""", unsafe_allow_html=True)
else:
    PLACEHOLDER_IMG = "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500"

    def safe_img(url):
        if pd.isna(url) or str(url).strip() == "":
            return PLACEHOLDER_IMG
        return str(url).strip()

    group_keys = df_fil[["Nombre del Artículo","Marca Principal","Modelo Exacto"]].drop_duplicates()
    grouped_list = []
    for _, gk in group_keys.iterrows():
        mask = (
            (df_fil["Nombre del Artículo"] == gk["Nombre del Artículo"]) &
            (df_fil["Marca Principal"]      == gk["Marca Principal"]) &
            (df_fil["Modelo Exacto"]        == gk["Modelo Exacto"])
        )
        grouped_list.append(df_fil[mask])

    items_per_page = 9
    total_pages    = max(1, (len(grouped_list) + items_per_page - 1) // items_per_page)
    if st.session_state.get("catalog_page", 1) > total_pages:
        st.session_state.catalog_page = 1
    curr_page   = st.session_state.get("catalog_page", 1)
    start_idx   = (curr_page - 1) * items_per_page
    page_groups = grouped_list[start_idx:start_idx + items_per_page]

    # Section header
    _total_prods = len(grouped_list)
    st.markdown(f"""
<div class="section-header">
  <h2 class="section-title">📱 Catálogo</h2>
  <span class="section-subtitle">{_total_prods} producto{"s" if _total_prods != 1 else ""} encontrado{"s" if _total_prods != 1 else ""}</span>
</div>""", unsafe_allow_html=True)

    # ── CARD RENDERING ────────────────────────────────────────────────────────
    for g_idx in range(0, len(page_groups), 3):
        cols = st.columns(3)
        for col_idx in range(3):
            gi = g_idx + col_idx
            if gi >= len(page_groups):
                break
            grupo_df = page_groups[gi]
            first    = grupo_df.iloc[0]
            nombre_c = f"{first['Nombre del Artículo']} {first['Modelo Exacto']}"
            marca_c  = first["Marca Principal"]
            cid = f"c{start_idx + gi}"

            variantes = []
            for vi_idx, (vi_row_i, vi_row) in enumerate(grupo_df.iterrows()):
                variantes.append({
                    "idx":    vi_row_i,
                    "color":  vi_row["Color / Diseño (Variación)"],
                    "precio": vi_row["Precio Mercado"],
                    "stock":  vi_row["Cantidad"],
                    "img":    safe_img(vi_row["Imagen_URL"]),
                    "oferta": vi_row.get("En Oferta", False),
                    "vi":     vi_idx,
                })

            n_var = len(variantes)

            # Radio inputs for carousel
            radios = "".join(
                f'<input type="radio" name="{cid}" id="{cid}s{i}" {"checked" if i == 0 else ""}>'
                for i in range(n_var)
            )
            # Zoom checkboxes
            zoom_cbs = "".join(
                f'<input type="checkbox" id="z{cid}s{i}" class="zoom-cb">'
                for i in range(n_var)
            )

            # Slides
            slides_items = []
            for i, v in enumerate(variantes):
                prev_i = (i - 1 + n_var) % n_var
                next_i = (i + 1) % n_var
                nav = (
                    f'<label class="cprev" for="{cid}s{prev_i}">&#8249;</label>'
                    f'<label class="cnext" for="{cid}s{next_i}">&#8250;</label>'
                ) if n_var > 1 else ""

                # Stock badge
                if v["stock"] <= 0:
                    stock_badge = '<span class="badge-stock badge-stock-out">● Sin stock</span>'
                elif v["stock"] <= 3:
                    stock_badge = f'<span class="badge-stock badge-stock-low">⚡ ¡Últimas {v["stock"]} unidades!</span>'
                else:
                    stock_badge = '<span class="badge-stock badge-stock-ok">● Stock disponible</span>'

                offer_badge = '<span class="badge-offer">🔥 OFERTA</span>' if v.get("oferta") else ""

                # CTA button
                if v["stock"] <= 0:
                    cta_html = '<span class="btn-add-cart-disabled">Sin Stock Momentáneo</span>'
                else:
                    cta_html = f'<a class="btn-add-cart" href="?add_cart={v["idx"]}" target="_self">AGREGAR AL CARRITO</a>'

                slide_info = (
                    f'<div class="slide-data">'
                    f'<div class="slide-variant">🎨 {v["color"]}</div>'
                    f'<div class="slide-price">${v["precio"]:,.0f}</div>'
                    f'{stock_badge}'
                    f'{cta_html}'
                    f'</div>'
                )
                img_wrap = (
                    f'<label for="z{cid}s{i}" class="slide-img-wrap">'
                    f'{offer_badge}'
                    f'<img src="{v["img"]}" alt="{v["color"]}" loading="lazy" '
                    f'onerror="this.src=\'{PLACEHOLDER_IMG}\'">'
                    f'<span class="zoom-hint">🔍</span>'
                    f'</label>'
                )
                slides_items.append(f'<li>{img_wrap}{nav}{slide_info}</li>')

            slides_ul = f'<ul class="card-slides">{"".join(slides_items)}</ul>'

            # Dots
            if n_var > 1:
                dots_ol = '<ol class="cdots">' + "".join(
                    f'<li><label for="{cid}s{i}"></label></li>' for i in range(n_var)
                ) + '</ol>'
            else:
                dots_ol = ""

            # Zoom overlays
            zoom_ovs = "".join(
                f'<label for="z{cid}s{i}" class="zoom-ov" id="zo{cid}s{i}">'
                f'<img src="{v["img"]}" alt="{v["color"]}">'
                f'<span class="zoom-close">✕ Tocá para cerrar</span>'
                f'</label>'
                for i, v in enumerate(variantes)
            )

            # Per-carousel CSS
            show_rules = "".join(
                f'#{cid}s{i}:checked~.card-slides>li:nth-child({i+1})'
                f'{{position:relative!important;width:100%!important;visibility:visible!important;opacity:1!important;pointer-events:auto!important}}'
                f'#{cid}s{i}:checked~.card-slides>li:nth-child({i+1}) .cprev'
                f'{{visibility:visible!important;opacity:1!important;pointer-events:auto!important}}'
                f'#{cid}s{i}:checked~.card-slides>li:nth-child({i+1}) .cnext'
                f'{{visibility:visible!important;opacity:1!important;pointer-events:auto!important}}'
                f'#{cid}s{i}:checked~.cdots>li:nth-child({i+1})>label'
                f'{{background:var(--accent)!important;transform:scale(1.3);}}'
                for i in range(n_var)
            )
            zoom_rules = "".join(
                f'#z{cid}s{i}:checked~#zo{cid}s{i}{{display:flex}}'
                for i in range(n_var)
            )

            card_html = f"""
<div class="tech-card" onclick="event.stopPropagation()">
<style>{show_rules}{zoom_rules}</style>
<div class="card-topline">
  <div class="card-brand-tag">{marca_c}</div>
  <div class="card-name">{nombre_c}</div>
</div>
{radios}{zoom_cbs}
{slides_ul}
{dots_ol}
{zoom_ovs}
</div>"""

            with cols[col_idx]:
                st.markdown(card_html, unsafe_allow_html=True)

    # ── PAGINATION ────────────────────────────────────────────────────────────
    if total_pages > 1:
        st.markdown("<br>", unsafe_allow_html=True)
        p_col1, p_col2, p_col3 = st.columns([1, 2, 1])
        with p_col1:
            if st.button("← Anterior", disabled=(curr_page == 1),
                         use_container_width=True, key="cat_prev_page"):
                st.session_state.catalog_page -= 1; st.rerun()
        with p_col2:
            st.markdown(f"<p style='text-align:center;font-weight:600;font-size:0.9rem;color:var(--text2);padding:8px 0;'>Página {curr_page} de {total_pages}</p>",
                        unsafe_allow_html=True)
        with p_col3:
            if st.button("Siguiente →", disabled=(curr_page == total_pages),
                         use_container_width=True, key="cat_next_page"):
                st.session_state.catalog_page += 1; st.rerun()

# ── CHECKOUT CTA (bottom) ─────────────────────────────────────────────────────
if st.session_state.carrito:
    st.markdown("---")
    num_items = sum(st.session_state.carrito.values())
    if st.button(f"🛒 FINALIZAR COMPRA — {num_items} producto(s) →",
                 type="primary", use_container_width=True, key="btn_go_cart_bottom"):
        st.session_state.vista = "carrito"; st.rerun()

# ── WHATSAPP CTA BAR ──────────────────────────────────────────────────────────
_ws_cta_url = f"https://wa.me/{NUMERO_WS}?text={urllib.parse.quote('Hola BEJO! Tengo una consulta antes de comprar...')}"
st.markdown(f"""
<div class="wa-cta-bar">
  <span class="wa-cta-text">💬 ¿Tenés dudas antes de comprar? Escribinos sin compromiso.</span>
  <a href="{_ws_cta_url}" target="_blank" class="wa-btn">
    Consultar por WhatsApp 📲
  </a>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PANEL ADMINISTRADOR
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")

if not st.session_state.admin_autenticado:
    st.markdown("""
<style>
div[data-testid="stExpander"] { opacity: 0.02 !important; transition: opacity 0.3s !important; }
div[data-testid="stExpander"]:hover,
div[data-testid="stExpander"]:focus-within { opacity: 1.0 !important; }
div[data-testid="stExpander"] div[data-testid="stExpander"] { opacity: 1.0 !important; }
</style>""", unsafe_allow_html=True)

with st.expander("⚙️ Panel de Control – Solo Administrador"):
    if not st.session_state.admin_autenticado:
        st.markdown("🔐 **Ingresá la clave de administrador:**")
        kc, kb = st.columns([3, 1])
        clave_ing = kc.text_input("Clave:", type="password", placeholder="Contraseña...", label_visibility="collapsed")
        if kb.button("Entrar 🔓"):
            if clave_ing == CLAVE_ADMIN:
                st.session_state.admin_autenticado = True; st.rerun()
            else:
                st.markdown('<div class="error-box">❌ Clave incorrecta.</div>', unsafe_allow_html=True)
    else:
        col_tit, col_out = st.columns([4, 1])
        col_tit.markdown("### 🛠️ Panel BEJO · Administración")

        has_mp = obtener_access_token_mp() is not None
        if has_mp:
            st.success("🟢 **Mercado Pago:** Configurado correctamente.")
        else:
            st.error("🔴 **Mercado Pago:** No se detectó el Access Token. Agregá `MERCADOPAGO_ACCESS_TOKEN` en los Secretos de Streamlit.")

        if col_out.button("Salir 🔒"):
            st.session_state.admin_autenticado = False
            st.session_state.admin_modo = None
            st.session_state.admin_idx_sel = None
            st.rerun()

        if df_stock.empty:
            st.warning("No hay datos cargados de Google Sheets.")
        else:
            dc1, dc2 = st.columns(2)
            with dc1:
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

            if not df_pedidos_all.empty:
                with st.expander("📦 Gestionar Estados de Pedidos"):
                    pedidos_list = df_pedidos_all["ID Pedido"].tolist()[::-1]
                    ped_sel = st.selectbox("Seleccioná un Pedido:", pedidos_list, key="adm_ped_sel")
                    if ped_sel:
                        ped_row = df_pedidos_all[df_pedidos_all["ID Pedido"] == ped_sel].iloc[0]
                        st.markdown(f"📅 **Fecha:** {ped_row['Fecha']}")
                        st.markdown(f"💰 **Total:** ${float(ped_row['Total']):,.0f}")
                        st.markdown(f"👤 **Cliente/Contacto:** {ped_row['Cliente / Contacto']}")
                        st.markdown(f"📌 **Estado actual:** `{ped_row['Estado']}`")
                        with st.expander("📝 Ver Mensaje Completo WS"):
                            st.text(ped_row["Detalle Pedido WS"])
                        estados_posibles = ["Pendiente", "Entregado", "Rechazado", "Cancelado"]
                        idx_est_actual = estados_posibles.index(ped_row["Estado"]) if ped_row["Estado"] in estados_posibles else 0
                        nuevo_est = st.selectbox("Cambiar Estado a:", estados_posibles, index=idx_est_actual, key="adm_nuevo_est")
                        if st.button("💾 Actualizar Estado", type="primary", use_container_width=True):
                            if actualizar_estado_pedido(ped_sel, nuevo_est, df_pedidos_all):
                                st.success(f"✅ Estado del pedido {ped_sel} actualizado a '{nuevo_est}'.")
                                time.sleep(1); st.rerun()

            st.markdown("---")
            # ── FILTROS CASCADA ──
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

            filtros_activos = (t_a != "(Todos)" or m_a != "(Todas)" or mo_a != "(Todos)" or co_a != "(Todos)")

            if not filtros_activos:
                st.info("👆 Seleccioná al menos un filtro para buscar un producto.")
            elif df_a.empty:
                st.markdown("""<div class="info-box info-box-blue">🔎 <b>No se encontró ningún producto con esos filtros.</b><br>¿Querés agregarlo al catálogo?</div>""", unsafe_allow_html=True)
                if st.button("➕ Sí, agregar este producto nuevo", type="primary", key="btn_ir_nuevo"):
                    st.session_state.admin_modo = "nuevo"
            else:
                st.markdown(f"✅ **{len(df_a)} producto(s) encontrado(s):**")
                for i_row, r_row in df_a.iterrows():
                    tag = (f'<span class="admin-badge-stock">Stock: {r_row["Cantidad"]}</span>'
                           if r_row["Cantidad"] > 0
                           else '<span class="admin-badge-nostock">Sin stock</span>')
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

            st.markdown("")
            if st.button("➕ Agregar producto nuevo", key="btn_nuevo_siempre"):
                st.session_state.admin_modo    = "nuevo"
                st.session_state.admin_idx_sel = None

            st.markdown("---")

            # ── MODO EDITAR ──────────────────────────────────────────────────
            if st.session_state.admin_modo == "editar" and st.session_state.admin_idx_sel is not None:
                idx_e = st.session_state.admin_idx_sel
                prod  = df_stock.loc[idx_e]
                st.markdown(f"""<div class="info-box info-box-blue">
                    ✏️ <b>Editando:</b> {prod['Nombre del Artículo']} {prod['Modelo Exacto']} – {prod['Color / Diseño (Variación)']}
                </div>""", unsafe_allow_html=True)
                col_foto_act, col_info_act = st.columns([1, 2])
                with col_foto_act:
                    mostrar_imagen(prod["Imagen_URL"], caption="Foto actual", use_container_width=True)
                with col_info_act:
                    st.markdown(f"**Marca:** {prod['Marca Principal']}")
                    st.markdown(f"**Modelo:** {prod['Modelo Exacto']}")
                    st.markdown(f"**Color:** {prod['Color / Diseño (Variación)']}")
                    tag_s = (f'<span class="admin-badge-stock">Stock: {prod["Cantidad"]}</span>'
                             if prod["Cantidad"] > 0
                             else '<span class="admin-badge-nostock">Sin stock</span>')
                    st.markdown(tag_s, unsafe_allow_html=True)
                    st.markdown(f"**Precio:** ${prod['Precio Mercado']:,.0f}")

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
                foto_col1, foto_col2 = st.columns(2)
                with foto_col1:
                    archivo_foto = st.file_uploader("📷 Subir imagen (jpg, png, webp):",
                                                    type=["jpg","jpeg","png","webp"], key="e_foto_file")
                with foto_col2:
                    e_url_imgur = st.text_input("O pegá link de Imgur:", placeholder="https://i.imgur.com/...",
                                                value="", key="e_url_imgur")

                if archivo_foto is not None:
                    st.markdown("**Vista previa:**")
                    st.image(archivo_foto, width=200)

                be1, be2 = st.columns([3, 1])
                if be1.button("💾 Guardar todos los cambios", key="btn_guardar_editar", type="primary"):
                    try:
                        sheet      = get_sheet()
                        fila_sheet = idx_e + 5
                        nueva_url_foto = str(prod["Imagen_URL"])
                        if archivo_foto is not None:
                            data_url = imagen_a_base64(archivo_foto)
                            if data_url:
                                nueva_url_foto = data_url
                            else:
                                st.warning("⚠️ Instalá Pillow: `pip install Pillow`")
                        elif e_url_imgur.strip():
                            nueva_url_foto = e_url_imgur.strip()
                        nuevo_stock = int(prod["Cantidad"]) + int(e_sumar)
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
                    st.session_state.admin_modo = None; st.rerun()

            # ── MODO NUEVO ───────────────────────────────────────────────────
            elif st.session_state.admin_modo == "nuevo":
                st.markdown("""<div class="info-box info-box-blue">
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
                    fn1, fn2 = st.columns(2)
                    with fn1:
                        n_foto_file = st.file_uploader("📷 Subir imagen (jpg, png, webp):",
                                                       type=["jpg","jpeg","png","webp"], key="n_foto_file")
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
                            url_foto_nueva = ""
                            if n_foto_file is not None:
                                data_url = imagen_a_base64(n_foto_file)
                                url_foto_nueva = data_url or ""
                            elif n_url_imgur.strip():
                                url_foto_nueva = n_url_imgur.strip()
                            sheet = get_sheet()
                            sheet.append_row([
                                n_marca.strip(), n_nombre.strip(), n_modelo.strip(),
                                n_color.strip(), str(n_precio), "", str(n_cantidad), url_foto_nueva
                            ])
                            st.success(f"✅ ¡Producto **{n_nombre}** agregado al catálogo!")
                            st.cache_data.clear()
                            st.session_state.admin_modo = None
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al guardar: {e}")

                if st.button("❌ Cancelar", key="btn_cancel_nuevo"):
                    st.session_state.admin_modo = None; st.rerun()

            # ── ELIMINAR ─────────────────────────────────────────────────────
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
                            sheet  = get_sheet()
                            fila_s = idx_elim + 5
                            sheet.delete_rows(fila_s)
                            st.success("✅ Producto eliminado.")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"No se pudo eliminar: {e}")

# ── FLOATING BARGAIN BUTTON (REGATEO) ──
msg_regateo = """¡Hola BEJO! ⚡ Quiero negociar un precio.

👉 ¿Qué buscás?: [Escribir si es Funda, Cargador, Hidrogel, etc.]
📱 Modelo: [Escribir qué celular, ej: Galaxy S20]
📦 Cantidad: [Escribir cuántas unidades]
💰 Mi Oferta es: $ [Poner precio total ofertado]

¿Hacemos trato? 🤝"""

url_regateo = f"https://wa.me/{NUMERO_WS}?text={urllib.parse.quote(msg_regateo)}"

st.markdown(f"""
<style>
.floating-bargain-btn {{
    position: fixed;
    bottom: 85px;
    right: 20px;
    z-index: 9999;
    background: linear-gradient(135deg, #FF9F0A 0%, #FF3B30 100%);
    box-shadow: 0 8px 30px rgba(255, 59, 48, 0.35);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 9999px;
    padding: 12px 18px;
    color: white !important;
    text-decoration: none !important;
    font-size: 14px;
    font-weight: 900;
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    font-family: sans-serif;
}}

.floating-bargain-btn:hover {{
    transform: scale(1.08) translateY(-3px);
    box-shadow: 0 12px 35px rgba(255, 59, 48, 0.45);
    background: linear-gradient(135deg, #ffa826 0%, #ff4b40 100%);
}}

.floating-bargain-btn:active {{
    transform: scale(0.95) translateY(0);
}}

@keyframes shakePulse {{
    0%, 100% {{
        transform: scale(1);
    }}
    5%, 15% {{
        transform: scale(1.06) rotate(-3deg);
    }}
    10%, 20% {{
        transform: scale(1.06) rotate(3deg);
    }}
    25% {{
        transform: scale(1.06) rotate(0deg);
    }}
    30%, 90% {{
        transform: scale(1);
    }}
}}

.shake-pulse-animation {{
    animation: shakePulse 5s infinite ease-in-out;
}}
</style>
<a href="{url_regateo}" target="_blank" class="floating-bargain-btn shake-pulse-animation">
    ¡Hacé tu Oferta! 🌟
</a>
""", unsafe_allow_html=True)
