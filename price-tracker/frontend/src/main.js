/**
 * Scrapo — Main Application Entry Point
 *
 * Handles auth, views, theme toggle, search/filter, and product management.
 */

import "./style.css";
import {
  fetchProducts, addProduct, getProductDetail, deleteProduct, refreshPrice,
  login, register, logout, isLoggedIn, getUser, updateProfile, getProfile,
} from "./api.js";
import { createProductCard } from "./components/productCard.js";
import { renderProductDetail } from "./components/productDetail.js";
import { destroyChart } from "./components/priceChart.js";
import { renderCompareView } from "./components/compareView.js";

// ── DOM References ──────────────────────────────────────────────────

const authScreen = document.getElementById("auth-screen");
const appWrapper = document.getElementById("app-wrapper");

const heroSection = document.getElementById("hero-section");
const productsSection = document.getElementById("products-section");
const detailSection = document.getElementById("detail-section");
const compareSection = document.getElementById("compare-section");
const settingsSection = document.getElementById("settings-section");
const productsGrid = document.getElementById("products-grid");
const productCountBadge = document.getElementById("product-count-badge");

const modalOverlay = document.getElementById("modal-overlay");
const formAddProduct = document.getElementById("form-add-product");
const inputUrl = document.getElementById("input-product-url");
const inputTarget = document.getElementById("input-target-price");
const submitSpinner = document.getElementById("submit-spinner");
const submitText = document.getElementById("submit-text");
const formError = document.getElementById("form-error");

const toastContainer = document.getElementById("toast-container");

const inputSearch = document.getElementById("input-search");
const filterPlatform = document.getElementById("filter-platform");

// ── State ───────────────────────────────────────────────────────────

let products = [];
let currentView = "home"; // "home" | "detail" | "compare" | "settings"

// ── Theme ───────────────────────────────────────────────────────────

function initTheme() {
  const saved = localStorage.getItem("scrapo_theme") || "dark";
  document.documentElement.setAttribute("data-theme", saved);
  updateThemeIcon(saved);
}

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme");
  const next = current === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("scrapo_theme", next);
  updateThemeIcon(next);
}

function updateThemeIcon(theme) {
  const btn = document.getElementById("btn-theme-toggle");
  if (btn) btn.textContent = theme === "dark" ? "🌙" : "☀️";
}

// ── Toast Notifications ─────────────────────────────────────────────

