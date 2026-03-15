const state = {
  watchlist: [],
  stockAlerts: [],
  currencyAlerts: [],
  newsAlerts: [],
  notifications: [],
  unreadCount: 0,
  installPrompt: null,
};

const elements = {
  loginPanel: document.getElementById("login-panel"),
  appPanel: document.getElementById("app-panel"),
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
};

async function request(path, options = {}) {
  const response = await fetch(path, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

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

function showToast(message, kind = "info") {
  const root = document.getElementById("toast-root");
  const toast = document.createElement("div");
  toast.className = `toast ${kind}`;
  toast.textContent = message;
  root.appendChild(toast);
  setTimeout(() => toast.remove(), 3200);
}

function setView(name) {
  document.querySelectorAll(".tab-button").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === name);
  });
  document.querySelectorAll(".view").forEach((panel) => {
    panel.classList.toggle("active", panel.dataset.viewPanel === name);
  });
  window.location.hash = name;
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
    elements.watchlistList.innerHTML = `<li class="empty-state">아직 관심종목이 없습니다. 위에서 종목 코드를 추가해 주세요.</li>`;
    return;
  }

  elements.watchlistList.innerHTML = state.watchlist
    .map(
      (item) => `
        <li class="resource-item">
          <div class="resource-meta">
            <strong>${item.symbol}</strong>
            <small>등록 ${toLocalDate(item.created_at)}</small>
          </div>
          <button class="danger-button" type="button" data-action="delete-watchlist" data-symbol="${item.symbol}">삭제</button>
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

function renderNotifications(listTarget) {
  if (!state.notifications.length) {
    listTarget.innerHTML = `<li class="empty-state">알림 기록이 아직 없습니다.</li>`;
    return;
  }

  listTarget.innerHTML = state.notifications
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
  renderNotifications(elements.dashboardNotifications);
  renderNotifications(elements.settingsNotifications);
}

async function refreshData() {
  const [watchlist, stockAlerts, currencyAlerts, newsAlerts, notifications, unread] = await Promise.all([
    request("/watchlist"),
    request("/alerts/stocks"),
    request("/alerts/currencies"),
    request("/alerts/news"),
    request("/notifications"),
    request("/notifications/unread-count"),
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
}

async function bootstrap() {
  try {
    await request("/session/me");
    showLoggedIn();
    await refreshData();
  } catch {
    showLoggedOut();
  }
}

async function handleLogin(event) {
  event.preventDefault();
  elements.loginError.classList.add("hidden");
  const formData = new FormData(event.currentTarget);

  try {
    await request("/session/login", {
      method: "POST",
      body: JSON.stringify({ password: formData.get("password") }),
    });
    event.currentTarget.reset();
    showLoggedIn();
    await refreshData();
    showToast("로그인되었습니다.", "success");
  } catch (error) {
    elements.loginError.textContent = error.message;
    elements.loginError.classList.remove("hidden");
  }
}

async function handleLogout() {
  await request("/session/logout", { method: "POST" });
  showLoggedOut();
  showToast("로그아웃되었습니다.", "info");
}

async function handleWatchlistSubmit(event) {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  await request("/watchlist", {
    method: "POST",
    body: JSON.stringify({ symbol: formData.get("symbol") }),
  });
  event.currentTarget.reset();
  await refreshData();
  showToast("관심종목을 추가했습니다.", "success");
}

async function handleStockAlertSubmit(event) {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  await request("/alerts/stocks", {
    method: "POST",
    body: JSON.stringify({
      stock_symbol: formData.get("stock_symbol"),
      target_price: Number(formData.get("target_price")),
      condition: formData.get("condition"),
    }),
  });
  event.currentTarget.reset();
  await refreshData();
  showToast("주식 알림을 추가했습니다.", "success");
}

async function handleCurrencyAlertSubmit(event) {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  await request("/alerts/currencies", {
    method: "POST",
    body: JSON.stringify({
      base_currency: formData.get("base_currency"),
      target_currency: formData.get("target_currency"),
      target_rate: Number(formData.get("target_rate")),
      condition: formData.get("condition"),
    }),
  });
  event.currentTarget.reset();
  await refreshData();
  showToast("환율 알림을 추가했습니다.", "success");
}

async function handleNewsAlertSubmit(event) {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  await request("/alerts/news", {
    method: "POST",
    body: JSON.stringify({ keywords: formData.get("keywords") }),
  });
  event.currentTarget.reset();
  await refreshData();
  showToast("뉴스 알림을 추가했습니다.", "success");
}

async function handleStockSearch(event) {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const query = formData.get("query");
  const payload = await request(`/stocks/search?query=${encodeURIComponent(query)}`);
  const results = payload.results || [];
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
            <small>${item.price} ${item.currency || ""}</small>
            <small>${item.source}</small>
          </div>
          <button class="ghost-button small" type="button" data-action="fill-stock-symbol" data-symbol="${item.symbol}">알림에 사용</button>
        </li>
      `
    )
    .join("");
}

async function handleFxLookup(event) {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const base = String(formData.get("base")).toUpperCase();
  const target = String(formData.get("target")).toUpperCase();
  const payload = await request(`/currency/rate?base=${encodeURIComponent(base)}&target=${encodeURIComponent(target)}`);
  elements.fxResult.innerHTML = `
    <div class="stat-card">
      <small>${payload.source}</small>
      <strong>${payload.base_currency}/${payload.target_currency} ${payload.rate}</strong>
    </div>
  `;
}

async function handleNewsSearch(event) {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const query = formData.get("query");
  const qs = query ? `?query=${encodeURIComponent(query)}` : "";
  const payload = await request(`/news${qs}`);
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
}

async function handleListActions(event) {
  const action = event.target.dataset.action;
  if (!action) {
    return;
  }

  try {
    if (action === "delete-watchlist") {
      await request(`/watchlist/${event.target.dataset.symbol}`, { method: "DELETE" });
      showToast("관심종목을 삭제했습니다.", "info");
    } else if (action === "delete-stock-alert") {
      await request(`/alerts/stocks/${event.target.dataset.id}`, { method: "DELETE" });
      showToast("주식 알림을 삭제했습니다.", "info");
    } else if (action === "delete-currency-alert") {
      await request(`/alerts/currencies/${event.target.dataset.id}`, { method: "DELETE" });
      showToast("환율 알림을 삭제했습니다.", "info");
    } else if (action === "delete-news-alert") {
      await request(`/alerts/news/${event.target.dataset.id}`, { method: "DELETE" });
      showToast("뉴스 알림을 삭제했습니다.", "info");
    } else if (action === "read-notification") {
      await request(`/notifications/${event.target.dataset.id}/read`, { method: "PATCH" });
      showToast("알림을 읽음 처리했습니다.", "success");
    } else if (action === "fill-stock-symbol") {
      document.querySelector('#stock-alert-form input[name="stock_symbol"]').value = event.target.dataset.symbol;
      setView("alerts");
      showToast("주식 알림 폼에 종목 코드를 넣었습니다.", "info");
      return;
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

  const initialView = window.location.hash.replace("#", "") || "dashboard";
  setView(initialView);
}

function setupServiceWorker() {
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/sw.js").catch(() => {});
  }
}

document.getElementById("watchlist-form").addEventListener("submit", handleWatchlistSubmit);
document.getElementById("stock-alert-form").addEventListener("submit", handleStockAlertSubmit);
document.getElementById("currency-alert-form").addEventListener("submit", handleCurrencyAlertSubmit);
document.getElementById("news-alert-form").addEventListener("submit", handleNewsAlertSubmit);
document.getElementById("stock-search-form").addEventListener("submit", handleStockSearch);
document.getElementById("fx-form").addEventListener("submit", handleFxLookup);
document.getElementById("news-form").addEventListener("submit", handleNewsSearch);
document.getElementById("app").addEventListener("click", handleListActions);
elements.loginForm.addEventListener("submit", handleLogin);
elements.logoutButton.addEventListener("click", handleLogout);
elements.settingsLogoutButton.addEventListener("click", handleLogout);
elements.refreshDashboard.addEventListener("click", async () => {
  await refreshData();
  showToast("데이터를 새로고침했습니다.", "success");
});

setupRouting();
setupPwaInstall();
setupServiceWorker();
bootstrap();
