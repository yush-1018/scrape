/**
 * Price Chart Component — renders a Chart.js line chart for price history.
 */

let chartInstance = null;

export function renderPriceChart(canvasId, priceHistory) {
  // Destroy previous chart if exists
  if (chartInstance) {
    chartInstance.destroy();
    chartInstance = null;
  }

  const canvas = document.getElementById(canvasId);
  if (!canvas || !priceHistory || priceHistory.length === 0) return;

  const ctx = canvas.getContext("2d");

  // Parse data
  const labels = priceHistory.map((entry) => {
    const d = new Date(entry.recorded_at);
    return d.toLocaleDateString("en-IN", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
  });

  const prices = priceHistory.map((entry) => entry.price);

  // Create gradient fill
  const gradient = ctx.createLinearGradient(0, 0, 0, 300);
  gradient.addColorStop(0, "rgba(99, 115, 255, 0.3)");
  gradient.addColorStop(1, "rgba(99, 115, 255, 0.0)");

  chartInstance = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Price (₹)",
          data: prices,
          borderColor: "#6373ff",
          backgroundColor: gradient,
          borderWidth: 2.5,
          fill: true,
          tension: 0.35,
          pointRadius: priceHistory.length > 20 ? 0 : 4,
          pointHoverRadius: 6,
          pointBackgroundColor: "#6373ff",
          pointBorderColor: "#0d0f18",
          pointBorderWidth: 2,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { intersect: false, mode: "index" },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "rgba(13, 15, 24, 0.95)",
          borderColor: "rgba(99, 115, 255, 0.3)",
          borderWidth: 1,
          titleColor: "#8b8fa3",
          bodyColor: "#e8eaed",
          bodyFont: { size: 14, weight: "bold" },
          padding: 12,
          cornerRadius: 8,
          displayColors: false,
          callbacks: {
            label: (ctx) => `₹${ctx.parsed.y.toLocaleString("en-IN")}`,
          },
        },
      },
      scales: {
        x: {
          grid: { color: "rgba(99, 115, 255, 0.06)" },
          ticks: { color: "#5c6078", font: { size: 11 }, maxTicksLimit: 8 },
        },
        y: {
          grid: { color: "rgba(99, 115, 255, 0.06)" },
          ticks: {
            color: "#5c6078",
            font: { size: 11 },
            callback: (val) => `₹${val.toLocaleString("en-IN")}`,
          },
        },
      },
    },
  });
}

export function destroyChart() {
  if (chartInstance) {
    chartInstance.destroy();
    chartInstance = null;
  }
}
