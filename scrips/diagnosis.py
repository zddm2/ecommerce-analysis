# ========== Day 3：深入诊断复购率极低的原因 ==========
# 目标：分析为什么用户几乎不回来购买？从物流、评分、退货、价格、用户行为等角度挖掘线索。
# 同时构建 RFM 模型，进一步刻画用户价值。

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# 设置显示选项
pd.set_option('display.max_columns', None)
pd.set_option('display.float_format', '{:.2f}'.format)

# 1. 加载清洗后的数据（20万行）
print("=" * 60)
print("第一步：加载数据")
print("=" * 60)
df = pd.read_csv('../data/ecommerce_clean_sample.csv')
# 转换日期格式
df['order_date'] = pd.to_datetime(df['order_date'])
print(f"数据形状: {df.shape}")
print(f"日期范围: {df['order_date'].min()} 至 {df['order_date'].max()}")
print(f"用户数: {df['customer_id'].nunique()}, 订单数: {df['order_id'].nunique()}")

# ============================================================
# 2. 物流与体验分析：配送天数、评分、退货原因
# ============================================================
print("\n" + "=" * 60)
print("第二步：物流与体验分析（潜在流失原因）")
print("=" * 60)

# 2.1 配送天数分布
delivery_stats = df['delivery_days'].describe()
print("\n配送天数统计：")
print(delivery_stats)

# 配送天数分组看销售额占比
df['delivery_bin'] = pd.cut(df['delivery_days'], bins=[0, 3, 5, 7, 100],
                            labels=['快速(≤3天)', '正常(4-5天)', '较慢(6-7天)', '很慢(>7天)'])
delivery_sales = df.groupby('delivery_bin', observed=False)['total_price_usd'].sum()
delivery_pct = delivery_sales / df['total_price_usd'].sum() * 100
print("\n不同配送时长下的销售额占比：")
for bin_name, pct in delivery_pct.items():
    print(f"  {bin_name}: {pct:.1f}%")

# 2.2 用户评分分布
print(f"\n用户评分（rating）统计：")
print(df['rating'].describe())
# 评分与销售额的关系（按评分分组）
rating_sales = df.groupby('rating')['total_price_usd'].sum()
print("\n各评分对应的总销售额：")
print(rating_sales)

# 2.3 退货原因（仅看有退货的订单）
if 'return_reason' in df.columns:
    return_reason_counts = df['return_reason'].value_counts(dropna=False)
    print("\n退货原因分布（含缺失）：")
    print(return_reason_counts)
    # 退货率
    return_orders = df[df['return_reason'].notna()]['order_id'].nunique()
    total_orders = df['order_id'].nunique()
    print(f"\n退货订单占比: {return_orders / total_orders * 100:.2f}%")

# ============================================================
# 3. 价格与折扣敏感度分析
# ============================================================
print("\n" + "=" * 60)
print("第三步：价格与折扣对复购的潜在影响")
print("=" * 60)

# 3.1 客单价分层（看高客单价用户是否更容易复购？但复购用户太少，只能看整体）
df['price_tier'] = pd.cut(df['unit_price_usd'], bins=[0, 50, 100, 200, 500],
                          labels=['<50', '50-100', '100-200', '200-500'])
price_sales = df.groupby('price_tier', observed=False)['total_price_usd'].sum()
price_pct = price_sales / df['total_price_usd'].sum() * 100
print("不同单价区间的销售额占比：")
for tier, pct in price_pct.items():
    print(f"  {tier}: {pct:.1f}%")

# 3.2 折扣力度分析
print(f"\n折扣百分比统计：")
print(df['discount_percent'].describe())
# 折扣使用情况（是否有折扣 vs 无折扣）
df['has_discount'] = df['discount_percent'] > 0
discount_sales = df.groupby('has_discount')['total_price_usd'].sum()
discount_pct = discount_sales / df['total_price_usd'].sum() * 100
print("\n有折扣订单与无折扣订单的销售额占比：")
print(f"  有折扣: {discount_pct[True]:.1f}%")
print(f"  无折扣: {discount_pct[False]:.1f}%")

# 3.3 优惠券使用与客单价的关系
if 'coupon_used' in df.columns:
    coupon_aov = df.groupby('coupon_used')['total_price_usd'].mean()
    print("\n使用/未使用优惠券的客单价对比：")
    print(coupon_aov)

# ============================================================
# 4. 用户行为与设备分析
# ============================================================
print("\n" + "=" * 60)
print("第四步：用户行为与设备分析")
print("=" * 60)

# 4.1 设备类型销售额占比
if 'device_type' in df.columns:
    device_sales = df.groupby('device_type')['total_price_usd'].sum().sort_values(ascending=False)
    device_pct = device_sales / df['total_price_usd'].sum() * 100
    print("设备类型销售额占比：")
    for device, pct in device_pct.items():
        print(f"  {device}: {pct:.1f}%")

