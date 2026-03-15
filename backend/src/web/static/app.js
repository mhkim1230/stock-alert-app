const FX_WATCHLIST_KEY = "stock-alert-fx-watchlist-v1";
const FX_OPTIONS = ["USD", "KRW", "JPY", "EUR", "CNY", "GBP", "HKD", "AUD"];
const SWIPE_ACTION_WIDTH = 208;

const state = {
  watchlist: [],
  stockQuotes: {},
  fxWatchlist: [],
  fxRates: {},
  stockAlerts: [],
  currencyAlerts: [],
  newsAlerts: [],
  notifications: [],
  unreadCount: 0,
  installPrompt: null,
  selectedAlertSymbol: "",
  selectedFxPair: null,
  lastFxLookup: { base: "USD", target: "KRW" },
  currentFxResult: null,
  analysisContext: null,
  openSwipeId: "",
};

const loadingState = {
  pending: 0,
  message: "불러오는 중입니다...",
};

const elements = {
  loginPanel: document.getElementById("login-panel"),
  appPanel: document.getElementById("app-panel"),
  loadingIndicator: document.getElementById("loading-indicator"),
  loadingText: document.getElementById("loading-text"),
  loginForm: document.getElementById("login-form"),
  loginError: document.getElementById("login-error"),
  logoutButton: document.getElementById("logout-button"),
  installButton: document.getElementById("install-button"),
  settingsInstallButton: document.getElementById("settings-install-button"),
  refreshWatchlistButton: document.getElementById("refresh-watchlist"),
  watchlistList: document.getElementById("watchlist-list"),
  fxWatchlistList: document.getElementById("fx-watchlist-list"),
  stockSearchResults: document.getElementById("stock-search-results"),
  fxResult: document.getElementById("fx-result"),
  fxForm: document.getElementById("fx-form"),
  fxBaseSelect: document.getElementById("fx-base-select"),
  fxTargetSelect: document.getElementById("fx-target-select"),
  refreshDashboard: document.getElementById("refresh-dashboard"),
  stockSearchModal: document.getElementById("stock-search-modal"),
  stockSearchQuery: document.getElementById("stock-search-query"),
  stockAlertModal: document.getElementById("stock-alert-modal"),
  selectedAlertSymbol: document.getElementById("selected-alert-symbol"),
  selectedStockAlerts: document.getElementById("selected-stock-alerts"),
  selectedNewsAlerts: document.getElementById("selected-news-alerts"),
  quickStockSymbol: document.getElementById("quick-stock-symbol"),
  quickNewsKeywords: document.getElementById("quick-news-keywords"),
  quickStockAlertForm: document.getElementById("quick-stock-alert-form"),
  fxAlertModal: document.getElementById("fx-alert-modal"),
  selectedFxPair: document.getElementById("selected-fx-pair"),
  selectedCurrencyAlerts: document.getElementById("selected-currency-alerts"),
  quickFxBase: document.getElementById("quick-fx-base"),
  quickFxTarget: document.getElementById("quick-fx-target"),
  quickFxAlertForm: document.getElementById("quick-fx-alert-form"),
  analysisModal: document.getElementById("analysis-modal"),
  analysisTitle: document.getElementById("analysis-title"),
  analysisSubtitle: document.getElementById("analysis-subtitle"),
  analysisPrice: document.getElementById("analysis-price"),
  analysisRangeSwitch: document.getElementById("analysis-range-switch"),
  analysisBody: document.getElementById("analysis-body"),
};

async function request(path, options = {}) {
  const { loadingMessage = "불러오는 중입니다...", skipLoading = false, ...fetchOptions } = options;
  beginLoading(loadingMessage, skipLoading);

  let response;
  try {
    response = await fetch(path, {
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        ...(fetchOptions.headers || {}),
      },
      ...fetchOptions,
    });
  } finally {
    endLoading(skipLoading);
  }

  if (response.status === 401) {
    showLoggedOut();
    throw new Error("로그인이 필요합니다.");
  }

  if (response.status === 204) {
    return null;
  }

  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : await response.text();
  if (!response.ok) {
    throw new Error(payload.detail || payload.message || "요청에 실패했습니다.");
  }
  return payload;
}

function beginLoading(message, skipLoading) {
  if (skipLoading) {
    return;
  }
  loadingState.pending += 1;
  loadingState.message = message;
  elements.loadingText.textContent = message;
  elements.loadingIndicator.classList.remove("hidden");
}

function endLoading(skipLoading) {
  if (skipLoading) {
    return;
  }
  loadingState.pending = Math.max(loadingState.pending - 1, 0);
  if (loadingState.pending === 0) {
    elements.loadingIndicator.classList.add("hidden");
    elements.loadingText.textContent = "불러오는 중입니다...";
  }
}

function setFormBusy(form, busy, busyText = "처리 중...") {
  form.querySelectorAll("button[type='submit']").forEach((button) => {
    if (!button.dataset.defaultLabel) {
      button.dataset.defaultLabel = button.textContent;
    }
    button.disabled = busy;
    button.textContent = busy ? busyText : button.dataset.defaultLabel;
  });
}

function setButtonBusy(button, busy, busyText = "처리 중...") {
  if (!button) {
    return;
  }
  if (!button.dataset.defaultLabel) {
    button.dataset.defaultLabel = button.textContent;
  }
  button.disabled = busy;
  button.textContent = busy ? busyText : button.dataset.defaultLabel;
}

async function withFormBusy(form, busyText, task) {
  setFormBusy(form, true, busyText);
  try {
    return await task();
  } finally {
    setFormBusy(form, false, busyText);
  }
}

async function withButtonBusy(button, busyText, task) {
  setButtonBusy(button, true, busyText);
  try {
    return await task();
  } finally {
    setButtonBusy(button, false, busyText);
  }
}

function formatPrice(value, unit = "KRW") {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return "-";
  }
  if (unit === "KRW") {
    return `${numeric.toLocaleString("ko-KR")}원`;
  }
  if (unit === "USD") {
    return `${numeric.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} USD`;
  }
  return `${numeric.toLocaleString("ko-KR", { minimumFractionDigits: 2, maximumFractionDigits: 4 })} ${unit}`;
}

