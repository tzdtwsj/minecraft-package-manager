#!/usr/bin/env python3
import sys
import os
from func import *

config = {
    "action": None,
    "data": [],
    "params": {}
}

def parse_param(arg):
    global config
    if len(arg) == 0:
        show_help()
    for i in arg:
        if config.get("action") == None:
            if i == "install" or i == "i":
                config['action'] = "install"
            elif i == "remove" or i == "uninstall" or i == "r":
                config['action'] = "remove"
            elif i == "m-install" or i == "m-i":
                config['action'] = "m-install"
            elif i == "m-search" or i == "m-s":
                config['action'] = "m-search"
            elif i == "m-show":
                config['action'] = "m-show"
            elif i == "config":
                config['action'] = "config"
            elif i == "help" or i == "-h" or i == "--help":
                show_help()
            else:
                raise ParamError("无效操作 "+i)
        else:
            if i == "--help" or i == "-h":
                show_help()
            config["data"].append(i)

def config_minecraft(config):
    global_config = GolbalConfig()
    if len(config['data']) < 5:
        print("错误：缺少参数")
        print(f"用法：{os.path.basename(sys.argv[0])} config minecraft <id> <type> <name> <version> <path> [modPath] [installedMods]")
        return
    minecraft_id = config['data'][0]
    minecraft_type = config['data'][1]
    minecraft_name = config['data'][2]
    minecraft_version = config['data'][3]
    minecraft_path = config['data'][4]

    if minecraft_type not in ["forge", "fabric", "vanilla"]:
        print("错误：无效的Minecraft类型。类型只能是'forge'、'fabric'或'vanilla'")
        return

    if minecraft_type == "vanilla":
        mod_path = "null"
        installed_mods = ["null"]
    else:
        mod_path = config['data'][5] if len(config['data']) > 5 else "null"
        installed_mods = config['data'][6:] if len(config['data']) > 6 else ["null"]

    minecraft_config = {
        "type": minecraft_type,
        "name": minecraft_name,
        "version": minecraft_version,
        "path": minecraft_path,
        "modPath": mod_path,
        "installedMods": installed_mods
    }

    global_config.configs["minecrafts"][minecraft_id] = minecraft_config
    global_config.destory()
    print(f"Minecraft配置已更新：{minecraft_id}")

def main():
    global config
    parse_param(sys.argv[1:])
    if config.get("action") == "install":
        undefinedFunc()
    elif config.get("action") == "remove":
        undefinedFunc()
    elif config.get("action") == "m-install":
        modrinth_install_package(config)
    elif config.get("action") == "m-search":
        modrinth_search_package(config)
    elif config.get("action") == "m-show":
        modrinth_show_package(config)
    elif config.get("action") == "config":
        if config['data'][0] == "minecraft":
            config_minecraft(config)
        else:
            print("无效配置类型")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except ParamError as e:
        print("参数错误："+str(e))