# 4.2 流量来源销售额占比
if 'traffic_source' in df.columns:
    source_sales = df.groupby('traffic_source')['total_price_usd'].sum().sort_values(ascending=False)
    source_pct = source_sales / df['total_price_usd'].sum() * 100
    print("\n流量来源销售额占比：")
    for src, pct in source_pct.items():
        print(f"  {src}: {pct:.1f}%")

# ============================================================
# 5. RFM 模型（简化版，因复购极少，重点看 Recency 和 Monetary）
# ============================================================
print("\n" + "=" * 60)
print("第五步：RFM 模型（用户价值分层）")
print("=" * 60)

# 以当前日期为基准（数据集最后一天）
reference_date = df['order_date'].max()
print(f"参考日期（数据最后一天）: {reference_date}")

# 计算每个用户的 R, F, M
rfm = df.groupby('customer_id').agg({
    'order_date': lambda x: (reference_date - x.max()).days,  # Recency：距离最后一次购买的天数
    'order_id': 'nunique',  # Frequency：订单数（几乎都是1）
    'total_price_usd': 'sum'  # Monetary：总消费额
}).rename(columns={'order_date': 'Recency', 'order_id': 'Frequency', 'total_price_usd': 'Monetary'})

print(f"RFM 数据形状: {rfm.shape}")
print(f"频率分布（订单数）：\n{rfm['Frequency'].value_counts().sort_index()}")

# 由于 Frequency 几乎全为1，我们主要用 Recency 和 Monetary 做二维分组
# 将 Recency 和 Monetary 分为三等分（分位数）
rfm['R_score'] = pd.qcut(rfm['Recency'], q=3, labels=['3(最近)', '2(中等)', '1(最久)'])
rfm['M_score'] = pd.qcut(rfm['Monetary'], q=3, labels=['3(高)', '2(中)', '1(低)'])
# 组合得分
rfm['RFM_score'] = rfm['R_score'].astype(str) + rfm['M_score'].astype(str)

print("\n用户 RFM 分层（R_score + M_score）分布：")
print(rfm['RFM_score'].value_counts().head(10))

# 重点：高价值但很久没来的用户（R_score='1(最久)', M_score='3(高)'）
lost_high_value = rfm[(rfm['R_score'] == '1(最久)') & (rfm['M_score'] == '3(高)')]
print(f"\n流失的高价值用户数量: {len(lost_high_value)}")
print(f"这些用户贡献的总金额: ${lost_high_value['Monetary'].sum():,.2f}")

# ============================================================
# 6. 复购用户画像（与仅购买一次的用户对比）
# ============================================================
print("\n" + "=" * 60)
print("第六步：复购用户 vs 单次用户对比（找出复购用户的特征）")
print("=" * 60)

# 找出复购用户（订单数>=2）
user_orders = df.groupby('customer_id')['order_id'].nunique()
repeat_users = user_orders[user_orders >= 2].index.tolist()
print(f"复购用户数量: {len(repeat_users)}")

if len(repeat_users) > 0:
    # 复购用户的订单数据
    repeat_df = df[df['customer_id'].isin(repeat_users)]
    single_df = df[~df['customer_id'].isin(repeat_users)]

    # 对比平均客单价
    repeat_aov = repeat_df.groupby('order_id')['total_price_usd'].sum().mean()
    single_aov = single_df.groupby('order_id')['total_price_usd'].sum().mean()
    print(f"\n复购用户的平均客单价: ${repeat_aov:.2f}")
    print(f"单次用户的平均客单价: ${single_aov:.2f}")

    # 对比配送天数
    repeat_delivery = repeat_df['delivery_days'].mean()
    single_delivery = single_df['delivery_days'].mean()
    print(f"\n复购用户的平均配送天数: {repeat_delivery:.1f} 天")
    print(f"单次用户的平均配送天数: {single_delivery:.1f} 天")

    # 对比评分
    repeat_rating = repeat_df['rating'].mean()
    single_rating = single_df['rating'].mean()
    print(f"\n复购用户的平均评分: {repeat_rating:.2f}")
    print(f"单次用户的平均评分: {single_rating:.2f}")

    # 对比折扣力度
    repeat_discount = repeat_df['discount_percent'].mean()
    single_discount = single_df['discount_percent'].mean()
    print(f"\n复购用户的平均折扣%: {repeat_discount:.1f}%")
    print(f"单次用户的平均折扣%: {single_discount:.1f}%")
else:
    print("复购用户数量为0，无法对比。")

# ============================================================
# 7. 总结输出（关键发现）
# ============================================================
print("\n" + "=" * 60)
print("Day 3 诊断结论汇总")
print("=" * 60)
print("""
基于以上分析，针对复购率仅0.2%的可能原因：
1. 物流时长：平均配送天数XX天（上面输出），若超过5天可能影响体验。
2. 用户评分：平均评分XX，若偏低则用户不满意。
3. 价格敏感度：高客单价用户流失是否更严重？
4. 优惠券使用：复购用户是否更倾向于使用优惠券？
5. 设备/渠道：复购用户是否集中在某种设备或流量来源？

请根据实际输出数字，填写到简历的项目发现中。
""")

print("Day 3 代码执行完毕。")