function formatRate(value, unit) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return "-";
  }
  return `${numeric.toLocaleString("ko-KR", { minimumFractionDigits: 2, maximumFractionDigits: 4 })} ${unit}`;
}

function formatChangePercent(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return "";
  }
  return `${numeric > 0 ? "+" : ""}${numeric.toFixed(2)}%`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function toLocalDate(value) {
  if (!value) {
    return "-";
  }
  return new Date(value).toLocaleString("ko-KR");
}

function showLoadingList(target, message) {
  target.innerHTML = `<li class="empty-state loading-state">${message}</li>`;
}

function showLoadingCard(target, message) {
  target.innerHTML = `<div class="callout loading-state">${message}</div>`;
}

function showToast(message, kind = "info") {
  const root = document.getElementById("toast-root");
  const toast = document.createElement("div");
  toast.className = `toast ${kind}`;
  toast.textContent = message;
  root.appendChild(toast);
  setTimeout(() => toast.remove(), 3200);
}

function setView(name) {
  const nextView = document.querySelector(`.tab-button[data-view="${name}"]`) ? name : "dashboard";
  document.querySelectorAll(".tab-button").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === nextView);
  });
  document.querySelectorAll(".view").forEach((panel) => {
    panel.classList.toggle("active", panel.dataset.viewPanel === nextView);
  });
  window.location.hash = nextView;
}

function stockQuoteMarkup(symbol) {
  const quote = state.stockQuotes[symbol];
  if (!quote) {
    return `<small class="meta-line">시세를 아직 불러오지 못했습니다.</small>`;
  }
  const changeClass = Number(quote.change_percent) > 0 ? "up" : Number(quote.change_percent) < 0 ? "down" : "";
  return `
    <small class="meta-line">${quote.name || symbol} · ${quote.market || "-"}</small>
    <div class="quote-line">
      <span class="quote-price">${formatPrice(quote.price, quote.currency || "KRW")}</span>
      <span class="quote-change ${changeClass}">${formatChangePercent(quote.change_percent) || "보합"}</span>
    </div>
  `;
}

function fxRateMarkup(base, target) {
  const key = `${base}/${target}`;
  const rate = state.fxRates[key];
  if (!rate) {
    return `<small class="meta-line">현재 환율을 아직 불러오지 못했습니다.</small>`;
  }
  return `
    <small class="meta-line">${rate.source}</small>
    <div class="quote-line">
      <span class="quote-price">${formatRate(rate.rate, target)}</span>
    </div>
  `;
}

function renderStats() {
  return;
}

function setOpenSwipe(id = "") {
  state.openSwipeId = state.openSwipeId === id ? "" : id;
}

function closeSwipeActions() {
  state.openSwipeId = "";
}

function renderSwipeCard({ id, body, actions, extraClass = "" }) {
  const openedClass = state.openSwipeId === id ? " open" : "";
  return `
    <div class="swipe-card${openedClass}${extraClass ? ` ${extraClass}` : ""}" data-swipe-card="${id}">
      <div class="swipe-actions">
        ${actions}
      </div>
      <div class="swipe-surface" data-swipe-surface="${id}" role="button" tabindex="0" aria-expanded="${state.openSwipeId === id ? "true" : "false"}">
        ${body}
      </div>
    </div>
  `;
}

function renderStockWatchlist() {
  if (!state.watchlist.length) {
    elements.watchlistList.innerHTML =
      `<li class="empty-state">저장된 관심종목이 없습니다.</li>`;
    return;
  }

  elements.watchlistList.innerHTML = state.watchlist
    .map((item) => {
      const market = state.stockQuotes[item.symbol]?.market || "";
      return `
        <li>
          ${renderSwipeCard({
            id: `stock:${item.symbol}`,
            body: `
              <div class="resource-item quote-item swipe-item-content">
                <div class="resource-meta">
                  <strong class="resource-title">${escapeHtml(item.symbol)}</strong>
                  ${stockQuoteMarkup(item.symbol)}
                </div>
              </div>
            `,
            actions: `
              <button class="ghost-button small" type="button" data-action="open-stock-analysis" data-symbol="${escapeHtml(item.symbol)}" data-market="${escapeHtml(market)}">분석</button>
              <button class="ghost-button small" type="button" data-action="refresh-stock-quote" data-symbol="${escapeHtml(item.symbol)}">갱신</button>
              <button class="danger-button" type="button" data-action="delete-watchlist" data-symbol="${escapeHtml(item.symbol)}">삭제</button>
            `,
          })}
        </li>
      `;
    })
    .join("");

  bindSwipeCards();
}

function renderFxWatchlist() {
  if (!state.fxWatchlist.length) {
    elements.fxWatchlistList.innerHTML =
      `<li class="empty-state">저장된 관심환율이 없습니다.</li>`;
    return;
  }

  elements.fxWatchlistList.innerHTML = state.fxWatchlist
    .map((item) => {
      const pair = `${item.base}/${item.target}`;
      return `
        <li>
          ${renderSwipeCard({
            id: `fx:${pair}`,
            body: `
              <div class="resource-item quote-item swipe-item-content">
                <div class="resource-meta">
                  <strong class="resource-title">${escapeHtml(pair)}</strong>
                  ${fxRateMarkup(item.base, item.target)}
                </div>
              </div>
            `,
            actions: `
              <button class="ghost-button small" type="button" data-action="open-fx-analysis" data-base="${escapeHtml(item.base)}" data-target="${escapeHtml(item.target)}">분석</button>
              <button class="danger-button" type="button" data-action="delete-fx-watchlist" data-base="${escapeHtml(item.base)}" data-target="${escapeHtml(item.target)}">삭제</button>
            `,
          })}
        </li>
      `;
    })
    .join("");

  bindSwipeCards();
}

function renderNotifications(listTarget, items = state.notifications) {
  if (!items.length) {
    listTarget.innerHTML = `<li class="empty-state">알림 기록이 아직 없습니다.</li>`;
    return;
  }

  listTarget.innerHTML = items
    .map(
      (item) => `
        <li class="timeline-item">
          <strong>${item.message}</strong>
          <small>${item.alert_type} · ${toLocalDate(item.sent_at)}</small>
          <small>${item.is_read ? "읽음" : "안 읽음"} · 상태 ${item.status}</small>
          ${item.is_read ? "" : `<button class="ghost-button small" type="button" data-action="read-notification" data-id="${item.id}">읽음 처리</button>`}
        </li>
      `
    )
    .join("");
}

function renderSelectedStockAlerts() {
  const symbol = state.selectedAlertSymbol;
  const stockAlerts = state.stockAlerts.filter((item) => item.stock_symbol === symbol);
  const newsAlerts = state.newsAlerts.filter((item) => item.keywords.toLowerCase().includes(symbol.toLowerCase()));

  elements.selectedStockAlerts.innerHTML = stockAlerts.length
    ? stockAlerts
        .map(
          (item) => `
            <li class="resource-item compact-item">
              <div class="resource-meta">
                <strong>${item.condition} ${item.target_price}</strong>
                <small>등록 ${toLocalDate(item.created_at)}</small>
              </div>
              <button class="danger-button" type="button" data-action="delete-stock-alert" data-id="${item.id}">삭제</button>
            </li>
          `
        )
        .join("")
    : `<li class="empty-state">등록된 주식 알림이 없습니다.</li>`;

  elements.selectedNewsAlerts.innerHTML = newsAlerts.length
    ? newsAlerts
        .map(
          (item) => `
            <li class="resource-item compact-item">
              <div class="resource-meta">
                <strong>${item.keywords}</strong>
                <small>등록 ${toLocalDate(item.created_at)}</small>
              </div>
              <button class="danger-button" type="button" data-action="delete-news-alert" data-id="${item.id}">삭제</button>
            </li>
          `
        )
        .join("")
    : `<li class="empty-state">등록된 뉴스 알림이 없습니다.</li>`;
}

function renderSelectedCurrencyAlerts() {
  const selected = state.selectedFxPair;
  if (!selected) {
    elements.selectedCurrencyAlerts.innerHTML = `<li class="empty-state">선택된 환율이 없습니다.</li>`;
    return;
  }

  const items = state.currencyAlerts.filter(
    (item) => item.base_currency === selected.base && item.target_currency === selected.target
  );

  elements.selectedCurrencyAlerts.innerHTML = items.length
    ? items
        .map(
          (item) => `
            <li class="resource-item compact-item">
              <div class="resource-meta">
                <strong>${item.condition} ${item.target_rate}</strong>
                <small>등록 ${toLocalDate(item.created_at)}</small>
              </div>
              <button class="danger-button" type="button" data-action="delete-currency-alert" data-id="${item.id}">삭제</button>
            </li>
          `
        )
        .join("")
    : `<li class="empty-state">등록된 환율 알림이 없습니다.</li>`;
}

function prefillStockAlertForm(symbol, preset = {}) {
  const form = elements.quickStockAlertForm;
  form.reset();
  elements.quickStockSymbol.value = symbol;
  elements.quickNewsKeywords.value = symbol;
  const targetInput = form.querySelector("input[name='target_price']");
  const conditionSelect = form.querySelector("select[name='condition']");
  if (preset.targetPrice != null) {
    targetInput.value = Number(preset.targetPrice).toFixed(2);
  }
  conditionSelect.value = preset.condition || "above";
}

function prefillFxAlertForm(base, target, preset = {}) {
  const form = elements.quickFxAlertForm;
  form.reset();
  elements.quickFxBase.value = base;
  elements.quickFxTarget.value = target;
  const targetInput = form.querySelector("input[name='target_rate']");
  const conditionSelect = form.querySelector("select[name='condition']");
  if (preset.targetRate != null) {
    targetInput.value = Number(preset.targetRate).toFixed(4);
  }
  conditionSelect.value = preset.condition || "above";
}

function renderAnalysisValueCard({ label, value, priceUnit, formatter }) {
  return `
    <div class="stat-card">
      <small>${label}</small>
      <strong>${formatter(value, priceUnit)}</strong>
    </div>
  `;
}

function setAnalysisHeader({ title = "상세분석", subtitle = "종목을 선택하면 종합 보고서를 보여드립니다.", price = "-" } = {}) {
  elements.analysisTitle.textContent = title;
  elements.analysisSubtitle.textContent = subtitle;
  elements.analysisPrice.textContent = price;
}

function renderCurrentFxResult(payload) {
  const pair = `${payload.base_currency}/${payload.target_currency}`;
  elements.fxResult.innerHTML = renderSwipeCard({
    id: `lookup:${pair}`,
    extraClass: "fx-result-swipe",
    body: `
      <div class="resource-item quote-item swipe-item-content">
        <div class="resource-meta">
          <strong class="resource-title">${escapeHtml(pair)}</strong>
          <small class="meta-line">${escapeHtml(payload.source)}</small>
          <div class="quote-line">
            <span class="quote-price">${formatRate(payload.rate, payload.target_currency)}</span>
          </div>
        </div>
      </div>
    `,
    actions: `
      <button class="ghost-button small" type="button" data-action="add-current-fx-pair">저장</button>
      <button class="ghost-button small" type="button" data-action="open-current-fx-analysis">분석</button>
    `,
  });
  bindSwipeCards();
}

function renderCurrentFxResultFromState() {
  if (state.currentFxResult) {
    renderCurrentFxResult(state.currentFxResult);
    return;
  }
  renderFxSelectionError("조회 결과가 없습니다.");
}

function renderFxSelectionError(message) {
  elements.fxResult.innerHTML = `<div class="callout">${message}</div>`;
}

