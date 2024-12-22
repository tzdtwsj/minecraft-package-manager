import urllib.request
import urllib.parse
import urllib.error
import json
import sys
import os
from version import VERSION
import hashlib
from time import sleep

class ParamError(Exception):
    pass

def print_progress(downloaded_size,size=None):
    if not size == None:
        print("进度："+parse_size(downloaded_size)+" "+str(round(downloaded_size/size*100,2))+"%      ",end="\r")
    else:
        print("进度："+parse_size(downloaded_size)+"      ",end="\r")

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
        while os.path.exists(".mpm/lock") or pid_exists(pid):
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

def request(url, method='GET', data=None, headers=None, save_name=None, timeout=5):
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
                        print_progress(downloaded_size,int(size))
                print("                        ",end="\r")
                return status_code
            # 否则返回状态码和响应内容
            else:
                response_data = response.read()
                return status_code, response_data
    except urllib.error.HTTPError as e:
        # 如果发生HTTP错误，返回状态码和错误页面内容
        return e.code, e.read()
    except urllib.error.URLError as e:
        # 如果发生URL错误（例如连接失败或超时），返回True
        if isinstance(e.reason, TimeoutError):
            return True
        else:
            return False

def modrinth_search(name):
    data = request("https://api.modrinth.com/v2/search",data={"query":name})
    if data is False or data is True:
        return 0,""
    try:
        return data[0], json.loads(data[1])
    except json.decoder.JSONDecodeError:
        return 1, data[1]

def modrinth_search_package(config):
    if len(config.get("data")) == 0:
        print("错误：缺少参数")
        print("用法："+os.path.basename(sys.argv[0])+" m-search 内容 [内容 内容 ...]")
        return
    for i in config.get("data"):
        data = modrinth_search(i)
        if data[0] == 0:
            print("无法连接到modrinth")
        elif data[0] >= 300 or data[0] < 200:
            print("服务器返回了非200状态码："+data[1])
        elif data[0] < 300 and data[0] >= 200:
            if data[1].get("total_hits") == 0:
                print("\033[91m内容"+i+"无结果\033[0m")
                continue
            if os.path.exists(".mpm/package.json"):
                with open(".mpm/package.json","r") as f:
                    pkgcfg = json.loads(f.read(os.path.getsize(".mpm/package.json")))
            else:
                pkgcfg = {'installed':[]}
            print("\033[93m对于"+i+"，在modrinth搜索到"+str(data[1].get("total_hits"))+"个条目，这里只列出10条\033[0m")
            j=0
            while j < data[1].get("limit"):
                print("\033[92m"+data[1].get("hits")[j]['slug']+"\033[0m/"+data[1].get("hits")[j]['title'],end="")
                for k in pkgcfg['installed']:
                    if k['id'] == data[1].get("hits")[j]['project_id']:
                        print(" [已安装]",end="")
                        break
                print()
                print("  "+data[1].get("hits")[j]['description'])
                print()
                j += 1

def modrinth_show(name):
    data = request("https://api.modrinth.com/v2/project/"+urllib.parse.urlencode({'a':name})[2:])
    if data is False or data is True:
        return 0,""
    try:
        return data[0], json.loads(data[1])
    except json.decoder.JSONDecodeError:
        return data[0], data[1]

def modrinth_show_package(config):
    if len(config.get("data")) == 0:
        print("错误：缺少参数")
        print("用法："+os.path.basename(sys.argv[0])+" m-show 软件包 [软件包 软件包 ...]")
        return
    for i in config.get("data"):
        data = modrinth_show(i)
        if data[0] == 0:
            print("无法连接到modrinth")
        elif data[0] == 404:
            print("找不到软件包 "+i)
        elif data[0] >= 300 or data[0] < 200:
            print("服务器返回了非200状态码："+data[1])
        elif data[0] < 300 and data[0] >= 200:
            print("包名："+data[1]['slug'])
            print("标题："+data[1]['title'])
            print("介绍："+data[1]['description'])
            print("类型："+data[1]['project_type'])
            print("支持的MC版本：",end="")
            for j in data[1]['game_versions']:
                print(j+" ",end="")
            print()
            print("支持的加载器：",end="")
            for j in data[1]['loaders']:
                print(j+" ",end="")
            print()
            print("更新日期："+data[1]['updated'])
            print("源码链接："+data[1]['source_url'])
            print("下载量："+str(data[1]['downloads']))
            print()

