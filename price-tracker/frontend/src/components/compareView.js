/**
 * Compare View — displays products grouped by similarity for cross-platform comparison.
 */

import { compareProducts } from "../api.js";

export async function renderCompareView(container, { onViewProduct }) {
  container.innerHTML = `
    <div class="compare-header">
      <h2 class="section-title">📊 Price Comparison</h2>
      <p class="compare-subtitle">Compare the same products across different platforms to find the best deal.</p>
      <div class="compare-search">
        <span class="search-bar__icon">🔍</span>
        <input type="text" id="compare-search-input" class="search-bar__input" placeholder="Search by product name..." />
      </div>
    </div>
    <div id="compare-results" class="compare-results">
      <div class="compare-loading">
        <div class="spinner" style="display:inline-block;width:24px;height:24px;"></div>
        <span>Loading comparison data...</span>
      </div>
    </div>
  `;

  const resultsContainer = document.getElementById("compare-results");
  const searchInput = document.getElementById("compare-search-input");

  async function loadComparison(query = "") {
    try {
      resultsContainer.innerHTML = `
        <div class="compare-loading">
          <div class="spinner" style="display:inline-block;width:24px;height:24px;"></div>
          <span>Analyzing products...</span>
        </div>
      `;

      const data = await compareProducts(query);

      if (!data.groups || data.groups.length === 0) {
        resultsContainer.innerHTML = `
          <div class="compare-empty">
            <span class="compare-empty__icon">📭</span>
            <h3>No products to compare</h3>
            <p>Track the same product on multiple platforms to see comparisons here.</p>
          </div>
        `;
        return;
      }

      resultsContainer.innerHTML = data.groups.map((group, i) => `
        <div class="compare-group" style="animation-delay: ${i * 0.08}s">
          <div class="compare-group__header">
            <h3 class="compare-group__name">${group.name}</h3>
            <div class="compare-group__meta">
              <span class="compare-group__platforms">${group.platforms.length} platform${group.platforms.length !== 1 ? 's' : ''}</span>
              ${group.cheapest ? `<span class="compare-group__cheapest">Best: ₹${group.cheapest.toLocaleString("en-IN")}</span>` : ""}
            </div>
          </div>
          <div class="compare-group__products">
            ${group.products.map(p => `
              <div class="compare-product ${p.is_cheapest ? 'compare-product--cheapest' : ''}"
                   data-product-id="${p.id}">
                ${p.is_cheapest ? '<span class="compare-product__best-badge">🏆 Best Price</span>' : ""}
                ${!p.is_available ? '<span class="compare-product__oos">Out of Stock</span>' : ""}
                <div class="compare-product__platform">
                  <span class="card__platform card__platform--${p.platform}">${p.platform}</span>
                </div>
                <div class="compare-product__price ${!p.is_available ? 'card__price--oos' : ''}">
                  ${p.current_price ? `₹${p.current_price.toLocaleString("en-IN")}` : "N/A"}
                </div>
                <div class="compare-product__range">
                  ${p.lowest_price ? `Low: ₹${p.lowest_price.toLocaleString("en-IN")}` : ""}
                  ${p.highest_price ? ` · High: ₹${p.highest_price.toLocaleString("en-IN")}` : ""}
                </div>
                <a href="${p.url}" target="_blank" class="compare-product__link" onclick="event.stopPropagation()">View →</a>
              </div>
            `).join("")}
          </div>
        </div>
      `).join("");

      // Click handlers for comparison products
      resultsContainer.querySelectorAll(".compare-product").forEach(el => {
        el.addEventListener("click", () => {
          const id = parseInt(el.dataset.productId);
          if (id && onViewProduct) onViewProduct(id);
        });
      });

    } catch (err) {
      resultsContainer.innerHTML = `
        <div class="compare-empty">
          <span class="compare-empty__icon">⚠️</span>
          <h3>Failed to load comparison</h3>
          <p>${err.message}</p>
        </div>
      `;
    }
  }

  // Initial load
  await loadComparison();

  // Search with debounce
  let searchTimeout;
  searchInput.addEventListener("input", () => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => loadComparison(searchInput.value.trim()), 400);
  });
}
