// BEJO Accesorios – Client Side Logic (ES6)

let productsState = [];
let compatState = [];
let cartState = {}; // { index: qty }
let comboDetailsObj = JSON.parse(localStorage.getItem("bejo_comboDetails") || "{}");
let adminAuthenticated = false;
let adminToken = "";
let activeMainTab = "catalog"; // "catalog", "offers", "wholesale"
let currentPage = 1;
const itemsPerPage = 12;

// Image normalization utilities
function splitImageUrls(imagen_url) {
    if (!imagen_url || imagen_url.trim() === "") {
        return ["https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500"];
    }
    const parts = imagen_url.split(/[\n,]+/);
    const urls = [];
    for (let i = 0; i < parts.length; i++) {
        let part = parts[i].trim();
        if (part.startsWith("data:image/") && i + 1 < parts.length) {
            part = part + "," + parts[i + 1].trim();
            i++;
        }
        if (part !== "") {
            urls.push(part);
        }
    }
    if (urls.length === 0) {
        return ["https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500"];
    }
    return urls;
}

function normalizeImageUrl(url) {
    if (!url) return "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500";
    let clean = url.trim();
    if (clean === "") return "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500";
    
    const isBase64Prefix = clean.startsWith("data:image/");
    const seemsBase64 = !clean.startsWith("http://") && !clean.startsWith("https://") && !clean.startsWith("/") && !clean.startsWith("./");
    
    if (isBase64Prefix || seemsBase64) {
        if (isBase64Prefix) {
            const parts = clean.split(",");
            if (parts.length > 1) {
                const prefix = parts[0];
                const base64Data = parts.slice(1).join(",").replace(/\s+/g, "");
                return `${prefix},${base64Data}`;
            }
        }
        const stripped = clean.replace(/\s+/g, "");
        let mime = "image/jpeg";
        if (stripped.startsWith("iVBORw0KGgo")) {
            mime = "image/png";
        } else if (stripped.startsWith("R0lGOD")) {
            mime = "image/gif";
        } else if (stripped.startsWith("UklGR")) {
            mime = "image/webp";
        }
        return `data:${mime};base64,${stripped}`;
    }
    return clean;
}

// ── DOM ELEMENTS ──
const searchInput = document.getElementById("searchInput");
const searchInputMobile = document.getElementById("searchInputMobile");
const filterTipo = document.getElementById("filterTipo");
const filterSearch = document.getElementById("filterSearch");
const clearFiltersBtn = document.getElementById("clearFiltersBtn");
const emptyCatalogState = document.getElementById("emptyCatalogState");
const productosGrid = document.getElementById("productosGrid");
const resultsCount = document.getElementById("resultsCount");
const ofertasSection = document.getElementById("ofertasSection");
const ofertasGrid = document.getElementById("ofertasGrid");

// Compat widget
const compatResults = document.getElementById("compatResults");

// Cart Drawer
const cartBtn = document.getElementById("cartBtn");
const closeCartBtn = document.getElementById("closeCartBtn");
const cartDrawer = document.getElementById("cartDrawer");
const cartDrawerOverlay = document.getElementById("cartDrawerOverlay");
const cartItemsContainer = document.getElementById("cartItemsContainer");
const cartEmptyState = document.getElementById("cartEmptyState");
const cartFooter = document.getElementById("cartFooter");
const cartTotalSum = document.getElementById("cartTotalSum");
const cartCount = document.getElementById("cartCount");

// Checkout Modal
const checkoutBtn = document.getElementById("checkoutBtn");
const checkoutModal = document.getElementById("checkoutModal");
const closeCheckoutBtn = document.getElementById("closeCheckoutBtn");
const confirmOrderBtn = document.getElementById("confirmOrderBtn");
const checkoutTotal = document.getElementById("checkoutTotal");

// Delivery & Payment
const deliveryMethods = document.getElementsByName("deliveryMethod");
const deliveryDetails = document.getElementById("deliveryDetails");
const devCalle = document.getElementById("devCalle");
const devBarrio = document.getElementById("devBarrio");
const devLocalidad = document.getElementById("devLocalidad");
const devTelefono = document.getElementById("devTelefono");
const devObservacion = document.getElementById("devObservacion");
const paymentMethods = document.getElementsByName("paymentMethod");

// Success Modal
const successModal = document.getElementById("successModal");
const successOrderId = document.getElementById("successOrderId");
const successMPBtn = document.getElementById("successMPBtn");
const successWSBtn = document.getElementById("successWSBtn");
const successCloseBtn = document.getElementById("successCloseBtn");

// Admin Login & Panel
const adminLoginBtn = document.getElementById("adminLoginBtn");
const adminFooterLink = document.getElementById("adminFooterLink");
const adminLoginModal = document.getElementById("adminLoginModal");
const adminPasswordInput = document.getElementById("adminPasswordInput");
const adminLoginCancelBtn = document.getElementById("adminLoginCancelBtn");
const adminLoginSubmitBtn = document.getElementById("adminLoginSubmitBtn");
const adminPanel = document.getElementById("adminPanel");
const adminCloseBtn = document.getElementById("adminCloseBtn");
const adminDownloadInventario = document.getElementById("adminDownloadInventario");
const adminDownloadPedidos = document.getElementById("adminDownloadPedidos");

// Admin Tabs
const tabPedidosBtn = document.getElementById("tabPedidosBtn");
const tabProductosBtn = document.getElementById("tabProductosBtn");
const panelPedidos = document.getElementById("panelPedidos");
const panelProductos = document.getElementById("panelProductos");
const adminPedidosTableBody = document.getElementById("adminPedidosTableBody");
const adminProductosTableBody = document.getElementById("adminProductosTableBody");
const adminNewProdBtn = document.getElementById("adminNewProdBtn");

// Admin Edit modal
const productEditModal = document.getElementById("productEditModal");
const productEditModalTitle = document.getElementById("productEditModalTitle");
const productEditModalClose = document.getElementById("productEditModalClose");
const productEditForm = document.getElementById("productEditForm");
const productEditCancelBtn = document.getElementById("productEditCancelBtn");

// Toast Container
const toastContainer = document.getElementById("toastContainer");

// ── INITIALIZATION
document.addEventListener("DOMContentLoaded", init);

// ── COMBO LOGIC ─────────────────────────────────────────────────────────────

let comboConfig = { precio: 0, cantidad: 10 };
let comboProducts = [];
let comboSelections = {};
let comboTotalSelected = 0;

async function fetchComboData() {
    try {
        const confRes = await fetch("/api/combo-config");
        comboConfig = await confRes.json();
        document.getElementById("comboSubtitle").innerText = `Elige ${comboConfig.cantidad} productos por $${comboConfig.precio.toLocaleString('es-AR')}`;
        document.getElementById("comboCounter").innerText = `0 / ${comboConfig.cantidad}`;
        
        const prodRes = await fetch("/api/productos-combo");
        comboProducts = await prodRes.json();
        
        renderCatalog();
    } catch (e) {
        console.error("Error fetching combo data:", e);
        document.getElementById("comboSubtitle").innerText = "Error cargando combo. Intenta más tarde.";
    }
}



window.changeComboQty = function(index, offset) {
    const currentQty = comboSelections[index] || 0;
    const newQty = currentQty + offset;
    
    if (newQty < 0) return;
    
    const prod = comboProducts.find(p => p.index === index);
    if (!prod) return;
    
    if (offset > 0) {
        if (comboTotalSelected >= comboConfig.cantidad) {
            showToast(`⚠️ Ya elegiste los ${comboConfig.cantidad} productos`, "warning");
            return;
        }
        if (newQty > prod.cantidad) {
            showToast(`⚠️ Solo hay ${prod.cantidad} en stock`, "warning");
            return;
        }
    }
    
    comboSelections[index] = newQty;
    comboTotalSelected += offset;
    
    document.getElementById(`combo-qty-${index}`).innerText = newQty;
    document.getElementById("comboCounter").innerText = `${comboTotalSelected} / ${comboConfig.cantidad}`;
    
    const btn = document.getElementById("addComboBtn");
    if (comboTotalSelected === comboConfig.cantidad) {
        btn.classList.remove("bg-black/[0.06]", "text-textMuted", "cursor-not-allowed");
        btn.classList.add("bg-accentBlue", "text-white", "hover:bg-accentBlueHover", "shadow-md");
    } else {
        btn.classList.add("bg-black/[0.06]", "text-textMuted");
        btn.classList.remove("bg-accentBlue", "text-white", "hover:bg-accentBlueHover", "shadow-md");
    }
};