def modrinth_show_version(project,loaders,versions):
    data = request("https://api.modrinth.com/v2/project/"+urllib.parse.urlencode({'a':project})[2:]+"/version",data={"game_versions":json.dumps(versions),"loaders":json.dumps(loaders)})
    if data is False or data is True:
        return 0,""
    try:
        return data[0], json.loads(data[1])
    except json.decoder.JSONDecodeError:
        return data[0], data[1]

def modrinth_install_package(config):
    if len(config['data']) < 2:
        print("错误：缺少参数")
        print(f"用法：{os.path.basename(sys.argv[0])} m-install 加载器 软件包[,软件包] [游戏版本]")
        return
    pkgs = config['data'][1].split(",")
    for pkg in pkgs:
        pkgdata = modrinth_show(pkg)
        if pkgdata[0] == 0:
            print("无法连接到modrinth")
            return
        elif pkgdata[0] == 404:
            print("\033[91m找不到软件包 "+pkg+"\033[0m")
            continue
        pkgcfg = None
        if os.path.exists(".mpm/package.json"):
            with open(".mpm/package.json","r") as f:
                pkgcfg = json.loads(f.read(os.path.getsize(".mpm/package.json")))
            status = True
            for i in pkgcfg['installed']:
                if i['id'] == pkgdata[1]['id'] or i['package'] == pkgdata[1]['slug']:
                    print("软件包"+pkg+"已被安装")
                    status = False
                    break
            if not status:
                continue
        if not config['data'][0] in pkgdata[1]['loaders']:
            print("\033[91m错误：不支持的加载器"+config['data'][0]+"\033[0m\n该软件包仅支持以下加载器：",end="")
            for i in pkgdata[1]['loaders']:
                print(i+" ",end="")
            print()
            continue
        if len(config['data']) >= 3:
            version = config['data'][2]
            if not version in pkgdata[1]['game_versions']:
                print("\033[91m错误：不支持的MC版本"+version+"\033[0m\n该软件包仅支持以下MC版本：",end="")
                for i in pkgdata[1]['game_versions']:
                    print(i+" ",end="")
                print()
                continue
        else:
            version = pkgdata[1]['game_versions'][-1] # 最新版本
        if not pkgcfg == None:
            status = False
            for i in pkgcfg['installed']:
                if not i['game_version'] == version:
                    status = True
                    print("\033[93m软件包"+pkg+"安装的MC版本("+version+")和目前已安装软件包"+i['package']+"的MC("+i['game_version']+")版本不相同\033[0m")
            if status:
                print("\033[93m要继续进行安装吗？\033[0m")
                result = input("(y/N)")
                if not (result.lower() == "y" or result.lower() == "yes"):
                    continue
        vers = modrinth_show_version(pkg,[config['data'][0]],[version])[1]
        file_sha1 = vers[0]['files'][0]['hashes']['sha1']
        file_name = vers[0]['files'][0]['filename']
        file_url = vers[0]['files'][0]['url']
        file_size = vers[0]['files'][0]['size']
        if not os.path.exists(".mpm"):
            os.mkdir(".mpm")
        if not os.path.exists(".mpm/tmp"):
            os.mkdir(".mpm/tmp")
        print("正在下载软件包所需的内容，MC版本"+version)
        print("下载"+file_url+" 来自软件包"+pkg)
        response = request(file_url,save_name=".mpm/tmp/tmp_"+file_name,timeout=60)
        if not response == 200:
            print("\033[91m错误：在尝试下载软件包时出了错")
            print("原因：",end="")
            if response == False or response == True:
                print("无法连接到modrinth",end="")
            else:
                print(str(response[0])+"："+response[1],end="")
            print("\033[0m")
            continue
        if not file_sha1 == sha1_file(".mpm/tmp/tmp_"+file_name):
            print("\033[91m文件校验失败，似乎在下载时损坏？\033[0m")
            os.remove(".mpm/tmp/tmp_"+file_name)
            continue
        print("安装软件包中")
        if config['data'][0] == "forge" or config['data'][0] == "fabric" or config['data'][0] == "neoforge":
            if not os.path.exists("mods"):
                os.mkdir("mods")
            if os.path.exists("mods/"+file_name):
                print("\033[33m警告：原有的文件mods/"+ file_name+"将会被替换\033[0m")
            os.rename(".mpm/tmp/tmp_"+file_name,"mods/"+file_name)
        else:
            if not os.path.exists("plugins"):
                os.mkdir("plugins")
            if os.path.exists("plugins/"+file_name):
                print("\033[33m警告：原有的文件plugins/"+file_name+"将会被替换\033[0m")
            os.rename(".mpm/tmp/tmp_"+file_name,"plugins/"+file_name)
        if os.path.exists(".mpm/package.json"):
            with open(".mpm/package.json","r") as f:
                pkgcfg = json.loads(f.read(os.path.getsize(".mpm/package.json")))
        else:
            pkgcfg = {
                "installed": []
            }
        pkgcfg['installed'].append({"package":pkg,"source":"modrinth","loader":config['data'][0],"game_version":version,"id":vers[0]['project_id'],"version_id":vers[0]['id'],"files":{file_name:file_sha1}})
        with open(".mpm/package.json","w") as f:
            f.write(json.dumps(pkgcfg,indent=4)+"\n")
        print("\033[92m软件包"+pkg+"已成功安装\033[0m")

