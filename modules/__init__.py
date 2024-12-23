import os
import importlib
from func import *
import func as builtin

modules = {
    "builtin": builtin
}

# 获取当前文件夹中所有的.py文件（排除__init__.py）
module_files = [f[:-3] for f in os.listdir(os.path.dirname(__file__))
                if f.endswith('.py') and not f.startswith('__')]

# 导入所有.py文件作为模块
for module_file in module_files:
    module = importlib.import_module(f"{__name__}.{module_file}")
    modules[module_file] = module