const addComboBtnEl = document.getElementById("addComboBtn");
if(addComboBtnEl) {
    addComboBtnEl.addEventListener("click", () => {
        if (comboTotalSelected !== comboConfig.cantidad) {
            const faltan = comboConfig.cantidad - comboTotalSelected;
            showToast(`⚠️ Faltan elegir ${faltan} producto${faltan > 1 ? 's' : ''} para completar el combo.`, "warning");
            return;
        }
        
        const comboId = "combo_" + Date.now();
        let items = [];
        let itemNames = [];
        
        for (let k in comboSelections) {
            let qty = comboSelections[k];
            let p = comboProducts.find(x => x.index == parseInt(k));
            for (let i = 0; i < qty; i++) {
                items.push(p.index);
                itemNames.push(`${p.nombre} ${p.marca} ${p.modelo} (${p.color || 'Estándar'})`);
            }
        }
        
        comboDetailsObj[comboId] = {
            precio: comboConfig.precio,
            items: items,
            itemNames: itemNames
        };
        
        localStorage.setItem("bejo_comboDetails", JSON.stringify(comboDetailsObj));
        
        cartState[comboId] = 1;
        saveCartToLocalStorage();
        updateCartCount();
        renderCartItems();
        
        // Reset combo state
        comboSelections = {};
        comboTotalSelected = 0;
        renderCatalog(); // Reset all to 0 visually
        document.getElementById("comboCounter").innerText = `0 / ${comboConfig.cantidad}`;
        const btn = document.getElementById("addComboBtn");
        btn.classList.add("bg-black/[0.06]", "text-textMuted");
        btn.classList.remove("bg-accentBlue", "text-white", "hover:bg-accentBlueHover", "shadow-md");
        
        showToast("✅ ¡Combo agregado al carrito!", "success");
        setTimeout(() => {
            openCartDrawer();
        }, 50);
    });
}

function init() {
    loadCartFromLocalStorage();
    fetchData();
    setupEventListeners();
}
// ── DATA FETCHING ──
async function fetchData() {
    try {
        // Fetch products catalog
        const resProd = await fetch("/api/productos");
        productsState = await resProd.json();
        
        // Fetch compatibility data
        const resCompat = await fetch("/api/compatibilidad");
        compatState = await resCompat.json();
        
        populateFilters();
        populateCompatFilters();
        populateAdminFilters();
        renderCatalog();
        updateCartCount();
    } catch (err) {
        console.error("Error fetching data:", err);
        showToast("⚠️ Error al conectar con el servidor.", "error");
    }
}

// Populate dropdown filters based on products catalog
function populateFilters() {
    const tipos = new Set(["Todos"]);
    const marcas = new Set(["Todas"]);
    
    productsState.forEach(p => {
        if (p.nombre) tipos.add(p.nombre);
    });
    
    filterTipo.innerHTML = "";
    const sortedTipos = [...tipos].filter(t => t !== "Todos").sort();
    ["Todos", ...sortedTipos].forEach(t => {
        const opt = document.createElement("option");
        opt.value = t;
        opt.textContent = t === "Todos" ? "Todos" : t;
        filterTipo.appendChild(opt);
    });
}

// Remove diacritics / accents for search normalization
function removeAccents(str) {
    if (!str) return "";
    return str.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
}
    
    // Admin panel sync (if exists)
    if (typeof adminFilterModelo !== "undefined" && adminFilterModelo) {
        const prevAdminModel = adminFilterModelo.value;
        adminFilterModelo.innerHTML = "";
        sortedModelos.forEach(m => {
            const opt = document.createElement("option");
            opt.value = m;
            opt.textContent = m;
            adminFilterModelo.appendChild(opt);
        });
        if (sortedModelos.includes(prevAdminModel)) {
            adminFilterModelo.value = prevAdminModel;
        } else {
            adminFilterModelo.value = "Todos";
        }
    }
    
    const prevColorValue = filterColor.value;
    filterColor.innerHTML = "";
    const sortedColores = [...colores].filter(c => c !== "Todos").sort();
    sortedColores.unshift("Todos");
    
    sortedColores.forEach(c => {
        const opt = document.createElement("option");
        opt.value = c;
        opt.textContent = c;
        filterColor.appendChild(opt);
    });
    if (sortedColores.includes(prevColorValue)) {
        filterColor.value = prevColorValue;
    } else {
        filterColor.value = "Todos";
    }
    
    if (typeof adminFilterColor !== "undefined" && adminFilterColor) {
        const prevAdminColor = adminFilterColor.value;
        adminFilterColor.innerHTML = "";
        sortedColores.forEach(c => {
            const opt = document.createElement("option");
            opt.value = c;
            opt.textContent = c;
            adminFilterColor.appendChild(opt);
        });
        if (sortedColores.includes(prevAdminColor)) {
            adminFilterColor.value = prevAdminColor;
        } else {
            adminFilterColor.value = "Todos";
        }
    }
}

// ── CATALOG RENDERING ──
function renderCatalog() {
    const query = searchInput.value.toLowerCase().trim();
    const fsQuery = filterSearch ? filterSearch.value.toLowerCase().replace(/[\s-]/g, "") : "";
    
    const selTipo = filterTipo.value;
    
    // Check if any filters are active
    const isFiltered = query !== "" || fsQuery !== "" || selTipo !== "Todos";
    
    let baseProducts = activeMainTab === "combo" ? comboProducts : productsState;
    
    // Filter product state
    let filtered = baseProducts.filter(p => {
        // Active Tab filter
        if (activeMainTab === "offers") {
            if(!p.en_oferta) return false;
        }
        
        // Header Search matching
        if (query !== "") {
            const searchable = removeAccents(`${p.nombre} ${p.marca} ${p.modelo} ${p.color}`).toLowerCase();
            const words = removeAccents(query).split(/\s+/);
            for (let w of words) {
                if (!searchable.includes(w)) return false;
            }
        }
        
        // Fuzzy filter Search matching
        if (fsQuery !== "") {
            const searchable2 = removeAccents(`${p.marca} ${p.modelo} ${p.compatibilidad}`).toLowerCase().replace(/[\s-]/g, "");
            const cleanedQuery = removeAccents(fsQuery);
            if (!searchable2.includes(cleanedQuery)) return false;
        }

        // Category matching
        if (selTipo !== "Todos" && p.nombre !== selTipo) return false;
        
        return true;
    });
        
        return true;
    });

    // Clear grid
    productosGrid.innerHTML = "";
    
    const catalogTitle = document.getElementById("catalogTitle");
    const catalogSubtitle = document.getElementById("catalogSubtitle");
    
    if (activeMainTab === "offers") {
        catalogTitle.textContent = "🔥 Ofertas Exclusivas";
        catalogSubtitle.textContent = "Productos en Oferta";
        ofertasSection.classList.add("hidden");
        clearFiltersBtn.classList.add("hidden");
        resultsCount.textContent = `${filtered.length} ofertas disponibles`;
    } else {
        catalogTitle.textContent = "Encontrá tu accesorio";
        catalogSubtitle.textContent = isFiltered ? "Resultados de búsqueda" : "Catálogo Completo";
        
        // Show all featured offers unconditionally
        const offers = productsState.filter(p => p.en_oferta);
        if (offers.length > 0 && activeMainTab !== "combo") {
            ofertasSection.classList.remove("hidden");
            renderOffersGrid(offers);
        } else {
            ofertasSection.classList.add("hidden");
        }
        
        if (isFiltered) {
            clearFiltersBtn.classList.remove("hidden");
            resultsCount.textContent = `${filtered.length} artículo(s) encontrado(s)`;
        } else {
            clearFiltersBtn.classList.add("hidden");
            resultsCount.textContent = `Catálogo completo (${baseProducts.length})`;
        }
    }
    
    if (filtered.length === 0) {
        emptyCatalogState.classList.remove("hidden");
        emptyCatalogState.classList.add("flex");
        productosGrid.classList.add("hidden");
        
        const fallbackWsBtn = document.getElementById("fallbackWsBtn");
        const emptyCatalogTitle = document.getElementById("emptyCatalogTitle");
        
        if (fallbackWsBtn && emptyCatalogTitle) {
            const userSearch = filterSearch && filterSearch.value ? filterSearch.value : (query ? query : "tu modelo");
            emptyCatalogTitle.textContent = `¿No encontrás accesorios para ${userSearch}?`;
            
            const msg = `Hola! Busco accesorios para el modelo ${userSearch} y no lo encontré en la web.`;
            fallbackWsBtn.href = `https://wa.me/5493816582851?text=${encodeURIComponent(msg)}`;
        }
        
        const container = document.getElementById("paginationControls");
        if (container) container.innerHTML = "";
    } else {
        emptyCatalogState.classList.add("hidden");
        emptyCatalogState.classList.remove("flex");
        productosGrid.classList.remove("hidden");
        
        // Paginated items
        const startIndex = (currentPage - 1) * itemsPerPage;
        const endIndex = startIndex + itemsPerPage;
        const paginated = filtered.slice(startIndex, endIndex);
        
        // Render item cards
        paginated.forEach(p => {
            if (activeMainTab === "combo") {
                const imgUrls = splitImageUrls(p.imagen_url);
                const imgUrl = normalizeImageUrl(imgUrls[0]);
                
                const card = document.createElement("div");
                card.className = "bg-white border border-black/[0.06] rounded-2xl p-4 flex flex-col gap-3 shadow-sm hover:shadow-md transition-shadow";
                card.innerHTML = `
                    <div class="aspect-square bg-bgLight rounded-xl overflow-hidden relative">
                        <img src="${imgUrl}" alt="${p.nombre}" class="w-full h-full object-cover">
                    </div>
                    <div>
                        <h4 class="font-bold text-sm text-textDark leading-tight">${p.nombre} ${p.modelo}</h4>
                        <p class="text-[10px] text-textMuted mt-1">🎨 ${p.color || 'Estándar'}</p>
                        <p class="text-[10px] font-bold mt-1 ${p.cantidad > 0 ? 'text-successGreen' : 'text-offerRed'}">Stock: ${p.cantidad}</p>
                    </div>
                    <div class="mt-auto flex items-center justify-between border border-black/[0.08] rounded-xl p-1 bg-bgLight">
                        <button onclick="changeComboQty(${p.index}, -1)" class="w-8 h-8 flex items-center justify-center font-bold text-lg bg-white rounded-lg shadow-sm hover:bg-black/[0.02]">-</button>
                        <span id="combo-qty-${p.index}" class="font-bold text-sm">${comboSelections[p.index] || 0}</span>
                        <button onclick="changeComboQty(${p.index}, 1)" class="w-8 h-8 flex items-center justify-center font-bold text-lg bg-white rounded-lg shadow-sm hover:bg-black/[0.02]">+</button>
                    </div>
                `;
                productosGrid.appendChild(card);
            } else {
                productosGrid.appendChild(createProductCard(p, false));
            }
        });
        
        // Render pagination controls
        renderPaginationControls(filtered.length);
    }
}

