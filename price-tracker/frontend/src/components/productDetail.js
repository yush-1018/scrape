/**
 * Product Detail View — renders the expanded product detail with chart and CSV export.
 */

import { renderPriceChart, destroyChart } from "./priceChart.js";
import { exportPriceHistory } from "../api.js";

export function renderProductDetail(container, detail, { onBack, onRefresh, onDelete }) {
  destroyChart();

  const { product, price_history } = detail;
  const formatPrice = (p) => (p != null ? `₹${p.toLocaleString("en-IN")}` : "—");

  const imageHtml = product.image_url
    ? `<img class="detail__image" src="${product.image_url}" alt="${product.name}" />`
    : `<div class="detail__image card__image--placeholder" style="display:flex;align-items:center;justify-content:center;font-size:4rem;">📦</div>`;

  const priceRange = product.highest_price && product.lowest_price
    ? formatPrice(product.highest_price - product.lowest_price)
    : "—";

  // Availability badge
  const availBadge = product.is_available === false
    ? `<span class="detail__oos-badge">⚠️ Out of Stock</span>`
    : `<span class="detail__in-stock-badge">✅ In Stock</span>`;

  // Price drop percentage
  let dropInfo = "";
  if (product.current_price && product.highest_price && product.highest_price > product.current_price) {
    const dropPct = ((product.highest_price - product.current_price) / product.highest_price * 100).toFixed(1);
    dropInfo = `<span class="detail__drop-badge">↓${dropPct}% from highest</span>`;
  }

  container.innerHTML = `
    <div class="detail__back">
      <button class="btn btn--ghost" id="btn-detail-back">← Back to Products</button>
    </div>

    <div class="detail__header">
      ${imageHtml}
      <div class="detail__info">
        <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:8px;">
          <span class="card__platform card__platform--${product.platform}">${product.platform}</span>
          ${availBadge}
        </div>
        <h2 class="detail__name">${product.name || "Unknown Product"}</h2>
        <a class="detail__url" href="${product.url}" target="_blank" rel="noopener">${product.url}</a>
        <div class="detail__price-current">${formatPrice(product.current_price)} ${dropInfo}</div>
      </div>
    </div>

    <div class="detail__stats-grid">
      <div class="stat-card">
        <div class="stat-card__label">Current Price</div>
        <div class="stat-card__value" style="color:var(--accent)">${formatPrice(product.current_price)}</div>
      </div>
      <div class="stat-card">
        <div class="stat-card__label">Lowest Price</div>
        <div class="stat-card__value" style="color:var(--green)">${formatPrice(product.lowest_price)}</div>
      </div>
      <div class="stat-card">
        <div class="stat-card__label">Highest Price</div>
        <div class="stat-card__value" style="color:var(--red)">${formatPrice(product.highest_price)}</div>
      </div>
      <div class="stat-card">
        <div class="stat-card__label">Price Range</div>
        <div class="stat-card__value">${priceRange}</div>
      </div>
      ${product.target_price ? `
        <div class="stat-card">
          <div class="stat-card__label">Target Price</div>
          <div class="stat-card__value" style="color:var(--amber)">${formatPrice(product.target_price)}</div>
        </div>
      ` : ""}
      <div class="stat-card">
        <div class="stat-card__label">Data Points</div>
        <div class="stat-card__value">${price_history.length}</div>
      </div>
    </div>

    <div class="detail__chart-container">
      <h3 class="detail__chart-title">Price History</h3>
      <div class="chart-wrapper">
        <canvas id="price-chart"></canvas>
      </div>
      ${price_history.length === 0 ? '<p style="color:var(--text-muted);text-align:center;padding:2rem;">No price history yet. Click "Refresh Price" to record a data point.</p>' : ""}
    </div>

    <div class="detail__actions">
      <button class="btn btn--primary" id="btn-detail-refresh">↻ Refresh Price</button>
      <button class="btn btn--outline" id="btn-export-csv">📥 Export CSV</button>
      <a class="btn btn--outline" href="${product.url}" target="_blank" rel="noopener">🔗 Open Product Page</a>
      <button class="btn btn--danger" id="btn-detail-delete">✕ Stop Tracking</button>
    </div>
  `;

  // Render chart
  if (price_history.length > 0) {
    setTimeout(() => renderPriceChart("price-chart", price_history), 100);
  }

  // Event listeners
  document.getElementById("btn-detail-back").addEventListener("click", onBack);
  document.getElementById("btn-detail-refresh").addEventListener("click", () => onRefresh(product.id));
  document.getElementById("btn-detail-delete").addEventListener("click", () => onDelete(product.id));

  // CSV Export
  document.getElementById("btn-export-csv").addEventListener("click", async () => {
    try {
      const resp = await exportPriceHistory(product.id);
      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${product.name || "product"}_price_history.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("CSV export failed:", err);
    }
  });
}
