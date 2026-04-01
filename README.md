# 个人账单汇总工具 / Personal Bill Processor

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)

🔒 Local bill aggregator for WeChat, Alipay & JD.com. Privacy-first Python tool with auto-detection and monthly reports.

自动汇总多来源账单数据（支付宝、微信、京东等），生成月度消费统计报表。完全本地处理，保护隐私。

## ✨ 特点

- 🔒 **完全本地** - 所有数据在本地处理，无隐私风险
- 📊 **多来源支持** - 支付宝、微信、京东等多个账单来源
- 🎯 **自动识别** - 自动检测列头位置，无需手动配置
- 📈 **统计分析** - 按类别、来源、日期自动生成统计报表
- 🖥️ **交互友好** - 提供简单的交互式菜单，无需记忆命令
- ⚙️ **灵活配置** - 通过 YAML 配置文件轻松添加新的账单来源

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

配置驱动设计 — 新增支付平台只需添加一个 YAML 配置文件，无需修改 Python 代码。

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 准备账单文件

将账单文件放入 `bills/raw/` 目录：

```
bills/raw/
├── alipay_202602.csv      # 支付宝账单
├── wechat_202602.xlsx     # 微信账单
└── jingdong_202602.csv    # 京东账单
```

**文件命名规则：** `来源_YYYYMM.csv/xlsx`

### 3. 配置账单来源

复制示例配置并修改：

```bash
cp bills/config/example-alipay.yaml bills/config/alipay.yaml
```

根据你的账单格式调整配置文件。

### 4. 运行工具

#### 方式 1：交互式菜单（推荐）

**Windows：**

```bash
# 双击运行
run_interactive.bat

# 或命令行
python bill_processor_simple.py
```

**macOS/Linux：**

```bash
python bill_processor_simple.py
```

#### 方式 2：命令行参数

```bash
# 处理所有月份
python bill_processor.py

# 处理指定月份
python bill_processor.py -m 202602

# 自定义输出文件
python bill_processor.py -m 202602 -o custom.xlsx
```

### 5. 查看结果

输出文件在 `bills/output/` 目录：

```
bills/output/
└── summary_202602_20260307_v1.xlsx
```

文件包含 4 个工作表：

- **明细** - 所有账单记录
- **按类别统计** - 各类别的总金额、笔数、平均金额
- **按来源统计** - 各来源的统计
- **每日统计** - 每天的消费金额

---

## 📖 使用指南

### 交互式菜单

运行 `python bill_processor_simple.py` 后，会看到：

```
============================================================
个人账单汇总工具
自动汇总多来源账单，生成月度消费统计
============================================================

请选择功能：
  1. 处理本月账单
  2. 处理指定月份账单
  3. 处理所有账单
  4. 查看可用账单文件
  0. 退出

请选择 (0-4):
```

**选项说明：**

- **1** - 自动识别当前月份并处理
- **2** - 输入 YYYYMM 格式的月份（如 202602）
- **3** - 处理 raw 文件夹下所有账单
- **4** - 列出所有可用的账单文件

### 命令行参数

```bash
# 查看帮助
python bill_processor.py --help

# 处理指定月份
python bill_processor.py -m 202602
python bill_processor.py --month 202602

# 自定义输出文件
python bill_processor.py -m 202602 -o my_summary.xlsx
python bill_processor.py --month 202602 --output my_summary.xlsx
```

---

## ⚙️ 配置说明

### 配置文件结构

配置文件位于 `bills/config/` 目录，使用 YAML 格式：

```yaml
name: '支付宝'
file_pattern: 'alipay_*.csv'
encoding: 'gbk'

# 列名映射
column_mapping:
  date: '交易时间'
  description: '商品说明'
  amount: '金额'
  category: '交易分类'
  counterparty: '交易对方'
  payment_method: '收/支'

# 过滤支出记录
amount_filter: '支出'

# 自动检测列头
header_detection:
  enabled: true
  strategies:
    - type: 'keywords'
      keywords: ['交易时间', '商品说明', '金额']
      match_all: true
```

### 配置项说明

| 配置项             | 说明           | 示例             |
| ------------------ | -------------- | ---------------- |
| `name`             | 账单来源名称   | "支付宝"         |
| `file_pattern`     | 文件匹配模式   | "alipay\_\*.csv" |
| `encoding`         | 文件编码       | "gbk" 或 "utf-8" |
| `column_mapping`   | 列名映射       | 见上面示例       |
| `amount_filter`    | 支出过滤关键词 | "支出"           |
| `header_detection` | 自动检测列头   | 见上面示例       |

### 添加新的账单来源

1. 复制示例配置：

   ```bash
   cp bills/config/example-bank.yaml bills/config/mybank.yaml
   ```

2. 修改配置：
   - 更新 `name` 和 `file_pattern`
   - 根据账单格式调整 `column_mapping`
   - 设置正确的 `encoding`

3. 放入账单文件：

   ```
   bills/raw/mybank_202602.csv
   ```

4. 运行工具即可自动识别

---

## 🔧 Windows 乱码问题

### 问题原因

Windows 命令行默认使用 GBK 编码，可能导致中文显示乱码。

### 解决方案

#### 方案 1：使用启动脚本（推荐）

双击运行 `run_interactive.bat`，脚本会自动设置正确的编码。

#### 方案 2：使用简化版本

```bash
python bill_processor_simple.py
```

简化版本使用纯 ASCII 字符，不会出现乱码。

#### 方案 3：手动设置编码

```bash
chcp 65001
python bill_processor.py
```

---

## 📊 输出文件说明

### 文件命名规则

```
summary_[数据月份]_[更新日期]_v[版本号].xlsx
```

**示例：**

- `summary_202602_20260307_v1.xlsx` - 2026年2月数据，3月7日更新，版本1
- `summary_202602_20260307_v2.xlsx` - 同一天更新第2次，自动递增版本号

### Excel 工作表

1. **明细** - 所有账单记录，包含：
   - 日期、描述、金额、类别
   - 交易对方、支付方式
   - 来源（支付宝/微信/京东）

2. **按类别统计** - 各类别的：
   - 总金额
   - 笔数
   - 平均金额

3. **按来源统计** - 各来源的：
   - 总金额
   - 笔数

4. **每日统计** - 每天的消费金额

---

## 🛠️ 常见问题

### Q1：提示"没有找到任何账单数据"

**原因：**

- 账单文件不在 `bills/raw/` 目录
- 文件名格式不匹配
- 指定的月份没有对应文件

**解决：**

1. 检查文件位置
2. 确认文件名包含月份（如 `alipay_202602.csv`）
3. 使用菜单选项 4 查看可用文件

### Q2：处理失败，提示编码错误

**原因：**

- CSV 文件编码不是配置文件中指定的编码

**解决：**

- 用记事本打开 CSV，另存为 UTF-8 编码
- 或在配置文件中指定正确的编码（如 `gbk`）

### Q3：列名映射不正确

**原因：**

- 账单格式与配置文件不匹配

**解决：**

1. 打开账单文件，查看实际的列名
2. 更新配置文件中的 `column_mapping`
3. 确保列名完全匹配（包括空格）

### Q4：想要更漂亮的界面

**解决：**

```bash
pip install rich
```

安装 rich 库后，交互式界面会自动使用彩色输出和漂亮的表格。

---

## 📁 项目结构

```
bill-processor/
├── bill_processor.py              # 核心处理器
├── bill_processor_simple.py       # 简化交互版本
├── run_interactive.bat            # Windows 启动脚本
├── requirements.txt               # Python 依赖
├── .gitignore                     # Git 忽略规则
├── README.md                      # 本文档
└── bills/
    ├── config/                    # 配置文件目录
    │   ├── example-alipay.yaml    # 支付宝示例配置
    │   ├── example-wechat.yaml    # 微信示例配置
    │   └── example-bank.yaml      # 银行示例配置
    ├── raw/                       # 原始账单目录
    │   └── .gitkeep
    └── output/                    # 输出报表目录
        └── .gitkeep
```

---

## 🔒 隐私说明

- ✅ 所有数据完全在本地处理
- ✅ 不会上传到任何服务器
- ✅ 不依赖任何第三方服务
- ✅ 不会保存或传输个人信息

**建议：**

- 不要将个人账单文件提交到 Git
- 不要将个人配置文件提交到 Git
- `.gitignore` 已配置忽略这些文件

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

MIT License

---

## 🙏 致谢

感谢所有贡献者和使用者！

---

## 📞 联系方式

如有问题或建议，欢迎：

- 提交 Issue
- 发起 Discussion
- 提交 Pull Request

---

**享受简单可靠的账单管理！** 🚀
