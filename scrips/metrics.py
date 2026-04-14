# ========== 1. 加载清洗后的数据 ==========
import pandas as pd
import numpy as np

df = pd.read_csv('../data/ecommerce_clean_sample.csv')
# 将订单日期转为 datetime（如果还没转）
df['order_date'] = pd.to_datetime(df['order_date'])

# ========== 2. 核心指标计算 ==========
# 总销售额 (GMV)
gmv = df['total_price_usd'].sum()
# 总订单数（去重）
total_orders = df['order_id'].nunique()
# 总用户数（去重）
total_users = df['customer_id'].nunique()
# 客单价 (AOV)
aov = gmv / total_orders
# 平均每单件数
avg_items_per_order = df.groupby('order_id')['quantity'].sum().mean()
# 有利润的订单占比（利润 > 0）
profitable_orders_ratio = (df.groupby('order_id')['profit_usd'].sum() > 0).mean()

print("="*50)
print("全局核心指标")
print("="*50)
print(f"总销售额 (GMV): ${gmv:,.2f}")
print(f"总订单数: {total_orders:,}")
print(f"总用户数: {total_users:,}")
print(f"客单价 (AOV): ${aov:.2f}")
print(f"平均每单件数: {avg_items_per_order:.2f}")
print(f"盈利订单占比: {profitable_orders_ratio:.1%}")


user_order_counts = df.groupby('customer_id')['order_id'].nunique()
repeat_rate = (user_order_counts >= 2).sum() / len(user_order_counts) * 100
print(f"复购率: {repeat_rate:.2f}%")


# ========== 3. 时间趋势 ==========
# 按日聚合
daily = df.groupby(df['order_date'].dt.date).agg(
    daily_sales=('total_price_usd', 'sum'),
    daily_orders=('order_id', 'nunique')
).reset_index()

# 按月聚合
df['year_month'] = df['order_date'].dt.to_period('M')
monthly = df.groupby('year_month').agg(
    monthly_sales=('total_price_usd', 'sum'),
    monthly_orders=('order_id', 'nunique')
).reset_index()
monthly['year_month'] = monthly['year_month'].astype(str)

print("月度销售趋势（前6个月）：")
print(monthly.head(6))

# 找出销售额最高的月份
top_month = monthly.loc[monthly['monthly_sales'].idxmax()]
print(f"\n销售额最高的月份: {top_month['year_month']}，销售额 ${top_month['monthly_sales']:,.2f}")

# 找出订单量最高的星期几（需要从 order_date 提取 weekday）
df['weekday'] = df['order_date'].dt.dayofweek  # 0=周一, 6=周日
weekday_sales = df.groupby('weekday')['total_price_usd'].sum()
weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
best_weekday = weekday_names[weekday_sales.idxmax()]
print(f"销售额最高的星期: {best_weekday}")




# ========== 4. 用户分层分析 ==========
# 4.1 不同客户分层的销售额占比
segment_sales = df.groupby('customer_segment')['total_price_usd'].sum().sort_values(ascending=False)
segment_pct = segment_sales / gmv * 100
print("\n客户分层销售额占比：")
for seg, pct in segment_pct.items():
    print(f"  {seg}: {pct:.1f}%")

# 4.2 不同忠诚度分数的消费力（如果 loyalty_score 是数值）
# 将 loyalty_score 分箱（假设分数范围0-100）
if 'customer_loyalty_score' in df.columns:
    df['loyalty_group'] = pd.cut(df['customer_loyalty_score'], bins=[0, 30, 60, 100], labels=['低', '中', '高'])
    loyalty_sales = df.groupby('loyalty_group')['total_price_usd'].sum()
    print("\n忠诚度分组销售额：")
    print(loyalty_sales)

# 4.3 复购率：购买次数 >=2 的用户占比
user_orders = df.groupby('customer_id')['order_id'].nunique()
repeat_users = (user_orders >= 2).sum()
repeat_rate = repeat_users / total_users * 100
print(f"\n复购率: {repeat_rate:.1f}% （{repeat_users:,} / {total_users:,}）")

# 4.4 高价值用户（Top 10% 消费额）贡献占比
user_spend = df.groupby('customer_id')['total_price_usd'].sum().sort_values(ascending=False)
top10_threshold = user_spend.quantile(0.9)
top10_users = user_spend[user_spend >= top10_threshold]
top10_contribution = top10_users.sum() / gmv * 100
print(f"Top 10% 高价值用户贡献了 {top10_contribution:.1f}% 的销售额")



# ========== 5. 产品与类别分析 ==========
# 5.1 销售额 Top 5 类别
category_sales = df.groupby('category')['total_price_usd'].sum().sort_values(ascending=False)
print("\n销售额 Top 5 类别：")
print(category_sales.head(5))

# 5.2 销量 Top 5 品牌
brand_quantity = df.groupby('brand')['quantity'].sum().sort_values(ascending=False)
print("\n销量 Top 5 品牌：")
print(brand_quantity.head(5))

# 5.3 折扣使用情况（使用了优惠券的订单占比）
if 'coupon_used' in df.columns:
    coupon_orders = df[df['coupon_used'] == 'Yes']['order_id'].nunique()
    coupon_rate = coupon_orders / total_orders * 100
    print(f"\n使用优惠券的订单占比: {coupon_rate:.1f}%")