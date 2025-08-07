#!/bin/bash
# Author: IBC-AI CO.
# KONE 测试报告自动化系统 - 快速启动脚本

echo "🚀 KONE 测试报告自动化系统启动器"
echo "Author: IBC-AI CO."
echo "========================================="

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo "❌ Python 未安装，请先安装Python"
    exit 1
fi

# 检查FastAPI服务状态
check_api_status() {
    if curl -s http://localhost:8000/ > /dev/null 2>&1; then
        return 0  # 服务正在运行
    else
        return 1  # 服务未运行
    fi
}

echo "🔍 检查FastAPI服务状态..."
if check_api_status; then
    echo "✅ FastAPI服务已启动 (http://localhost:8000)"
else
    echo "⚠️ FastAPI服务未启动"
    echo "请先启动FastAPI服务："
    echo "   python acesslifts.py"
    echo ""
    read -p "是否继续？(y/N): " continue_choice
    if [[ ! "$continue_choice" =~ ^[Yy]$ ]]; then
        echo "退出程序"
        exit 1
    fi
fi

# 检查必要文件
if [ ! -f "main.py" ]; then
    echo "❌ main.py 文件不存在"
    exit 1
fi

if [ ! -f "virtual_building_config.yml" ]; then
    echo "❌ virtual_building_config.yml 配置文件不存在"
    exit 1
fi

echo "✅ 环境检查通过"

# 提供操作选项
echo ""
echo "请选择操作："
echo "1. 运行完整测试（默认模式）"
echo "2. 运行完整测试（详细日志）"
echo "3. 运行指定测试用例"
echo "4. 模拟运行（不执行实际测试）"
echo "5. 测试验证组件"
echo "6. 测试报告生成功能"
echo "7. 查看帮助"

read -p "请输入选项 (1-7): " choice

case $choice in
    1)
        echo "🧪 运行完整测试（默认模式）..."
        python main.py
        ;;
    2)
        echo "🧪 运行完整测试（详细日志）..."
        python main.py --verbose
        ;;
    3)
        echo "🎯 运行指定测试用例..."
        echo ""
        echo "测试用例格式说明："
        echo "  单个测试: 1"
        echo "  多个测试: 1,2,5"
        echo "  范围测试: 1-10"
        echo "  混合格式: 1,3-5,8,10-12"
        echo ""
        read -p "请输入要执行的测试用例: " test_cases
        
        if [[ -n "$test_cases" ]]; then
            echo "📋 执行测试用例: $test_cases"
            read -p "是否启用详细日志？(y/N): " verbose_choice
            
            if [[ "$verbose_choice" =~ ^[Yy]$ ]]; then
                python main.py --tests "$test_cases" --verbose
            else
                python main.py --tests "$test_cases"
            fi
        else
            echo "❌ 未指定测试用例"
            exit 1
        fi
        ;;
    4)
        echo "🔍 模拟运行..."
        echo ""
        read -p "指定测试用例（留空执行全部）: " test_cases
        
        if [[ -n "$test_cases" ]]; then
            echo "📋 模拟执行测试用例: $test_cases"
            python main.py --dry-run --tests "$test_cases"
        else
            echo "📋 模拟执行全部测试"
            python main.py --dry-run
        fi
        ;;
    5)
        echo "🔍 运行测试验证..."
        echo "验证测试协调器..."
        python test_coordinator_verify.py
        echo "验证测试映射器..."
        python test_mapper_verify.py
        echo "验证建筑数据管理器..."
        python building_manager_verify.py
        echo "验证报告生成器..."
        python report_generator_verify.py
        echo "验证执行阶段..."
        python test_phases_verify.py
        ;;
    6)
        echo "📊 测试报告生成功能..."
        python test_report_generation.py
        ;;
    7)
        echo "📖 查看帮助..."
        python main.py --help
        ;;
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac
