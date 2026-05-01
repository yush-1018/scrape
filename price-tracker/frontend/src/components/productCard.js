/**
 * Product Card Component — renders a single tracked product card.
 * Features: price drop %, availability badge, target hit indicator.
 */

export function createProductCard(product, { onView, onRefresh, onDelete }) {
  const card = document.createElement("div");
  card.className = "product-card";
  card.setAttribute("data-product-id", product.id);

  // Calculate price drop percentage from highest
  let dropBadge = "";
  if (product.current_price && product.highest_price && product.highest_price > product.current_price) {
    const dropPct = ((product.highest_price - product.current_price) / product.highest_price * 100).toFixed(1);
    dropBadge = `<span class="card__price-change card__price-change--down">↓${dropPct}%</span>`;
  } else if (product.current_price && product.lowest_price && product.current_price > product.lowest_price) {
    const upPct = ((product.current_price - product.lowest_price) / product.lowest_price * 100).toFixed(1);
    dropBadge = `<span class="card__price-change card__price-change--up">↑${upPct}%</span>`;
  }

  // Check if target price is hit
  const targetHit = product.target_price && product.current_price && product.current_price <= product.target_price;

  // Check availability
  const isOOS = product.is_available === false;

  // Build image element
  const imageHtml = product.image_url
    ? `<img class="card__image" src="${product.image_url}" alt="${product.name || 'Product'}" loading="lazy" />`
    : `<div class="card__image card__image--placeholder">📦</div>`;

  // Platform badge class
  const platformClass = `card__platform--${product.platform}`;

  const formatPrice = (p) => p != null ? `₹${p.toLocaleString("en-IN")}` : "—";

  card.innerHTML = `
    ${targetHit ? '<span class="card__target-hit">🎯 Target Hit!</span>' : ""}
    ${isOOS ? '<span class="card__oos-badge">Out of Stock</span>' : ""}
    <div class="card__top">
      ${imageHtml}
      <div class="card__info">
        <span class="card__platform ${platformClass}">${product.platform}</span>
        <h3 class="card__name">${product.name || "Unknown Product"}</h3>
        <div class="card__price-row">
          <span class="card__price ${isOOS ? 'card__price--oos' : ''}">${formatPrice(product.current_price)}</span>
          ${dropBadge}
        </div>
      </div>
    </div>
    <div class="card__stats">
      <div class="card__stat">
        <div class="card__stat-label">Lowest</div>
        <div class="card__stat-value card__stat-value--low">${formatPrice(product.lowest_price)}</div>
      </div>
      <div class="card__stat">
        <div class="card__stat-label">Highest</div>
        <div class="card__stat-value card__stat-value--high">${formatPrice(product.highest_price)}</div>
      </div>
      ${product.target_price ? `
        <div class="card__stat">
          <div class="card__stat-label">Target</div>
          <div class="card__stat-value card__stat-value--target">${formatPrice(product.target_price)}</div>
        </div>
      ` : ""}
    </div>
    <div class="card__actions">
      <button class="btn btn--outline btn--sm btn-card-refresh" title="Refresh price">↻ Refresh</button>
      <button class="btn btn--danger btn--sm btn-card-delete" title="Stop tracking">✕ Remove</button>
    </div>
  `;

  // Event delegation
  card.addEventListener("click", (e) => {
    if (e.target.closest(".btn-card-refresh")) {
      e.stopPropagation();
      onRefresh(product.id);
    } else if (e.target.closest(".btn-card-delete")) {
      e.stopPropagation();
      onDelete(product.id);
    } else {
      onView(product.id);
    }
  });

  return card;
}
