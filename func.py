import urllib.request
import urllib.parse
import urllib.error
import json
import sys
import os
import version
import hashlib
from time import sleep
import zipfile
import tarfile

class ParamError(Exception):
    pass

class ShowHelpException(Exception):
    pass

def print_progress(downloaded_size,size=None):
    if not size == None:
        print("进度："+parse_size(downloaded_size)+" "+str(round(downloaded_size/size*100,2))+"%      ",end="\r")
    else:
        print("进度："+parse_size(downloaded_size)+"      ",end="\r")

def get_module_name(name):
    return name.split(".")[-1]

def windows_open_ansi(): # 使Windows的终端支持ANSI转义序列
    from ctypes import windll, byref, wintypes
    kernel32 = windll.kernel32
    hStdout = kernel32.GetStdHandle(wintypes.DWORD(-11))
    mode = wintypes.DWORD()
    kernel32.GetConsoleMode(hStdout, byref(mode))
    mode.value |= 0x0004  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
    kernel32.SetConsoleMode(hStdout, mode)

def get_lock():
    if not os.path.exists(".mpm"):
        os.mkdir(".mpm")
    if not os.path.exists(".mpm/lock"):
        with open(".mpm/lock","w") as f:
            f.write(str(os.getpid()))
    else:
        with open(".mpm/lock","r") as f:
            pid = f.read(1024)
        if pid.isnumeric():
            pid = int(pid)
        else:
            with open(".mpm/lock","w") as f:
                f.write(str(os.getpid()))
            return
        time = 0
        while os.path.exists(".mpm/lock") and pid_exists(pid):
            print("发现锁文件，似乎有另一个mpm程序正在运行("+str(pid)+")，请等待锁文件释放，已等待"+str(time)+"秒")
            sleep(1)
            time += 1
        with open(".mpm/lock","w") as f:
            f.write(str(os.getpid()))

def release_lock():
    if os.path.exists(".mpm/lock"):
        with open(".mpm/lock","r") as f:
            pid = int(f.read(1024))
        if pid == os.getpid():
            os.remove(".mpm/lock")

def pid_exists(pid:int):
    try:
        os.kill(pid,0)
        return True
    except OSError:
        return False

def parse_size(size,isbin=True):
    i = 0
    dw = "BKMGT"
    bj = 1024
    if not isbin:
        bj = 1000
    while size >= bj and not i >= 4:
        size /= bj
        i += 1
    if i == 0:
        return str(size)+dw[i]
    if not isbin:
        return str(size)+dw[i]+"i"+"B"
    else:
        return str(size)+dw[i]+"B"

def sha1_file(path):
    h = hashlib.sha1()
    with open(path,"rb") as f:
        while True:
            data = f.read(1048576)
            if not data:
                break
            h.update(data)
    return h.hexdigest()

def request(url, method='GET', data=None, headers=None, save_name=None, timeout=15):
    # 如果没有提供headers，则初始化为空字典
    if headers is None:
        headers = {}

    # 创建一个Request对象
    req = urllib.request.Request(url, headers=headers, method=method)

    # 如果data不是None，并且是GET请求，则将data作为查询参数附加到URL上
    if data is not None and method.upper() == 'GET':
        query_string = urllib.parse.urlencode(data)
        url = f"{url}?{query_string}"
        req = urllib.request.Request(url, headers=headers, method=method)

    # 如果data不是None，并且是POST请求，则将data编码为字节
    elif data is not None and method.upper() == 'POST':
        if isinstance(data, dict):
            data = urllib.parse.urlencode(data).encode('utf-8')
        req.data = data

    try:
        # 发送请求并获取响应，设置超时
        with urllib.request.urlopen(req, timeout=timeout) as response:
            # 获取HTTP状态码
            status_code = response.status
            # 获取HTTP Header
            headers = response.info()
            size = headers.get("Content-Length",None)
            if size != None:
                size = int(size)
            # 如果提供了save_name，则分块保存响应体到文件
            if save_name:
                with open(save_name, 'wb') as file:
                    downloaded_size = 0
                    while True:
                        chunk = response.read(1024 * 1024)  # 读取1MB大小的块
                        if not chunk:
                            break
                        file.write(chunk)
                        downloaded_size += 1024*1024
                        print_progress(downloaded_size,size)
                print("                        ",end="\r")
                return status_code
            # 否则返回状态码和响应内容
            else:
                response_data = response.read()
                return status_code, response_data
    except urllib.error.HTTPError as e:
        # 如果发生HTTP错误，返回状态码和错误页面内容
        return e.code, e.read()
    except TimeoutError:
        return True
    except urllib.error.URLError as e:
        return False