function renderAnalysis(data) {
  const formatter = data.asset_type === "currency" ? formatRate : formatPrice;
  const buySellCards = [
    renderAnalysisValueCard({
      label: "1차 매수가",
      value: data.first_buy,
      priceUnit: data.price_unit,
      formatter,
    }),
    renderAnalysisValueCard({
      label: "2차 매수가",
      value: data.second_buy,
      priceUnit: data.price_unit,
      formatter,
    }),
    renderAnalysisValueCard({
      label: "1차 매도가",
      value: data.first_sell,
      priceUnit: data.price_unit,
      formatter,
    }),
    renderAnalysisValueCard({
      label: "2차 매도가",
      value: data.second_sell,
      priceUnit: data.price_unit,
      formatter,
    }),
  ];

  setAnalysisHeader({
    title: `${data.name}`,
    subtitle: `${data.symbol} · ${data.timeframe}`,
    price: formatter(data.current_price, data.price_unit),
  });

  elements.analysisBody.innerHTML = `
    <section class="analysis-hero-card">
      <p class="analysis-chip">${data.trend}</p>
      <h4>${data.summary_title}</h4>
      <p class="analysis-copy">${data.summary_body}</p>
      <div class="analysis-meta-grid">
        <div class="stat-card">
          <small>분석 신뢰도</small>
          <strong>${data.confidence_score}점 · ${data.confidence_label}</strong>
        </div>
        <div class="stat-card">
          <small>기본 대응</small>
          <strong>${data.bias}</strong>
        </div>
      </div>
    </section>
    <section class="analysis-section-card">
      <h5>추세 예측</h5>
      <p class="analysis-copy">${data.trend_outlook}</p>
    </section>
    <section class="analysis-section-card">
      <h5>대응 전략</h5>
      <p class="analysis-copy">${data.action_plan}</p>
    </section>
    <section class="analysis-section-card">
      <h5>매수 · 매도 · 손절 구간</h5>
      <div class="analysis-grid analysis-plan-grid">
        ${buySellCards.join("")}
        <div class="stat-card">
          <small>손절 기준</small>
          <strong>${formatter(data.stop_loss, data.price_unit)}</strong>
        </div>
      </div>
      <div class="analysis-copy-group">
        <p class="analysis-copy"><strong>매수 전략</strong> ${data.buy_plan}</p>
        <p class="analysis-copy"><strong>매도 전략</strong> ${data.sell_plan}</p>
        <p class="analysis-copy"><strong>손절 전략</strong> ${data.loss_cut_plan}</p>
      </div>
    </section>
    ${data.investor_summary ? `
      <section class="analysis-section-card">
        <h5>수급 해석</h5>
        <p class="analysis-copy">${data.investor_summary}</p>
      </section>
    ` : ""}
    ${data.news_brief ? `
      <section class="analysis-section-card">
        <h5>뉴스·국제정세 영향</h5>
        <p class="analysis-copy">${data.news_brief}</p>
      </section>
    ` : ""}
    <section class="analysis-section-card">
      <h5>위험 요인</h5>
      <ul class="analysis-notes">
        ${(data.risk_notes || []).length ? data.risk_notes.map((note) => `<li>${note}</li>`).join("") : "<li>현재 확인된 특이 위험 요인은 제한적입니다.</li>"}
      </ul>
    </section>
    <section class="analysis-section-card">
      <h5>판단 근거</h5>
      <ul class="analysis-notes">
      ${data.notes.map((note) => `<li>${note}</li>`).join("")}
      </ul>
    </section>
  `;
}

async function migrateLegacyFxWatchlist() {
  try {
    const raw = localStorage.getItem(FX_WATCHLIST_KEY);
    if (!raw) {
      return;
    }
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed) || !parsed.length) {
      localStorage.removeItem(FX_WATCHLIST_KEY);
      return;
    }

    for (const item of parsed) {
      const base = String(item.base || "").toUpperCase();
      const target = String(item.target || "").toUpperCase();
      if (base.length !== 3 || target.length !== 3) {
        continue;
      }
      try {
        await request("/watchlist/fx", {
          method: "POST",
          body: JSON.stringify({ base_currency: base, target_currency: target }),
          skipLoading: true,
        });
      } catch (error) {
        if (!String(error.message).includes("already exists")) {
          throw error;
        }
      }
    }
    localStorage.removeItem(FX_WATCHLIST_KEY);
  } catch {
    // Ignore legacy migration issues and continue with DB-backed state.
  }
}

function bindSwipeCards() {
  document.querySelectorAll("[data-swipe-surface]").forEach((surface) => {
    const cardId = surface.dataset.swipeSurface;
    const card = surface.closest("[data-swipe-card]");
    if (!card) {
      return;
    }

    let startX = 0;
    let currentX = 0;
    let dragging = false;

    const applyOffset = (value) => {
      card.style.setProperty("--swipe-offset", `${value}px`);
    };

    const resetOffset = () => {
      card.style.removeProperty("--swipe-offset");
    };

    surface.onpointerdown = (event) => {
      if (event.pointerType === "mouse" && event.button !== 0) {
        return;
      }
      startX = event.clientX;
      currentX = event.clientX;
      dragging = true;
      card.classList.add("dragging");
      surface.setPointerCapture?.(event.pointerId);
    };

    surface.onpointermove = (event) => {
      if (!dragging) {
        return;
      }
      currentX = event.clientX;
      const delta = Math.max(-SWIPE_ACTION_WIDTH, Math.min(0, currentX - startX));
      applyOffset(delta);
    };

    surface.onpointerup = (event) => {
      if (!dragging) {
        return;
      }
      dragging = false;
      card.classList.remove("dragging");
      resetOffset();
      surface.releasePointerCapture?.(event.pointerId);
      const delta = currentX - startX;
      if (delta <= -52) {
        state.openSwipeId = cardId;
      } else if (delta >= 32) {
        state.openSwipeId = "";
      } else if (event.pointerType === "mouse") {
        setOpenSwipe(cardId);
      }
      renderAll();
    };

    surface.onpointercancel = () => {
      dragging = false;
      card.classList.remove("dragging");
      resetOffset();
      renderAll();
    };

    surface.onkeydown = (event) => {
      if (event.key !== "Enter" && event.key !== " ") {
        return;
      }
      event.preventDefault();
      setOpenSwipe(cardId);
      renderAll();
    };
  });
}

function renderAll() {
  renderStats();
  renderCurrentFxResultFromState();
  renderStockWatchlist();
  renderFxWatchlist();
}

