#!/bin/bash
# Author: IBC-AI CO.
# KONE 测试报告自动化系统 - 快速启动脚本

echo "🚀 KONE 测试报告自动化系统启动器"
echo "Author: IBC-AI CO."
echo "========================================="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装Python3"
    exit 1
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
echo "1. 启动FastAPI服务"
echo "2. 运行完整测试（默认模式）"
echo "3. 运行完整测试（详细日志）"
echo "4. 运行测试验证"
echo "5. 模拟运行（不执行实际测试）"
echo "6. 查看帮助"

read -p "请输入选项 (1-6): " choice

case $choice in
    1)
        echo "🌐 启动FastAPI服务..."
        python3 app.py
        ;;
    2)
        echo "🧪 运行完整测试（默认模式）..."
        python3 main.py
        ;;
    3)
        echo "🧪 运行完整测试（详细日志）..."
        python3 main.py --verbose
        ;;
    4)
        echo "🔍 运行测试验证..."
        echo "验证测试协调器..."
        python3 test_coordinator_verify.py
        echo "验证测试映射器..."
        python3 test_mapper_verify.py
        echo "验证建筑数据管理器..."
        python3 building_manager_verify.py
        echo "验证报告生成器..."
        python3 report_generator_verify.py
        echo "验证执行阶段..."
        python3 test_phases_verify.py
        ;;
    5)
        echo "🔍 模拟运行..."
        python3 main.py --dry-run
        ;;
    6)
        echo "📖 查看帮助..."
        python3 main.py --help
        ;;
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac
