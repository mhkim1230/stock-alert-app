import os

from bs4 import BeautifulSoup

os.environ.setdefault("DATABASE_URL", "postgresql://placeholder:placeholder@placeholder.invalid:5432/postgres")
os.environ.setdefault("ADMIN_API_KEY", "placeholder-admin-key")

from src.services.naver_stock_service import NaverStockService


def test_extract_change_percent_prefers_regular_session_over_preopen_zero():
    html = """
    <div class="rate_info">
      <p class="no_exday">
        <span class="sptxt sp_txt1">전일대비</span>
        <em><span class="ico sam">보합</span><span class="blind">0</span></em>
        <span class="bar">l</span>
        <em><span class="blind">0.00</span><span class="per">%</span></em>
      </p>
      <div class="new_totalinfo">종목 시세 정보 2026년 03월 16일 기준 개장전 거래량 0</div>
    </div>
    <div class="rate_info">
      <p class="no_exday">
        <span class="sptxt sp_txt1">전일대비</span>
        <em><span class="ico up">상승</span><span class="blind">11,000</span></em>
        <span class="bar">l</span>
        <em><span class="blind">1.21</span><span class="per">%</span></em>
      </p>
      <div class="new_totalinfo">SK하이닉스 오늘의시세 거래량 329,206</div>
    </div>
    """
    soup = BeautifulSoup(html, "html.parser")

    service = NaverStockService()
    assert service._extract_change_percent(soup) == 1.21


def test_extract_change_percent_keeps_real_zero_when_only_flat_value_exists():
    html = """
    <div class="rate_info">
      <p class="no_exday">
        <span class="sptxt sp_txt1">전일대비</span>
        <em><span class="ico sam">보합</span><span class="blind">0</span></em>
        <span class="bar">l</span>
        <em><span class="blind">0.00</span><span class="per">%</span></em>
      </p>
      <div class="new_totalinfo">거래량 12,345</div>
    </div>
    """
    soup = BeautifulSoup(html, "html.parser")

    service = NaverStockService()
    assert service._extract_change_percent(soup) == 0.0


def test_extract_domestic_market_snapshot_keeps_price_and_change_in_same_block():
    html = """
    <div class="new_totalinfo">
      종목 시세 정보 2026년 03월 16일 09시 21분 기준 장중
      종목명 SK하이닉스 종목코드 000660
      현재가 941,000 전일대비 상승 31,000 플러스 3.41 퍼센트
      전일가 910,000 시가 925,000 고가 945,000 저가 924,000 거래량 735,601
    </div>
    """
    soup = BeautifulSoup(html, "html.parser")

    service = NaverStockService()
    snapshot = service._extract_domestic_market_snapshot(soup)

    assert snapshot is not None
    assert snapshot["current_price"] == 941000.0
    assert snapshot["previous_close"] == 910000.0
    assert snapshot["change_percent"] == 3.41


def test_extract_domestic_market_snapshot_prefers_live_block_over_flat_helper_block():
    html = """
    <div class="new_totalinfo">
      종목 시세 정보 2026년 03월 17일 09시 30분 기준 장중
      SK하이닉스 오늘의시세 974,000 포인트 0 포인트 보합 0.00%
      전일대비 보합 0 0 l 0.00% 주요 시세 전일 974,000 고가 0 거래량 0
      SK하이닉스 오늘의시세 1,004,000 포인트 30,000 포인트 상승 3.08%
      전일대비 상승 30,000 l + 3.08% 주요 시세 전일 974,000 고가 1,008,000 저가 984,000 거래량 697,769
    </div>
    """
    soup = BeautifulSoup(html, "html.parser")

    service = NaverStockService()
    snapshot = service._extract_domestic_market_snapshot(soup)

    assert snapshot is not None
    assert snapshot["current_price"] == 1004000.0
    assert snapshot["previous_close"] == 974000.0
    assert snapshot["change_percent"] == 3.08
    assert snapshot["volume"] == 697769.0
