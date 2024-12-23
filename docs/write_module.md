# 编写模块 

---
## 编写示例
```python
from func import * # 导入内置函数
import commands

_cmds = [
    {
        "cmd": "example-cmd",
        "alias": ["e-c"],
        "func_name": "example_func",
        "help": "示例"
    }
]

commands.registers(get_module_name(__name__),_cmds) # 注意registers和register有区别

def example_func(params): # 调用时程序会往函数传一个命令行数组参数
    if len(params) == 0:
        print("没传参")
        return
    print("你传了以下参：")
    for i in params:
        print(i+" ",end="")
    print()
```
---
## API
### commands模块
#### def register(name:str, cmd:str, func\_name:str, alias:list=[], help\_text:str="无帮助"): 注册一条命令  
name: 模块名，需要和文件名xxx.py中的xxx相同，如果闲麻烦，可以传`get_module_name(__name__)`，不正确的模块名会导致命令回调函数无法调用  
cmd: 命令名  
func\_name: 需要被调用函数的函数名  
alias: 别名  
help\_text: 帮助信息（使用npm help时输出的内容）  

#### def registers(name:str, cmds:list): 注册多条命令
name: 模块名，需要和文件名xxx.py中的xxx相同，如果闲麻烦，可以传`get_module_name(__name__)`，不正确的模块名会导致命令回调函数无法调用  
cmds: 多条命令的列表  
该函数的使用示例已在上面的编写示例提到  

### func模块
#### def add\_package\_list(package\_name:str,data:dict): 往配置文件添加一个软件包
package\_name: 软件包名  
data: 软件包数据，是一个字典，可以写一些信息进去（例如软件包版本，软件包依赖等）  
返回值: bool（添加成功为True，软件包名重复为False）  

#### def remove\_package(package\_name:str): 删除配置文件里的软件包
package\_name: 软件包名  
返回值: bool（软件包不存在为False，删除成功为True）  

#### def get\_package(package\_name:str): 获取软件包数据
package\_name: 软件包名  
返回值: bool|dict（软件包不存在为False，否则为dict）
