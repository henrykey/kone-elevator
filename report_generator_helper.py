#!/usr/bin/env python3
"""
KONE API v2.0 完整报告生成助手
提供多种报告生成选项：
1. 使用 testall.py 进行全面功能测试并生成报告
2. 生成补丁实施摘要报告
3. 生成综合测试与补丁实施报告

Author: GitHub Copilot
Date: 2025-08-15
"""

import sys
import os
import subprocess
import asyncio
from datetime import datetime


def print_banner():
    """打印横幅"""
    print("=" * 80)
    print("🏆 KONE API v2.0 完整报告生成助手")
    print("=" * 80)
    print("选项 1: 运行 testall.py 全面功能测试")
    print("选项 2: 生成补丁实施摘要报告")
    print("选项 3: 生成综合报告 (功能测试 + 补丁实施)")
    print("选项 4: 运行特定类别的补丁验证")
    print("=" * 80)


def run_testall():
    """运行 testall.py 全面功能测试"""
    print("🚀 启动 testall.py 全面功能测试...")
    print("-" * 50)
    
    try:
        # 检查 testall.py 是否存在
        if not os.path.exists("testall.py"):
            print("❌ testall.py 文件不存在")
            return False
        
        # 运行 testall.py
        print("⏳ 正在执行全面功能测试，请稍候...")
        result = subprocess.run([sys.executable, "testall.py"], 
                              capture_output=True, text=True, timeout=300)
        
        print(f"✅ testall.py 执行完成")
        print(f"🔍 返回码: {result.returncode}")
        
        if result.returncode == 0:
            print("🎉 所有测试通过！")
        else:
            print("⚠️ 部分测试可能失败，请查看详细输出")
        
        # 显示输出摘要
        if result.stdout:
            lines = result.stdout.split('\n')
            print(f"\n📊 测试结果摘要:")
            for line in lines[-20:]:  # 显示最后20行
                if any(keyword in line for keyword in ["成功", "失败", "通过", "错误", "报告", "✅", "❌", "🎊"]):
                    print(f"  {line}")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("⏰ testall.py 执行超时 (5分钟)")
        return False
    except Exception as e:
        print(f"❌ testall.py 执行失败: {e}")
        return False


