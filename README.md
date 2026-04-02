# 个人账单汇总工具 / Personal Bill Processor

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

🔒 自动汇总多来源账单数据（支付宝、微信、京东等），生成月度消费统计报表。完全本地处理，保护隐私。

## ✨ 特点

- 🔒 **完全本地** — 所有数据在本地处理，无隐私风险
- 📊 **多来源支持** — 支付宝、微信、京东，通过 YAML 配置轻松扩展
- 🎯 **自动识别** — 自动检测列头位置，自动适配新旧表头格式
- 📈 **统计分析** — 按类别、来源、日期自动生成 Excel 报表（4 个 sheet）
- ⚙️ **配置驱动** — 新增支付平台只需添加一个 YAML 文件，无需改代码

## 🏗️ 数据处理流程

```
原始账单文件                YAML 配置文件
(CSV/XLSX)                 (每个平台一个)
    │                          │
    ▼                          ▼
┌──────────────────────────────────────┐
│  1. 文件发现                          │
│  按 file_pattern 匹配 + 按月份过滤    │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│  2. 表头检测                          │
│  策略链：关键词匹配 → 固定行数兜底     │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│  3. 列映射                            │
│  各平台列名 → 统一字段名              │
│  支持主映射 + 备选映射（应对格式变更）  │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│  4. 过滤 + 清洗                       │
│  · 只保留支出记录                     │
│  · 移除 ¥ $ , ，等符号               │
│  · 处理退款：30.46(已退款0.06) → 30.40│
│  · 日期解析 + 无效数据剔除            │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│  5. 合并 + 输出                       │
│  · 多平台数据合并                     │
│  · 按类别/来源/日期分组统计           │
│  · 输出 Excel（带元数据头 + 4 个 sheet）│
└──────────────────────────────────────┘
```

## 🚀 快速开始

```bash
pip install -r requirements.txt
```

将账单文件放入 `bills/raw/`，命名规则：`来源_YYYYMM.csv/xlsx`

```bash
# 处理指定月份
python bill_processor.py -m 202603

# 交互式菜单
python bill_processor_simple.py
```

输出在 `bills/output/`，包含 4 个 sheet：明细、按类别统计、按来源统计、每日统计。

## ⚙️ 配置示例

```yaml
# bills/config/alipay.yaml
name: 支付宝
file_pattern: 'alipay_*.csv'
encoding: gbk

column_mapping:
  date: 交易时间
  description: 商品说明
  amount: 金额
  category: 交易分类
  income_expense: 收/支

# 备选映射（支付宝换过表头格式）
column_mapping_alt:
  date: 记录时间
  description: 备注
  amount: 金额
  category: 分类
  income_expense: 收支类型

amount_filter: '支出'
```

添加新平台：复制 `bills/config/example-alipay.yaml`，改列名映射即可。

## 📁 项目结构

```
bill-processor/
├── bill_processor.py          # 核心处理器
├── bill_processor_simple.py   # 交互式菜单版
├── fix_jingdong_final.py      # 京东账单修复脚本
├── bills/
│   ├── config/                # YAML 配置
│   │   ├── example-alipay.yaml
│   │   ├── example-wechat.yaml
│   │   ├── example-jingdong.yaml
│   │   └── example-bank.yaml
│   ├── raw/                   # 原始账单文件
│   └── output/                # 输出报表
└── requirements.txt
```

## 🔒 隐私

所有数据完全本地处理。`.gitignore` 已配置忽略 `bills/raw/` 和 `bills/output/`。

## License

MIT