// Render pagination controls
function renderPaginationControls(totalItems) {
    const totalPages = Math.ceil(totalItems / itemsPerPage);
    const container = document.getElementById("paginationControls");
    if (!container) return;
    
    container.innerHTML = "";
    if (totalPages <= 1) {
        return;
    }
    
    // Previous Button
    const prevBtn = document.createElement("button");
    prevBtn.className = `px-4 py-2 text-xs font-bold rounded-xl border transition-all ${currentPage === 1 ? 'bg-black/[0.02] text-textMuted cursor-not-allowed border-black/[0.04]' : 'bg-white text-textDark hover:bg-bgLight border-black/[0.08] active:scale-95'}`;
    prevBtn.textContent = "◀ Anterior";
    prevBtn.disabled = currentPage === 1;
    prevBtn.addEventListener("click", () => {
        if (currentPage > 1) {
            currentPage--;
            renderCatalog();
            document.getElementById("productosCatalog").scrollIntoView({ behavior: 'smooth' });
        }
    });
    container.appendChild(prevBtn);
    
    // Page indicator
    const indicator = document.createElement("span");
    indicator.className = "text-xs font-bold text-textDark px-2";
    indicator.textContent = `Página ${currentPage} de ${totalPages}`;
    container.appendChild(indicator);
    
    // Next Button
    const nextBtn = document.createElement("button");
    nextBtn.className = `px-4 py-2 text-xs font-bold rounded-xl border transition-all ${currentPage === totalPages ? 'bg-black/[0.02] text-textMuted cursor-not-allowed border-black/[0.04]' : 'bg-white text-textDark hover:bg-bgLight border-black/[0.08] active:scale-95'}`;
    nextBtn.textContent = "Siguiente ▶";
    nextBtn.disabled = currentPage === totalPages;
    nextBtn.addEventListener("click", () => {
        if (currentPage < totalPages) {
            currentPage++;
            renderCatalog();
            document.getElementById("productosCatalog").scrollIntoView({ behavior: 'smooth' });
        }
    });
    container.appendChild(nextBtn);
}

// Render the top horizontal list of offers
function renderOffersGrid(offers) {
    ofertasGrid.innerHTML = "";
    offers.forEach(p => {
        ofertasGrid.appendChild(createProductCard(p, true));
    });
}

// Global function to toggle image inside product card
window.switchCardImage = function(prodIndex, imgIndex, totalImgs) {
    for (let i = 0; i < totalImgs; i++) {
        const img = document.getElementById(`img-${prodIndex}-${i}`);
        if (img) {
            if (i === imgIndex) {
                img.classList.remove("opacity-0", "z-0");
                img.classList.add("opacity-100", "z-10");
            } else {
                img.classList.remove("opacity-100", "z-10");
                img.classList.add("opacity-0", "z-0");
            }
        }
    }
    // update dots class
    const dotEls = document.querySelectorAll(`#dots-${prodIndex} .carousel-dot`);
    dotEls.forEach((dot, idx) => {
        if (idx === imgIndex) {
            dot.classList.add("active");
        } else {
            dot.classList.remove("active");
        }
    });
};

// Create Card element for products
function createProductCard(p, isOfferCard = false) {
    const card = document.createElement("div");
    card.className = `product-card bg-white border border-black/[0.04] rounded-2xl overflow-hidden shadow-sm flex flex-col relative ${isOfferCard ? 'border-accentBlue/25' : ''}`;
    
    // Offer Badge
    let offerBadge = "";
    if (p.en_oferta) {
        offerBadge = `<span class="absolute top-3 left-3 z-30 text-[10px] font-black uppercase bg-offerRed text-white px-2 py-0.5 rounded-md shadow-sm">🔥 Oferta</span>`;
    }
    
    // Split comma-separated multiple images
    const imgUrls = splitImageUrls(p.imagen_url);
        
    // Stock badge styling
    let stockBadge = "";
    let buttonHtml = "";
    
    if (p.cantidad <= 0) {
        stockBadge = `<span class="inline-flex items-center gap-1.5 text-xs text-offerRed font-semibold mt-1">● Agotado</span>`;
        buttonHtml = `<button disabled class="w-full mt-auto py-3 bg-black/[0.04] text-textMuted text-xs font-bold rounded-xl cursor-not-allowed">Sin Stock</button>`;
    } else {
        stockBadge = `<span class="inline-flex items-center gap-1.5 text-xs text-successGreen font-semibold mt-1">● Stock disponible</span>`;
        buttonHtml = `<button onclick="addToCart(${p.index})" class="w-full mt-auto py-3 bg-accentBlue hover:bg-accentBlueHover text-white text-xs font-bold rounded-xl transition-all shadow-sm transform active:scale-95">🛒 Agregar al Carrito</button>`;
    }
    
    // Check if compatibility information exists in the compat state for this model
    let compatText = "";
    const matches = compatState.filter(c => c.modelo.toLowerCase() === p.modelo.toLowerCase() || p.modelo.toLowerCase().includes(c.modelo.toLowerCase()));
    if (matches.length > 0 && matches[0].compatibilidad) {
        compatText = `<div class="text-[10px] text-textMuted mt-1 bg-black/[0.02] py-1 px-1.5 rounded-md inline-block">🔗 Compatible: ${matches[0].compatibilidad}</div>`;
    }

    // Build Image Area HTML with carousel and zoom overlay
    let imageAreaHtml = `
        <div class="relative w-full aspect-square overflow-hidden bg-bgLight product-card-img-container">
            ${offerBadge}
            <div class="zoom-overlay" onclick="openImageZoom(this.parentElement)">🔍</div>
            ${imgUrls.map((url, idx) => `
                <img src="${normalizeImageUrl(url)}" alt="${p.nombre}" 
                     id="img-${p.index}-${idx}"
                     class="product-card-img w-full h-full object-cover absolute inset-0 transition-all duration-300 ${idx === 0 ? 'opacity-100 z-10' : 'opacity-0 z-0'}" 
                     loading="lazy" 
                     onerror="this.src='https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500'">
            `).join('')}
            
            ${imgUrls.length > 1 ? `
                <div id="dots-${p.index}" class="carousel-dots">
                    ${imgUrls.map((_, idx) => `
                        <span class="carousel-dot ${idx === 0 ? 'active' : ''}" 
                              onclick="event.stopPropagation(); switchCardImage(${p.index}, ${idx}, ${imgUrls.length})">
                        </span>
                    `).join('')}
                </div>
            ` : ''}
        </div>
    `;

    card.innerHTML = `
        ${imageAreaHtml}
        <div class="p-4 flex-1 flex flex-col gap-1.5">
            <span class="text-[10px] font-bold text-accentBlue uppercase tracking-wider">${p.marca}</span>
            <h4 class="font-bold text-sm text-textDark leading-tight">${p.nombre} ${p.modelo}</h4>
            <div class="text-[11px] text-textMuted flex items-center gap-1">
                <span>🎨 Diseño:</span>
                <span class="font-semibold text-textDark">${p.color || 'Estándar'}</span>
            </div>
            ${compatText}
            <div class="flex items-center justify-between mt-1">
                <span class="text-base font-black text-textDark">$${p.precio.toLocaleString('es-AR', {minimumFractionDigits: 0})}</span>
                ${stockBadge}
            </div>
            <div class="mt-3 flex">
                ${buttonHtml}
            </div>
        </div>
    `;
    
    return card;
}