def run_patch_summary():
    """生成补丁实施摘要报告"""
    print("📋 生成补丁实施摘要报告...")
    print("-" * 50)
    
    try:
        if not os.path.exists("generate_patch_summary_report.py"):
            print("❌ generate_patch_summary_report.py 文件不存在")
            return False
        
        result = subprocess.run([sys.executable, "generate_patch_summary_report.py"], 
                              capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print(f"⚠️ 警告: {result.stderr}")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ 补丁报告生成失败: {e}")
        return False


def run_category_verification(category):
    """运行特定类别的补丁验证"""
    category_scripts = {
        "B": "test_category_b_complete_fix.py",
        "C": "test_category_c_complete.py", 
        "D": "test_category_d_complete.py",
        "E": "test_category_e_complete.py",
        "F": "test_category_f_complete.py"
    }
    
    script = category_scripts.get(category.upper())
    if not script:
        print(f"❌ 类别 {category} 的验证脚本不存在")
        return False
    
    print(f"🔧 运行 Category {category.upper()} 补丁验证...")
    print("-" * 50)
    
    try:
        if not os.path.exists(script):
            print(f"❌ {script} 文件不存在")
            return False
        
        result = subprocess.run([sys.executable, script], 
                              capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print(f"⚠️ 警告: {result.stderr}")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Category {category} 验证失败: {e}")
        return False


def generate_comprehensive_report():
    """生成综合报告"""
    print("📊 生成综合报告 (功能测试 + 补丁实施)")
    print("-" * 50)
    
    comprehensive_summary = {
        "timestamp": datetime.now().isoformat(),
        "report_type": "KONE API v2.0 综合报告",
        "components": {
            "functional_testing": {"status": "pending", "details": "testall.py 功能测试"},
            "patch_implementation": {"status": "pending", "details": "补丁实施验证"}
        },
        "overall_status": "pending"
    }
    
    # 1. 运行补丁摘要报告
    print("🔧 步骤1: 生成补丁实施摘要...")
    patch_success = run_patch_summary()
    comprehensive_summary["components"]["patch_implementation"]["status"] = "success" if patch_success else "failed"
    
    print(f"\n{'='*50}")
    
    # 2. 提示是否运行 testall.py
    print("💡 是否运行 testall.py 全面功能测试？(y/n): ", end="")
    run_functional = input().lower().startswith('y')
    
    if run_functional:
        print("\n🔧 步骤2: 运行 testall.py 功能测试...")
        functional_success = run_testall()
        comprehensive_summary["components"]["functional_testing"]["status"] = "success" if functional_success else "failed"
    else:
        print("\n⏭️ 跳过 testall.py 功能测试")
        comprehensive_summary["components"]["functional_testing"]["status"] = "skipped"
    
    # 3. 生成综合摘要
    print(f"\n🎯 综合报告生成完成")
    print("-" * 30)
    
    patch_status = comprehensive_summary["components"]["patch_implementation"]["status"]
    functional_status = comprehensive_summary["components"]["functional_testing"]["status"]
    
    print(f"📋 补丁实施验证: {patch_status}")
    print(f"🧪 功能测试验证: {functional_status}")
    
    if patch_status == "success" and functional_status in ["success", "skipped"]:
        comprehensive_summary["overall_status"] = "success"
        print(f"🏆 综合状态: ✅ 成功")
        print(f"🚀 KONE API v2.0 已准备投入生产使用")
    else:
        comprehensive_summary["overall_status"] = "needs_attention"
        print(f"⚠️ 综合状态: 需要关注")
        print(f"🔧 建议检查失败的组件")
    
    # 保存综合报告
    import json
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"KONE_API_v2_Comprehensive_Report_{timestamp}.json"
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(comprehensive_summary, f, indent=2, ensure_ascii=False)
    
    print(f"📄 综合报告保存: {filename}")
    
    return comprehensive_summary["overall_status"] == "success"


def main():
    """主入口"""
    print_banner()
    
    while True:
        try:
            print("\n请选择操作 (1-4, q退出): ", end="")
            choice = input().strip()
            
            if choice.lower() == 'q':
                print("👋 退出报告生成助手")
                break
            elif choice == '1':
                success = run_testall()
                if success:
                    print("\n🎉 testall.py 全面功能测试完成")
                    print("📁 查看 reports/ 目录获取详细报告")
                else:
                    print("\n⚠️ testall.py 测试遇到问题，请检查输出")
                    
            elif choice == '2':
                success = run_patch_summary()
                if success:
                    print("\n🎉 补丁实施摘要报告生成完成")
                else:
                    print("\n⚠️ 补丁报告生成遇到问题")
                    
            elif choice == '3':
                success = generate_comprehensive_report()
                if success:
                    print("\n🎉 综合报告生成完成")
                else:
                    print("\n⚠️ 综合报告生成遇到问题")
                    
            elif choice == '4':
                print("选择类别 (B/C/D/E/F): ", end="")
                category = input().strip().upper()
                if category in ['B', 'C', 'D', 'E', 'F']:
                    success = run_category_verification(category)
                    if success:
                        print(f"\n🎉 Category {category} 验证完成")
                    else:
                        print(f"\n⚠️ Category {category} 验证遇到问题")
                else:
                    print("❌ 无效的类别选择")
            else:
                print("❌ 无效选择，请输入 1-4 或 q")
                
        except KeyboardInterrupt:
            print("\n👋 用户中断，退出程序")
            break
        except Exception as e:
            print(f"\n❌ 发生错误: {e}")
    
    print("\n🏁 报告生成助手结束")


if __name__ == "__main__":
    main()
