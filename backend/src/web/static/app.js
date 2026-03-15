const FX_WATCHLIST_KEY = "stock-alert-fx-watchlist-v1";

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
  settingsLogoutButton: document.getElementById("settings-logout-button"),
  installButton: document.getElementById("install-button"),
  settingsInstallButton: document.getElementById("settings-install-button"),
  summaryGrid: document.getElementById("summary-grid"),
  heroStats: document.getElementById("hero-stats"),
  watchlistList: document.getElementById("watchlist-list"),
  fxWatchlistList: document.getElementById("fx-watchlist-list"),
  dashboardNotifications: document.getElementById("dashboard-notifications"),
  settingsNotifications: document.getElementById("settings-notifications"),
  stockSearchResults: document.getElementById("stock-search-results"),
  newsResults: document.getElementById("news-results"),
  fxResult: document.getElementById("fx-result"),
  refreshDashboard: document.getElementById("refresh-dashboard"),
  stockSearchModal: document.getElementById("stock-search-modal"),
  stockSearchQuery: document.getElementById("stock-search-query"),
  stockAlertModal: document.getElementById("stock-alert-modal"),
  selectedAlertSymbol: document.getElementById("selected-alert-symbol"),
  selectedStockAlerts: document.getElementById("selected-stock-alerts"),
  selectedNewsAlerts: document.getElementById("selected-news-alerts"),
  quickStockSymbol: document.getElementById("quick-stock-symbol"),
  quickNewsKeywords: document.getElementById("quick-news-keywords"),
  fxAlertModal: document.getElementById("fx-alert-modal"),
  selectedFxPair: document.getElementById("selected-fx-pair"),
  selectedCurrencyAlerts: document.getElementById("selected-currency-alerts"),
  quickFxBase: document.getElementById("quick-fx-base"),
  quickFxTarget: document.getElementById("quick-fx-target"),
  analysisModal: document.getElementById("analysis-modal"),
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

function setAssetView(name) {
  document.querySelectorAll(".asset-tab-button").forEach((button) => {
    button.classList.toggle("active", button.dataset.assetView === name);
  });
  document.querySelectorAll(".asset-view").forEach((panel) => {
    panel.classList.toggle("active", panel.dataset.assetPanel === name);
  });
}

function getStockAlertCount(symbol) {
  return state.stockAlerts.filter((item) => item.stock_symbol === symbol).length;
}

function getNewsAlertCount(symbol) {
  const normalized = symbol.toLowerCase();
  return state.newsAlerts.filter((item) => item.keywords.toLowerCase().includes(normalized)).length;
}

function getCurrencyAlertCount(base, target) {
  return state.currencyAlerts.filter(
    (item) => item.base_currency === base && item.target_currency === target
  ).length;
}

function stockQuoteMarkup(symbol) {
  const quote = state.stockQuotes[symbol];
  if (!quote) {
    return `<small>시세를 아직 불러오지 못했습니다.</small>`;
  }
  return `
    <small>${quote.market || "-"} · ${formatPrice(quote.price, quote.currency || "KRW")}</small>
    <small>${formatChangePercent(quote.change_percent)}</small>
  `;
}

function fxRateMarkup(base, target) {
  const key = `${base}/${target}`;
  const rate = state.fxRates[key];
  if (!rate) {
    return `<small>현재 환율을 아직 불러오지 못했습니다.</small>`;
  }
  return `
    <small>${formatRate(rate.rate, target)}</small>
    <small>${rate.source}</small>
  `;
}

function renderStats() {
  const cards = [
    { label: "관심주식", value: state.watchlist.length },
    { label: "관심환율", value: state.fxWatchlist.length },
    { label: "주식 알림", value: state.stockAlerts.length },
    { label: "환율 알림", value: state.currencyAlerts.length },
    { label: "안 읽은 알림", value: state.unreadCount },
  ];

  const markup = cards
    .map(
      (card) => `
        <div class="stat-card">
          <small>${card.label}</small>
          <strong>${card.value}</strong>
        </div>
      `
    )
    .join("");
  elements.summaryGrid.innerHTML = markup;
  elements.heroStats.innerHTML = markup;
}