function showToast(message, type = "info") {
  const toast = document.createElement("div");
  toast.className = `toast toast--${type}`;
  toast.textContent = message;
  toastContainer.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

// ── Modal ───────────────────────────────────────────────────────────

function openModal() {
  modalOverlay.style.display = "flex";
  inputUrl.value = "";
  inputTarget.value = "";
  formError.style.display = "none";
  setTimeout(() => inputUrl.focus(), 100);
}

function closeModal() {
  modalOverlay.style.display = "none";
}

// ── Auth ────────────────────────────────────────────────────────────

function showAuthScreen() {
  authScreen.style.display = "flex";
  appWrapper.style.display = "none";
}

function showApp() {
  authScreen.style.display = "none";
  appWrapper.style.display = "block";

  const user = getUser();
  if (user) {
    const displayName = document.getElementById("user-display-name");
    if (displayName) displayName.textContent = user.username;
  }
}

function setupAuth() {
  const tabLogin = document.getElementById("tab-login");
  const tabRegister = document.getElementById("tab-register");
  const formLogin = document.getElementById("form-login");
  const formRegister = document.getElementById("form-register");

  tabLogin.addEventListener("click", () => {
    tabLogin.classList.add("auth-tab--active");
    tabRegister.classList.remove("auth-tab--active");
    formLogin.style.display = "block";
    formRegister.style.display = "none";
  });

  tabRegister.addEventListener("click", () => {
    tabRegister.classList.add("auth-tab--active");
    tabLogin.classList.remove("auth-tab--active");
    formRegister.style.display = "block";
    formLogin.style.display = "none";
  });

  formLogin.addEventListener("submit", async (e) => {
    e.preventDefault();
    const username = document.getElementById("login-username").value.trim();
    const password = document.getElementById("login-password").value;
    const errEl = document.getElementById("login-error");
    const spinner = document.getElementById("login-spinner");
    const text = document.getElementById("login-text");

    errEl.style.display = "none";
    spinner.style.display = "inline-block";
    text.textContent = "Signing in...";

    try {
      await login(username, password);
      showApp();
      loadProducts();
    } catch (err) {
      errEl.textContent = err.message;
      errEl.style.display = "block";
    } finally {
      spinner.style.display = "none";
      text.textContent = "Sign In";
    }
  });

  formRegister.addEventListener("submit", async (e) => {
    e.preventDefault();
    const username = document.getElementById("register-username").value.trim();
    const email = document.getElementById("register-email").value.trim();
    const password = document.getElementById("register-password").value;
    const errEl = document.getElementById("register-error");
    const spinner = document.getElementById("register-spinner");
    const text = document.getElementById("register-text");

    errEl.style.display = "none";
    spinner.style.display = "inline-block";
    text.textContent = "Creating account...";

    try {
      await register(username, email, password);
      showApp();
      loadProducts();
    } catch (err) {
      errEl.textContent = err.message;
      errEl.style.display = "block";
    } finally {
      spinner.style.display = "none";
      text.textContent = "Create Account";
    }
  });
}

// ── Views ───────────────────────────────────────────────────────────

function hideAllSections() {
  heroSection.style.display = "none";
  productsSection.style.display = "none";
  detailSection.style.display = "none";
  compareSection.style.display = "none";
  settingsSection.style.display = "none";
  destroyChart();
}

function showHomeView() {
  currentView = "home";
  hideAllSections();
  setActiveNavTab("home");

  if (products.length === 0) {
    heroSection.style.display = "flex";
  } else {
    productsSection.style.display = "block";
  }
}

function showDetailView() {
  currentView = "detail";
  hideAllSections();
  detailSection.style.display = "block";
}

function showCompareView() {
  currentView = "compare";
  hideAllSections();
  setActiveNavTab("compare");
  compareSection.style.display = "block";
  renderCompareView(compareSection, {
    onViewProduct: handleViewProduct,
  });
}

function showSettingsView() {
  currentView = "settings";
  hideAllSections();
  settingsSection.style.display = "block";

  // Load current settings
  getProfile().then(user => {
    const telegramInput = document.getElementById("input-telegram-id");
    if (telegramInput && user.telegram_chat_id) {
      telegramInput.value = user.telegram_chat_id;
    }
  }).catch(() => {});
}

function setActiveNavTab(view) {
  document.querySelectorAll(".nav-tab").forEach(t => t.classList.remove("nav-tab--active"));
  const tab = document.querySelector(`.nav-tab[data-view="${view}"]`);
  if (tab) tab.classList.add("nav-tab--active");
}

// ── Render Products Grid ────────────────────────────────────────────

function renderProducts() {
  productsGrid.innerHTML = "";

  const searchQuery = inputSearch?.value?.toLowerCase().trim() || "";
  const platformFilter = filterPlatform?.value || "all";

  const filtered = products.filter(p => {
    const matchesSearch = !searchQuery || (p.name || "").toLowerCase().includes(searchQuery);
    const matchesPlatform = platformFilter === "all" || p.platform === platformFilter;
    return matchesSearch && matchesPlatform;
  });

  if (filtered.length === 0 && products.length > 0) {
    productsGrid.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 3rem; color: var(--text-muted);">
        <p style="font-size: 2rem; margin-bottom: 0.5rem;">🔍</p>
        <p>No products match your search or filter.</p>
      </div>
    `;
  } else {
    filtered.forEach((product, index) => {
      const card = createProductCard(product, {
        onView: handleViewProduct,
        onRefresh: handleRefreshProduct,
        onDelete: handleDeleteProduct,
      });
      card.style.animationDelay = `${index * 0.06}s`;
      productsGrid.appendChild(card);
    });
  }

  productCountBadge.textContent = `${products.length} product${products.length !== 1 ? "s" : ""} tracked`;
  showHomeView();
}

// ── Load Products ───────────────────────────────────────────────────

async function loadProducts() {
  try {
    products = await fetchProducts();
    renderProducts();
  } catch (err) {
    console.error("Failed to load products:", err);
    showToast("Failed to connect to the server. Is the backend running?", "error");
    heroSection.style.display = "flex";
    productsSection.style.display = "none";
  }
}

// ── Handlers ────────────────────────────────────────────────────────

async function handleAddProduct(e) {
  e.preventDefault();

  const url = inputUrl.value.trim();
  const target = inputTarget.value.trim();

  if (!url) return;

  submitSpinner.style.display = "inline-block";
  submitText.textContent = "Scraping...";
  formError.style.display = "none";

  try {
    const product = await addProduct(url, target || null);
    products.unshift(product);
    renderProducts();
    closeModal();
    showToast(`Now tracking: ${product.name || "Product"}`, "success");
  } catch (err) {
    formError.textContent = err.message;
    formError.style.display = "block";
  } finally {
    submitSpinner.style.display = "none";
    submitText.textContent = "Start Tracking";
  }
}

async function handleViewProduct(id) {
  try {
    const detail = await getProductDetail(id);
    showDetailView();
    renderProductDetail(detailSection, detail, {
      onBack: () => { showHomeView(); loadProducts(); },
      onRefresh: handleRefreshProduct,
      onDelete: handleDeleteProduct,
    });
  } catch (err) {
    showToast("Failed to load product details", "error");
  }
}

async function handleRefreshProduct(id) {
  try {
    showToast("Refreshing price...", "info");
    const updated = await refreshPrice(id);

    const idx = products.findIndex((p) => p.id === id);
    if (idx !== -1) products[idx] = updated;

    if (currentView === "home") {
      renderProducts();
    } else {
      await handleViewProduct(id);
    }

    showToast(`Price updated: ₹${updated.current_price?.toLocaleString("en-IN") || "N/A"}`, "success");
  } catch (err) {
    showToast("Failed to refresh price", "error");
  }
}

async function handleDeleteProduct(id) {
  if (!confirm("Stop tracking this product? All price history will be deleted.")) return;

  try {
    await deleteProduct(id);
    products = products.filter((p) => p.id !== id);
    showHomeView();
    renderProducts();
    showToast("Product removed", "success");
  } catch (err) {
    showToast("Failed to delete product", "error");
  }
}

async function handleRefreshAll() {
  showToast("Refreshing all products...", "info");
  for (const product of products) {
    try {
      const updated = await refreshPrice(product.id);
      const idx = products.findIndex((p) => p.id === product.id);
      if (idx !== -1) products[idx] = updated;
    } catch (err) {
      console.error(`Failed to refresh product ${product.id}:`, err);
    }
  }
  renderProducts();
  showToast("All prices refreshed!", "success");
}

// ── Event Listeners ─────────────────────────────────────────────────

// Theme
document.getElementById("btn-theme-toggle")?.addEventListener("click", toggleTheme);

// Product actions
document.getElementById("btn-add-product").addEventListener("click", openModal);
document.getElementById("btn-hero-add").addEventListener("click", openModal);
document.getElementById("btn-modal-close").addEventListener("click", closeModal);
document.getElementById("btn-form-cancel").addEventListener("click", closeModal);
document.getElementById("btn-refresh-all").addEventListener("click", handleRefreshAll);

// Modal backdrop
modalOverlay.addEventListener("click", (e) => {
  if (e.target === modalOverlay) closeModal();
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeModal();
});

formAddProduct.addEventListener("submit", handleAddProduct);

// Search & Filter
inputSearch?.addEventListener("input", () => {
  if (currentView === "home") {
    productsGrid.innerHTML = "";
    const searchQuery = inputSearch.value.toLowerCase().trim();
    const platformFilter = filterPlatform?.value || "all";

    const filtered = products.filter(p => {
      const matchesSearch = !searchQuery || (p.name || "").toLowerCase().includes(searchQuery);
      const matchesPlatform = platformFilter === "all" || p.platform === platformFilter;
      return matchesSearch && matchesPlatform;
    });

    filtered.forEach((product, index) => {
      const card = createProductCard(product, {
        onView: handleViewProduct,
        onRefresh: handleRefreshProduct,
        onDelete: handleDeleteProduct,
      });
      card.style.animationDelay = `${index * 0.06}s`;
      productsGrid.appendChild(card);
    });
  }
});

filterPlatform?.addEventListener("change", () => {
  if (currentView === "home") {
    inputSearch?.dispatchEvent(new Event("input"));
  }
});

// Navigation tabs
document.querySelectorAll(".nav-tab").forEach(tab => {
  tab.addEventListener("click", () => {
    const view = tab.dataset.view;
    if (view === "home") {
      renderProducts();
    } else if (view === "compare") {
      showCompareView();
    }
  });
});

// User dropdown
const btnUserMenu = document.getElementById("btn-user-menu");
const userDropdown = document.getElementById("user-dropdown");

btnUserMenu?.addEventListener("click", (e) => {
  e.stopPropagation();
  userDropdown.style.display = userDropdown.style.display === "none" ? "block" : "none";
});

document.addEventListener("click", () => {
  if (userDropdown) userDropdown.style.display = "none";
});

// Logout
document.getElementById("btn-logout")?.addEventListener("click", () => {
  logout();
  showAuthScreen();
});

// Compare view from dropdown
document.getElementById("btn-compare-view")?.addEventListener("click", () => {
  userDropdown.style.display = "none";
  showCompareView();
});

// Settings
document.getElementById("btn-settings")?.addEventListener("click", () => {
  userDropdown.style.display = "none";
  showSettingsView();
});

document.getElementById("btn-settings-back")?.addEventListener("click", () => {
  renderProducts();
});

document.getElementById("btn-save-settings")?.addEventListener("click", async () => {
  const telegramId = document.getElementById("input-telegram-id")?.value.trim();
  try {
    await updateProfile({ telegram_chat_id: telegramId || null });
    showToast("Settings saved!", "success");
  } catch (err) {
    showToast("Failed to save settings", "error");
  }
});

// ── Init ────────────────────────────────────────────────────────────

initTheme();
setupAuth();

if (isLoggedIn()) {
  showApp();
  loadProducts();
} else {
  showAuthScreen();
}
