const FX_OPTIONS = ["USD", "KRW", "JPY", "EUR", "CNY", "GBP", "HKD", "AUD"];
const SWIPE_ACTION_WIDTH = 208;

const state = {
  watchlist: [],
  stockQuotes: {},
  fxWatchlist: [],
  fxRates: {},
  installPrompt: null,
  lastFxLookup: { base: "USD", target: "" },
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
  analysisModal: document.getElementById("analysis-modal"),
  analysisTitle: document.getElementById("analysis-title"),
  analysisSubtitle: document.getElementById("analysis-subtitle"),
  analysisPrice: document.getElementById("analysis-price"),
  analysisRangeSwitch: document.getElementById("analysis-range-switch"),
  analysisBody: document.getElementById("analysis-body"),
};

const analysisTouchState = {
  active: false,
  x: 0,
  y: 0,
};

const bodyScrollLockState = {
  y: 0,
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
  if (value === null || value === undefined || value === "") {
    return "";
  }
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
  root.innerHTML = "";
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
  const changeText = formatChangePercent(quote.change_percent);
  return `
    <small class="meta-line">${quote.name || symbol} · ${quote.market || "-"}</small>
    <div class="quote-line">
      <span class="quote-price">${formatPrice(quote.price, quote.currency || "KRW")}</span>
      ${changeText ? `<span class="quote-change ${changeClass}">${changeText}</span>` : ""}
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
    <small class="meta-line">${rate.source}${rate.fetched_at ? ` · ${toLocalDate(rate.fetched_at)}` : ""}</small>
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
  const renderScoreDetailCard = (label, score, reasons) => `
    <div class="stat-card score-detail-card">
      <small>${label}</small>
      <strong>${score}점</strong>
      <ul class="analysis-notes compact">
        ${((reasons || []).length ? reasons : ["현재 계산 기준에서 특이 근거는 제한적입니다."]).map((reason) => `<li>${reason}</li>`).join("")}
      </ul>
    </div>
  `;
  const dedupeAnalysisReasons = (reasons = [], excluded = []) => {
    const blocked = new Set(
      excluded
        .map((item) => String(item || "").trim())
        .filter(Boolean),
    );
    const seen = new Set();
    return reasons.filter((reason) => {
      const normalized = String(reason || "").trim();
      if (!normalized || blocked.has(normalized) || seen.has(normalized)) {
        return false;
      }
      seen.add(normalized);
      return true;
    });
  };
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
  const decisionTitle = data.final_action === "매수" ? "매수 근거" : data.final_action === "매도" ? "매도 근거" : "홀드 근거";
  const hasFundamentals = data.fundamental_score !== null && data.fundamental_score !== undefined;
  const marketReasonList = dedupeAnalysisReasons([
    ...(data.macro_reasons || []),
    ...(data.news_reasons || []),
  ]);
  const filteredRiskReasons = dedupeAnalysisReasons(
    data.risk_reasons || [],
    [data.market_context_summary, ...marketReasonList],
  );

  setAnalysisHeader({
    title: `${data.name}`,
    subtitle: `${data.symbol} · ${data.timeframe}`,
    price: formatter(data.current_price, data.price_unit),
  });

  elements.analysisBody.innerHTML = `
    <section class="analysis-hero-card">
      <p class="analysis-chip">${data.final_action}</p>
      <h4>${data.final_score}점 · ${data.final_action}</h4>
      <p class="analysis-copy">${data.decision_summary}</p>
      <div class="analysis-meta-grid">
        <div class="stat-card">
          <small>최종 판단</small>
          <strong>${data.final_action}</strong>
        </div>
        <div class="stat-card">
          <small>최종 점수</small>
          <strong>${data.final_score}점</strong>
        </div>
      </div>
      <ul class="analysis-notes compact">
        <li>현재가 기준: ${data.price_basis || "실시간 현재가"}</li>
        <li>차트 기준: ${data.chart_basis || data.timeframe}</li>
        <li>시장환경 기준: ${data.market_context_basis || "전일 종가 대비 현재 지수·거시 지표"}</li>
      </ul>
    </section>
    ${hasFundamentals ? `
      <section class="analysis-section-card">
        <h5>기업 점검</h5>
        <p class="analysis-copy">${data.fundamental_summary || "실적 성장 데이터를 바탕으로 기업 체력을 점검했습니다."}</p>
        <ul class="analysis-notes">
          ${(data.fundamental_reasons || []).map((reason) => `<li>${reason}</li>`).join("")}
        </ul>
      </section>
      <section class="analysis-section-card">
        <h5>밸류 부담</h5>
        <p class="analysis-copy">${data.valuation_summary || "밸류 지표를 기준으로 현재 가격 부담을 점검했습니다."}</p>
        <ul class="analysis-notes">
          ${(data.valuation_reasons || []).map((reason) => `<li>${reason}</li>`).join("")}
        </ul>
      </section>
      <section class="analysis-section-card">
        <h5>재무 품질</h5>
        <p class="analysis-copy">${data.quality_summary || "재무 건전성과 자본 효율을 함께 확인했습니다."}</p>
        <ul class="analysis-notes">
          ${(data.quality_reasons || []).map((reason) => `<li>${reason}</li>`).join("")}
        </ul>
      </section>
    ` : ""}
    <section class="analysis-section-card">
      <h5>${decisionTitle}</h5>
      <ul class="analysis-notes">
        ${(data.decision_reasons || []).map((reason) => `<li>${reason}</li>`).join("")}
      </ul>
    </section>
    <section class="analysis-section-card">
      <h5>추세 분석</h5>
      <p class="analysis-copy">${data.trend_summary}</p>
      <ul class="analysis-notes">
        ${(data.trend_reasons || []).map((reason) => `<li>${reason}</li>`).join("")}
      </ul>
    </section>
    <section class="analysis-section-card">
      <h5>과열·타이밍 판단</h5>
      <p class="analysis-copy">${data.timing_summary}</p>
      <ul class="analysis-notes">
        ${(data.momentum_reasons || []).map((reason) => `<li>${reason}</li>`).join("")}
      </ul>
    </section>
    <section class="analysis-section-card">
      <h5>거래량·신뢰도</h5>
      <p class="analysis-copy">${data.volume_summary}</p>
      <ul class="analysis-notes">
        ${(data.volume_reasons || []).map((reason) => `<li>${reason}</li>`).join("")}
      </ul>
    </section>
    <section class="analysis-section-card">
      <h5>변동성 점검</h5>
      <p class="analysis-copy">${data.volatility_summary}</p>
      <ul class="analysis-notes">
        ${(data.volatility_reasons || []).map((reason) => `<li>${reason}</li>`).join("")}
      </ul>
    </section>
    <section class="analysis-section-card">
      <h5>시장환경 해석</h5>
      <p class="analysis-copy">${data.market_context_summary || "실시간 시장환경 근거가 충분하지 않아 보수적으로 해석했습니다."}</p>
      <ul class="analysis-notes">
        ${marketReasonList.length
          ? marketReasonList.map((reason) => `<li>${reason}</li>`).join("")
          : "<li>실시간 뉴스·지수·거시 근거가 부족해 시장환경 점수는 중립으로 반영했습니다.</li>"}
      </ul>
    </section>
    ${(data.flow_basis || data.investor_summary) ? `
      <section class="analysis-section-card">
        <h5>수급 반영</h5>
        <p class="analysis-copy">${data.investor_summary || data.flow_basis}</p>
        ${data.flow_mode === "excluded" ? '<ul class="analysis-notes"><li>이번 판단에서는 수급 점수를 계산에 넣지 않았습니다.</li></ul>' : ""}
      </section>
    ` : ""}
    <section class="analysis-section-card">
      <h5>매수 · 매도 · 손절 구간</h5>
      <div class="analysis-grid analysis-plan-grid">
        ${buySellCards.join("")}
        <div class="stat-card">
          <small>손절 기준</small>
          <strong>${formatter(data.stop_loss, data.price_unit)}</strong>
        </div>
      </div>
      <p class="analysis-copy">${data.price_reference_summary}</p>
    </section>
    ${data.investor_summary ? `
      <section class="analysis-section-card">
        <h5>수급 해석</h5>
        <p class="analysis-copy">${data.investor_summary}</p>
      </section>
    ` : ""}
    <section class="analysis-section-card">
      <h5>위험 요인</h5>
      <ul class="analysis-notes">
        ${filteredRiskReasons.length ? filteredRiskReasons.map((note) => `<li>${note}</li>`).join("") : "<li>현재 확인된 특이 위험 요인은 제한적입니다.</li>"}
      </ul>
    </section>
    <details class="analysis-section-card analysis-details">
      <summary>세부 점수 보기</summary>
      <div class="analysis-grid analysis-score-grid">
        ${renderScoreDetailCard("추세 점수", data.trend_score, data.trend_reasons)}
        ${renderScoreDetailCard("모멘텀 점수", data.momentum_score, data.momentum_reasons)}
        ${renderScoreDetailCard("거래량 점수", data.volume_score, data.volume_reasons)}
        ${renderScoreDetailCard("변동성 점수", data.volatility_score, data.volatility_reasons)}
        ${renderScoreDetailCard("시장환경 점수", data.market_context_score, marketReasonList)}
        ${hasFundamentals ? renderScoreDetailCard("실적 점수", data.fundamental_score, data.fundamental_reasons) : ""}
        ${hasFundamentals ? renderScoreDetailCard("밸류 점수", data.valuation_score, data.valuation_reasons) : ""}
        ${hasFundamentals ? renderScoreDetailCard("재무 품질", data.quality_score, data.quality_reasons) : ""}
        ${hasFundamentals ? renderScoreDetailCard("매수 타이밍", data.timing_score, [...(data.trend_reasons || []), ...(data.momentum_reasons || [])]) : ""}
        ${renderScoreDetailCard("위험 차감", data.weighted_risk_penalty ?? data.risk_penalty, filteredRiskReasons)}
      </div>
      <ul class="analysis-notes">
        ${(data.notes || []).map((note) => `<li>${note}</li>`).join("")}
      </ul>
    </details>
  `;
}

async function migrateLegacyFxWatchlist() {
  try {
    const raw = localStorage.getItem("stock-alert-fx-watchlist-v1");
    if (!raw) {
      return;
    }
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed) || !parsed.length) {
      localStorage.removeItem("stock-alert-fx-watchlist-v1");
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
    localStorage.removeItem("stock-alert-fx-watchlist-v1");
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
  const quotes = await request("/watchlist/quotes", {
    skipLoading: true,
  });
  state.stockQuotes = Object.fromEntries(
    quotes.map((quote) => [String(quote.symbol).toUpperCase(), quote])
  );
}

async function refreshSingleStockQuote(symbol) {
  const quotes = await request("/watchlist/quotes/refresh", {
    method: "POST",
    body: JSON.stringify({ symbols: [symbol] }),
    skipLoading: true,
  });
  const quote = quotes.find((item) => String(item.symbol).toUpperCase() === String(symbol).toUpperCase()) || null;
  if (!quote) {
    throw new Error("시세를 갱신하지 못했습니다.");
  }
  state.stockQuotes[symbol] = quote;
  return quote;
}

async function refreshFxRates() {
  const rates = await request("/watchlist/fx/quotes", {
    skipLoading: true,
  });
  state.fxRates = Object.fromEntries(
    rates.map((rate) => [
      `${String(rate.base_currency).toUpperCase()}/${String(rate.target_currency).toUpperCase()}`,
      rate,
    ])
  );
}

async function refreshData() {
  const [watchlist, fxWatchlist, stockQuotes, fxQuotes] = await Promise.all([
    request("/watchlist", { loadingMessage: "관심종목을 불러오는 중입니다..." }),
    request("/watchlist/fx", { loadingMessage: "관심환율을 불러오는 중입니다..." }),
    request("/watchlist/quotes", { skipLoading: true }),
    request("/watchlist/fx/quotes", { skipLoading: true }),
  ]);

  state.watchlist = watchlist;
  state.fxWatchlist = fxWatchlist.map((item) => ({
    id: item.id,
    base: item.base_currency,
    target: item.target_currency,
  }));
  state.stockQuotes = Object.fromEntries(
    stockQuotes.map((quote) => [String(quote.symbol).toUpperCase(), quote])
  );
  state.fxRates = Object.fromEntries(
    fxQuotes.map((rate) => [
      `${String(rate.base_currency).toUpperCase()}/${String(rate.target_currency).toUpperCase()}`,
      rate,
    ])
  );
  renderAll();
}

function hasSelectedFxPair() {
  return FX_OPTIONS.includes(state.lastFxLookup.base) && FX_OPTIONS.includes(state.lastFxLookup.target);
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
  closeAnalysisModal();
}

function resetStockSearchModalState() {
  elements.stockSearchQuery.value = "";
  elements.stockSearchResults.innerHTML = `<li class="empty-state">검색어를 입력해 주세요.</li>`;
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
  resetStockSearchModalState();
  elements.stockSearchModal.classList.remove("hidden");
  if (query) {
    elements.stockSearchQuery.value = query;
  }
  elements.stockSearchQuery.focus();
}

function closeStockSearchModal() {
  resetStockSearchModalState();
  elements.stockSearchModal.classList.add("hidden");
}

function openAnalysisModal() {
  closeSwipeActions();
  syncAnalysisRangeSwitch();
  lockBodyScroll();
  elements.analysisModal.classList.remove("hidden");
}

function closeAnalysisModal() {
  elements.analysisModal.classList.add("hidden");
  unlockBodyScroll();
  elements.analysisBody.innerHTML = "";
  setAnalysisHeader();
  state.analysisContext = null;
}

function lockBodyScroll() {
  bodyScrollLockState.y = window.scrollY || window.pageYOffset || 0;
  document.documentElement.classList.add("modal-open");
  document.body.classList.add("modal-open");
  document.body.style.top = `-${bodyScrollLockState.y}px`;
}

function unlockBodyScroll() {
  document.documentElement.classList.remove("modal-open");
  document.body.classList.remove("modal-open");
  document.body.style.top = "";
  window.scrollTo(0, bodyScrollLockState.y);
}

function renderStockSearchResults(results) {
  if (!results.length) {
    elements.stockSearchResults.innerHTML = `<li class="empty-state">검색 결과가 없습니다.</li>`;
    return;
  }

  elements.stockSearchResults.innerHTML = results
    .map(
      (item) => {
        const changeText = formatChangePercent(item.change_percent);
        return `
        <li class="resource-item quote-item">
          <div class="resource-meta">
            <strong class="resource-title">${item.symbol} · ${item.name}</strong>
            <small class="meta-line">${item.market || "-"} · ${formatPrice(item.price, item.currency || "KRW")}</small>
            <small class="meta-line">${changeText ? `${changeText} · ` : ""}${item.source}</small>
          </div>
          <div class="resource-actions">
            <button class="primary-button small-button" type="button" data-action="add-watchlist-symbol" data-symbol="${item.symbol}">추가</button>
            <button class="ghost-button small-button" type="button" data-action="open-stock-analysis" data-symbol="${item.symbol}" data-market="${item.market || ""}">상세분석</button>
          </div>
        </li>
      `;
      }
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

  if (!base || !target) {
    renderFxSelectionError("기준 통화와 대상 통화를 선택해 주세요.");
    return;
  }
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
  const current = state.analysisContext?.period || "intraday";
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

  syncAnalysisRangeSwitch();
  const { assetType, symbol, market, base, target, period } = state.analysisContext;
  const basisLabel =
    period === "intraday" ? "30분봉" : period === "medium" ? "주봉" : period === "long" ? "월봉" : "일봉";
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
        skipLoading: true,
      });
    } else {
      payload = await request(`/analysis/currencies/${encodeURIComponent(base)}/${encodeURIComponent(target)}/${period}`, {
        loadingMessage: `${basisLabel} 기준 환율 상세분석을 준비하는 중입니다...`,
        skipLoading: true,
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
        const created = await request("/watchlist/fx", {
          method: "POST",
          body: JSON.stringify({ base_currency: base, target_currency: target }),
          loadingMessage: "현재 환율 페어를 저장하는 중입니다...",
        });
        state.fxWatchlist = [
          ...state.fxWatchlist,
          { id: created.id, base: created.base_currency, target: created.target_currency },
        ].sort((left, right) => `${left.base}/${left.target}`.localeCompare(`${right.base}/${right.target}`, "ko-KR"));
        const snapshots = await request("/watchlist/fx/quotes/refresh", {
          method: "POST",
          body: JSON.stringify({ pairs: [`${base}/${target}`] }),
          skipLoading: true,
        });
        snapshots.forEach((rate) => {
          const key = `${String(rate.base_currency).toUpperCase()}/${String(rate.target_currency).toUpperCase()}`;
          state.fxRates[key] = rate;
        });
        renderFxWatchlist();
      }
      showToast("현재 환율 페어를 저장했습니다.", "success");
      return;
    }
    if (action === "open-current-fx-analysis") {
      await openFxAnalysis(state.lastFxLookup.base, state.lastFxLookup.target);
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
        const quote = await request("/watchlist/quotes/refresh", {
          method: "POST",
          body: JSON.stringify({ symbols: [trigger.dataset.symbol] }),
          loadingMessage: "현재가를 다시 불러오는 중입니다...",
        });
        state.stockQuotes[trigger.dataset.symbol] = quote[0] || null;
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
        const created = await request("/watchlist", {
          method: "POST",
          body: JSON.stringify({ symbol: trigger.dataset.symbol }),
          loadingMessage: "관심종목에 추가하는 중입니다...",
        });
        const symbol = String(created.symbol || trigger.dataset.symbol).toUpperCase();
        const exists = state.watchlist.some((item) => String(item.symbol).toUpperCase() === symbol);
        if (!exists) {
          state.watchlist = [...state.watchlist, created].sort((left, right) =>
            String(left.symbol).localeCompare(String(right.symbol), "ko-KR")
          );
        }
        renderStockWatchlist();
        setView("watchlist");
        closeStockSearchModal();
        try {
          await refreshSingleStockQuote(symbol);
        } catch {
          state.stockQuotes[symbol] = null;
        }
      });
      renderStockWatchlist();
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
      {
        const symbol = String(trigger.dataset.symbol || "").toUpperCase();
        state.watchlist = state.watchlist.filter((item) => String(item.symbol).toUpperCase() !== symbol);
        delete state.stockQuotes[symbol];
      }
      renderStockWatchlist();
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
      {
        const pair = `${String(trigger.dataset.base).toUpperCase()}/${String(trigger.dataset.target).toUpperCase()}`;
        state.fxWatchlist = state.fxWatchlist.filter((item) => `${item.base}/${item.target}` !== pair);
        delete state.fxRates[pair];
      }
      renderFxWatchlist();
      showToast("관심환율을 삭제했습니다.", "info");
      return;
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
    navigator.serviceWorker
      .register("/sw.js", { updateViaCache: "none" })
      .then((registration) => registration.update().catch(() => {}))
      .catch(() => {});
  }
}

function setupAnalysisModalTouchLock() {
  const card = document.querySelector(".analysis-modal-card");
  if (!card) {
    return;
  }

  card.addEventListener(
    "touchstart",
    (event) => {
      const touch = event.touches?.[0];
      if (!touch) {
        return;
      }
      analysisTouchState.active = true;
      analysisTouchState.x = touch.clientX;
      analysisTouchState.y = touch.clientY;
    },
    { passive: true }
  );

  card.addEventListener(
    "touchmove",
    (event) => {
      if (!analysisTouchState.active) {
        return;
      }
      const touch = event.touches?.[0];
      if (!touch) {
        return;
      }
      const dx = touch.clientX - analysisTouchState.x;
      const dy = touch.clientY - analysisTouchState.y;
      if (Math.abs(dx) > Math.abs(dy) && Math.abs(dx) > 6) {
        event.preventDefault();
      }
    },
    { passive: false }
  );

  const resetTouch = () => {
    analysisTouchState.active = false;
  };
  card.addEventListener("touchend", resetTouch, { passive: true });
  card.addEventListener("touchcancel", resetTouch, { passive: true });
}

document.getElementById("stock-search-form").addEventListener("submit", handleStockSearch);
document.getElementById("app").addEventListener("click", handleListActions);
document.getElementById("stock-search-modal").addEventListener("click", handleListActions);
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
  elements.refreshWatchlistButton.disabled = true;
  elements.refreshWatchlistButton.classList.add("is-busy");
  elements.refreshWatchlistButton.setAttribute("aria-busy", "true");
  try {
    const quotes = await request("/watchlist/quotes/refresh", {
      method: "POST",
      body: JSON.stringify({ symbols: state.watchlist.map((item) => item.symbol) }),
      loadingMessage: "관심종목 시세를 갱신하는 중입니다...",
    });
    state.stockQuotes = Object.fromEntries(
      quotes.map((quote) => [String(quote.symbol).toUpperCase(), quote])
    );
  } finally {
    elements.refreshWatchlistButton.disabled = false;
    elements.refreshWatchlistButton.classList.remove("is-busy");
    elements.refreshWatchlistButton.removeAttribute("aria-busy");
  }
  renderStockWatchlist();
  showToast("관심종목 시세를 갱신했습니다.", "success");
});
elements.refreshDashboard.addEventListener("click", async () => {
  await withButtonBusy(elements.refreshDashboard, "새로고침 중...", async () => {
    await refreshData();
  });
  showToast("데이터를 새로고침했습니다.", "success");
});

setupRouting();
setupPwaInstall();
setupServiceWorker();
setupAnalysisModalTouchLock();
setupEnterSubmit();
bootstrap();