function renderStockWatchlist() {
  if (!state.watchlist.length) {
    elements.watchlistList.innerHTML =
      `<li class="empty-state">아직 관심종목이 없습니다. 종목 검색으로 먼저 추가해 주세요.</li>`;
    return;
  }

  elements.watchlistList.innerHTML = state.watchlist
    .map((item) => {
      const stockAlerts = getStockAlertCount(item.symbol);
      const newsAlerts = getNewsAlertCount(item.symbol);
      const market = state.stockQuotes[item.symbol]?.market || "";
      return `
        <li class="resource-item quote-item">
          <div class="resource-meta">
            <strong>${item.symbol}</strong>
            ${stockQuoteMarkup(item.symbol)}
            <div class="pill-row">
              <span class="result-pill">주식알림 ${stockAlerts}</span>
              <span class="result-pill">뉴스알림 ${newsAlerts}</span>
            </div>
          </div>
          <div class="resource-actions">
            <button class="ghost-button small" type="button" data-action="open-stock-analysis" data-symbol="${item.symbol}" data-market="${market}">상세분석</button>
            <button class="ghost-button small" type="button" data-action="open-alert-modal" data-symbol="${item.symbol}">알림</button>
            <button class="danger-button" type="button" data-action="delete-watchlist" data-symbol="${item.symbol}">삭제</button>
          </div>
        </li>
      `;
    })
    .join("");
}