def list_package(params):
    if not os.path.exists(".mpm/package.json"):
        print("\033[93m没有软件包被安装\033[0m")
        return
    with open(".mpm/package.json","r") as f:
        pkgcfg = json.loads(f.read(os.path.getsize(".mpm/package.json")))
    print("已安装的软件包")
    print("\033[92m软件包名\033[0m|版本|类型 加载器")
    for i in pkgcfg['installed']:
        print(f"\033[92m{i.get('package')}\033[0m|{i.get('version')}|{i.get('type')} {i.get('loader')}")

def add_package_to_list(package_name:str,package_type:str,data:dict):
    if not os.path.exists(".mpm/package.json"):
        if not os.path.exists(".mpm"):
            os.mkdir(".mpm")
        with open(".mpm/package.json","w") as f:
            f.write(json.dumps({"installed":[]},indent=4)+"\n")
    with open(".mpm/package.json","r") as f:
        pkgcfg = json.loads(f.read(os.path.getsize(".mpm/package.json")))
    if pkgcfg.get('installed') == None:
        pkgcfg['installed'] = []
    for i in pkgcfg['installed']:
        if i['package'] == package_name:
            return False
    pkgcfg['installed'].append({"package":package_name,"type":package_type})
    for i in data:
        pkgcfg['installed'][len(pkgcfg['installed'])-1][i] = data[i]
    with open(".mpm/package.json","w") as f:
        f.write(json.dumps(pkgcfg,indent=4)+"\n")
    return True

def remove_package_from_list(package_name:str,package_type:str):
    if not os.path.exists(".mpm/package.json"):
        return False
    with open(".mpm/package.json","r") as f:
        pkgcfg = json.loads(f.read(os.path.getsize(".mpm/package.json")))
    if pkgcfg.get('installed') == None:
        return False
    new_pkgcfg_installed = []
    for i in pkgcfg['installed']:
        if not (package_name == i['package'] and package_type == i['type']):
            new_pkgcfg_installed.append(i)
    pkgcfg['installed'] = new_pkgcfg_installed
    with open(".mpm/package.json","w") as f:
        f.write(json.dumps(pkgcfg,indent=4)+"\n")
    return True

def get_package_from_list(package_name:str,package_type:str):
    if not os.path.exists(".mpm/package.json"):
        return False
    with open(".mpm/package.json","r") as f:
        pkgcfg = json.loads(f.read(os.path.getsize(".mpm/package.json")))
    if pkgcfg.get('installed') == None:
        return False
    for i in pkgcfg['installed']:
        if i['package'] == package_name and i['type'] == package_type:
            return i
    return False

def unzip(zip_file,save_dir):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    with zipfile.ZipFile(zip_file,"r") as zip_ref:
        zip_ref.extractall(save_dir)

def untgz(tgz_file,save_dir):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    with tarfile.open(tgz_file, "r:gz") as tar:
        tar.extractall(save_dir)

def show_help(_=None):
    from commands import commands
    print(f"""mpm v{version.VERSION} By tzdtwsj
用法：{os.path.basename(sys.argv[0])} [参数] 命令

mpm是一个在命令行使用的《Minecraft》服务端软件包管理工具""")
    for i in commands:
        print()
        print((i if not i == "builtin" else "内置")+"命令：")
        for j in commands[i]:
            print("  "+j['cmd'],end="")
            if len(j['alias']) > 0:
                print(" ",end="")
                for k in j['alias']:
                    print(k+" ",end="")
            print("\n    "+j['help'])
    print("""
项目地址：https://github.com/tzdtwsj/minecraft-package-manager
                                        这个MPM没有超级牛力.""")
    raise ShowHelpException()

def show_version(_=None):
    print(f"""mpm v{version.VERSION} By tzdtwsj
project link: https://github.com/tzdtwsj/minecraft-package-manager""")