async function refreshStockQuotes() {
  const quotes = await Promise.all(
    state.watchlist.map(async (item) => {
      try {
        const quote = await request(`/stocks/${item.symbol}`, {
          skipLoading: true,
        });
        return [item.symbol, quote];
      } catch {
        return [item.symbol, null];
      }
    })
  );
  state.stockQuotes = Object.fromEntries(quotes);
}

async function refreshFxRates() {
  const rates = await Promise.all(
    state.fxWatchlist.map(async (pair) => {
      try {
        const payload = await request(
          `/currency/rate?base=${encodeURIComponent(pair.base)}&target=${encodeURIComponent(pair.target)}`,
          { skipLoading: true }
        );
        return [`${pair.base}/${pair.target}`, payload];
      } catch {
        return [`${pair.base}/${pair.target}`, null];
      }
    })
  );
  state.fxRates = Object.fromEntries(rates);
}

async function refreshData() {
  const [watchlist, fxWatchlist] = await Promise.all([
    request("/watchlist", { loadingMessage: "관심종목을 불러오는 중입니다..." }),
    request("/watchlist/fx", { loadingMessage: "관심환율을 불러오는 중입니다..." }),
  ]);

  state.watchlist = watchlist;
  state.fxWatchlist = fxWatchlist.map((item) => ({
    id: item.id,
    base: item.base_currency,
    target: item.target_currency,
  }));

  await Promise.all([refreshStockQuotes(), refreshFxRates()]);
  renderAll();
}

function showLoggedIn() {
  elements.loginPanel.classList.add("hidden");
  elements.appPanel.classList.remove("hidden");
  elements.logoutButton.classList.remove("hidden");
}

function showLoggedOut() {
  closeSwipeActions();
  elements.loginPanel.classList.remove("hidden");
  elements.appPanel.classList.add("hidden");
  elements.logoutButton.classList.add("hidden");
  closeStockSearchModal();
  closeStockAlertModal();
  closeFxAlertModal();
  closeAnalysisModal();
}

async function bootstrap() {
  try {
    await request("/session/me", { loadingMessage: "세션을 확인하는 중입니다..." });
    await migrateLegacyFxWatchlist();
    showLoggedIn();
    await refreshData();
    await handleFxLookupWithPair(state.lastFxLookup.base, state.lastFxLookup.target);
  } catch {
    showLoggedOut();
  }
}

async function handleLogin(event) {
  event.preventDefault();
  elements.loginError.classList.add("hidden");
  const form = event.currentTarget;
  const formData = new FormData(form);

  try {
    await withFormBusy(form, "접속 중...", async () => {
      await request("/session/login", {
        method: "POST",
        body: JSON.stringify({ password: formData.get("password") }),
        loadingMessage: "로그인하는 중입니다...",
      });
    });
    form.reset();
    showLoggedIn();
    await refreshData();
    await handleFxLookupWithPair(state.lastFxLookup.base, state.lastFxLookup.target);
    showToast("로그인되었습니다.", "success");
  } catch (error) {
    elements.loginError.textContent = error.message;
    elements.loginError.classList.remove("hidden");
  }
}

async function handleLogout() {
  await withButtonBusy(elements.logoutButton, "로그아웃 중...", async () => {
    await request("/session/logout", {
      method: "POST",
      loadingMessage: "로그아웃하는 중입니다...",
    });
  });
  showLoggedOut();
  showToast("로그아웃되었습니다.", "info");
}

function openStockSearchModal(query = "") {
  elements.stockSearchModal.classList.remove("hidden");
  if (query) {
    elements.stockSearchQuery.value = query;
  }
  elements.stockSearchQuery.focus();
}

function closeStockSearchModal() {
  elements.stockSearchModal.classList.add("hidden");
}

function openStockAlertModal(symbol, preset = null) {
  closeSwipeActions();
  state.selectedAlertSymbol = symbol;
  elements.selectedAlertSymbol.textContent = symbol;
  prefillStockAlertForm(symbol, preset || {});
  renderSelectedStockAlerts();
  elements.stockAlertModal.classList.remove("hidden");
}

function closeStockAlertModal() {
  state.selectedAlertSymbol = "";
  elements.stockAlertModal.classList.add("hidden");
}

function openFxAlertModal(base, target, preset = null) {
  closeSwipeActions();
  state.selectedFxPair = { base, target };
  elements.selectedFxPair.textContent = `${base}/${target}`;
  prefillFxAlertForm(base, target, preset || {});
  renderSelectedCurrencyAlerts();
  elements.fxAlertModal.classList.remove("hidden");
}

function closeFxAlertModal() {
  state.selectedFxPair = null;
  elements.fxAlertModal.classList.add("hidden");
}

function openAnalysisModal() {
  closeSwipeActions();
  syncAnalysisRangeSwitch();
  elements.analysisModal.classList.remove("hidden");
}

function closeAnalysisModal() {
  elements.analysisModal.classList.add("hidden");
  elements.analysisBody.innerHTML = "";
  setAnalysisHeader();
  state.analysisContext = null;
}

function renderStockSearchResults(results) {
  if (!results.length) {
    elements.stockSearchResults.innerHTML = `<li class="empty-state">검색 결과가 없습니다.</li>`;
    return;
  }

  elements.stockSearchResults.innerHTML = results
    .map(
      (item) => `
        <li class="resource-item quote-item">
          <div class="resource-meta">
            <strong>${item.symbol} · ${item.name}</strong>
            <small>${item.market || "-"} · ${formatPrice(item.price, item.currency || "KRW")}</small>
            <small>${formatChangePercent(item.change_percent)} · ${item.source}</small>
          </div>
          <div class="resource-actions">
            <button class="primary-button small-button" type="button" data-action="add-watchlist-symbol" data-symbol="${item.symbol}">추가</button>
            <button class="ghost-button small" type="button" data-action="open-stock-analysis" data-symbol="${item.symbol}" data-market="${item.market || ""}">상세분석</button>
          </div>
        </li>
      `
    )
    .join("");
}