// ── CART MANAGEMENT ──
function loadCartFromLocalStorage() {
    const saved = localStorage.getItem("bejo_cart");
    if (saved) {
        try {
            cartState = JSON.parse(saved);
        } catch (e) {
            cartState = {};
        }
    }
}

function saveCartToLocalStorage() {
    localStorage.setItem("bejo_cart", JSON.stringify(cartState));
}

function addToCart(index) {
    const product = productsState.find(p => p.index === index);
    if (!product) return;
    
    const currentQty = cartState[index] || 0;
    if (currentQty >= product.cantidad) {
        showToast(`😔 No hay más stock disponible de ${product.nombre}.`, "error");
        return;
    }
    if (currentQty >= 10) {
        showToast("Límite de 10 unidades por producto en la web.", "warning");
        return;
    }
    
    cartState[index] = currentQty + 1;
    saveCartToLocalStorage();
    updateCartCount();
    showToast(`✅ ${product.nombre} agregado al carrito!`, "success");
    
    // Automatically open drawer to show items added
    openCartDrawer();
}

function updateCartCount() {
    const totalQty = Object.values(cartState).reduce((acc, curr) => acc + curr, 0);
    cartCount.textContent = totalQty;
    if (totalQty > 0) {
        cartCount.classList.remove("scale-0");
        cartCount.classList.add("scale-100");
    } else {
        cartCount.classList.remove("scale-100");
        cartCount.classList.add("scale-0");
    }
}

function openCartDrawer() {
    cartDrawer.classList.add("active");
    cartDrawerOverlay.classList.add("active");
    renderCartItems();
}

function closeCartDrawer() {
    cartDrawer.classList.remove("active");
    cartDrawerOverlay.classList.remove("active");
}

function renderCartItems() {
    cartItemsContainer.innerHTML = "";
    
    const cartIndices = Object.keys(cartState);
    if (cartIndices.length === 0) {
        cartEmptyState.classList.remove("hidden");
        cartEmptyState.classList.add("flex");
        cartFooter.classList.add("hidden");
        return;
    }
    
    cartEmptyState.classList.add("hidden");
    cartEmptyState.classList.remove("flex");
    cartFooter.classList.remove("hidden");
    
    let sumTotal = 0;
    
    cartIndices.forEach(idxStr => {
        if (idxStr.startsWith("combo_")) {
            const qty = cartState[idxStr];
            let cDetail = comboDetailsObj[idxStr];
            if (!cDetail) return;
            
            const sub = cDetail.precio * qty;
            sumTotal += sub;
            
            const cartItem = document.createElement("div");
            cartItem.className = "flex gap-3 py-3 border-b border-black/[0.04]";
            cartItem.innerHTML = `
                <div class="w-16 h-16 rounded-xl bg-bgLight overflow-hidden shrink-0 border border-black/[0.04] flex items-center justify-center text-3xl">
                    🎁
                </div>
                <div class="flex-1 flex flex-col gap-0.5 justify-center min-w-0">
                    <h5 class="font-bold text-xs leading-tight text-textDark">Combo Personalizado x${cDetail.items.length}</h5>
                    <span class="text-[10px] text-textMuted overflow-hidden text-ellipsis whitespace-nowrap">${cDetail.itemNames.join(", ")}</span>
                    <span class="text-xs font-black text-textDark mt-1">$${cDetail.precio.toLocaleString('es-AR')}</span>
                </div>
                <div class="flex flex-col items-end justify-between shrink-0">
                    <button onclick="removeCartItem('${idxStr}')" class="text-textMuted hover:text-offerRed p-1 rounded-full hover:bg-bgLight transition-colors">
                        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                    </button>
                    <div class="flex items-center border border-black/[0.08] rounded-lg overflow-hidden bg-white text-xs">
                        <button onclick="changeCartItemQty('${idxStr}', -1)" class="px-2 py-1 hover:bg-bgLight font-bold">-</button>
                        <span class="px-2 font-bold min-w-6 text-center select-none">${qty}</span>
                        <button onclick="changeCartItemQty('${idxStr}', 1)" class="px-2 py-1 hover:bg-bgLight font-bold">+</button>
                    </div>
                </div>
            `;
            cartItemsContainer.appendChild(cartItem);
            return;
        }

        const idx = parseInt(idxStr);
        const qty = cartState[idx];
        const product = productsState.find(p => p.index === idx);
        
        if (!product) return;
        
        const sub = product.precio * qty;
        sumTotal += sub;
        
        const imgUrls = splitImageUrls(product.imagen_url);
        const imgUrl = normalizeImageUrl(imgUrls[0]);
            
        const cartItem = document.createElement("div");
        cartItem.className = "flex gap-3 py-3 border-b border-black/[0.04]";
        cartItem.innerHTML = `
            <div class="w-16 h-16 rounded-xl bg-bgLight overflow-hidden shrink-0 border border-black/[0.04]">
                <img src="${imgUrl}" alt="${product.nombre}" class="w-full h-full object-cover">
            </div>
            <div class="flex-1 flex flex-col gap-0.5 justify-center">
                <h5 class="font-bold text-xs leading-tight text-textDark">${product.nombre} ${product.modelo}</h5>
                <span class="text-[10px] text-textMuted">🎨 ${product.color || 'Estándar'}</span>
                <span class="text-xs font-black text-textDark mt-1">$${product.precio.toLocaleString('es-AR')}</span>
            </div>
            <div class="flex flex-col items-end justify-between shrink-0">
                <button onclick="removeCartItem(${idx})" class="text-textMuted hover:text-offerRed p-1 rounded-full hover:bg-bgLight transition-colors">
                    <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                </button>
                <div class="flex items-center border border-black/[0.08] rounded-lg overflow-hidden bg-white text-xs">
                    <button onclick="changeCartItemQty(${idx}, -1)" class="px-2 py-1 hover:bg-bgLight font-bold">-</button>
                    <span class="px-2 font-bold min-w-6 text-center select-none">${qty}</span>
                    <button onclick="changeCartItemQty(${idx}, 1)" class="px-2 py-1 hover:bg-bgLight font-bold">+</button>
                </div>
            </div>
        `;
        cartItemsContainer.appendChild(cartItem);
    });
    
    cartTotalSum.textContent = `$${sumTotal.toLocaleString('es-AR')}`;
}

function removeCartItem(idx) {
    delete cartState[idx];
    saveCartToLocalStorage();
    updateCartCount();
    renderCartItems();
}

function changeCartItemQty(idx, offset) {
    const product = productsState.find(p => p.index === idx);
    if (!product) return;
    
    const newQty = (cartState[idx] || 0) + offset;
    if (newQty <= 0) {
        removeCartItem(idx);
        return;
    }
    
    if (offset > 0 && newQty > product.cantidad) {
        showToast(`😔 No hay más unidades de stock de ${product.nombre}.`, "error");
        return;
    }
    
    if (newQty > 10) {
        showToast("Límite de 10 unidades por producto.", "warning");
        return;
    }
    
    cartState[idx] = newQty;
    saveCartToLocalStorage();
    updateCartCount();
    renderCartItems();
}

// ── CHECKOUT MODAL ──
function openCheckoutModal() {
    closeCartDrawer();
    
    let sumTotal = 0;
    Object.keys(cartState).forEach(idxStr => {
        const idx = parseInt(idxStr);
        const qty = cartState[idx];
        const p = productsState.find(p => p.index === idx);
        if (p) sumTotal += p.precio * qty;
    });
    
    checkoutTotal.textContent = `$${sumTotal.toLocaleString('es-AR')}`;
    
    // Clear delivery input values
    const devNombre = document.getElementById("devNombre");
    if (devNombre) devNombre.value = "";
    devCalle.value = "";
    devBarrio.value = "";
    devLocalidad.value = "";
    devTelefono.value = "";
    devObservacion.value = "";
    
    // Deselect radio buttons
    deliveryMethods.forEach(rm => rm.checked = false);
    paymentMethods.forEach(pm => pm.checked = false);
    deliveryDetails.classList.add("hidden");
    
    checkoutModal.classList.remove("hidden");
    checkoutModal.classList.add("flex");
}

function closeCheckoutModal() {
    checkoutModal.classList.add("hidden");
    checkoutModal.classList.remove("flex");
}

// Handle delivery options changes (DOM layout triggers)
function handleDeliveryMethodChange() {
    const selected = document.querySelector('input[name="deliveryMethod"]:checked');
    if (selected && selected.value === "Envío a domicilio") {
        deliveryDetails.classList.remove("hidden");
        deliveryDetails.classList.add("flex");
    } else {
        deliveryDetails.classList.add("hidden");
    }
}

