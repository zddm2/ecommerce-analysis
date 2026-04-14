 "1. GMV 与客单价":
        SELECT
            SUM(total_price_usd) AS GMV,
            ROUND(AVG(total_price_usd), 2) AS AOV
        FROM orders;


    "2. 总订单数、总用户数":
        SELECT
            COUNT(DISTINCT order_id) AS total_orders,
            COUNT(DISTINCT customer_id) AS total_users
        FROM orders;


    "3. 复购率":
        WITH user_orders AS (
            SELECT customer_id, COUNT(DISTINCT order_id) AS order_cnt
            FROM orders
            GROUP BY customer_id
        )
        SELECT
            ROUND(100.0 * SUM(CASE WHEN order_cnt >= 2 THEN 1 ELSE 0 END) / COUNT(*), 2) || '%' AS repeat_rate
        FROM user_orders;


    "4. 月度销售趋势（前6个月）":
        SELECT
            STRFTIME('%Y-%m', order_date) AS month,
            ROUND(SUM(total_price_usd), 2) AS monthly_sales
        FROM orders
        GROUP BY month
        ORDER BY month
        LIMIT 6;


    "5. 配送时长分组销售额占比":
        SELECT
            CASE
                WHEN delivery_days <= 3 THEN '≤3天'
                WHEN delivery_days <= 5 THEN '4-5天'
                WHEN delivery_days <= 7 THEN '6-7天'
                ELSE '>7天'
            END AS delivery_group,
            ROUND(100.0 * SUM(total_price_usd) / (SELECT SUM(total_price_usd) FROM orders), 2) || '%' AS sales_pct
        FROM orders
        GROUP BY delivery_group
        ORDER BY MIN(delivery_days);


    "6. 退货原因 Top 5":
        SELECT
            return_reason,
            COUNT(*) AS cnt
        FROM orders
        WHERE return_reason IS NOT NULL
        GROUP BY return_reason
        ORDER BY cnt DESC
        LIMIT 5;


    "7. 客户分层销售额占比":
        SELECT
            customer_segment,
            ROUND(100.0 * SUM(total_price_usd) / (SELECT SUM(total_price_usd) FROM orders), 2) || '%' AS sales_pct
        FROM orders
        GROUP BY customer_segment;


    "8. Top 10% 高价值用户贡献占比":
        WITH user_spend AS (
    SELECT customer_id, SUM(total_price_usd) AS spend
    FROM orders
    GROUP BY customer_id
),
ranked AS (
    SELECT
        spend,
        ROW_NUMBER() OVER (ORDER BY spend DESC) AS rn,
        COUNT(*) OVER () AS total_cnt
    FROM user_spend
)
SELECT
    ROUND(100.0 * SUM(CASE WHEN rn <= total_cnt * 0.1 THEN spend ELSE 0 END) / SUM(spend), 2) || '%' AS top10_contribution
FROM ranked;