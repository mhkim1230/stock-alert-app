const state = {
  watchlist: [],
  stockAlerts: [],
  currencyAlerts: [],
  newsAlerts: [],
  notifications: [],
  unreadCount: 0,
  installPrompt: null,
  selectedAlertSymbol: "",
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
  stockAlertList: document.getElementById("stock-alert-list"),
  currencyAlertList: document.getElementById("currency-alert-list"),
  newsAlertList: document.getElementById("news-alert-list"),
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
  quickStockSymbol: document.getElementById("quick-stock-symbol"),
  quickNewsKeywords: document.getElementById("quick-news-keywords"),
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

function formatPrice(value, currency = "KRW") {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return "-";
  }

  if (currency === "USD") {
    return `${numeric.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} USD`;
  }

  return `${numeric.toLocaleString("ko-KR")}원`;
}

function formatChangePercent(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return "";
  }
  return `${numeric > 0 ? "+" : ""}${numeric.toFixed(2)}%`;
}

function showLoadingResult(target, message) {
  target.innerHTML = `<li class="empty-state loading-state">${message}</li>`;
}

function showLoadingCard(target, message) {
  target.innerHTML = `<div class="callout loading-state">${message}</div>`;
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

function toLocalDate(value) {
  if (!value) {
    return "-";
  }
  return new Date(value).toLocaleString("ko-KR");
}

function renderStats() {
  const cards = [
    { label: "관심종목", value: state.watchlist.length },
    { label: "주식 알림", value: state.stockAlerts.length },
    { label: "환율 알림", value: state.currencyAlerts.length },
    { label: "뉴스 알림", value: state.newsAlerts.length },
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

function renderWatchlist() {
  if (!state.watchlist.length) {
    elements.watchlistList.innerHTML = `<li class="empty-state">아직 관심종목이 없습니다. 종목 검색 팝업에서 바로 추가해 주세요.</li>`;
    return;
  }

  elements.watchlistList.innerHTML = state.watchlist
    .map(
      (item) => `
        <li class="resource-item">
          <div class="resource-meta">
            <strong>${item.symbol}</strong>
            <small>관심종목 등록 ${toLocalDate(item.created_at)}</small>
          </div>
          <div class="resource-actions">
            <button class="ghost-button small" type="button" data-action="open-alert-modal" data-symbol="${item.symbol}">알림</button>
            <button class="danger-button" type="button" data-action="delete-watchlist" data-symbol="${item.symbol}">삭제</button>
          </div>
        </li>
      `
    )
    .join("");
}

function renderAlertList(target, items, formatter, deleteAction) {
  if (!items.length) {
    target.innerHTML = `<li class="empty-state">등록된 항목이 없습니다.</li>`;
    return;
  }

  target.innerHTML = items
    .map(
      (item) => `
        <li class="resource-item">
          <div class="resource-meta">
            <strong>${formatter(item)}</strong>
            <small>등록 ${toLocalDate(item.created_at)}</small>
            ${item.triggered_at ? `<small>마지막 트리거 ${toLocalDate(item.triggered_at)}</small>` : ""}
          </div>
          <button class="danger-button" type="button" data-action="${deleteAction}" data-id="${item.id}">삭제</button>
        </li>
      `
    )
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

function renderAll() {
  renderStats();
  renderWatchlist();
  renderAlertList(
    elements.stockAlertList,
    state.stockAlerts,
    (item) => `${item.stock_symbol} ${item.condition} ${item.target_price}`,
    "delete-stock-alert"
  );
  renderAlertList(
    elements.currencyAlertList,
    state.currencyAlerts,
    (item) => `${item.base_currency}/${item.target_currency} ${item.condition} ${item.target_rate}`,
    "delete-currency-alert"
  );
  renderAlertList(
    elements.newsAlertList,
    state.newsAlerts,
    (item) => item.keywords,
    "delete-news-alert"
  );
  renderNotifications(elements.dashboardNotifications, state.notifications.slice(0, 5));
  renderNotifications(elements.settingsNotifications);
}

async function refreshData() {
  const [watchlist, stockAlerts, currencyAlerts, newsAlerts, notifications, unread] = await Promise.all([
    request("/watchlist", { loadingMessage: "관심종목을 불러오는 중입니다..." }),
    request("/alerts/stocks", { loadingMessage: "주식 알림을 불러오는 중입니다..." }),
    request("/alerts/currencies", { loadingMessage: "환율 알림을 불러오는 중입니다..." }),
    request("/alerts/news", { loadingMessage: "뉴스 알림을 불러오는 중입니다..." }),
    request("/notifications", { loadingMessage: "알림 기록을 불러오는 중입니다..." }),
    request("/notifications/unread-count", { loadingMessage: "읽지 않은 알림 수를 확인하는 중입니다..." }),
  ]);

  state.watchlist = watchlist;
  state.stockAlerts = stockAlerts;
  state.currencyAlerts = currencyAlerts;
  state.newsAlerts = newsAlerts;
  state.notifications = notifications;
  state.unreadCount = unread.unread_count;
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
  closeAlertModal();
}

async function bootstrap() {
  try {
    await request("/session/me", { loadingMessage: "세션을 확인하는 중입니다..." });
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
    await request("/session/logout", { method: "POST", loadingMessage: "로그아웃하는 중입니다..." });
  });
  showLoggedOut();
  showToast("로그아웃되었습니다.", "info");
}

async function handleWatchlistSubmit(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const formData = new FormData(form);
  await request("/watchlist", {
    method: "POST",
    body: JSON.stringify({ symbol: formData.get("symbol") }),
  });
  form.reset();
  await refreshData();
  showToast("관심종목을 추가했습니다.", "success");
}

function openStockSearchModal(query = "") {
  elements.stockSearchModal.classList.remove("hidden");
  if (typeof query === "string" && query) {
    elements.stockSearchQuery.value = query;
  }
  elements.stockSearchQuery.focus();
}

function closeStockSearchModal() {
  elements.stockSearchModal.classList.add("hidden");
}

function openAlertModal(symbol) {
  state.selectedAlertSymbol = symbol;
  elements.selectedAlertSymbol.textContent = symbol;
  elements.quickStockSymbol.value = symbol;
  elements.quickNewsKeywords.value = symbol;
  elements.stockAlertModal.classList.remove("hidden");
}

function closeAlertModal() {
  state.selectedAlertSymbol = "";
  elements.stockAlertModal.classList.add("hidden");
}

function renderStockSearchResults(results) {
  if (!results.length) {
    elements.stockSearchResults.innerHTML = `<li class="empty-state">검색 결과가 없습니다.</li>`;
    return;
  }

  elements.stockSearchResults.innerHTML = results
    .map(
      (item) => `
        <li class="resource-item">
          <div class="resource-meta">
            <strong>${item.symbol} · ${item.name}</strong>
            <small>${item.market || "-"} · ${formatPrice(item.price, item.currency || "KRW")}</small>
            <small>${formatChangePercent(item.change_percent)} · ${item.source}</small>
          </div>
          <div class="resource-actions">
            <button class="primary-button small-button" type="button" data-action="add-watchlist-symbol" data-symbol="${item.symbol}">관심종목 추가</button>
            <button class="ghost-button small" type="button" data-action="open-alert-modal" data-symbol="${item.symbol}">알림</button>
          </div>
        </li>
      `
    )
    .join("");
}

async function handleStockAlertSubmit(event) {
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
    await refreshData();
    showToast("주식 알림을 추가했습니다.", "success");
  } catch (error) {
    showToast(error.message, "error");
  }
}

async function handleCurrencyAlertSubmit(event) {
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
    await refreshData();
    showToast("환율 알림을 추가했습니다.", "success");
  } catch (error) {
    showToast(error.message, "error");
  }
}

async function handleNewsAlertSubmit(event) {
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
    await refreshData();
    showToast("뉴스 알림을 추가했습니다.", "success");
  } catch (error) {
    showToast(error.message, "error");
  }
}

