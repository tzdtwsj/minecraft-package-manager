#!/usr/bin/env python3
import sys
import os
from func import *
import traceback
import signal

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
            elif i == "list" or i == "l":
                config['action'] = "list"
            elif i == "m-install" or i == "m-i":
                config['action'] = "m-install"
            elif i == "m-search" or i == "m-s":
                config['action'] = "m-search"
            elif i == "m-show":
                config['action'] = "m-show"
            elif i == "m-remove" or i == "m-uninstall" or i == "m-r":
                config['action'] = "m-remove"
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
    if sys.platform.startswith("win"):
        windows_open_ansi()
    parse_param(sys.argv[1:])
    get_lock()
    if config.get("action") == "install":
        install_package(config)
    elif config.get("action") == "remove":
        remove_package(config)
    elif config.get("action") == "list":
        list_package(config)
    elif config.get("action") == "m-install":
        modrinth_install_package(config)
    elif config.get("action") == "m-search":
        modrinth_search_package(config)
    elif config.get("action") == "m-show":
        modrinth_show_package(config)
    elif config.get("action") == "m-remove":
        modrinth_remove_package(config)

def sigterm():
    release_lock()

signal.signal(signal.SIGINT,sigterm)
signal.signal(signal.SIGTERM,sigterm)
signal.signal(signal.SIGQUIT,sigterm)

if __name__ == "__main__":
    try:
        main()
        release_lock()
        sys.exit(0)
    except ParamError as e:
        print("参数错误："+str(e))
    except Exception:
        traceback.print_exc()
        release_lock()
