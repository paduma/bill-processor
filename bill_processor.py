#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
个人账单汇总工具
自动汇总不同来源的账单数据，生成月度消费统计报表
"""

import pandas as pd
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import sys
import argparse
import re

# 设置标准输出为 UTF-8（Windows 兼容）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

class BillProcessor:
    """账单处理器"""

    def __init__(self, config_dir: str = 'bills/config', raw_dir: str = 'bills/raw', target_month: str = None):
        self.config_dir = Path(config_dir)
        self.raw_dir = Path(raw_dir)
        self.target_month = target_month  # 格式: YYYYMM，如 202602
        self.configs = self._load_configs()
        print(f"📁 加载了 {len(self.configs)} 个配置文件")
        if self.target_month:
            print(f"🎯 目标月份: {self.target_month}")

    def _load_configs(self) -> List[Dict]:
        """加载所有配置文件"""
        configs = []
        for config_file in self.config_dir.glob('*.yaml'):
            # 跳过示例配置
            if config_file.stem.startswith('example-'):
                continue

            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                configs.append(config)
                print(f"  ✅ {config['name']}: {config_file.name}")

        return configs

    def _detect_header_row(self, file_path: Path, config: Dict) -> int:
        """自动检测列头所在行"""
        header_config = config.get('header_detection', {})

        if not header_config.get('enabled', False):
            # 如果没有启用自动检测，使用固定的 skip_rows
            return config.get('skip_rows', 0)

        strategies = header_config.get('strategies', [])
        encoding = config.get('encoding', 'utf-8')

        # 按优先级尝试每个策略
        for strategy in strategies:
            strategy_type = strategy.get('type')

            try:
                if strategy_type == 'keywords':
                    row = self._detect_by_keywords(file_path, strategy, encoding)
                    if row is not None:
                        print(f"    🔍 使用关键词检测: 第 {row} 行")
                        return row

                elif strategy_type == 'fixed':
                    row = strategy.get('skip_rows', 0)
                    print(f"    🔍 使用固定行数: 第 {row} 行")
                    return row

            except Exception as e:
                print(f"    ⚠️ 策略 '{strategy_type}' 失败: {e}")
                continue

        # 所有策略都失败，返回 0
        print(f"    ❌ 所有策略都失败，使用默认值: 0")
        return 0

    def _detect_by_keywords(self, file_path: Path, strategy: Dict, encoding: str) -> Optional[int]:
        """通过关键词检测列头"""
        keywords = strategy.get('keywords', [])
        match_all = strategy.get('match_all', True)

        if file_path.suffix == '.csv':
            # CSV 文件
            with open(file_path, 'r', encoding=encoding) as f:
                for i, line in enumerate(f):
                    if i >= 100:  # 只搜索前 100 行
                        break

                    if match_all:
                        if all(keyword in line for keyword in keywords):
                            return i
                    else:
                        if any(keyword in line for keyword in keywords):
                            return i

        elif file_path.suffix in ['.xlsx', '.xls']:
            # Excel 文件
            df_preview = pd.read_excel(file_path, nrows=100, header=None)

            for i in range(len(df_preview)):
                row = df_preview.iloc[i]
                row_str = ' '.join(str(cell) for cell in row if pd.notna(cell))

                if match_all:
                    if all(keyword in row_str for keyword in keywords):
                        return i
                else:
                    if any(keyword in row_str for keyword in keywords):
                        return i

        return None

    def _read_file(self, file_path: Path, config: Dict) -> pd.DataFrame:
        """根据配置读取文件"""
        encoding = config.get('encoding', 'utf-8')

        # 检测列头位置
        header_row = self._detect_header_row(file_path, config)

        # 读取文件
        if file_path.suffix == '.csv':
            # 特殊处理：某些 CSV 文件可能包含制表符，需要清理
            df = pd.read_csv(
                file_path,
                encoding=encoding,
                skiprows=header_row,
                header=0,
                sep=',',  # 明确指定逗号分隔
                engine='python'  # 使用 Python 引擎以更好地处理特殊字符
            )

            # 清理列名和数据中的空白字符（包括制表符）
            df.columns = df.columns.str.strip()
            for col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str).str.replace('\t', '').str.strip()

        elif file_path.suffix in ['.xlsx', '.xls']:
            df = pd.read_excel(
                file_path,
                skiprows=header_row,
                header=0
            )
        else:
            raise ValueError(f"不支持的文件格式: {file_path.suffix}")

        return df

    def _map_columns(self, df: pd.DataFrame, config: Dict) -> pd.DataFrame:
        """映射列名到统一格式，支持主映射和备选映射"""
        column_mapping = config['column_mapping']

        # 反向映射（原始列名 -> 标准列名）
        reverse_mapping = {v: k for k, v in column_mapping.items()}

        # 检查主映射是否匹配当前 DataFrame 的列
        matched = sum(1 for v in column_mapping.values() if v in df.columns)
        total = len(column_mapping)

        # 如果主映射匹配率低于 50%，尝试备选映射
        if matched < total * 0.5 and 'column_mapping_alt' in config:
            alt_mapping = config['column_mapping_alt']
            alt_matched = sum(1 for v in alt_mapping.values() if v in df.columns)
            if alt_matched > matched:
                print(f"    🔄 使用备选列映射（匹配 {alt_matched}/{len(alt_mapping)} 列）")
                reverse_mapping = {v: k for k, v in alt_mapping.items()}

        # 重命名列
        df = df.rename(columns=reverse_mapping)

        # 只保留需要的列（如果存在）
        required_columns = ['date', 'description', 'amount', 'category']
        available_columns = [col for col in required_columns if col in df.columns]

        # 添加可选列
        optional_columns = ['counterparty', 'payment_method', 'income_expense']
        for col in optional_columns:
            if col in df.columns:
                available_columns.append(col)

        df = df[available_columns].copy()

        # 添加来源
        df['source'] = config['name']

        return df

    def _filter_expenses(self, df: pd.DataFrame, config: Dict) -> pd.DataFrame:
        """过滤出支出记录"""
        amount_filter = config.get('amount_filter')

        if amount_filter:
            # 优先检查 income_expense 列
            if 'income_expense' in df.columns:
                df = df[df['income_expense'].astype(str).str.contains(amount_filter, na=False)].copy()
            # 其次检查 category 列
            elif 'category' in df.columns:
                df = df[df['category'].astype(str).str.contains(amount_filter, na=False)].copy()
            else:
                # 在所有列中查找
                found = False
                for col in df.columns:
                    if df[col].astype(str).str.contains(amount_filter, na=False).any():
                        df = df[df[col].astype(str).str.contains(amount_filter, na=False)].copy()
                        found = True
                        break

                if not found:
                    print(f"    ⚠️ 未找到包含 '{amount_filter}' 的列，返回所有记录")
        else:
            # 否则通过金额正负判断（负数为支出）
            df = df[df['amount'] < 0].copy()
            df['amount'] = df['amount'].abs()

        return df

        return df

    def process_all(self) -> pd.DataFrame:
        """处理所有账单"""
        all_bills = []
        self.processed_files = []  # 记录处理的文件

        for config in self.configs:
            # 找到匹配的文件
            pattern = config['file_pattern']
            files = list(self.raw_dir.glob(pattern))

            # 如果指定了目标月份，过滤文件
            if self.target_month:
                filtered_files = []
                for f in files:
                    # 从文件名中提取月份（支持 YYYYMM 格式）
                    match = re.search(r'(\d{6})', f.stem)
                    if match and match.group(1) == self.target_month:
                        filtered_files.append(f)
                files = filtered_files

            print(f"\n📊 处理 {config['name']}: 找到 {len(files)} 个文件")

            for file_path in files:
                try:
                    print(f"  📄 {file_path.name}")

                    # 读取文件
                    df = self._read_file(file_path, config)
                    print(f"    ✅ 读取成功: {len(df)} 行")

                    # 映射列名
                    df = self._map_columns(df, config)

                    # 过滤支出
                    df = self._filter_expenses(df, config)
                    print(f"    ✅ 支出记录: {len(df)} 条")

                    all_bills.append(df)

                    self.processed_files.append({
                        'source': config['name'],
                        'file': file_path.name,
                        'total_rows': len(df),
                    })
                except Exception as e:
                    print(f"    ❌ 处理失败: {e}")
                    import traceback
                    traceback.print_exc()

        # 合并所有账单
        if not all_bills:
            raise ValueError("没有找到任何账单数据")

        combined = pd.concat(all_bills, ignore_index=True)

        # 数据清洗
        print(f"\n🧹 数据清洗...")
        combined['date'] = pd.to_datetime(combined['date'], errors='coerce')

        # 清理金额：移除货币符号（¥、$等）、英文逗号和中文逗号
        if combined['amount'].dtype == 'object':
            # 处理括号内的退款信息，如 "30.46(已退款0.06)" → 30.46 - 0.06 = 30.40
            def parse_amount(val: str) -> str:
                val = str(val).replace('¥', '').replace('$', '').replace(',', '').replace('，', '').strip()
                import re as _re
                m = _re.match(r'^([\d.]+)\(.*?([\d.]+)\)$', val)
                if m:
                    try:
                        return str(round(float(m.group(1)) - float(m.group(2)), 2))
                    except ValueError:
                        pass
                return val
            combined['amount'] = combined['amount'].apply(parse_amount)

        combined['amount'] = pd.to_numeric(combined['amount'], errors='coerce')

        # 删除无效数据
        before_count = len(combined)
        combined = combined.dropna(subset=['date', 'amount'])
        after_count = len(combined)

        if before_count > after_count:
            print(f"  ⚠️ 删除了 {before_count - after_count} 条无效数据")

        # 按日期排序
        combined = combined.sort_values('date')

        return combined

    def generate_summary(self, df: pd.DataFrame, output_path: str = None, data_month: str = None):
        """生成汇总报表

        Args:
            df: 账单数据
            output_path: 输出路径（可选）
            data_month: 数据月份 YYYYMM（可选，用于文件命名）
        """
        if output_path is None:
            # 从数据中推断月份
            if data_month is None and not df.empty:
                # 使用数据中最早的日期作为数据月份
                data_month = df['date'].min().strftime('%Y%m')
            elif data_month is None:
                # 兜底：使用当前月份
                data_month = datetime.now().strftime('%Y%m')

            # 生成文件名：summary_数据月份_更新日期_v版本号.xlsx
            # 例如：summary_202602_20260307_v1.xlsx
            update_date = datetime.now().strftime('%Y%m%d')

            # 检查是否已有同数据月份和更新日期的文件，自动递增版本号
            output_dir = Path('bills/output')
            output_dir.mkdir(parents=True, exist_ok=True)

            version = 1
            while True:
                filename = f'summary_{data_month}_{update_date}_v{version}.xlsx'
                output_path = output_dir / filename
                if not output_path.exists():
                    break
                version += 1

        print(f"\n📈 生成汇总报表...")

        # 按类别统计
        if 'category' in df.columns:
            category_summary = df.groupby('category').agg({
                'amount': ['sum', 'count', 'mean']
            }).round(2)
            category_summary.columns = ['总金额', '笔数', '平均金额']
            category_summary = category_summary.sort_values('总金额', ascending=False)
        else:
            category_summary = pd.DataFrame()

        # 按来源统计
        source_summary = df.groupby('source').agg({
            'amount': ['sum', 'count']
        }).round(2)
        source_summary.columns = ['总金额', '笔数']

        # 按日期统计（每日）
        df['date_only'] = df['date'].dt.date
        daily_summary = df.groupby('date_only').agg({
            'amount': 'sum'
        }).round(2)
        daily_summary.columns = ['总金额']

        # 导出到 Excel（带元数据头）
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # 明细 sheet：先写元数据头，再写数据
            meta_rows = [
                [f'个人账单汇总 — {data_month[:4]}年{data_month[4:]}月'],
                [f'生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M")}'],
                [f'总记录：{len(df)} 条 | 总支出：¥{df["amount"].sum():.2f}'],
                [f'数据来源文件：'],
            ]
            for pf in getattr(self, 'processed_files', []):
                meta_rows.append([f'  · {pf["source"]} — {pf["file"]}（{pf["total_rows"]} 条）'])
            meta_rows.append([])  # 空行分隔

            meta_df = pd.DataFrame(meta_rows)
            meta_df.to_excel(writer, sheet_name='明细', index=False, header=False, startrow=0)
            df.to_excel(writer, sheet_name='明细', index=False, startrow=len(meta_rows))

            if not category_summary.empty:
                category_summary.to_excel(writer, sheet_name='按类别统计')

            source_summary.to_excel(writer, sheet_name='按来源统计')
            daily_summary.to_excel(writer, sheet_name='每日统计')

        print(f"\n✅ 汇总完成！")
        print(f"📊 总记录数: {len(df)}")
        print(f"💰 总支出: ¥{df['amount'].sum():.2f}")
        print(f"📅 日期范围: {df['date'].min().date()} 至 {df['date'].max().date()}")
        print(f"📁 输出文件: {output_path.absolute()}")

        # 显示按来源统计
        print(f"\n📊 按来源统计:")
        for source, row in source_summary.iterrows():
            print(f"  {source}: ¥{row['总金额']:.2f} ({int(row['笔数'])}笔)")

        # 显示按类别统计（前 5 名）
        if not category_summary.empty:
            print(f"\n📊 消费类别 TOP 5:")
            for i, (category, row) in enumerate(category_summary.head(5).iterrows(), 1):
                print(f"  {i}. {category}: ¥{row['总金额']:.2f} ({int(row['笔数'])}笔)")

        return output_path

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description='个人账单汇总工具 - 自动汇总不同来源的账单数据',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python bill_processor.py                    # 处理所有月份的数据
  python bill_processor.py -m 202602          # 只处理 2026年2月 的数据
  python bill_processor.py --month 202601     # 只处理 2026年1月 的数据
  python bill_processor.py -m 202602 -o custom.xlsx  # 自定义输出文件名
        """
    )

    parser.add_argument(
        '-m', '--month',
        type=str,
        help='指定要处理的月份，格式为 YYYYMM（如 202602）。不指定则处理所有月份'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        help='自定义输出文件路径（可选）'
    )

    args = parser.parse_args()

    # 验证月份格式
    if args.month:
        if not re.match(r'^\d{6}$', args.month):
            print(f"❌ 错误：月份格式不正确，应为 YYYYMM（如 202602），您输入的是: {args.month}")
            return 1

        # 验证月份的合理性
        try:
            year = int(args.month[:4])
            month = int(args.month[4:6])
            if not (1 <= month <= 12):
                raise ValueError("月份必须在 1-12 之间")
            if not (2000 <= year <= 2100):
                raise ValueError("年份必须在 2000-2100 之间")
        except ValueError as e:
            print(f"❌ 错误：月份值不合理 - {e}")
            return 1

    print("=" * 60)
    print("个人账单汇总工具")
    print("=" * 60)

    try:
        # 创建处理器
        processor = BillProcessor(target_month=args.month)

        # 处理所有账单
        bills = processor.process_all()

        # 生成汇总
        processor.generate_summary(bills, output_path=args.output, data_month=args.month)

        print("\n" + "=" * 60)
        print("✅ 处理完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == '__main__':
    exit(main())