async function handleStockSearch(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const formData = new FormData(form);
  const query = formData.get("query");
  showLoadingResult(elements.stockSearchResults, "종목을 조회하는 중입니다...");
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
  showLoadingCard(elements.fxResult, "환율을 조회하는 중입니다...");
  try {
    await withFormBusy(form, "조회 중...", async () => {
      const payload = await request(`/currency/rate?base=${encodeURIComponent(base)}&target=${encodeURIComponent(target)}`, {
        loadingMessage: "환율을 조회하는 중입니다...",
      });
      elements.fxResult.innerHTML = `
        <div class="stat-card">
          <small>${payload.source}</small>
          <strong>${payload.base_currency}/${payload.target_currency} ${payload.rate}</strong>
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
  showLoadingResult(elements.newsResults, "뉴스를 불러오는 중입니다...");
  try {
    await withFormBusy(form, "조회 중...", async () => {
      const payload = await request(`/news${qs}`, { loadingMessage: "뉴스를 불러오는 중입니다..." });
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
    closeAlertModal();
    await refreshData();
    setView("alerts");
    setAlertView("stocks");
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
    closeAlertModal();
    await refreshData();
    setView("alerts");
    setAlertView("news");
    showToast("뉴스 알림을 추가했습니다.", "success");
  } catch (error) {
    showToast(error.message, "error");
  }
}

function setAlertView(name) {
  document.querySelectorAll(".sub-tab-button").forEach((button) => {
    button.classList.toggle("active", button.dataset.alertView === name);
  });
  document.querySelectorAll(".alert-view").forEach((panel) => {
    panel.classList.toggle("active", panel.dataset.alertPanel === name);
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
    } else if (action === "close-stock-search") {
      closeStockSearchModal();
      return;
    } else if (action === "go-to-alerts") {
      setView("alerts");
      return;
    } else if (action === "go-to-watchlist") {
      closeAlertModal();
      setView("watchlist");
      return;
    } else if (action === "go-to-currency-alert") {
      setView("alerts");
      setAlertView("currencies");
      return;
    } else if (action === "open-alert-modal") {
      openAlertModal(trigger.dataset.symbol);
      return;
    } else if (action === "close-alert-modal") {
      closeAlertModal();
      return;
    } else if (action === "add-watchlist-symbol") {
      await withButtonBusy(trigger, "추가 중...", async () => {
        await request("/watchlist", {
          method: "POST",
          body: JSON.stringify({ symbol: trigger.dataset.symbol }),
          loadingMessage: "관심종목에 추가하는 중입니다...",
        });
      });
      closeStockSearchModal();
      setView("watchlist");
      showToast("관심종목을 추가했습니다.", "success");
    } else if (action === "delete-watchlist") {
      await withButtonBusy(trigger, "삭제 중...", async () => {
        await request(`/watchlist/${trigger.dataset.symbol}`, {
          method: "DELETE",
          loadingMessage: "관심종목을 삭제하는 중입니다...",
        });
      });
      showToast("관심종목을 삭제했습니다.", "info");
    } else if (action === "delete-stock-alert") {
      await withButtonBusy(trigger, "삭제 중...", async () => {
        await request(`/alerts/stocks/${trigger.dataset.id}`, {
          method: "DELETE",
          loadingMessage: "주식 알림을 삭제하는 중입니다...",
        });
      });
      showToast("주식 알림을 삭제했습니다.", "info");
    } else if (action === "delete-currency-alert") {
      await withButtonBusy(trigger, "삭제 중...", async () => {
        await request(`/alerts/currencies/${trigger.dataset.id}`, {
          method: "DELETE",
          loadingMessage: "환율 알림을 삭제하는 중입니다...",
        });
      });
      showToast("환율 알림을 삭제했습니다.", "info");
    } else if (action === "delete-news-alert") {
      await withButtonBusy(trigger, "삭제 중...", async () => {
        await request(`/alerts/news/${trigger.dataset.id}`, {
          method: "DELETE",
          loadingMessage: "뉴스 알림을 삭제하는 중입니다...",
        });
      });
      showToast("뉴스 알림을 삭제했습니다.", "info");
    } else if (action === "read-notification") {
      await withButtonBusy(trigger, "처리 중...", async () => {
        await request(`/notifications/${trigger.dataset.id}/read`, {
          method: "PATCH",
          loadingMessage: "알림을 읽음 처리하는 중입니다...",
        });
      });
      showToast("알림을 읽음 처리했습니다.", "success");
    }
    await refreshData();
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

  document.querySelectorAll(".sub-tab-button").forEach((button) => {
    button.addEventListener("click", () => setAlertView(button.dataset.alertView));
  });

  const initialView = window.location.hash.replace("#", "") || "dashboard";
  setView(initialView);
  setAlertView("stocks");
}

function setupServiceWorker() {
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/sw.js").catch(() => {});
  }
}

document.getElementById("currency-alert-form").addEventListener("submit", handleCurrencyAlertSubmit);
document.getElementById("news-alert-form").addEventListener("submit", handleNewsAlertSubmit);
document.getElementById("stock-search-form").addEventListener("submit", handleStockSearch);
document.getElementById("fx-form").addEventListener("submit", handleFxLookup);
document.getElementById("news-form").addEventListener("submit", handleNewsSearch);
document.getElementById("quick-stock-alert-form").addEventListener("submit", handleQuickStockAlertSubmit);
document.getElementById("quick-news-alert-form").addEventListener("submit", handleQuickNewsAlertSubmit);
document.getElementById("app").addEventListener("click", handleListActions);
document.getElementById("stock-search-modal").addEventListener("click", handleListActions);
document.getElementById("stock-alert-modal").addEventListener("click", handleListActions);
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
