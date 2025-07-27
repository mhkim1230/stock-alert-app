# 알림 및 관심항목 조회 쿼리 예제

## 1. 관심항목 (WATCHLIST) 조회

### 1.1 사용자별 전체 관심항목 조회
```sql
SELECT w.id, w.symbol, w.created_at, u.username
FROM WATCHLIST w
JOIN USER u ON w.user_id = u.id
WHERE w.user_id = :user_id
ORDER BY w.created_at DESC;
```

### 1.2 특정 종목 관심항목 조회
```sql
SELECT w.id, w.symbol, w.created_at, u.username
FROM WATCHLIST w
JOIN USER u ON w.user_id = u.id
WHERE w.symbol = :symbol;
```

## 2. 주식 알림 (STOCK_ALERT) 조회

### 2.1 활성화된 주식 알림 조회
```sql
SELECT 
    sa.id,
    sa.stock_symbol,
    sa.target_price,
    sa.condition,
    sa.created_at,
    sa.triggered_at,
    sa.last_checked,
    u.username
FROM STOCK_ALERT sa
JOIN USER u ON sa.user_id = u.id
WHERE sa.is_active = 1
ORDER BY sa.created_at DESC;
```

### 2.2 사용자별 주식 알림 조회
```sql
SELECT 
    sa.id,
    sa.stock_symbol,
    sa.target_price,
    sa.condition,
    sa.created_at,
    sa.triggered_at
FROM STOCK_ALERT sa
WHERE sa.user_id = :user_id
ORDER BY sa.created_at DESC;
```

### 2.3 트리거된 주식 알림 조회
```sql
SELECT 
    sa.id,
    sa.stock_symbol,
    sa.target_price,
    sa.condition,
    sa.triggered_at,
    u.username
FROM STOCK_ALERT sa
JOIN USER u ON sa.user_id = u.id
WHERE sa.triggered_at IS NOT NULL
ORDER BY sa.triggered_at DESC;
```

## 3. 환율 알림 (CURRENCY_ALERT) 조회

### 3.1 활성화된 환율 알림 조회
```sql
SELECT 
    ca.id,
    ca.base_currency,
    ca.target_currency,
    ca.target_rate,
    ca.condition,
    ca.created_at,
    ca.triggered_at,
    u.username
FROM CURRENCY_ALERT ca
JOIN USER u ON ca.user_id = u.id
WHERE ca.is_active = true
ORDER BY ca.created_at DESC;
```

### 3.2 사용자별 환율 알림 조회
```sql
SELECT 
    ca.id,
    ca.base_currency,
    ca.target_currency,
    ca.target_rate,
    ca.condition,
    ca.created_at,
    ca.triggered_at
FROM CURRENCY_ALERT ca
WHERE ca.user_id = :user_id
ORDER BY ca.created_at DESC;
```

## 4. 뉴스 알림 (NEWS_ALERT) 조회

### 4.1 활성화된 뉴스 알림 조회
```sql
SELECT 
    na.id,
    na.keywords,
    na.created_at,
    na.last_checked,
    u.username
FROM NEWS_ALERT na
JOIN USER u ON na.user_id = u.id
WHERE na.is_active = true
ORDER BY na.created_at DESC;
```

### 4.2 사용자별 뉴스 알림 조회
```sql
SELECT 
    na.id,
    na.keywords,
    na.created_at,
    na.last_checked
FROM NEWS_ALERT na
WHERE na.user_id = :user_id
ORDER BY na.created_at DESC;
```

## 5. 알림 로그 (NOTIFICATION_LOG) 조회

### 5.1 전체 알림 로그 조회
```sql
SELECT 
    nl.id,
    nl.alert_type,
    nl.message,
    nl.sent_at,
    nl.status,
    u.username
FROM NOTIFICATION_LOG nl
JOIN USER u ON nl.user_id = u.id
ORDER BY nl.sent_at DESC;
```

### 5.2 사용자별 알림 로그 조회
```sql
SELECT 
    nl.id,
    nl.alert_type,
    nl.message,
    nl.sent_at,
    nl.status
FROM NOTIFICATION_LOG nl
WHERE nl.user_id = :user_id
ORDER BY nl.sent_at DESC;
```

### 5.3 실패한 알림 로그 조회
```sql
SELECT 
    nl.id,
    nl.alert_type,
    nl.message,
    nl.sent_at,
    nl.error_message,
    u.username
FROM NOTIFICATION_LOG nl
JOIN USER u ON nl.user_id = u.id
WHERE nl.status = 'failed'
ORDER BY nl.sent_at DESC;
```

## 6. 통계 쿼리

### 6.1 사용자별 알림 개수 통계
```sql
SELECT 
    u.username,
    COUNT(DISTINCT sa.id) as stock_alerts,
    COUNT(DISTINCT ca.id) as currency_alerts,
    COUNT(DISTINCT na.id) as news_alerts
FROM USER u
LEFT JOIN STOCK_ALERT sa ON u.id = sa.user_id
LEFT JOIN CURRENCY_ALERT ca ON u.id = ca.user_id
LEFT JOIN NEWS_ALERT na ON u.id = na.user_id
GROUP BY u.id, u.username;
```

### 6.2 알림 타입별 트리거 통계
```sql
SELECT 
    'stock' as alert_type,
    COUNT(*) as total_alerts,
    COUNT(CASE WHEN triggered_at IS NOT NULL THEN 1 END) as triggered_alerts
FROM STOCK_ALERT
UNION ALL
SELECT 
    'currency' as alert_type,
    COUNT(*) as total_alerts,
    COUNT(CASE WHEN triggered_at IS NOT NULL THEN 1 END) as triggered_alerts
FROM CURRENCY_ALERT;
``` 