#!/bin/bash

# 가상 환경 활성화
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 테스트 실행
pytest tests/ \
    --cov=src \
    --cov-report=term-missing \
    --cov-report=html:coverage_report \
    -v -s

# 커버리지 보고서 열기
open coverage_report/index.html

# 가상 환경 비활성화
deactivate 