// Order Confirmation Submit Call
async function submitOrder() {
    const devMethod = document.querySelector('input[name="deliveryMethod"]:checked');
    const payMethod = document.querySelector('input[name="paymentMethod"]:checked');
    
    if (!devMethod) {
        showToast("⚠️ Seleccioná cómo querés recibir tu pedido.", "warning");
        return;
    }
    if (!payMethod) {
        showToast("⚠️ Seleccioná el método de pago.", "warning");
        return;
    }
    
    let address = "";
    let observation = "";
    
    const nombre = document.getElementById("devNombre").value.trim();
    const tel = devTelefono.value.trim();
    
    if (!nombre) {
        showToast("⚠️ Ingresá tu Nombre y Apellido.", "warning");
        return;
    }
    if (!tel) {
        showToast("⚠️ Ingresá tu Teléfono de contacto.", "warning");
        return;
    }
    
    if (devMethod.value === "Envío a domicilio") {
        const calle = devCalle.value.trim();
        const barrio = devBarrio.value.trim();
        const loc = devLocalidad.value;
        
        if (!calle) {
            showToast("⚠️ Ingresá calle y número para el envío.", "warning");
            return;
        }
        if (!loc) {
            showToast("⚠️ Seleccioná tu localidad.", "warning");
            return;
        }
        
        const addrParts = [`Nombre: ${nombre}`, calle];
        if (barrio) addrParts.push(`Barrio ${barrio}`);
        addrParts.push(loc);
        addrParts.push(`Tel: ${tel}`);
        
        address = addrParts.join(" | ");
    } else {
        address = `Retiro por Local | Nombre: ${nombre} | Tel: ${tel}`;
    }
    
    // Prepare payload
    const payload = {
        carrito: cartState,
        comboDetails: comboDetailsObj,
        entrega: {
            metodo: devMethod.value,
            direccion: address,
            observacion: observation,
            nombre: nombre
        },
        pago: {
            metodo: payMethod.value
        }
    };
    
    // UI state indicator
    confirmOrderBtn.disabled = true;
    confirmOrderBtn.textContent = "Procesando pedido... ⏳";
    
    try {
        const response = await fetch("/api/checkout", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });
        
        const res = await response.json();
        if (res.success) {
            closeCheckoutModal();
            
            // Set success modal states
            successOrderId.textContent = res.id_pedido;
            
            // Setup buttons
            successWSBtn.href = res.ws_url;
            
            if (res.mp_url) {
                successMPBtn.href = res.mp_url;
                successMPBtn.classList.remove("hidden");
            } else {
                successMPBtn.classList.add("hidden");
            }
            
            // Clear cart
            cartState = {};
            saveCartToLocalStorage();
            updateCartCount();
            
            // local pickup warning notice in success modal
            const successLocalAlert = document.getElementById("successLocalAlert");
            if (successLocalAlert) successLocalAlert.remove();
            
            if (devMethod.value === "Retiro en local") {
                successOrderId.insertAdjacentHTML('afterend', `
                    <div id="successLocalAlert" class="my-3 p-3 bg-warningOrange/10 border border-warningOrange/20 text-warningOrange text-xs font-semibold rounded-xl">
                        ⚠️ Se coordinará con el local para el punto de entrega.
                    </div>
                `);
            }
            
            // Open success visual
            successModal.classList.remove("hidden");
            successModal.classList.add("flex");
            
            // Re-fetch catalog to update current stocks
            fetchData();
            
            // Auto trigger removed as per request
        } else {
            showToast(`❌ Error: ${res.error || 'No se pudo procesar el pedido'}`, "error");
        }
    } catch (e) {
        console.error(e);
        showToast("⚠️ Error de conexión al procesar la orden.", "error");
    } finally {
        confirmOrderBtn.disabled = false;
        confirmOrderBtn.textContent = "Confirmar Pedido 🚀";
    }
}

// ── COMPATIBILITY FILTER SEARCH ──
function populateCompatFilters() {
    const compatFilterTipo = document.getElementById("compatFilterTipo");
    const compatFilterMarca = document.getElementById("compatFilterMarca");
    const compatFilterModelo = document.getElementById("compatFilterModelo");
    if (!compatFilterTipo || !compatFilterMarca || !compatFilterModelo) return;
    
    const tipos = new Set();
    compatState.forEach(c => {
        if (c.tipo) tipos.add(c.tipo);
    });
    
    compatFilterTipo.innerHTML = '<option value="">Seleccionar categoría...</option>';
    [...tipos].sort().forEach(t => {
        const opt = document.createElement("option");
        opt.value = t;
        opt.textContent = t;
        compatFilterTipo.appendChild(opt);
    });
    
    const marcas = new Set();
    compatState.forEach(c => {
        if (c.marca) marcas.add(c.marca);
    });
    
    compatFilterMarca.innerHTML = '<option value="">Seleccionar marca...</option>';
    [...marcas].sort().forEach(m => {
        const opt = document.createElement("option");
        opt.value = m;
        opt.textContent = m;
        compatFilterMarca.appendChild(opt);
    });
    
    compatFilterModelo.innerHTML = '<option value="">Seleccionar modelo...</option>';
    compatFilterModelo.disabled = true;
}

function updateCompatModels() {
    const compatFilterTipo = document.getElementById("compatFilterTipo");
    const compatFilterMarca = document.getElementById("compatFilterMarca");
    const compatFilterModelo = document.getElementById("compatFilterModelo");
    if (!compatFilterTipo || !compatFilterMarca || !compatFilterModelo) return;
    
    const selTipo = compatFilterTipo.value;
    const selMarca = compatFilterMarca.value;
    
    compatResults.innerHTML = "";
    compatResults.classList.add("hidden");
    
    if (!selTipo || !selMarca) {
        compatFilterModelo.innerHTML = '<option value="">Seleccionar modelo...</option>';
        compatFilterModelo.disabled = true;
        return;
    }
    
    const models = new Set();
    compatState.forEach(c => {
        if (c.tipo === selTipo && c.marca === selMarca && c.modelo) {
            models.add(c.modelo);
        }
    });
    
    compatFilterModelo.innerHTML = '<option value="">Seleccionar modelo...</option>';
    if (models.size > 0) {
        compatFilterModelo.disabled = false;
        [...models].sort().forEach(m => {
            const opt = document.createElement("option");
            opt.value = m;
            opt.textContent = m;
            compatFilterModelo.appendChild(opt);
        });
    } else {
        compatFilterModelo.disabled = true;
        compatFilterModelo.innerHTML = '<option value="">Sin modelos compatibles</option>';
    }
}

function handleCompatModelChange() {
    const compatFilterTipo = document.getElementById("compatFilterTipo");
    const compatFilterMarca = document.getElementById("compatFilterMarca");
    const compatFilterModelo = document.getElementById("compatFilterModelo");
    if (!compatFilterTipo || !compatFilterMarca || !compatFilterModelo) return;
    
    const selTipo = compatFilterTipo.value;
    const selMarca = compatFilterMarca.value;
    const selModelo = compatFilterModelo.value;
    
    if (!selModelo) {
        compatResults.innerHTML = "";
        compatResults.classList.add("hidden");
        return;
    }
    
    const match = compatState.find(c => c.tipo === selTipo && c.marca === selMarca && c.modelo === selModelo);
    
    compatResults.innerHTML = "";
    compatResults.classList.remove("hidden");
    
    if (!match) {
        compatResults.innerHTML = `
            <div class="text-textMuted py-1 text-center font-medium">
                ℹ️ No encontramos datos específicos de compatibilidad para este modelo. Coordiná la consulta por WhatsApp.
            </div>
        `;
    } else {
        compatResults.innerHTML = `
            <div class="flex flex-col gap-2.5">
                <div class="font-bold text-xs uppercase text-accentBlue">${match.marca} · ${match.tipo}</div>
                <div class="font-semibold text-sm text-textDark">${match.modelo}</div>
                <div class="text-xs text-textMuted mt-0.5">Compatible con: <span class="text-textDark font-medium">${match.compatibilidad || 'Ninguno'}</span></div>
                
                <button onclick="buscarModeloEnCatalogo('${match.marca}', '${match.modelo}')" 
                        class="mt-2 w-full py-2 bg-textDark hover:bg-black text-white text-xs font-bold rounded-xl transition-all shadow-sm transform active:scale-95 text-center font-bold">
                    🔍 Buscar en el catálogo
                </button>
            </div>
        `;
    }
}

window.buscarModeloEnCatalogo = function(marca, modelo) {
    const navCatalogBtn = document.getElementById("navCatalogBtn");
    if (navCatalogBtn) {
        navCatalogBtn.click();
    }
    
    searchInput.value = "";
    searchInputMobile.value = "";
    
    filterMarca.value = marca;
    updateCascadingFilters();
    
    const modelOptions = Array.from(filterModelo.options).map(o => o.value);
    if (modelOptions.includes(modelo)) {
        filterModelo.value = modelo;
    } else {
        filterModelo.value = "Todos";
        searchInput.value = modelo;
        if (searchInputMobile) searchInputMobile.value = modelo;
    }
    
    currentPage = 1;
    renderCatalog();
    
    document.getElementById("productosCatalog").scrollIntoView({ behavior: 'smooth' });
};

// ── ADMIN PANEL CLIENT LOGIC ──
function openAdminLogin() {
    adminPasswordInput.value = "";
    adminLoginModal.classList.remove("hidden");
    adminLoginModal.classList.add("flex");
}

