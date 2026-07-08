import sys
import os
import subprocess

# 确保能向上找到外层的 tools 文件夹
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 1. 先导入底层的物理工具
from tools.finance_tools import get_stock_price, get_fundamental_factors, get_technical_factors
from tools.file_tools import write_flie, read_flie

# 2. 封装需要特殊处理的包装函数 (Wrapper)
def write_flie_wrapper(path: str, content: str) -> str:
    """包装原本没有返回值的写文件操作"""
    write_flie(path, content)
    return f"系统提示：已成功将内容写入文件 {path}"

def run_terminal_command_wrapper(command: str) -> str:
    """包装原生 subprocess 命令执行"""
    print(f"⚠️ 警告：AI 正在物理机执行：{command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        return f"系统提示：命令执行成功！输出结果：\n{result.stdout}"
    else:
        return f"系统提示：命令执行失败！错误信息：\n{result.stderr}"

# 3. 建立动态插件注册中心 (映射大模型传来的名字和本地真实函数)
TOOL_REGISTRY = {
    "get_stock_price": get_stock_price,
    "get_fundamental_factors": get_fundamental_factors,
    "get_technical_factors": get_technical_factors,
    "read_flie": read_flie,
    "write_flie": write_flie_wrapper,
    "run_terminal_command": run_terminal_command_wrapper
}

def dispatch_tool(function_name: str, args: dict) -> str:
    """
    Agent 核心调度中心：接收大模型的调用指令，动态分发给对应的物理兵器
    """
    print(f"\n [调度中心] 收到大脑指令，准备发射武器：{function_name}")
    print(f"传入参数：{args}")

    try:
        # 4. 极致优雅的路由分发（永远告别一长串的 if/elif 面条代码）
        if function_name in TOOL_REGISTRY:
            target_func = TOOL_REGISTRY[function_name]
            # **args 会自动把大模型传过来的字典参数，解包给函数
            return target_func(**args) 
        else:
            return f"系统报错：本地兵器库中不存在该工具 {function_name}"
            
    except Exception as e:
        return f"工具物理执行时发生崩溃报错: {str(e)}"