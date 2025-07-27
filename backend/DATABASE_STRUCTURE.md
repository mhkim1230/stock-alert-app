# 데이터베이스 구조

## 테이블 구조

### 1. USER (사용자)
- `id`: String(36), Primary Key, UUID
- `username`: String(50), Unique, Not Null
- `email`: String(100), Unique, Not Null
- `password_hash`: String(100), Not Null
- `is_active`: Boolean, Default: True
- `created_at`: TIMESTAMP, Default: CURRENT_TIMESTAMP

### 2. DEVICE_TOKEN (디바이스 토큰)
- `id`: String(36), Primary Key, UUID
- `user_id`: String(36), Foreign Key -> USER.id
- `token`: String(200), Not Null
- `device_type`: String(20)
- `created_at`: TIMESTAMP, Default: CURRENT_TIMESTAMP

### 3. WATCHLIST (관심 종목)
- `id`: String(36), Primary Key, UUID
- `user_id`: String(36), Foreign Key -> USER.id
- `symbol`: String(20), Not Null
- `created_at`: TIMESTAMP, Default: CURRENT_TIMESTAMP

### 4. STOCK_ALERT (주식 알림)
- `id`: String(36), Primary Key, UUID
- `user_id`: String(36), Foreign Key -> USER.id
- `stock_symbol`: String(20), Not Null
- `target_price`: Numeric(10,2), Not Null
- `condition`: String(10), Not Null (above/below/equal)
- `is_active`: Integer, Default: 1
- `created_at`: TIMESTAMP, Default: CURRENT_TIMESTAMP
- `triggered_at`: TIMESTAMP, Nullable
- `last_checked`: TIMESTAMP, Nullable

### 5. CURRENCY_ALERT (환율 알림)
- `id`: String(36), Primary Key, UUID
- `user_id`: String(36), Foreign Key -> USER.id
- `base_currency`: String(3), Not Null
- `target_currency`: String(3), Not Null
- `target_rate`: Numeric(10,4), Not Null
- `condition`: String(10), Not Null (above/below/equal)
- `is_active`: Boolean, Default: True
- `created_at`: TIMESTAMP, Default: CURRENT_TIMESTAMP
- `triggered_at`: TIMESTAMP, Nullable

### 6. NEWS_ALERT (뉴스 알림)
- `id`: String(36), Primary Key, UUID
- `user_id`: String(36), Foreign Key -> USER.id
- `keywords`: String(200), Not Null
- `is_active`: Boolean, Default: True
- `created_at`: TIMESTAMP, Default: CURRENT_TIMESTAMP
- `last_checked`: TIMESTAMP, Nullable

### 7. NOTIFICATION_LOG (알림 로그)
- `id`: String(36), Primary Key, UUID
- `user_id`: String(36), Foreign Key -> USER.id
- `alert_id`: String(36), Not Null
- `alert_type`: String(20), Not Null (stock/currency/news)
- `message`: String(500), Not Null
- `sent_at`: TIMESTAMP, Default: CURRENT_TIMESTAMP
- `status`: String(20), Not Null (success/failed)
- `error_message`: String(500), Nullable

## 관계
- USER -> DEVICE_TOKEN: 1:N
- USER -> WATCHLIST: 1:N
- USER -> STOCK_ALERT: 1:N
- USER -> CURRENCY_ALERT: 1:N
- USER -> NEWS_ALERT: 1:N
- USER -> NOTIFICATION_LOG: 1:N

## 날짜/시간 처리
모든 TIMESTAMP 컬럼은 Oracle DB 형식을 사용합니다:
- 현재 시간: `CURRENT_TIMESTAMP`
- 시간 간격: `INTERVAL`
- 날짜 비교: `column_name < CURRENT_TIMESTAMP - INTERVAL '30' MINUTE` 