async function handleStockSearch(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const formData = new FormData(form);
  const query = formData.get("query");

  showLoadingList(elements.stockSearchResults, "종목을 조회하는 중입니다...");
  try {
    await withFormBusy(form, "조회 중...", async () => {
      const payload = await request(`/stocks/search?query=${encodeURIComponent(query)}`, {
        loadingMessage: "종목을 검색하는 중입니다...",
      });
      renderStockSearchResults(payload.results || []);
    });
  } catch (error) {
    elements.stockSearchResults.innerHTML = `<li class="empty-state">${error.message}</li>`;
    showToast(error.message, "error");
  }
}

async function handleFxLookup(event) {
  event?.preventDefault();
  await handleFxSelectionChange();
}

async function handleFxLookupWithPair(base, target) {
  state.lastFxLookup = { base, target };
  state.currentFxResult = null;
  closeSwipeActions();

  if (!FX_OPTIONS.includes(base) || !FX_OPTIONS.includes(target)) {
    renderFxSelectionError("지원하지 않는 통화입니다.");
    return;
  }
  if (base === target) {
    renderFxSelectionError("같은 통화끼리는 조회할 수 없습니다.");
    return;
  }

  showLoadingCard(elements.fxResult, "환율을 조회하는 중입니다...");
  try {
    const payload = await request(`/currency/rate?base=${encodeURIComponent(base)}&target=${encodeURIComponent(target)}`, {
      loadingMessage: "환율을 조회하는 중입니다...",
    });
    state.currentFxResult = payload;
    renderCurrentFxResultFromState();
  } catch (error) {
    state.currentFxResult = null;
    showLoadingCard(elements.fxResult, error.message);
    showToast(error.message, "error");
  }
}

async function handleFxSelectionChange() {
  const base = String(elements.fxBaseSelect.value).toUpperCase();
  const target = String(elements.fxTargetSelect.value).toUpperCase();
  if (
    state.currentFxResult &&
    state.lastFxLookup.base === base &&
    state.lastFxLookup.target === target &&
    state.currentFxResult.base_currency === base &&
    state.currentFxResult.target_currency === target
  ) {
    return;
  }
  await handleFxLookupWithPair(base, target);
}

async function handleFxWatchlistSubmit(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const formData = new FormData(form);
  const base = String(formData.get("base")).toUpperCase();
  const target = String(formData.get("target")).toUpperCase();
  const exists = state.fxWatchlist.some((item) => item.base === base && item.target === target);
  if (exists) {
    showToast("이미 저장된 환율 페어입니다.", "info");
    return;
  }

  try {
    await withFormBusy(form, "저장 중...", async () => {
      await request("/watchlist/fx", {
        method: "POST",
        body: JSON.stringify({ base_currency: base, target_currency: target }),
        loadingMessage: "관심환율을 저장하는 중입니다...",
      });
    });
    form.reset();
    await refreshData();
    showToast("관심환율을 저장했습니다.", "success");
  } catch (error) {
    showToast(error.message, "error");
  }
}

async function handleQuickStockAlertSubmit(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const formData = new FormData(form);

  try {
    await withFormBusy(form, "추가 중...", async () => {
      await request("/alerts/stocks", {
        method: "POST",
        body: JSON.stringify({
          stock_symbol: formData.get("stock_symbol"),
          target_price: Number(formData.get("target_price")),
          condition: formData.get("condition"),
        }),
        loadingMessage: "주식 알림을 추가하는 중입니다...",
      });
    });
    form.reset();
    elements.quickStockSymbol.value = state.selectedAlertSymbol;
    await refreshData();
    renderSelectedStockAlerts();
    showToast("주식 알림을 추가했습니다.", "success");
  } catch (error) {
    showToast(error.message, "error");
  }
}

async function handleQuickNewsAlertSubmit(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const formData = new FormData(form);

  try {
    await withFormBusy(form, "추가 중...", async () => {
      await request("/alerts/news", {
        method: "POST",
        body: JSON.stringify({ keywords: formData.get("keywords") }),
        loadingMessage: "뉴스 알림을 추가하는 중입니다...",
      });
    });
    form.reset();
    elements.quickNewsKeywords.value = state.selectedAlertSymbol;
    await refreshData();
    renderSelectedStockAlerts();
    showToast("뉴스 알림을 추가했습니다.", "success");
  } catch (error) {
    showToast(error.message, "error");
  }
}

async function handleQuickFxAlertSubmit(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const formData = new FormData(form);

  try {
    await withFormBusy(form, "추가 중...", async () => {
      await request("/alerts/currencies", {
        method: "POST",
        body: JSON.stringify({
          base_currency: formData.get("base_currency"),
          target_currency: formData.get("target_currency"),
          target_rate: Number(formData.get("target_rate")),
          condition: formData.get("condition"),
        }),
        loadingMessage: "환율 알림을 추가하는 중입니다...",
      });
    });
    form.reset();
    elements.quickFxBase.value = state.selectedFxPair.base;
    elements.quickFxTarget.value = state.selectedFxPair.target;
    await refreshData();
    renderSelectedCurrencyAlerts();
    showToast("환율 알림을 추가했습니다.", "success");
  } catch (error) {
    showToast(error.message, "error");
  }
}

async function openStockAnalysis(symbol, market = "") {
  state.analysisContext = {
    assetType: "stock",
    symbol,
    market,
    period: state.analysisContext?.assetType === "stock" && state.analysisContext?.symbol === symbol ? state.analysisContext.period : "short",
  };
  openAnalysisModal();
  await loadCurrentAnalysis();
}

async function openFxAnalysis(base, target) {
  state.analysisContext = {
    assetType: "currency",
    base,
    target,
    period: state.analysisContext?.assetType === "currency" && state.analysisContext?.base === base && state.analysisContext?.target === target ? state.analysisContext.period : "short",
  };
  openAnalysisModal();
  await loadCurrentAnalysis();
}

function syncAnalysisRangeSwitch() {
  const current = state.analysisContext?.period || "short";
  elements.analysisRangeSwitch.querySelectorAll(".analysis-range-tab").forEach((button) => {
    const active = button.dataset.period === current;
    button.classList.toggle("active", active);
    button.setAttribute("aria-selected", active ? "true" : "false");
  });
}

