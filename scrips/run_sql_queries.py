import pandas as pd
import sqlite3

# 1. 加载清洗后的数据
df = pd.read_csv('../data/ecommerce_clean_sample.csv')
print(f"✅ 数据加载成功，共 {len(df)} 行，{len(df.columns)} 列")

# 2. 创建内存数据库并导入数据
conn = sqlite3.connect(':memory:')
df.to_sql('orders', conn, index=False, if_exists='replace')
print("✅ 数据已导入 SQLite 数据库（表名：orders）\n")

# 3. 定义 SQL 查询（与你的项目指标对应）
sql_queries = {
    "1. GMV 与客单价": """
        SELECT 
            SUM(total_price_usd) AS GMV,
            ROUND(AVG(total_price_usd), 2) AS AOV
        FROM orders;
    """,

    "2. 总订单数、总用户数": """
        SELECT 
            COUNT(DISTINCT order_id) AS total_orders,
            COUNT(DISTINCT customer_id) AS total_users
        FROM orders;
    """,

    "3. 复购率": """
        WITH user_orders AS (
            SELECT customer_id, COUNT(DISTINCT order_id) AS order_cnt
            FROM orders
            GROUP BY customer_id
        )
        SELECT 
            ROUND(100.0 * SUM(CASE WHEN order_cnt >= 2 THEN 1 ELSE 0 END) / COUNT(*), 2) || '%' AS repeat_rate
        FROM user_orders;
    """,

    "4. 月度销售趋势（前6个月）": """
        SELECT 
            STRFTIME('%Y-%m', order_date) AS month,
            ROUND(SUM(total_price_usd), 2) AS monthly_sales
        FROM orders
        GROUP BY month
        ORDER BY month
        LIMIT 6;
    """,

    "5. 配送时长分组销售额占比": """
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
    """,

    "6. 退货原因 Top 5": """
        SELECT 
            return_reason,
            COUNT(*) AS cnt
        FROM orders
        WHERE return_reason IS NOT NULL
        GROUP BY return_reason
        ORDER BY cnt DESC
        LIMIT 5;
    """,

    "7. 客户分层销售额占比": """
        SELECT 
            customer_segment,
            ROUND(100.0 * SUM(total_price_usd) / (SELECT SUM(total_price_usd) FROM orders), 2) || '%' AS sales_pct
        FROM orders
        GROUP BY customer_segment;
    """,

    "8. Top 10% 高价值用户贡献占比": """
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
    """
}

# 4. 执行并打印结果
for name, sql in sql_queries.items():
    print(f"--- {name} ---")
    try:
        result = pd.read_sql_query(sql, conn)
        print(result.to_string(index=False))
        print()
    except Exception as e:
        print(f"❌ 查询出错：{e}\n")

# 5. 关闭连接
conn.close()