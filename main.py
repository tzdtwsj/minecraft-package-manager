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
        modrinth_show_package(config)
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except ParamError as e:
        print("参数错误："+str(e))