def modrinth_remove_package(config):
    if len(config['data']) == 0:
        print("错误：缺少参数")
        print("用法："+os.path.basename(sys.argv[0])+" m-remove 软件包 [软件包 软件包 ...]")
        return
    if not os.path.exists(".mpm/package.json"):
        print("\033[91m没有软件包被安装，因此无法卸载\033[0m")
        return
    for i in config['data']:
        with open(".mpm/package.json","r") as f:
            pkgcfg = json.loads(f.read(os.path.getsize(".mpm/package.json")))
        status = False
        pkg = None
        for j in pkgcfg['installed']:
            if i == j['package']:
                status = True
                pkg = j
                break
        if not status:
            print("\033[91m软件包"+i+"没有被安装，因此无法卸载\033[0m")
            continue
        install_dir = "plugins/"
        if pkg['loader'] == "forge" or pkg['loader'] == "neoforge" or pkg['loader'] == "fabric":
            install_dir = "mods/"
        print("确定要卸载"+i+"吗？它包含了以下文件")
        for j in pkg['files']:
            print(install_dir+j)
        result = input("(Y/n)")
        if result.lower() == "n" or result.lower() == "no":
            print("跳过卸载软件包 "+i)
            continue
        print("卸载软件包"+i+"中")
        for j in pkg['files']:
            if not os.path.exists(install_dir+j):
                print("\033[93m警告：缺少文件"+install_dir+j+"，忽略\033[0m")
                continue
            if not pkg['files'][j] == sha1_file(install_dir+j):
                print("\033[93m警告：文件"+install_dir+j+"不是原来的文件，忽略\033[0m")
                continue
            os.remove(install_dir+j)
        new_pkgcfg = pkgcfg.copy()
        new_pkgcfg['installed'] = []
        for j in pkgcfg['installed']:
            if not pkg['id'] == j['id']:
                new_pkgcfg['installed'].append(j)
        with open(".mpm/package.json","w") as f:
            f.write(json.dumps(new_pkgcfg,indent=4)+"\n")
        print("软件包"+i+"已成功卸载")

def list_package(config):
    if not os.path.exists(".mpm/package.json"):
        print("没有软件包被安装")
        return
    with open(".mpm/package.json","r") as f:
        pkgcfg = json.loads(f.read(os.path.getsize(".mpm/package.json")))
    print("已安装的软件包")
    print("软件包名/源 加载器 游戏版本")
    for i in pkgcfg['installed']:
        print("\033[92m"+i['package']+"\033[0m/"+i['source']+" "+i['loader']+" "+i['game_version'])

def show_help():
    print(f"""mpm v{VERSION} By tzdtwsj
用法：{os.path.basename(sys.argv[0])} [参数] 命令

mpm是一个在命令行使用的《Minecraft》服务端软件包管理工具

命令：
    install, i\t\t\t安装软件包
    remove, uninstall, r\t删除软件包
    help\t\t\t显示该帮助

modrinth命令：
    m-install, m-i\t\t安装软件包
    m-search, m-s\t\t搜索内容，如果内容有空格，
    \t\t\t\t请使用引号把整个条目引起来
    m-show\t\t\t显示内容详情，如果内容有空格，
    \t\t\t\t请使用引号把整个条目引起来
    m-remove, m-uninstall, m-r\t删除软件包

项目地址：https://github.com/tzdtwsj/minecraft-package-tool
                                        这个MPM没有超级牛力.""")
    sys.exit(0)