async function loadCurrentAnalysis() {
  if (!state.analysisContext) {
    return;
  }

  const { assetType, symbol, market, base, target, period } = state.analysisContext;
  const basisLabel = period === "medium" ? "주봉" : period === "long" ? "월봉" : "일봉";
  setAnalysisHeader({
    title: "상세분석 준비 중",
    subtitle: `${basisLabel} 기준 종합 보고서를 만드는 중입니다.`,
    price: "-",
  });
  showLoadingCard(elements.analysisBody, `${basisLabel} 기준으로 상세분석을 준비하는 중입니다...`);

  try {
    let payload;
    if (assetType === "stock") {
      const qs = market ? `?market=${encodeURIComponent(market)}` : "";
      payload = await request(`/analysis/stocks/${encodeURIComponent(symbol)}/${period}${qs}`, {
        loadingMessage: `${basisLabel} 기준 주식 상세분석을 준비하는 중입니다...`,
      });
    } else {
      payload = await request(`/analysis/currencies/${encodeURIComponent(base)}/${encodeURIComponent(target)}/${period}`, {
        loadingMessage: `${basisLabel} 기준 환율 상세분석을 준비하는 중입니다...`,
      });
    }
    renderAnalysis(payload);
  } catch (error) {
    showLoadingCard(elements.analysisBody, error.message);
    showToast(error.message, "error");
  }
}

function submitOnEnter(event) {
  if (event.key !== "Enter" || event.shiftKey) {
    return;
  }
  const form = event.currentTarget.form;
  if (!form) {
    return;
  }
  event.preventDefault();
  form.requestSubmit();
}

function setupEnterSubmit() {
  document.querySelectorAll("input").forEach((input) => {
    input.addEventListener("keydown", submitOnEnter);
  });
}

async function handleListActions(event) {
  const surface = event.target.closest("[data-swipe-surface]");
  if (surface && !event.target.closest("[data-action]")) {
    setOpenSwipe(surface.dataset.swipeSurface || "");
    renderAll();
    return;
  }

  if (!event.target.closest("[data-swipe-card]") && state.openSwipeId) {
    closeSwipeActions();
    renderAll();
  }

  const trigger = event.target.closest("[data-action]");
  const action = trigger?.dataset.action;
  if (!action) {
    return;
  }

  try {
    if (action === "open-stock-search") {
      openStockSearchModal();
      return;
    }
    if (action === "close-stock-search") {
      closeStockSearchModal();
      return;
    }
    if (action === "add-current-fx-pair") {
      const { base, target } = state.lastFxLookup;
      const exists = state.fxWatchlist.some((item) => item.base === base && item.target === target);
      if (!exists) {
        await request("/watchlist/fx", {
          method: "POST",
          body: JSON.stringify({ base_currency: base, target_currency: target }),
          loadingMessage: "현재 환율 페어를 저장하는 중입니다...",
        });
        await refreshData();
      }
      showToast("현재 환율 페어를 저장했습니다.", "success");
      return;
    }
    if (action === "open-current-fx-analysis") {
      await openFxAnalysis(state.lastFxLookup.base, state.lastFxLookup.target);
      return;
    }
    if (action === "open-current-fx-alert") {
      openFxAlertModal(state.lastFxLookup.base, state.lastFxLookup.target);
      return;
    }
    if (action === "open-alert-modal") {
      openStockAlertModal(trigger.dataset.symbol);
      return;
    }
    if (action === "prefill-stock-alert") {
      openStockAlertModal(trigger.dataset.symbol, {
        targetPrice: Number(trigger.dataset.targetPrice),
        condition: trigger.dataset.condition,
      });
      return;
    }
    if (action === "close-alert-modal") {
      closeStockAlertModal();
      return;
    }
    if (action === "open-fx-alert-modal") {
      openFxAlertModal(trigger.dataset.base, trigger.dataset.target);
      return;
    }
    if (action === "prefill-fx-alert") {
      openFxAlertModal(trigger.dataset.base, trigger.dataset.target, {
        targetRate: Number(trigger.dataset.targetRate),
        condition: trigger.dataset.condition,
      });
      return;
    }
    if (action === "close-fx-alert-modal") {
      closeFxAlertModal();
      return;
    }
    if (action === "open-stock-analysis") {
      await openStockAnalysis(trigger.dataset.symbol, trigger.dataset.market || "");
      return;
    }
    if (action === "open-fx-analysis") {
      await openFxAnalysis(trigger.dataset.base, trigger.dataset.target);
      return;
    }
    if (action === "refresh-stock-quote") {
      await withButtonBusy(trigger, "갱신 중...", async () => {
        const quote = await request(`/stocks/${encodeURIComponent(trigger.dataset.symbol)}`, {
          loadingMessage: "현재가를 다시 불러오는 중입니다...",
        });
        state.stockQuotes[trigger.dataset.symbol] = quote;
      });
      renderStockWatchlist();
      showToast("현재가를 갱신했습니다.", "success");
      return;
    }
    if (action === "close-analysis-modal") {
      closeAnalysisModal();
      return;
    }
    if (action === "add-watchlist-symbol") {
      await withButtonBusy(trigger, "추가 중...", async () => {
        await request("/watchlist", {
          method: "POST",
          body: JSON.stringify({ symbol: trigger.dataset.symbol }),
          loadingMessage: "관심종목에 추가하는 중입니다...",
        });
      });
      closeStockSearchModal();
      setView("watchlist");
      await refreshData();
      showToast("관심종목을 추가했습니다.", "success");
      return;
    }
    if (action === "delete-watchlist") {
      await withButtonBusy(trigger, "삭제 중...", async () => {
        await request(`/watchlist/${trigger.dataset.symbol}`, {
          method: "DELETE",
          loadingMessage: "관심종목을 삭제하는 중입니다...",
        });
      });
      await refreshData();
      showToast("관심종목을 삭제했습니다.", "info");
      return;
    }
    if (action === "delete-fx-watchlist") {
      await withButtonBusy(trigger, "삭제 중...", async () => {
        await request(
          `/watchlist/fx/${encodeURIComponent(trigger.dataset.base)}/${encodeURIComponent(trigger.dataset.target)}`,
          {
            method: "DELETE",
            loadingMessage: "관심환율을 삭제하는 중입니다...",
          }
        );
      });
      await refreshData();
      showToast("관심환율을 삭제했습니다.", "info");
      return;
    }
    if (action === "delete-stock-alert") {
      await withButtonBusy(trigger, "삭제 중...", async () => {
        await request(`/alerts/stocks/${trigger.dataset.id}`, {
          method: "DELETE",
          loadingMessage: "주식 알림을 삭제하는 중입니다...",
        });
      });
      await refreshData();
      renderSelectedStockAlerts();
      showToast("주식 알림을 삭제했습니다.", "info");
      return;
    }
    if (action === "delete-currency-alert") {
      await withButtonBusy(trigger, "삭제 중...", async () => {
        await request(`/alerts/currencies/${trigger.dataset.id}`, {
          method: "DELETE",
          loadingMessage: "환율 알림을 삭제하는 중입니다...",
        });
      });
      await refreshData();
      renderSelectedCurrencyAlerts();
      showToast("환율 알림을 삭제했습니다.", "info");
      return;
    }
    if (action === "delete-news-alert") {
      await withButtonBusy(trigger, "삭제 중...", async () => {
        await request(`/alerts/news/${trigger.dataset.id}`, {
          method: "DELETE",
          loadingMessage: "뉴스 알림을 삭제하는 중입니다...",
        });
      });
      await refreshData();
      renderSelectedStockAlerts();
      showToast("뉴스 알림을 삭제했습니다.", "info");
      return;
    }
    if (action === "read-notification") {
      await withButtonBusy(trigger, "처리 중...", async () => {
        await request(`/notifications/${trigger.dataset.id}/read`, {
          method: "PATCH",
          loadingMessage: "알림을 읽음 처리하는 중입니다...",
        });
      });
      await refreshData();
      showToast("알림을 읽음 처리했습니다.", "success");
    }
  } catch (error) {
    showToast(error.message, "error");
  }
}

