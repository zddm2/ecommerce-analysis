# 电商数据集数据字典（清洗后）

| 字段名 | 类型 | 说明 | 清洗/备注 |
|--------|------|------|-----------|
| order_id | object | 订单唯一ID | 无缺失，主键 |
| customer_id | object | 用户ID | 无缺失 |
| order_date | datetime | 订单日期 | 删除2024-2026外数据 |
| unit_price_usd | float64 | 单价(美元) | 删除≤0或>5000；缺失用中位数填充 |
| quantity | int64 | 购买数量 | 删除≤0或>1000；缺失填充1 |
| discount_percent | int64 | 折扣百分比 | 缺失填充0 |
| total_price_usd | float64 | 订单总金额(美元) | 已含折扣 |
| profit_usd | float64 | 利润 | 过滤负值 |
| category | object | 产品大类 | 缺失填'Unknown' |
| brand | object | 品牌 | 缺失填'Unknown' |
| age | int64 | 用户年龄 | 保留0-120 |
| customer_segment | object | 用户分层 | 原始值 |
| country | object | 国家 | 用于地理分析 |
| payment_method | object | 支付方式 | 分类变量 |
| shipping_cost_usd | float64 | 运费 | 直接使用 |
| delivery_days | int64 | 配送天数 | 直接使用 |
| review_sentiment | object | 评论情感 | 分类变量 |
| device_type | object | 设备类型 | 用于渠道分析 |
| ... | ... | ... | ... |