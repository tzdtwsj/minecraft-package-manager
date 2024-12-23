# 注册命令

commands = {
    "builtin": [
        {
            "cmd": "help",
            "alias": ["-h","--help"],
            "func_name": "show_help",
            "help": "显示该帮助"
        },
        {
            "cmd": "version",
            "alias": ["-v","--version"],
            "func_name": "show_version",
            "help": "显示版本"
        },
        {
            "cmd": "install",
            "alias": ["i"],
            "func_name": "install_package",
            "help": "安装软件包"
        },
        {
            "cmd": "remove",
            "alias": ["uninstall","r"],
            "func_name": "remove_package",
            "help": "删除软件包"
        },
        {
            "cmd": "list",
            "alias": ["l"],
            "func_name": "list_package",
            "help": "列出已安装的软件包"
        }
    ]
}

def register(name:str,cmd:str,func_name:str,alias:list=[],help_text:str="无帮助"):
    global commands
    if commands.get(name) == None:
        commands[name] = []
    commands[name].append({"cmd":cmd,"alias":alias,"func_name":func_name,"help":help_text})

def registers(name:str,cmds:list):
    for i in cmds:
        register(name,i['cmd'],i['func_name'],i.get("alias",[]),i.get("help","无帮助"))
