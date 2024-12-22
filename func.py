
import urllib.request
import urllib.parse
import urllib.error
import json
import sys
import os
from version import VERSION
import hashlib

class ParamError(Exception):
    pass

def print_progress(downloaded_size,size=None):
    if not size == None:
        print("进度："+parse_size(downloaded_size)+" "+str(round(downloaded_size/size*100,2))+"%      ",end="\r")
    else:
        print("进度："+parse_size(downloaded_size)+"      ",end="\r")

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
        print("请输入要搜索的内容")
        return
    for i in config.get("data"):
        data = modrinth_search(i)
        if data[0] == 0:
            print("无法连接到modrinth")
        elif data[0] >= 300 or data[0] < 200:
            print("服务器返回了非200状态码："+data[1])
        elif data[0] < 300 and data[0] >= 200:
            if data[1].get("total_hits") == 0:
                print("\033[31m内容"+i+"无结果\033[0m")
                continue
            if os.path.exists(".mpm/package.json"):
                with open(".mpm/package.json","r") as f:
                    pkgcfg = json.loads(f.read(os.path.getsize(".mpm/package.json")))
            else:
                pkgcfg = {'installed':[]}
            print("\033[33m对于"+i+"，在modrinth搜索到"+str(data[1].get("total_hits"))+"个条目，这里只列出10条\033[0m")
            j=0
            while j < data[1].get("limit"):
                print("\033[32m"+data[1].get("hits")[j]['slug']+"\033[0m/"+data[1].get("hits")[j]['title'],end="")
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
        print("请输入要查询的内容")
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
        print(f"用法：{os.path.basename(sys.argv[0])} m-install 加载器 软件包 [游戏版本]")
        return
    pkgdata = modrinth_show(config['data'][1])
    if pkgdata[0] == 0:
        print("无法连接到modrinth")
        return
    elif pkgdata[0] == 404:
        print("找不到软件包 "+config['data'][1])
        return
    if os.path.exists(".mpm/package.json"):
        with open(".mpm/package.json","r") as f:
            pkgcfg = json.loads(f.read(os.path.getsize(".mpm/package.json")))
        for i in pkgcfg['installed']:
            if i['id'] == pkgdata[1]['id']:
                print("该软件包"+config['data'][1]+"已被安装")
                return
    if not config['data'][0] in pkgdata[1]['loaders']:
        print("错误：不支持的加载器"+config['data'][0]+"，该软件包仅支持以下加载器：",end="")
        for i in pkgdata[1]['loaders']:
            print(i+" ",end="")
        print()
        return
    if len(config['data']) >= 3:
        version = config['data'][2]
        if not version in pkgdata[1]['game_versions']:
            print("错误：不支持的MC版本"+version+"，该软件包仅支持以下MC版本：",end="")
            for i in pkgdata[1]['game_versions']:
                print(i+" ",end="")
            print()
            return
    else:
        version = pkgdata[1]['game_versions'][-1] # 最新版本
    vers = modrinth_show_version(config['data'][1],[config['data'][0]],[version])[1]
    file_sha1 = vers[0]['files'][0]['hashes']['sha1']
    file_name = vers[0]['files'][0]['filename']
    file_url = vers[0]['files'][0]['url']
    file_size = vers[0]['files'][0]['size']
    if not os.path.exists(".mpm"):
        os.mkdir(".mpm")
    if not os.path.exists(".mpm/tmp"):
        os.mkdir(".mpm/tmp")
    print("正在下载软件包所需的内容，MC版本"+version)
    print("下载"+file_url+" 来自软件包"+config['data'][1])
    response = request(file_url,save_name=".mpm/tmp/tmp_"+file_name,timeout=60)
    if not response == 200:
        print("错误：在尝试下载软件包时出了错")
        print("原因：",end="")
        if response == False or response == True:
            print("无法连接到modrinth")
        else:
            print(str(response[0])+"："+response[1])
        return
    if not file_sha1 == sha1_file(".mpm/tmp/tmp_"+file_name):
        print("文件校验失败，似乎在下载时损坏？")
        os.remove(".mpm/tmp/tmp_"+file_name)
        return
    print("安装软件包中")
    if config['data'][0] == "forge" or config['data'][0] == "fabric" or config['data'][0] == "neoforge":
        if not os.path.exists("mods"):
            os.mkdir("mods")
        os.rename(".mpm/tmp/tmp_"+file_name,"mods/"+file_name)
    else:
        if not os.path.exists("plugins"):
            os.mkdir("plugins")
        os.rename(".mpm/tmp/tmp_"+file_name,"plugins/"+file_name)
    if os.path.exists(".mpm/package.json"):
        with open(".mpm/package.json","r") as f:
            pkgcfg = json.loads(f.read(os.path.getsize(".mpm/package.json")))
    else:
        pkgcfg = {
            "installed": []
        }
    pkgcfg['installed'].append({"package":config['data'][1],"source":"modrinth","loader":config['data'][0],"game_version":version,"id":vers[0]['project_id'],"version_id":vers[0]['id'],"files":{file_name:file_sha1}})
    with open(".mpm/package.json","w") as f:
        f.write(json.dumps(pkgcfg,indent=4))
    print("软件包"+config['data'][1]+"已成功安装")

def show_help():
    print(f"""mpm v{VERSION} By tzdtwsj
用法：{os.path.basename(sys.argv[0])} [参数] 命令

mpm是一个在命令行使用的《我的世界》服务端软件包管理工具

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

项目地址：https://github.com/tzdtwsj/minecraft-package-tool
                                        这个MPM没有超级牛力.""")
    sys.exit(0)
