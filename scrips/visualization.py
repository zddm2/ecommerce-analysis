import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# 设置中文字体（如果报错，可以注释掉下面两行，改用英文标签）
plt.rcParams['font.sans-serif'] = ['SimHei']  # Windows
# plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']  # Mac
plt.rcParams['axes.unicode_minus'] = False

# 加载清洗后的数据
df = pd.read_csv('../data/ecommerce_clean_sample.csv')
df['order_date'] = pd.to_datetime(df['order_date'])

# 创建输出文件夹
os.makedirs('../output/figures', exist_ok=True)

# 1. 配送天数分布（直方图 + 箱线图）
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
sns.histplot(df['delivery_days'], bins=20, kde=True, ax=axes[0])
axes[0].set_title('配送天数分布')
axes[0].set_xlabel('天数')
sns.boxplot(y=df['delivery_days'], ax=axes[1])
axes[1].set_title('配送天数箱线图')
plt.tight_layout()
plt.savefig('../output/figures/delivery_distribution.png', dpi=100)
plt.show()

# 2. 不同配送时长区间的销售额占比（饼图）
delivery_bins = pd.cut(df['delivery_days'], bins=[0,3,5,7,100], labels=['≤3天', '4-5天', '6-7天', '>7天'])
delivery_sales = df.groupby(delivery_bins, observed=False)['total_price_usd'].sum()
plt.figure(figsize=(8, 8))
plt.pie(delivery_sales, labels=delivery_sales.index, autopct='%1.1f%%', startangle=90)
plt.title('不同配送时长销售额占比')
plt.savefig('../output/figures/delivery_sales_pie.png', dpi=100)
plt.show()

# 3. 退货原因分布（只取非空，前5）
return_reasons = df['return_reason'].value_counts().dropna().head(5)
plt.figure(figsize=(10, 6))
sns.barplot(x=return_reasons.values, y=return_reasons.index, palette='Reds_r')
plt.title('退货原因 Top 5')
plt.xlabel('订单数')
plt.tight_layout()
plt.savefig('../output/figures/return_reasons.png', dpi=100)
plt.show()

# 4. 用户评分分布与销售额关系（双轴图）
rating_sales = df.groupby('rating')['total_price_usd'].sum()
rating_count = df['rating'].value_counts().sort_index()
fig, ax1 = plt.subplots(figsize=(10, 6))
ax1.bar(rating_sales.index, rating_sales.values, color='skyblue', label='销售额')
ax1.set_xlabel('评分')
ax1.set_ylabel('销售额（美元）', color='skyblue')
ax2 = ax1.twinx()
ax2.plot(rating_count.index, rating_count.values, color='red', marker='o', label='订单数')
ax2.set_ylabel('订单数', color='red')
plt.title('各评分的销售额与订单数')
fig.legend(loc='upper left')
plt.savefig('../output/figures/rating_analysis.png', dpi=100)
plt.show()

# 5. 折扣使用情况（需要先创建 has_discount 列）
df['has_discount'] = df['discount_percent'] > 0
discount_usage = df['has_discount'].value_counts()
labels = ['有折扣', '无折扣']
plt.figure(figsize=(6,6))
plt.pie(discount_usage, labels=labels, autopct='%1.1f%%', startangle=90)
plt.title('订单是否使用折扣')
plt.savefig('../output/figures/discount_usage.png', dpi=100)
plt.show()

# 6. RFM 热力图（R_score vs M_score 用户数）
reference_date = df['order_date'].max()
rfm = df.groupby('customer_id').agg({
    'order_date': lambda x: (reference_date - x.max()).days,
    'order_id': 'nunique',
    'total_price_usd': 'sum'
}).rename(columns={'order_date': 'Recency', 'order_id': 'Frequency', 'total_price_usd': 'Monetary'})
rfm['R_score'] = pd.qcut(rfm['Recency'], q=3, labels=['R3(最近)', 'R2(中等)', 'R1(最久)'])
rfm['M_score'] = pd.qcut(rfm['Monetary'], q=3, labels=['M3(高)', 'M2(中)', 'M1(低)'])
rfm_matrix = rfm.groupby(['R_score', 'M_score']).size().unstack(fill_value=0)
plt.figure(figsize=(8,6))
sns.heatmap(rfm_matrix, annot=True, fmt='d', cmap='YlGnBu')
plt.title('RFM 用户分层矩阵（用户数）')
plt.savefig('../output/figures/rfm_heatmap.png', dpi=100)
plt.show()

print("所有图表已保存至 ../output/figures/ 目录")