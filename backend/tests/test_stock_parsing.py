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
