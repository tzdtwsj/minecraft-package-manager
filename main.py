#!/usr/bin/env python3
import sys
import os
from func import *
import modules
import traceback
import signal
import commands

config = {
    "action": None,
    "data": None,
    "params": {}
}

def parse_param(arg):
    global config
    if len(arg) == 0:
        show_help()
    action = None
    module_name = None
    func_name = None
    data = []
    for i in arg:
        if action == None:
            for j in commands.commands:
                for k in commands.commands[j]:
                    if i == k['cmd'] or i in k['alias']:
                        action = k['cmd']
                        func_name = k['func_name']
                        module_name = j
                        break
                if not action == None:
                    break
            if action == None:
                raise ParamError("无效操作 "+i)
        else:
            data.append(i)
    return action, data, func_name, module_name
        

def main():
    global config
    if sys.platform.startswith("win"):
        windows_open_ansi()
    config['action'], config['data'], func_name, module_name = parse_param(sys.argv[1:])
    get_lock()
    for i in modules.modules:
        if i == module_name:
            try:
                action_func = getattr(modules.modules[i],func_name)
            except AttributeError:
                print("不存在的函数名"+func_name+"，功能尚未实现？")
                return
            break
    action_func(config)

def sigterm(_1,_2):
    release_lock()
    sys.exit(143)

def sigint(_1,_2):
    release_lock()
    sys.exit(130)

def sigquit(_1,_2):
    release_lock()
    sys.exit(131)

signal.signal(signal.SIGINT,sigint)
signal.signal(signal.SIGTERM,sigterm)
signal.signal(signal.SIGQUIT,sigterm)

if __name__ == "__main__":
    try:
        main()
        release_lock()
        sys.exit(0)
    except ParamError as e:
        print("参数错误："+str(e))
    except ShowHelpException:
        pass
    except Exception:
        traceback.print_exc()
    release_lock()
