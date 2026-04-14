import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

pd.set_option('display.max_columns',None)
pd.set_option('display.float_format','{:.2f}'.format)

# 只读取前5000行，查看结构
file_path = '../data/ecommerce_dataset_+1m.csv'
df_sample = pd.read_csv(file_path, nrows=5000)

# 查看行列数
print("数据形状（行, 列）:", df_sample.shape)

# 查看所有列名
print("\n列名列表：")
print(df_sample.columns.tolist())

# 查看每列数据类型和非空数量
print("\n数据类型与缺失值：")
print(df_sample.info())

# 查看前5行数据
print("\n前5行数据：")
print(df_sample.head())


# 1. 缺失值统计
missing = df_sample.isnull().sum()
missing_percent = (missing / len(df_sample)) * 100
missing_df = pd.DataFrame({'缺失数量': missing, '缺失比例(%)': missing_percent})
print("缺失值统计：")
print(missing_df[missing_df['缺失数量'] > 0])  # 只显示有缺失的列

# 2. 数值列描述统计
numeric_cols = df_sample.select_dtypes(include=[np.number]).columns.tolist()
print("\n数值列描述统计：")
print(df_sample[numeric_cols].describe())







# ========== 3. 定义清洗函数 ==========
def clean_chunk(df_chunk):
    """
    清洗每一个数据块
    处理：缺失值、异常值、重复值、派生列
    """
    # ---------- 1. 删除完全重复行 ----------
    df_chunk = df_chunk.drop_duplicates()

    # ---------- 2. 关键字段缺失处理 ----------
    # 订单ID和用户ID不能为空，否则删除行
    df_chunk = df_chunk.dropna(subset=['order_id', 'customer_id'])

    # 价格/数量缺失：用中位数/1填充（极少数情况）
    if 'unit_price_usd' in df_chunk.columns:
        df_chunk['unit_price_usd'] = df_chunk['unit_price_usd'].fillna(df_chunk['unit_price_usd'].median())
    if 'quantity' in df_chunk.columns:
        df_chunk['quantity'] = df_chunk['quantity'].fillna(1)

    # 折扣缺失：默认为0
    if 'discount_percent' in df_chunk.columns:
        df_chunk['discount_percent'] = df_chunk['discount_percent'].fillna(0)

    # ---------- 3. 异常值过滤 ----------
    # 单价：保留 0.01 ~ 5000 美元之间（合理范围，可调整）
    if 'unit_price_usd' in df_chunk.columns:
        df_chunk = df_chunk[(df_chunk['unit_price_usd'] >= 0.01) & (df_chunk['unit_price_usd'] <= 5000)]

    # 数量：保留 1 ~ 1000 之间
    if 'quantity' in df_chunk.columns:
        df_chunk = df_chunk[(df_chunk['quantity'] >= 1) & (df_chunk['quantity'] <= 1000)]

    # 利润、成本不能为负（若有负值，可能是退货，暂时过滤）
    if 'profit_usd' in df_chunk.columns:
        df_chunk = df_chunk[df_chunk['profit_usd'] >= 0]
    if 'cost_usd' in df_chunk.columns:
        df_chunk = df_chunk[df_chunk['cost_usd'] >= 0]

    # 年龄合理范围 0~120
    if 'age' in df_chunk.columns:
        df_chunk = df_chunk[(df_chunk['age'] >= 0) & (df_chunk['age'] <= 120)]

    # ---------- 4. 日期时间列标准化 ----------
    # order_date 转为 datetime，并过滤 2024-2026 年
    if 'order_date' in df_chunk.columns:
        df_chunk['order_date'] = pd.to_datetime(df_chunk['order_date'], errors='coerce')
        df_chunk = df_chunk.dropna(subset=['order_date'])
        df_chunk = df_chunk[(df_chunk['order_date'] >= '2024-01-01') &
                            (df_chunk['order_date'] <= '2026-12-31')]

    # 如果需要，可以派生“订单年份月份”列（便于后续分析）
    if 'order_date' in df_chunk.columns:
        df_chunk['order_year_month'] = df_chunk['order_date'].dt.strftime('%Y-%m')

    # ---------- 5. 派生总金额（若原始有 total_price_usd 则保留，否则用单价*数量） ----------
    # 该数据集已有 total_price_usd，但可能存在计算不一致，可以校验并保留原始列
    # 新增一个“订单总金额（折扣后）”确认列
    if 'unit_price_usd' in df_chunk.columns and 'quantity' in df_chunk.columns and 'discount_percent' in df_chunk.columns:
        df_chunk['calculated_total'] = df_chunk['unit_price_usd'] * df_chunk['quantity'] * (
                    1 - df_chunk['discount_percent'] / 100)
        # 如果原始 total_price_usd 与 calculated_total 差异过大（>1美元），标记异常，但不删除
        if 'total_price_usd' in df_chunk.columns:
            df_chunk['price_mismatch'] = abs(df_chunk['total_price_usd'] - df_chunk['calculated_total']) > 1

    # ---------- 6. 类别/品牌缺失：填充 'Unknown' ----------
    if 'category' in df_chunk.columns:
        df_chunk['category'] = df_chunk['category'].fillna('Unknown')
    if 'brand' in df_chunk.columns:
        df_chunk['brand'] = df_chunk['brand'].fillna('Unknown')

    # 删除一些明显无用或高基数列（可选，为节省内存）
    # 例如：order_second, order_minute 等细粒度时间可以保留，但也可以删除（根据分析需求）
    # 这里为了后续分析简洁，删除 order_second, order_minute（订单时间精确到小时足够）
    cols_to_drop = ['order_second', 'order_minute']
    for col in cols_to_drop:
        if col in df_chunk.columns:
            df_chunk = df_chunk.drop(columns=[col])

    return df_chunk


# ========== 4. 分块清洗并保存 ==========
chunk_size = 10000  # 每块1万行
max_rows_to_keep = 200000  # 最终保留20万行
cleaned_rows = 0
first_chunk = True
output_file = '../data/ecommerce_clean_sample.csv'

print("开始分块清洗（基于实际62列数据集）...")
for i, chunk in enumerate(pd.read_csv(file_path, chunksize=chunk_size, low_memory=False)):
    print(f"处理第 {i + 1} 块，原始行数: {len(chunk)}")
    chunk_clean = clean_chunk(chunk)
    chunk_clean = chunk_clean.reset_index(drop=True)
    cleaned_rows += len(chunk_clean)
    print(f"  清洗后行数: {len(chunk_clean)}，累计: {cleaned_rows}")

    if first_chunk:
        chunk_clean.to_csv(output_file, index=False, mode='w')
        first_chunk = False
    else:
        chunk_clean.to_csv(output_file, index=False, mode='a', header=False)

    if cleaned_rows >= max_rows_to_keep:
        print(f"已达到目标行数 {max_rows_to_keep}，停止处理。")
        break

print(f"清洗后样本已保存至: {output_file}")
print(f"最终保留行数: {cleaned_rows}")


# ========== 5. 验证清洗结果 ==========
df_check = pd.read_csv(output_file)
print("清洗后样本形状:", df_check.shape)
print("\n各列缺失值数量（非零）:")
print(df_check.isnull().sum()[df_check.isnull().sum() > 0])
print("\n关键数值列描述统计:")
key_cols = ['unit_price_usd', 'quantity', 'total_price_usd', 'profit_usd', 'age']
existing_cols = [c for c in key_cols if c in df_check.columns]
print(df_check[existing_cols].describe())