function closeAdminLogin() {
    adminLoginModal.classList.add("hidden");
    adminLoginModal.classList.remove("flex");
}

async function submitAdminLogin() {
    const pw = adminPasswordInput.value;
    if (!pw) return;
    
    try {
        const response = await fetch("/api/admin/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ password: pw })
        });
        
        const data = await response.json();
        if (data.success) {
            adminAuthenticated = true;
            adminToken = data.token;
            closeAdminLogin();
            openAdminPanel();
        } else {
            showToast("❌ Contraseña incorrecta", "error");
        }
    } catch (e) {
        showToast("⚠️ Error al conectar con la autenticación", "error");
    }
}

function openAdminPanel() {
    adminPanel.classList.remove("hidden");
    adminPanel.classList.add("flex");
    loadAdminTab("pedidos");
}

function closeAdminPanel() {
    adminPanel.classList.add("hidden");
    adminPanel.classList.remove("flex");
    adminAuthenticated = false;
    adminToken = "";
}

function loadAdminTab(tab) {
    if (tab === "pedidos") {
        tabPedidosBtn.className = "text-left px-4 py-3 text-sm font-semibold rounded-xl bg-accentBlue/10 text-accentBlue";
        tabProductosBtn.className = "text-left px-4 py-3 text-sm font-semibold rounded-xl text-textMuted hover:bg-bgLight hover:text-textDark";
        panelPedidos.classList.remove("hidden");
        panelPedidos.classList.add("flex");
        panelProductos.classList.add("hidden");
        fetchAdminPedidos();
    } else {
        tabProductosBtn.className = "text-left px-4 py-3 text-sm font-semibold rounded-xl bg-accentBlue/10 text-accentBlue";
        tabPedidosBtn.className = "text-left px-4 py-3 text-sm font-semibold rounded-xl text-textMuted hover:bg-bgLight hover:text-textDark";
        panelProductos.classList.remove("hidden");
        panelProductos.classList.add("flex");
        panelPedidos.classList.add("hidden");
        renderAdminProductosTable();
    }
}

async function fetchAdminPedidos() {
    try {
        const response = await fetch("/api/admin/pedidos", {
            headers: { "Authorization": adminToken }
        });
        const pedidos = await response.json();
        renderAdminPedidosTable(pedidos);
    } catch (err) {
        showToast("Error al cargar pedidos admin.", "error");
    }
}

function extractProductos(wsText) {
    if (!wsText) return "";
    const match = wsText.match(/📦 \*Productos:\*([\s\S]*?)\n\n💰 \*Total:\*/);
    return match ? match[1].trim() : "No detallado";
}

function renderAdminPedidosTable(pedidos) {
    adminPedidosTableBody.innerHTML = "";
    if (pedidos.length === 0) {
        adminPedidosTableBody.innerHTML = `<tr><td colspan="7" class="py-4 text-center text-textMuted">No hay pedidos registrados</td></tr>`;
        return;
    }
    
    // Render in reverse chronological order (latest first)
    pedidos.slice().reverse().forEach(p => {
        const tr = document.createElement("tr");
        tr.className = "hover:bg-bgLight/40 transition-colors border-b border-black/[0.03]";
        
        let selectHtml = `
            <select onchange="updatePedidoEstado('${p.id_pedido}', this.value)" class="text-xs bg-bgLight border-0 rounded-lg py-1 px-2 cursor-pointer font-semibold">
                <option value="Pendiente" ${p.estado === 'Pendiente' ? 'selected' : ''}>Pendiente</option>
                <option value="Entregado" ${p.estado === 'Entregado' ? 'selected' : ''}>Entregado</option>
                <option value="Rechazado" ${p.estado === 'Rechazado' ? 'selected' : ''}>Rechazado</option>
                <option value="Cancelado" ${p.estado === 'Cancelado' ? 'selected' : ''}>Cancelado</option>
            </select>
        `;
        
        tr.innerHTML = `
            <td class="py-3 px-4 font-medium text-xs whitespace-nowrap">${p.fecha}</td>
            <td class="py-3 px-4 font-mono font-bold text-accentBlue text-xs">
                <button onclick="toggleOrderDetails('${p.id_pedido}')" class="hover:underline flex items-center gap-1 text-left text-accentBlue">
                    <span>👁️</span> ${p.id_pedido}
                </button>
            </td>
            <td class="py-3 px-4 text-xs">
                <div class="font-bold text-textDark">${p.nombre_apellido || 'Sin nombre'}</div>
                <div class="text-[10px] text-textMuted mt-0.5">${p.cliente_contacto}</div>
            </td>
            <td class="py-3 px-4 text-[11px] whitespace-pre-line">${p.productos || extractProductos(p.detalle_ws)}</td>
            <td class="py-3 px-4 font-bold text-xs">$${parseInt(p.total).toLocaleString('es-AR')}</td>
            <td class="py-3 px-4 text-xs">
                <span class="font-semibold rounded px-1.5 py-0.5 text-[10px] uppercase
                    ${p.estado === 'Pendiente' ? 'bg-warningOrange/10 text-warningOrange' : ''}
                    ${p.estado === 'Entregado' ? 'bg-successGreen/10 text-successGreen' : ''}
                    ${p.estado === 'Rechazado' || p.estado === 'Cancelado' ? 'bg-offerRed/10 text-offerRed' : ''}
                ">${p.estado}</span>
            </td>
            <td class="py-3 px-4 text-right">${selectHtml}</td>
        `;
        
        // Append detail row
        const detailTr = document.createElement("tr");
        detailTr.className = "bg-bgLight/20";
        detailTr.innerHTML = `
            <td colspan="7" class="p-0 border-b border-black/[0.03]">
                <div id="details-${p.id_pedido}" class="order-details-pre text-xs text-textMuted bg-bgLight/50 rounded-xl border border-black/[0.03] mx-4 font-mono">
                    ${p.detalle_ws}
                </div>
            </td>
        `;
        
        adminPedidosTableBody.appendChild(tr);
        adminPedidosTableBody.appendChild(detailTr);
    });
}

window.toggleOrderDetails = function(id_pedido) {
    const el = document.getElementById(`details-${id_pedido}`);
    if (el) {
        el.classList.toggle("expanded");
    }
};

async function updatePedidoEstado(id_pedido, estado) {
    try {
        const response = await fetch("/api/admin/pedidos/estado", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": adminToken
            },
            body: JSON.stringify({ id_pedido, estado })
        });
        const res = await response.json();
        if (res.success) {
            showToast(`Pedido ${id_pedido} actualizado a ${estado}.`, "success");
            fetchAdminPedidos();
        } else {
            showToast("Error al actualizar pedido.", "error");
        }
    } catch (e) {
        showToast("Error de red", "error");
    }
}

// Admin panel cascade filters
function populateAdminFilters() {
    const adminFilterTipo = document.getElementById("adminFilterTipo");
    const adminFilterMarca = document.getElementById("adminFilterMarca");
    if (!adminFilterTipo || !adminFilterMarca) return;
    
    const tipos = new Set(["Todos"]);
    const marcas = new Set(["Todas"]);
    
    productsState.forEach(p => {
        if (p.nombre) tipos.add(p.nombre);
        if (p.marca) marcas.add(p.marca);
    });
    
    adminFilterTipo.innerHTML = "";
    const sortedAdminTipos = [...tipos].filter(t => t !== "Todos").sort();
    ["Todos", ...sortedAdminTipos].forEach(t => {
        const opt = document.createElement("option");
        opt.value = t;
        opt.textContent = t === "Todos" ? "Todos" : t;
        adminFilterTipo.appendChild(opt);
    });

    adminFilterMarca.innerHTML = "";
    const sortedAdminMarcas = [...marcas].filter(m => m !== "Todas").sort();
    ["Todas", ...sortedAdminMarcas].forEach(m => {
        const opt = document.createElement("option");
        opt.value = m;
        opt.textContent = m === "Todas" ? "Todos" : m;
        adminFilterMarca.appendChild(opt);
    });
    
    updateAdminCascadingFilters();
}

