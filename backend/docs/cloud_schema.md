# Cloud DB Schema

Production and test databases are both hosted PostgreSQL.

## Tables

### `watchlist_items`
- `id` UUID string primary key
- `symbol` unique stock symbol
- `created_at`
- `updated_at`

Single-user app watchlist. This is the interest-items table.

### `stock_alerts`
- `id`
- `stock_symbol`
- `target_price`
- `condition`
- `is_active`
- `triggered_at`
- `created_at`
- `updated_at`

### `currency_alerts`
- `id`
- `base_currency`
- `target_currency`
- `target_rate`
- `condition`
- `is_active`
- `triggered_at`
- `created_at`
- `updated_at`

### `news_alerts`
- `id`
- `keywords`
- `is_active`
- `last_checked`
- `triggered_at`
- `created_at`
- `updated_at`

### `device_tokens`
- `id`
- `token`
- `platform`
- `is_active`
- `last_used_at`
- `created_at`
- `updated_at`

### `notification_logs`
- `id`
- `alert_id`
- `alert_type`
- `message`
- `status`
- `is_read`
- `extra_data`
- `sent_at`
- `created_at`

## Ownership Model
- No `users` table
- No `user_id`
- All rows belong to the one app owner
- Access control is enforced at API layer with `ADMIN_API_KEY`