function renderFxWatchlist() {
  if (!state.fxWatchlist.length) {
    elements.fxWatchlistList.innerHTML =
      `<li class="empty-state">관심환율이 없습니다. USD/KRW 같은 페어를 저장해 주세요.</li>`;
    return;
  }

  elements.fxWatchlistList.innerHTML = state.fxWatchlist
    .map((item) => {
      const pair = `${item.base}/${item.target}`;
      const alertCount = getCurrencyAlertCount(item.base, item.target);
      return `
        <li class="resource-item quote-item">
          <div class="resource-meta">
            <strong>${pair}</strong>
            ${fxRateMarkup(item.base, item.target)}
            <div class="pill-row">
              <span class="result-pill">환율알림 ${alertCount}</span>
            </div>
          </div>
          <div class="resource-actions">
            <button class="ghost-button small" type="button" data-action="open-fx-analysis" data-base="${item.base}" data-target="${item.target}">상세분석</button>
            <button class="ghost-button small" type="button" data-action="open-fx-alert-modal" data-base="${item.base}" data-target="${item.target}">알림</button>
            <button class="danger-button" type="button" data-action="delete-fx-watchlist" data-base="${item.base}" data-target="${item.target}">삭제</button>
          </div>
        </li>
      `;
    })
    .join("");
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

function renderAnalysis(data) {
  const formatter = data.asset_type === "currency" ? formatRate : formatPrice;
  const indicatorRows = [
    { label: "거래량 신호", value: data.volume_signal || "데이터 없음" },
    { label: "거래량 비율", value: data.volume_ratio ? `${data.volume_ratio.toFixed(2)}배` : "-" },
    { label: "RSI(14)", value: data.rsi14 ?? "-" },
    { label: "MACD", value: data.macd ?? "-" },
    { label: "MACD Signal", value: data.macd_signal ?? "-" },
    { label: "ATR(14)", value: data.atr14 ?? "-" },
  ];

  const investorMarkup = data.investor_flow
    ? `
      <div class="analysis-section">
        <h5>수급 흐름</h5>
        <div class="analysis-grid compact-analysis-grid">
          <div class="stat-card"><small>외국인 5일</small><strong>${data.investor_flow.foreign_direction} ${Number(data.investor_flow.foreign_5d).toLocaleString("ko-KR")}</strong></div>
          <div class="stat-card"><small>기관 5일</small><strong>${data.investor_flow.institution_direction} ${Number(data.investor_flow.institution_5d).toLocaleString("ko-KR")}</strong></div>
        </div>
      </div>
    `
    : `
      <div class="analysis-section">
        <h5>수급 흐름</h5>
        <div class="callout">기관/외국인 수급 데이터는 현재 국내 주식에만 반영됩니다.</div>
      </div>
    `;

  const newsMarkup = `
    <div class="analysis-section">
      <h5>뉴스/국제정세 영향</h5>
      <div class="callout">${data.market_context || "현재 반영할 뉴스 요약이 없습니다."}</div>
      <div class="pill-row">
        <span class="result-pill">뉴스 영향 ${data.news_bias || "중립"}</span>
      </div>
      ${(data.related_headlines || []).length ? `<ul class="analysis-headlines">${data.related_headlines.map((headline) => `<li>${headline}</li>`).join("")}</ul>` : ""}
      ${(data.macro_headlines || []).length ? `<ul class="analysis-headlines muted-list">${data.macro_headlines.map((headline) => `<li>${headline}</li>`).join("")}</ul>` : ""}
    </div>
  `;

  elements.analysisBody.innerHTML = `
    <div class="analysis-hero">
      <div>
        <p class="eyebrow">${data.timeframe}</p>
        <h4>${data.name}</h4>
        <p class="muted">${data.symbol} · ${data.trend} · ${data.bias}</p>
      </div>
      <div class="analysis-price">${formatter(data.current_price, data.price_unit)}</div>
    </div>
    <div class="analysis-grid">
      <div class="stat-card"><small>분석 신뢰도</small><strong>${data.confidence_score}점 · ${data.confidence_label}</strong></div>
      <div class="stat-card"><small>1차 매수가</small><strong>${formatter(data.first_buy, data.price_unit)}</strong></div>
      <div class="stat-card"><small>2차 매수가</small><strong>${formatter(data.second_buy, data.price_unit)}</strong></div>
      <div class="stat-card"><small>1차 매도가</small><strong>${formatter(data.first_sell, data.price_unit)}</strong></div>
      <div class="stat-card"><small>2차 매도가</small><strong>${formatter(data.second_sell, data.price_unit)}</strong></div>
      <div class="stat-card"><small>손절 기준</small><strong>${formatter(data.stop_loss, data.price_unit)}</strong></div>
      <div class="stat-card"><small>데이터 소스</small><strong>${data.source}</strong></div>
    </div>
    <div class="analysis-section">
      <h5>기술 지표</h5>
      <div class="analysis-grid compact-analysis-grid">
        ${indicatorRows.map((item) => `<div class="stat-card"><small>${item.label}</small><strong>${item.value}</strong></div>`).join("")}
      </div>
    </div>
    ${investorMarkup}
    ${newsMarkup}
    <ul class="analysis-notes">
      ${data.notes.map((note) => `<li>${note}</li>`).join("")}
    </ul>
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

function renderAll() {
  renderStats();
  renderStockWatchlist();
  renderFxWatchlist();
  renderNotifications(elements.dashboardNotifications, state.notifications.slice(0, 5));
  renderNotifications(elements.settingsNotifications);
  if (state.selectedAlertSymbol) {
    renderSelectedStockAlerts();
  }
  if (state.selectedFxPair) {
    renderSelectedCurrencyAlerts();
  }
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
  const [watchlist, fxWatchlist, stockAlerts, currencyAlerts, newsAlerts, notifications, unread] = await Promise.all([
    request("/watchlist", { loadingMessage: "관심종목을 불러오는 중입니다..." }),
    request("/watchlist/fx", { loadingMessage: "관심환율을 불러오는 중입니다..." }),
    request("/alerts/stocks", { loadingMessage: "주식 알림을 불러오는 중입니다..." }),
    request("/alerts/currencies", { loadingMessage: "환율 알림을 불러오는 중입니다..." }),
    request("/alerts/news", { loadingMessage: "뉴스 알림을 불러오는 중입니다..." }),
    request("/notifications", { loadingMessage: "알림 기록을 불러오는 중입니다..." }),
    request("/notifications/unread-count", { loadingMessage: "읽지 않은 알림 수를 확인하는 중입니다..." }),
  ]);

  state.watchlist = watchlist;
  state.fxWatchlist = fxWatchlist.map((item) => ({
    id: item.id,
    base: item.base_currency,
    target: item.target_currency,
  }));
  state.stockAlerts = stockAlerts;
  state.currencyAlerts = currencyAlerts;
  state.newsAlerts = newsAlerts;
  state.notifications = notifications;
  state.unreadCount = unread.unread_count;

  await Promise.all([refreshStockQuotes(), refreshFxRates()]);
  renderAll();
}

function showLoggedIn() {
  elements.loginPanel.classList.add("hidden");
  elements.appPanel.classList.remove("hidden");
  elements.logoutButton.classList.remove("hidden");
}

function showLoggedOut() {
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

function openStockAlertModal(symbol) {
  state.selectedAlertSymbol = symbol;
  elements.selectedAlertSymbol.textContent = symbol;
  elements.quickStockSymbol.value = symbol;
  elements.quickNewsKeywords.value = symbol;
  renderSelectedStockAlerts();
  elements.stockAlertModal.classList.remove("hidden");
}

function closeStockAlertModal() {
  state.selectedAlertSymbol = "";
  elements.stockAlertModal.classList.add("hidden");
}

function openFxAlertModal(base, target) {
  state.selectedFxPair = { base, target };
  elements.selectedFxPair.textContent = `${base}/${target}`;
  elements.quickFxBase.value = base;
  elements.quickFxTarget.value = target;
  renderSelectedCurrencyAlerts();
  elements.fxAlertModal.classList.remove("hidden");
}

function closeFxAlertModal() {
  state.selectedFxPair = null;
  elements.fxAlertModal.classList.add("hidden");
}

function openAnalysisModal() {
  elements.analysisModal.classList.remove("hidden");
}

function closeAnalysisModal() {
  elements.analysisModal.classList.add("hidden");
  elements.analysisBody.innerHTML = "";
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
            <button class="ghost-button small" type="button" data-action="open-alert-modal" data-symbol="${item.symbol}">알림</button>
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
  event.preventDefault();
  const form = event.currentTarget;
  const formData = new FormData(form);
  const base = String(formData.get("base")).toUpperCase();
  const target = String(formData.get("target")).toUpperCase();
  state.lastFxLookup = { base, target };

  showLoadingCard(elements.fxResult, "환율을 조회하는 중입니다...");
  try {
    await withFormBusy(form, "조회 중...", async () => {
      const payload = await request(`/currency/rate?base=${encodeURIComponent(base)}&target=${encodeURIComponent(target)}`, {
        loadingMessage: "환율을 조회하는 중입니다...",
      });
      elements.fxResult.innerHTML = `
        <div class="stat-card">
          <small>${payload.source}</small>
          <strong>${payload.base_currency}/${payload.target_currency} ${formatRate(payload.rate, payload.target_currency)}</strong>
        </div>
      `;
    });
  } catch (error) {
    showLoadingCard(elements.fxResult, error.message);
    showToast(error.message, "error");
  }
}

async function handleNewsSearch(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const formData = new FormData(form);
  const query = formData.get("query");
  const qs = query ? `?query=${encodeURIComponent(query)}` : "";

  showLoadingList(elements.newsResults, "뉴스를 불러오는 중입니다...");
  try {
    await withFormBusy(form, "조회 중...", async () => {
      const payload = await request(`/news${qs}`, {
        loadingMessage: "뉴스를 불러오는 중입니다...",
      });
      if (!payload.length) {
        elements.newsResults.innerHTML = `<li class="empty-state">뉴스가 없습니다.</li>`;
        return;
      }
      elements.newsResults.innerHTML = payload
        .map(
          (item) => `
            <li class="news-item">
              <strong>${item.title}</strong>
              <small>${item.source} · ${item.published}</small>
              <p class="muted">${item.summary}</p>
              <a class="result-pill" href="${item.url}" target="_blank" rel="noreferrer">원문 보기</a>
            </li>
          `
        )
        .join("");
    });
  } catch (error) {
    elements.newsResults.innerHTML = `<li class="empty-state">${error.message}</li>`;
    showToast(error.message, "error");
  }
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
  openAnalysisModal();
  showLoadingCard(elements.analysisBody, "주식 차트를 분석하는 중입니다...");
  try {
    const qs = market ? `?market=${encodeURIComponent(market)}` : "";
    const payload = await request(`/analysis/stocks/${encodeURIComponent(symbol)}${qs}`, {
      loadingMessage: "주식 상세분석을 준비하는 중입니다...",
    });
    renderAnalysis(payload);
  } catch (error) {
    showLoadingCard(elements.analysisBody, error.message);
    showToast(error.message, "error");
  }
}

async function openFxAnalysis(base, target) {
  openAnalysisModal();
  showLoadingCard(elements.analysisBody, "환율 흐름을 분석하는 중입니다...");
  try {
    const payload = await request(`/analysis/currencies/${encodeURIComponent(base)}/${encodeURIComponent(target)}`, {
      loadingMessage: "환율 상세분석을 준비하는 중입니다...",
    });
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
    if (action === "go-to-fx-watchlist") {
      setView("watchlist");
      setAssetView("fx");
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
      setView("watchlist");
      setAssetView("fx");
      showToast("현재 환율 페어를 저장했습니다.", "success");
      return;
    }
    if (action === "open-alert-modal") {
      openStockAlertModal(trigger.dataset.symbol);
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
      setAssetView("stocks");
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
}

function setupRouting() {
  document.querySelectorAll(".tab-button").forEach((button) => {
    button.addEventListener("click", () => setView(button.dataset.view));
  });
  document.querySelectorAll(".asset-tab-button").forEach((button) => {
    button.addEventListener("click", () => setAssetView(button.dataset.assetView));
  });
  const initialView = window.location.hash.replace("#", "") || "dashboard";
  setView(initialView);
  setAssetView("stocks");
}

function setupServiceWorker() {
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/sw.js").catch(() => {});
  }
}

document.getElementById("stock-search-form").addEventListener("submit", handleStockSearch);
document.getElementById("fx-form").addEventListener("submit", handleFxLookup);
document.getElementById("news-form").addEventListener("submit", handleNewsSearch);
document.getElementById("fx-watchlist-form").addEventListener("submit", handleFxWatchlistSubmit);
document.getElementById("quick-stock-alert-form").addEventListener("submit", handleQuickStockAlertSubmit);
document.getElementById("quick-news-alert-form").addEventListener("submit", handleQuickNewsAlertSubmit);
document.getElementById("quick-fx-alert-form").addEventListener("submit", handleQuickFxAlertSubmit);
document.getElementById("app").addEventListener("click", handleListActions);
document.getElementById("stock-search-modal").addEventListener("click", handleListActions);
document.getElementById("stock-alert-modal").addEventListener("click", handleListActions);
document.getElementById("fx-alert-modal").addEventListener("click", handleListActions);
document.getElementById("analysis-modal").addEventListener("click", handleListActions);
elements.loginForm.addEventListener("submit", handleLogin);
elements.logoutButton.addEventListener("click", handleLogout);
elements.settingsLogoutButton.addEventListener("click", handleLogout);
elements.refreshDashboard.addEventListener("click", async () => {
  await withButtonBusy(elements.refreshDashboard, "새로고침 중...", async () => {
    await refreshData();
  });
  showToast("데이터를 새로고침했습니다.", "success");
});

setupRouting();
setupPwaInstall();
setupServiceWorker();
setupEnterSubmit();
bootstrap();