function updateAdminCascadingFilters() {
    const adminFilterTipo = document.getElementById("adminFilterTipo");
    const adminFilterMarca = document.getElementById("adminFilterMarca");
    const adminFilterModelo = document.getElementById("adminFilterModelo");
    const adminFilterColor = document.getElementById("adminFilterColor");
    if (!adminFilterTipo || !adminFilterMarca || !adminFilterModelo || !adminFilterColor) return;
    
    const selectedTipo = adminFilterTipo.value;
    const selectedMarca = adminFilterMarca.value;
    
    let filtered = productsState;
    if (selectedTipo !== "Todos") {
        filtered = filtered.filter(p => p.nombre === selectedTipo);
    }
    if (selectedMarca !== "Todas") {
        filtered = filtered.filter(p => p.marca === selectedMarca);
    }
    
    const modelos = new Set(["Todos"]);
    filtered.forEach(p => {
        if (p.modelo) modelos.add(p.modelo);
    });
    
    const prevModelValue = adminFilterModelo.value;
    adminFilterModelo.innerHTML = "";
    const sortedAdminModelos = [...modelos].filter(m => m !== "Todos").sort();
    ["Todos", ...sortedAdminModelos].forEach(m => {
        const opt = document.createElement("option");
        opt.value = m;
        opt.textContent = m === "Todos" ? "Todos" : m;
        adminFilterModelo.appendChild(opt);
    });
    if ([...modelos].includes(prevModelValue)) {
        adminFilterModelo.value = prevModelValue;
    } else {
        adminFilterModelo.value = "Todos";
    }
    
    const colores = new Set(["Todos"]);
    filtered.forEach(p => {
        if (p.color) colores.add(p.color);
    });
    
    const prevColorValue = adminFilterColor.value;
    adminFilterColor.innerHTML = "";
    const sortedAdminColores = [...colores].filter(c => c !== "Todos").sort();
    ["Todos", ...sortedAdminColores].forEach(c => {
        const opt = document.createElement("option");
        opt.value = c;
        opt.textContent = c === "Todos" ? "Todos" : c;
        adminFilterColor.appendChild(opt);
    });
    if ([...colores].includes(prevColorValue)) {
        adminFilterColor.value = prevColorValue;
    } else {
        adminFilterColor.value = "Todos";
    }
}

function renderAdminProductosTable() {
    const query = (document.getElementById("adminSearchInput")?.value || "").toLowerCase().trim();
    
    const adminFilterTipo = document.getElementById("adminFilterTipo");
    const adminFilterMarca = document.getElementById("adminFilterMarca");
    const adminFilterModelo = document.getElementById("adminFilterModelo");
    const adminFilterColor = document.getElementById("adminFilterColor");
    
    const selTipo = adminFilterTipo ? adminFilterTipo.value : "Todos";
    const selMarca = adminFilterMarca ? adminFilterMarca.value : "Todas";
    const selModelo = adminFilterModelo ? adminFilterModelo.value : "Todos";
    const selColor = adminFilterColor ? adminFilterColor.value : "Todos";
    
    adminProductosTableBody.innerHTML = "";
    
    let filtered = productsState.filter(p => {
        if (query) {
            const searchable = removeAccents(`${p.nombre} ${p.marca} ${p.modelo} ${p.color}`).toLowerCase();
            const words = removeAccents(query).split(/\s+/);
            for (let w of words) {
                if (!searchable.includes(w)) return false;
            }
        }
        if (selTipo !== "Todos" && p.nombre !== selTipo) return false;
        if (selMarca !== "Todas" && p.marca !== selMarca) return false;
        if (selModelo !== "Todos" && p.modelo !== selModelo) return false;
        if (selColor !== "Todos" && p.color !== selColor) return false;
        return true;
    });
    
    if (filtered.length === 0) {
        adminProductosTableBody.innerHTML = `<tr><td colspan="6" class="py-4 text-center text-textMuted">No se encontraron productos</td></tr>`;
        return;
    }
    
    filtered.forEach(p => {
        const tr = document.createElement("tr");
        tr.className = "hover:bg-bgLight/40 transition-colors border-b border-black/[0.03]";
        
        const imgUrls = splitImageUrls(p.imagen_url);
        const imgUrl = normalizeImageUrl(imgUrls[0]);
            
        tr.innerHTML = `
            <td class="py-3 px-4 w-12 h-12">
                <img src="${imgUrl}" alt="${p.nombre}" class="w-10 h-10 object-cover rounded-lg">
            </td>
            <td class="py-3 px-4 font-bold text-xs">
                ${p.nombre} ${p.modelo}
                <div class="text-[10px] font-normal text-textMuted">🎨 Color: ${p.color || 'Estándar'}</div>
            </td>
            <td class="py-3 px-4 text-xs font-semibold text-accentBlue">${p.marca}</td>
            <td class="py-3 px-4 font-bold text-xs">$${p.precio.toLocaleString('es-AR')}</td>
            <td class="py-3 px-4 text-xs font-bold">${p.cantidad} uds</td>
            <td class="py-3 px-4 text-right flex items-center justify-end gap-1.5 h-16">
                <button onclick="openEditProductModal(${p.index})" class="text-xs bg-bgLight hover:bg-black/[0.04] text-textDark py-1 px-2.5 rounded-lg font-bold transition-all">✏️ Editar</button>
                <button onclick="deleteProduct(${p.index})" class="text-xs bg-offerRed/10 hover:bg-offerRed text-offerRed hover:text-white py-1 px-2.5 rounded-lg font-bold transition-all">🗑️</button>
            </td>
        `;
        adminProductosTableBody.appendChild(tr);
    });
}

function openEditProductModal(index = null) {
    productEditForm.reset();
    document.getElementById("editFotoFile1").value = "";
    document.getElementById("editFotoFile2").value = "";
    document.getElementById("editFotoFile3").value = "";
    
    if (index !== null) {
        productEditModalTitle.textContent = "Editar Producto";
        const prod = productsState.find(p => p.index === index);
        if (!prod) return;
        
        document.getElementById("editIndex").value = index;
        document.getElementById("editNombre").value = prod.nombre;
        document.getElementById("editMarca").value = prod.marca;
        document.getElementById("editModelo").value = prod.modelo;
        document.getElementById("editColor").value = prod.color;
        document.getElementById("editPrecio").value = prod.precio;
        document.getElementById("editCantidad").value = prod.cantidad;
        
        const imgUrls = splitImageUrls(prod.imagen_url);
        document.getElementById("editUrlImgur1").value = imgUrls.length > 0 && !imgUrls[0].startsWith("data:image") ? imgUrls[0].trim() : "";
        document.getElementById("editUrlImgur2").value = imgUrls.length > 1 && !imgUrls[1].startsWith("data:image") ? imgUrls[1].trim() : "";
        document.getElementById("editUrlImgur3").value = imgUrls.length > 2 && !imgUrls[2].startsWith("data:image") ? imgUrls[2].trim() : "";
    } else {
        productEditModalTitle.textContent = "Agregar Producto";
        document.getElementById("editIndex").value = "";
    }
    
    productEditModal.classList.remove("hidden");
    productEditModal.classList.add("flex");
}

function closeEditProductModal() {
    productEditModal.classList.add("hidden");
    productEditModal.classList.remove("flex");
}

async function handleProductFormSubmit(e) {
    e.preventDefault();
    
    const formData = new FormData(productEditForm);
    
    try {
        const response = await fetch("/api/admin/productos", {
            method: "POST",
            headers: {
                "Authorization": adminToken
            },
            body: formData
        });
        
        const res = await response.json();
        if (res.success) {
            showToast("💾 Cambios guardados correctamente.", "success");
            closeEditProductModal();
            // Refresh local product catalogue
            await fetchData();
            if (panelProductos.classList.contains("hidden")) {
                loadAdminTab("pedidos");
            } else {
                loadAdminTab("productos");
            }
        } else {
            showToast(`❌ Error: ${res.error}`, "error");
        }
    } catch (err) {
        showToast("⚠️ Error de conexión al guardar cambios.", "error");
    }
}

async function deleteProduct(index) {
    if (!confirm("🚨 ¿Estás seguro de que deseás eliminar este producto permanentemente de Google Sheets?")) {
        return;
    }
    
    try {
        const response = await fetch(`/api/admin/productos/${index}`, {
            method: "DELETE",
            headers: { "Authorization": adminToken }
        });
        const res = await response.json();
        if (res.success) {
            showToast("🗑️ Producto eliminado del catálogo.", "success");
            await fetchData();
            renderAdminProductosTable();
        } else {
            showToast("Error al eliminar el producto.", "error");
        }
    } catch (e) {
        showToast("Error de red al eliminar.", "error");
    }
}

