#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
个人账单汇总工具 - 简化版本
纯 ASCII 字符，避免乱码问题
"""

import sys
import os
from pathlib import Path

# Windows 编码设置
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# 导入原有的处理器
from bill_processor import BillProcessor


class SimpleBillProcessor:
    """简化版账单处理器（纯 ASCII）"""

    def show_banner(self):
        """显示欢迎横幅"""
        print("=" * 60)
        print("个人账单汇总工具")
        print("自动汇总多来源账单，生成月度消费统计")
        print("=" * 60)
        print()

    def show_menu(self):
        """显示主菜单"""
        print("请选择功能：")
        print("  1. 处理本月账单")
        print("  2. 处理指定月份账单")
        print("  3. 处理所有账单")
        print("  4. 查看可用账单文件")
        print("  0. 退出")
        print()

    def get_choice(self) -> str:
        """获取用户选择"""
        while True:
            choice = input("请选择 (0-4): ").strip()
            if choice in ["0", "1", "2", "3", "4"]:
                return choice
            print("[错误] 无效选择，请重新输入")

    def get_month(self) -> str:
        """获取月份输入"""
        month = input("请输入月份 (格式: YYYYMM，如 202602): ").strip()
        if not month:
            month = "202602"

        # 验证格式
        import re
        if not re.match(r'^\d{6}$', month):
            print("[错误] 格式错误！应为 YYYYMM（如 202602）")
            return None

        # 验证合理性
        try:
            year = int(month[:4])
            month_num = int(month[4:6])
            if not (1 <= month_num <= 12):
                raise ValueError("月份必须在 1-12 之间")
            if not (2000 <= year <= 2100):
                raise ValueError("年份必须在 2000-2100 之间")
        except ValueError as e:
            print(f"[错误] 月份值不合理：{e}")
            return None

        return month

    def list_available_files(self):
        """列出可用的账单文件"""
        raw_dir = Path('bills/raw')

        if not raw_dir.exists():
            print("[警告] 账单目录不存在")
            return

        files = list(raw_dir.glob('*'))
        files = [f for f in files if f.suffix in ['.csv', '.xlsx', '.xls'] and not f.name.startswith('.')]

        if not files:
            print("[警告] 未找到任何账单文件")
            return

        print("\n可用账单文件：")
        print("-" * 60)
        for f in sorted(files):
            size = f.stat().st_size
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size / (1024 * 1024):.1f} MB"

            print(f"  {f.name:<40} {size_str:>10}")
        print("-" * 60)

    def process_bills(self, month: str = None):
        """处理账单"""
        print()
        print("开始处理账单...")
        print()

        try:
            # 创建处理器
            processor = BillProcessor(target_month=month)

            # 处理所有账单
            bills = processor.process_all()

            # 生成汇总
            output_path = processor.generate_summary(bills, data_month=month)

            print()
            print("=" * 60)
            print("[成功] 处理完成！")
            print(f"输出文件：{output_path}")
            print("=" * 60)

            return True

        except Exception as e:
            print()
            print(f"[错误] 处理失败：{e}")
            import traceback
            traceback.print_exc()
            return False

    def run(self):
        """运行交互式界面"""
        self.show_banner()

        while True:
            self.show_menu()
            choice = self.get_choice()

            if choice == "0":
                print("\n再见！")
                break

            elif choice == "1":
                # 处理本月账单
                from datetime import datetime
                current_month = datetime.now().strftime("%Y%m")
                print(f"\n[信息] 处理本月账单（{current_month}）")
                self.process_bills(current_month)

            elif choice == "2":
                # 处理指定月份
                month = self.get_month()
                if month:
                    print(f"\n[信息] 处理 {month} 的账单")
                    self.process_bills(month)

            elif choice == "3":
                # 处理所有账单
                confirm = input("\n[警告] 确定要处理所有月份的账单吗？(y/n): ").strip().lower()
                if confirm in ['y', 'yes']:
                    print("\n[信息] 处理所有账单")
                    self.process_bills(None)

            elif choice == "4":
                # 查看可用文件
                print()
                self.list_available_files()

            # 等待用户按键继续
            print()
            input("按 Enter 继续...")
            print()


def main():
    """主函数"""
    app = SimpleBillProcessor()
    app.run()


if __name__ == '__main__':
    main()