function setupPwaInstall() {
  const isStandalone = window.matchMedia?.("(display-mode: standalone)")?.matches || window.navigator.standalone === true;
  if (!isStandalone) {
    elements.installButton.classList.remove("hidden");
    elements.settingsInstallButton.classList.remove("hidden");
  }

  window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();
    state.installPrompt = event;
    elements.installButton.classList.remove("hidden");
    elements.settingsInstallButton.classList.remove("hidden");
  });

  async function promptInstall() {
    if (!state.installPrompt) {
      showToast("iPhone Safari에서는 공유 메뉴에서 '홈 화면에 추가'를 눌러 주세요.", "info");
      return;
    }
    await state.installPrompt.prompt();
    state.installPrompt = null;
    elements.installButton.classList.add("hidden");
    elements.settingsInstallButton.classList.add("hidden");
  }

  elements.installButton.addEventListener("click", promptInstall);
  elements.settingsInstallButton.addEventListener("click", promptInstall);

  window.addEventListener("appinstalled", () => {
    elements.installButton.classList.add("hidden");
    elements.settingsInstallButton.classList.add("hidden");
  });
}

function setupRouting() {
  document.querySelectorAll(".tab-button").forEach((button) => {
    button.addEventListener("click", () => setView(button.dataset.view));
  });
  const initialView = window.location.hash.replace("#", "") || "dashboard";
  setView(initialView);
}

function setupServiceWorker() {
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/sw.js").catch(() => {});
  }
}

document.getElementById("stock-search-form").addEventListener("submit", handleStockSearch);
document.getElementById("quick-stock-alert-form").addEventListener("submit", handleQuickStockAlertSubmit);
document.getElementById("quick-news-alert-form").addEventListener("submit", handleQuickNewsAlertSubmit);
document.getElementById("quick-fx-alert-form").addEventListener("submit", handleQuickFxAlertSubmit);
document.getElementById("app").addEventListener("click", handleListActions);
document.getElementById("stock-search-modal").addEventListener("click", handleListActions);
document.getElementById("stock-alert-modal").addEventListener("click", handleListActions);
document.getElementById("fx-alert-modal").addEventListener("click", handleListActions);
document.getElementById("analysis-modal").addEventListener("click", handleListActions);
elements.analysisRangeSwitch.addEventListener("click", async (event) => {
  const target = event.target.closest(".analysis-range-tab");
  if (!(target instanceof HTMLButtonElement) || !state.analysisContext) {
    return;
  }
  state.analysisContext.period = target.dataset.period;
  await loadCurrentAnalysis();
});
elements.fxBaseSelect.addEventListener("change", handleFxSelectionChange);
elements.fxTargetSelect.addEventListener("change", handleFxSelectionChange);
elements.fxBaseSelect.addEventListener("input", handleFxSelectionChange);
elements.fxTargetSelect.addEventListener("input", handleFxSelectionChange);
elements.fxBaseSelect.addEventListener("blur", handleFxSelectionChange);
elements.fxTargetSelect.addEventListener("blur", handleFxSelectionChange);
elements.loginForm.addEventListener("submit", handleLogin);
elements.logoutButton.addEventListener("click", handleLogout);
elements.refreshWatchlistButton?.addEventListener("click", async () => {
  await withButtonBusy(elements.refreshWatchlistButton, "갱신 중...", async () => {
    await refreshStockQuotes();
  });
  renderStockWatchlist();
  showToast("관심종목 현재가를 갱신했습니다.", "success");
});
elements.refreshDashboard.addEventListener("click", async () => {
  await withButtonBusy(elements.refreshDashboard, "새로고침 중...", async () => {
    await refreshData();
    await handleFxLookupWithPair(state.lastFxLookup.base, state.lastFxLookup.target);
  });
  showToast("데이터를 새로고침했습니다.", "success");
});

setupRouting();
setupPwaInstall();
setupServiceWorker();
setupEnterSubmit();
bootstrap();