// ── AUXILIARY: EVENT LISTENERS SETUP ──
function setupEventListeners() {
    // Tabs Navigation switch triggers
    const navCatalogBtn = document.getElementById("navCatalogBtn");
    const navOffersBtn = document.getElementById("navOffersBtn");
    const navComboBtn = document.getElementById("navComboBtn");
    const navWholesaleBtn = document.getElementById("navWholesaleBtn");
    const catalogContent = document.getElementById("catalogContent");
    const wholesaleContent = document.getElementById("wholesaleContent");
    
    const selectTab = (tab) => {
        activeMainTab = tab;
        
        const resetTabs = () => {
            navCatalogBtn.className = "pb-4 border-b-2 border-transparent text-textMuted hover:text-textDark flex items-center gap-1.5 transition-all";
            navOffersBtn.className = "pb-4 border-b-2 border-transparent text-textMuted hover:text-textDark flex items-center gap-1.5 transition-all";
            if(navComboBtn) navComboBtn.className = "pb-4 border-b-2 border-transparent text-textMuted hover:text-textDark flex items-center gap-1.5 transition-all";
            navWholesaleBtn.className = "pb-4 border-b-2 border-transparent text-textMuted hover:text-textDark flex items-center gap-1.5 transition-all";
            
            catalogContent.classList.add("hidden");
            wholesaleContent.classList.add("hidden");
            
            document.getElementById("catalogHeaderNormal").classList.remove("hidden");
            document.getElementById("catalogHeaderNormal").classList.add("flex");
            document.getElementById("comboStickyHeader").classList.add("hidden");
            document.getElementById("comboStickyHeader").classList.remove("flex");
        };
        
        resetTabs();
        
        if (tab === "catalog") {
            navCatalogBtn.classList.add("text-accentBlue", "border-accentBlue", "font-bold");
            catalogContent.classList.remove("hidden");
        } else if (tab === "offers") {
            navOffersBtn.classList.add("text-offerRed", "border-offerRed", "font-bold");
            catalogContent.classList.remove("hidden");
        } else if (tab === "wholesale") {
            navWholesaleBtn.classList.add("text-accentBlue", "border-accentBlue", "font-bold");
            wholesaleContent.classList.remove("hidden");
            renderWholesaleCatalog();
        } else if (tab === "combo") {
            if(navComboBtn) navComboBtn.classList.add("text-comboPurple", "border-comboPurple", "font-bold");
            catalogContent.classList.remove("hidden");
            
            document.getElementById("catalogHeaderNormal").classList.add("hidden");
            document.getElementById("catalogHeaderNormal").classList.remove("flex");
            document.getElementById("comboStickyHeader").classList.remove("hidden");
            document.getElementById("comboStickyHeader").classList.add("flex");
            
            // Check config
            if (activeMainTab === "combo" && comboConfig.precio === 0) {
                fetch("/api/combo-config").then(r => r.json()).then(data => {
                    comboConfig = data;
                    document.getElementById("comboSubtitle").innerText = `${data.cantidad} productos a $${data.precio.toLocaleString("es-AR")}`;
                    document.getElementById("comboCounter").innerText = `${comboTotalSelected} / ${comboConfig.cantidad}`;
                });
            }
            if(comboProducts.length === 0) fetchComboData();
        }
        
        // Reset filters globally on tab switch
        if (searchInput) searchInput.value = "";
        if (searchInputMobile) searchInputMobile.value = "";
        if (filterSearch) filterSearch.value = "";
        if (filterTipo) filterTipo.value = "Todos";
        currentPage = 1;
        renderCatalog();
    };
    
    navCatalogBtn.addEventListener("click", () => selectTab("catalog"));
    navOffersBtn.addEventListener("click", () => selectTab("offers"));
    if(navComboBtn) navComboBtn.addEventListener("click", () => selectTab("combo"));
    navWholesaleBtn.addEventListener("click", () => selectTab("wholesale"));

    // Search input filters
    searchInput.addEventListener("input", () => {
        currentPage = 1;
        renderCatalog();
    });
    searchInputMobile.addEventListener("input", () => {
        currentPage = 1;
        renderCatalog();
    });
    
    // Filters cascading triggers
    if (filterTipo) {
        filterTipo.addEventListener("change", () => {
            currentPage = 1;
            renderCatalog();
        });
    }
    
    if (filterSearch) {
        filterSearch.addEventListener("input", () => {
            currentPage = 1;
            renderCatalog();
        });
    }
    
    // Clean filters CTAs
    const resetAllFilters = () => {
        if (searchInput) searchInput.value = "";
        if (searchInputMobile) searchInputMobile.value = "";
        if (filterSearch) filterSearch.value = "";
        if (filterTipo) filterTipo.value = "Todos";
        currentPage = 1;
        renderCatalog();
    };
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener("click", resetAllFilters);
    }
    
    // Compat dropdown filters cascading triggers
    const compatFilterTipo = document.getElementById("compatFilterTipo");
    const compatFilterMarca = document.getElementById("compatFilterMarca");
    const compatFilterModelo = document.getElementById("compatFilterModelo");
    
    if (compatFilterTipo) {
        compatFilterTipo.addEventListener("change", () => {
            updateCompatModels();
            handleCompatModelChange();
        });
    }
    if (compatFilterMarca) {
        compatFilterMarca.addEventListener("change", () => {
            updateCompatModels();
            handleCompatModelChange();
        });
    }
    if (compatFilterModelo) {
        compatFilterModelo.addEventListener("change", handleCompatModelChange);
    }
    
    // Admin filter cascading triggers
    const adminFilterTipo = document.getElementById("adminFilterTipo");
    const adminFilterMarca = document.getElementById("adminFilterMarca");
    const adminFilterModelo = document.getElementById("adminFilterModelo");
    const adminFilterColor = document.getElementById("adminFilterColor");
    
    if (adminFilterTipo) {
        adminFilterTipo.addEventListener("change", () => {
            updateAdminCascadingFilters();
            renderAdminProductosTable();
        });
    }
    if (adminFilterMarca) {
        adminFilterMarca.addEventListener("change", () => {
            updateAdminCascadingFilters();
            renderAdminProductosTable();
        });
    }
    if (adminFilterModelo) {
        adminFilterModelo.addEventListener("change", renderAdminProductosTable);
    }
    if (adminFilterColor) {
        adminFilterColor.addEventListener("change", renderAdminProductosTable);
    }
    
    // Cart open/close
    cartBtn.addEventListener("click", openCartDrawer);
    closeCartBtn.addEventListener("click", closeCartDrawer);
    cartDrawerOverlay.addEventListener("click", closeCartDrawer);
    
    // Checkout step triggers
    checkoutBtn.addEventListener("click", openCheckoutModal);
    closeCheckoutBtn.addEventListener("click", closeCheckoutModal);
    confirmOrderBtn.addEventListener("click", submitOrder);
    
    // Success Modal Close
    successCloseBtn.addEventListener("click", () => {
        successModal.classList.add("hidden");
        successModal.classList.remove("flex");
    });
    
    // Admin login modal controls
    const toggleAdminLogin = (e) => {
        e.preventDefault();
        openAdminLogin();
    };
    adminLoginBtn.addEventListener("click", toggleAdminLogin);
    adminFooterLink.addEventListener("click", toggleAdminLogin);
    adminLoginCancelBtn.addEventListener("click", closeAdminLogin);
    adminLoginSubmitBtn.addEventListener("click", submitAdminLogin);
    adminPasswordInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") submitAdminLogin();
    });
    
    // Admin dashboard controls
    adminCloseBtn.addEventListener("click", closeAdminPanel);
    tabPedidosBtn.addEventListener("click", () => loadAdminTab("pedidos"));
    tabProductosBtn.addEventListener("click", () => loadAdminTab("productos"));
    adminNewProdBtn.addEventListener("click", () => openEditProductModal(null));
    
    // Admin download Excel actions
    adminDownloadInventario.addEventListener("click", () => {
        window.open(`/api/admin/download/inventario?token=${adminToken}`, "_blank");
    });
    adminDownloadPedidos.addEventListener("click", () => {
        window.open(`/api/admin/download/pedidos?token=${adminToken}`, "_blank");
    });
    
    // Edit Product actions
    productEditModalClose.addEventListener("click", closeEditProductModal);
    productEditCancelBtn.addEventListener("click", closeEditProductModal);
    productEditForm.addEventListener("submit", handleProductFormSubmit);
    
    // Checkout forms conditional details trigger
    Array.from(deliveryMethods).forEach(rm => {
        rm.addEventListener("change", handleDeliveryMethodChange);
    });

    // Admin product quick search
    const adminSearchInput = document.getElementById("adminSearchInput");
    if (adminSearchInput) {
        adminSearchInput.addEventListener("input", renderAdminProductosTable);
    }
}

// ── TOAST MESSAGES HELPER ──
function showToast(message, type = "success") {
    const toast = document.createElement("div");
    toast.className = `toast-in flex items-center gap-2.5 px-4 py-3 text-xs font-bold rounded-xl shadow-lg border text-white transition-all max-w-sm
        ${type === 'success' ? 'bg-successGreen border-successGreen/20 shadow-successGreen/10' : ''}
        ${type === 'error' ? 'bg-offerRed border-offerRed/20 shadow-offerRed/10' : ''}
        ${type === 'warning' ? 'bg-warningOrange border-warningOrange/20 shadow-warningOrange/10' : ''}
    `;
    
    let icon = "⚡";
    if (type === "success") icon = "✓";
    if (type === "error") icon = "✕";
    if (type === "warning") icon = "⚠️";
    
    toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
    toastContainer.appendChild(toast);
    
    // Remove toast after 3 seconds
    setTimeout(() => {
        toast.classList.remove("toast-in");
        toast.classList.add("toast-out");
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 3000);
}

// Image Zoom Modal Functions
window.openImageZoom = function(container) {
    const activeImg = container.querySelector('img.opacity-100');
    if (activeImg) {
        document.getElementById("imageZoomContent").src = activeImg.src;
        const modal = document.getElementById("imageZoomModal");
        modal.classList.remove("hidden");
        modal.classList.add("flex");
    }
};
window.closeImageZoom = function() {
    const modal = document.getElementById("imageZoomModal");
    modal.classList.add("hidden");
    modal.classList.remove("flex");
};
