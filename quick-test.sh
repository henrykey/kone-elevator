#!/bin/bash

# KONE测试系统快速运行脚本 - 支持命令行参数
# Author: IBC-AI CO.

# 快速运行，支持直接传递测试用例参数
# 使用方法:
#   ./quick-test.sh 1          # 执行测试1
#   ./quick-test.sh 1,2,5      # 执行测试1、2、5
#   ./quick-test.sh 1-10       # 执行测试1到10
#   ./quick-test.sh 1-5 -v     # 执行测试1-5，详细日志

TESTS="$1"
VERBOSE=""

# 检查第二个参数是否为verbose标志
if [[ "$2" == "-v" || "$2" == "--verbose" ]]; then
    VERBOSE="--verbose"
fi

# 显示执行信息
if [[ -n "$TESTS" ]]; then
    echo "🎯 执行指定测试用例: $TESTS"
else
    echo "🧪 执行全部测试"
fi

# 构建命令
CMD="python main.py"

if [[ -n "$TESTS" ]]; then
    CMD="$CMD --tests $TESTS"
fi

if [[ -n "$VERBOSE" ]]; then
    CMD="$CMD $VERBOSE"
fi

# 执行命令
echo "执行命令: $CMD"
echo ""
eval $CMD
