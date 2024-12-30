from func import *
from commands import registers
import json
import shutil
from packaging.specifiers import SpecifierSet
import os
import sys
import platform
import glob

_cmds = [
    {
        "cmd": "t-install",
        "alias": ["t-i"],
        "func_name": "tooth_install",
        "help": "安装软件包"
    },
    {
        "cmd": "t-remove",
        "alias": ["t-uninstall","t-r"],
        "func_name": "tooth_remove",
        "help": "删除软件包"
    }
]

registers(get_module_name(__name__),_cmds)

GHPROXY = "https://gh.tuanzi.eu.org/" # 尾部要加/
#GHPROXY="https://ghgo.xyz/"
#GHPROXY=""

INSTALLED_NUM = 0

def tooth_install(params):
    if len(params) == 0:
        print(f"缺少参数\n用法：{os.path.basename(sys.argv[0])} t-install 软件包[@X.X.X 软件包 ...]")
        return
    for i in params:
        pre_version = None
        pkg = i
        if len(i.split("@")) == 2:
            pre_version = i.split("@")[-1]
            pkg = i.split("@")[0]
        else:
            if len(i.split("@")) > 2:
                print("错误的语法")
                print(f"用法：{os.path.basename(sys.argv[0])} t-install 软件包[@X.X.X 软件包 ...]")
                return
        if install(i,pre_version) == False:
            print("\033[91m安装"+pkg+"失败\033[0m")
            return
    print(f"\033[92m有{INSTALLED_NUM}个软件包安装成功\033[0m")


def install(pkg,pre_version=None):
    if get_package_from_list(pkg,get_module_name(__name__)) != False:
        print("该软件包"+pkg+"已安装")
        return True
    if pkg.split("/")[0] == "github.com" and len(pkg.split("/")) == 3:
        print("获取软件包"+pkg+"中")
        print("获取标签中",end="\r")
        resp = request("https://api.github.com/repos/"+pkg.split("/")[1]+"/"+pkg.split("/")[2]+"/tags")
        if resp == False:
            print("获取仓库数据错误")
            return False
        elif resp == True:
            print("获取仓库数据超时")
            return False
        if not resp[0] == 200:
            print("获取仓库数据错误："+str(resp[0]))
            return False
        tags = json.loads(resp[1])
        if len(tags) == 0:
            print("错误：该仓库没有任何标签")
            return False
        version = None
        commit_sha = None
        if pre_version != None:
            for j in tags:
                if j['name'][:1] == "v" and j['name'][1:2].isnumeric() and compare_version(j['name'][1:],pre_version):
                    version = j['name']
                    commit_sha = j['commit']['sha']
                    break
            if version == None:
                print("在远程服务器上没有找到这个版本："+pre_version)
                return False
        else:
            version = tags[0]["name"]
            commit_sha = tags[0]['commit']['sha']
        print("获取tooth数据中",end="\r")
        tooth_data = request(GHPROXY+"https://github.com/"+pkg.split("/")[1]+"/"+pkg.split("/")[2]+"/raw/"+version+"/tooth.json",headers={"User-Agent":"Mozilla/5.0 (Linux; Android 13; Phone) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Mobile Safari/537.36 EdgA/113.0.1774.38"})
        if tooth_data == False:
            print("请求tooth包数据失败")
            if GHPROXY == "":
                print("\033[93m检测到GHPROXY环境变量未设置，可能无法从github获取软件包\n在Linux中，你可以这么设置环境变量：\nexport GHPROXY=https://ghgo.xyz/\n在Windows中，你可以这么设置环境变量：\nset GHPROXY=https://ghgo.xyz/ \n网上有很多github代理加速，可以自行寻找地址\n注意：结尾要加斜杠\033[0m")
            return False
        elif tooth_data == True:
            print("请求tooth包数据超时")
            return False
        elif tooth_data[0] != 200:
            print("请求tooth包数据失败："+str(tooth_data))
            return False
        try:
            tooth_data = json.loads(tooth_data[1])
        except json.decoder.JSONDecodeError:
            print("\033[91m该软件包的tooth.json无效，JSON解析失败\033[0m")
            return False
        base_dir = "/"
        if not check_tooth_data(pkg,tooth_data):
            print("\033[91m该软件包的tooth.json无效\033[0m")
            return False
        pkg = tooth_data.get('tooth')
        if tooth_data.get("platforms"): # 特定架构的配置替代原本的配置
            for i in tooth_data.get("platforms"): # 同系统没指定架构
                if i['goos'] == GOOS and i.get('goarch') == None:
                    for j in ["asset_url","commands","dependencies","prerequisites","files"]:
                        if i.get(j) != None:
                            tooth_data[j] = i.get(j)
            for i in tooth_data.get("platforms"):# 同系统同架构
                if i['goos'] == GOOS and i.get('goarch') != None and i.get('goarch') == GOARCH:
                    for j in ["asset_url","commands","dependencies","prerequisites","files"]:
                        if i.get(j) != None:
                            tooth_data[j] = i.get(j)
        if tooth_data.get("asset_url") != None:
            url = tooth_data.get("asset_url").replace("$(version)",version[1:])
            if url[:19] == "https://github.com/":
                url = GHPROXY + url
        else:
            url = "https://api.github.com/repos/"+pkg.split("/")[1]+"/"+pkg.split("/")[2]+"/zipball/refs/tags/"+version
            base_dir = "/"+pkg.split("/")[1]+"-"+pkg.split("/")[2]+"-"+commit_sha[:7]+"/"
        save_name = pkg.replace("/","_")
        if tooth_data.get("dependencies") != None:
            for j in tooth_data.get("dependencies"):
                depdata = get_package_from_list(j,get_module_name(__name__))
                if depdata == False:
                    if install(j,tooth_data.get("dependencies")[j]) == False:
                        return False
                elif not compare_version(depdata['version'],tooth_data.get("dependencies")[j]):
                    print("\033[91m错误：该软件包所依赖的另一个软件包"+j+"已安装，但版本"+depdata['version']+"与该软件包所定义的依赖版本范围"+tooth_data.get("dependencies")[j]+"不符合\033[0m")
                    return False
        if tooth_data.get("prerequisites") != None:
            for j in tooth_data.get("prerequisites"):
                reqdata = get_package_from_list(j,get_module_name(__name__))
                if reqdata == False:
                    print("\033[91m错误：该软件包依赖"+j+"未安装，请手动安装该依赖\033[0m")
                    return False
                elif not compare_version(reqdata['version'],tooth_data.get("prerequisites")[j]):
                    print("\033[91m错误：该软件包所依赖的另一个软件包"+j+"已安装，但版本"+depdata['version']+"与该软件包所定义的依赖版本范围"+tooth_data.get("dependencies")[j]+"不符合\033[0m")
                    return False
        suffix = ".zip"
        if url.endswith(".zip"):
            suffix = ".zip"
        elif url.endswith(".tar.gz") or url.endswith(".tgz"):
            suffix = ".tar.gz"
        if not os.path.exists(".mpm/tmp"):
            os.mkdir(".mpm/tmp")
        print("下载数据中，从"+url)
        request(url=url,save_name=".mpm/tmp/"+save_name+suffix,headers={"User-Agent":"Mozilla/5.0 (Linux; Android 13; Phone) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Mobile Safari/537.36 EdgA/113.0.1774.38"})
        if suffix == ".zip":
            unzip(".mpm/tmp/"+save_name+suffix,".mpm/tmp/"+save_name)
        elif suffix == ".tar.gz":
            untgz(".mpm/tmp/"+save_name+suffix,".mpm/tmp/"+save_name)
        print("安装"+pkg+"中")
        if tooth_data.get("commands") != None and tooth_data.get("commands").get("pre-install") != None:
            for i in tooth_data.get("commands").get("pre-install"):
                ret = os.system(i)
        elif tooth_data.get("commands") != None and tooth_data.get("commands").get("pre_install") != None:
            for i in tooth_data.get("commands").get("pre_install"):
                ret = os.system(i)
        files = {}
        if tooth_data.get("files") != None and tooth_data.get("files").get("place") != None:
            for i in tooth_data.get("files").get("place"):
                places = place_files(".mpm/tmp/"+save_name+base_dir,i['src'],i['dest'])
                if places == False:
                    print("\033[91m源文件"+i[src]+"不存在，无法安装文件\033[0m")
                    return False
                for j in places:
                    files[j] = places[j]
        if tooth_data.get("commands") != None and tooth_data.get("commands").get("post-install") != None:
            for i in tooth_data.get("commands").get("post-install"):
                ret = os.system(i)
        elif tooth_data.get("commands") != None and tooth_data.get("commands").get("post_install") != None:
            for i in tooth_data.get("commands").get("post_install"):
                ret = os.system(i)
        add_package_to_list(pkg,get_module_name(__name__),{'version':version[1:],'files':files,'tooth_data':tooth_data})
        shutil.rmtree(".mpm/tmp/"+save_name)
        os.remove(".mpm/tmp/"+save_name+suffix)
    else:
        if not os.path.exists(pkg):
            print("\033[91m找不到软件包"+pkg+"\033[0m")
            return False
        save_name = "Local_"+pkg.replace("/","_").replace("\\","_")
        try:
            unzip(pkg,".mpm/tmp/"+save_name)
        except zipfile.BadZipFile:
            print("\033[91m无效的软件包"+pkg+"\033[0m")
            return False
        if not os.path.exists(".mpm/tmp/"+save_name+"/tooth.json"):
            print("\033[91m找不到tooth.json，软件包打包时是否套文件夹？\033[0m")
            shutil.rmtree(".mpm/tmp/"+save_name)
            return False
        with open(".mpm/tmp/"+save_name+"/tooth.json","r") as f:
            tooth_data = f.read(os.path.getsize(".mpm/tmp/"+save_name+"/tooth.json"))
        try:
            tooth_data = json.loads(tooth_data)
        except json.decoder.JSONDecodeError:
            print("\033[91m该软件包的tooth.json无效，JSON解析失败\033[0m")
            shutil.rmtree(".mpm/tmp/"+save_name)
            return False
        if not check_tooth_data(pkg,tooth_data,no_check_pkg_name=True):
            print("\033[91m该软件包的tooth.json无效\033[0m")
            shutil.rmtree(".mpm/tmp/"+save_name)
            return False
        pkg = tooth_data.get('tooth')
        if get_package_from_list(pkg,get_module_name(__name__)) != False:
            print("该软件包"+pkg+"已安装")
            return True
        version = tooth_data.get('version')
        if tooth_data.get("platforms"): # 特定架构的配置替代原本的配置
            for i in tooth_data.get("platforms"): # 同系统没指定架构
                if i['goos'] == GOOS and i.get('goarch') == None:
                    for j in ["asset_url","commands","dependencies","prerequisites","files"]:
                        if i.get(j) != None:
                            tooth_data[j] = i.get(j)
            for i in tooth_data.get("platforms"):# 同系统同架构
                if i['goos'] == GOOS and i.get('goarch') != None and i.get('goarch') == GOARCH:
                    for j in ["asset_url","commands","dependencies","prerequisites","files"]:
                        if i.get(j) != None:
                            tooth_data[j] = i.get(j)
        if tooth_data.get("dependencies") != None:
            for j in tooth_data.get("dependencies"):
                depdata = get_package_from_list(j,get_module_name(__name__))
                if depdata == False:
                    if install(j,tooth_data.get("dependencies")[j]) == False:
                        shutil.rmtree(".mpm/tmp/"+save_name)
                        return False
                elif not compare_version(depdata['version'],tooth_data.get("dependencies")[j]):
                    print("\033[91m错误：该软件包所依赖的另一个软件包"+j+"已安装，但版本"+depdata['version']+"与该软件包所定义的依赖版本范围"+tooth_data.get("dependencies")[j]+"不符合\033[0m")
                    shutil.rmtree(".mpm/tmp/"+save_name)
                    return False
        if tooth_data.get("prerequisites") != None:
            for j in tooth_data.get("prerequisites"):
                reqdata = get_package_from_list(j,get_module_name(__name__))
                if reqdata == False:
                    print("\033[91m错误：该软件包依赖"+j+"未安装，请手动安装该依赖\033[0m")
                    shutil.rmtree(".mpm/tmp/"+save_name)
                    return False
                elif not compare_version(reqdata['version'],tooth_data.get("prerequisites")[j]):
                    print("\033[91m错误：该软件包所依赖的另一个软件包"+j+"已安装，但版本"+depdata['version']+"与该软件包所定义的依赖版本范围"+tooth_data.get("dependencies")[j]+"不符合\033[0m")
                    shutil.rmtree(".mpm/tmp/"+save_name)
                    return False
        suffix = ".zip"
        if tooth_data.get("asset_url") != None:
            url = tooth_data.get("asset_url").replace("$(version)",version[1:])
            if url[:19] == "https://github.com/":
                url = GHPROXY + url
            if url.endswith(".zip"):
                suffix = ".zip"
            elif url.endswith(".tar.gz") or url.endswith(".tgz"):
                suffix = ".tar.gz"
            if not os.path.exists(".mpm/tmp"):
                os.mkdir(".mpm/tmp")
            shutil.rmtree(".mpm/tmp/"+save_name)
            print("下载数据中，从"+url)
            request(url=url,save_name=".mpm/tmp/"+save_name+suffix,headers={"User-Agent":"Mozilla/5.0 (Linux; Android 13; Phone) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Mobile Safari/537.36 EdgA/113.0.1774.38"})
            if suffix == ".zip":
                unzip(".mpm/tmp/"+save_name+suffix,".mpm/tmp/"+save_name)
            elif suffix == ".tar.gz":
                untgz(".mpm/tmp/"+save_name+suffix,".mpm/tmp/"+save_name)
        print("安装"+pkg+"中")
        if tooth_data.get("commands") != None and tooth_data.get("commands").get("pre-install") != None:
            for i in tooth_data.get("commands").get("pre-install"):
                ret = os.system(i)
        elif tooth_data.get("commands") != None and tooth_data.get("commands").get("pre_install") != None:
            for i in tooth_data.get("commands").get("pre_install"):
                ret = os.system(i)
        files = {}
        if tooth_data.get("files") != None and tooth_data.get("files").get("place") != None:
            for i in tooth_data.get("files").get("place"):
                places = place_files(".mpm/tmp/"+save_name+"/",i['src'],i['dest'])
                if places == False:
                    print("\033[91m源文件"+i[src]+"不存在，无法安装文件\033[0m")
                    return False
                for j in places:
                    files[j] = places[j]
        if tooth_data.get("commands") != None and tooth_data.get("commands").get("post-install") != None:
            for i in tooth_data.get("commands").get("post-install"):
                ret = os.system(i)
        elif tooth_data.get("commands") != None and tooth_data.get("commands").get("post_install") != None:
            for i in tooth_data.get("commands").get("post_install"):
                ret = os.system(i)
        add_package_to_list(pkg,get_module_name(__name__),{'version':version[1:],'files':files,'tooth_data':tooth_data})
        shutil.rmtree(".mpm/tmp/"+save_name)
        if os.path.exists(".mpm/tmp/"+save_name+suffix):
            os.remove(".mpm/tmp/"+save_name+suffix)
    print("\033[92m安装"+pkg+"成功\033[0m")
    global INSTALLED_NUM
    INSTALLED_NUM += 1
    return True

def check_tooth_data(pkg_name, tooth_data,no_check_pkg_name=False):
    if not tooth_data.get("format_version") == 2:
        return False
    if no_check_pkg_name == False and not tooth_data.get("tooth").lower() == pkg_name.lower():
        return False
    if not tooth_data.get("version"):
        return False
    if not ( tooth_data.get("info") and type(tooth_data.get("info")) == dict and tooth_data['info'].get("name") and tooth_data['info'].get("description") and tooth_data['info'].get("author") and tooth_data['info'].get("tags") != None and type(tooth_data['info'].get("tags")) == list ):
        return False
    return True

def compare_version(version,pattern):
    # 版本对比函数，检测version是否在pattern范围里，写这玩意真要写死我了
    for i in pattern.split(" || "):
        yf = []
        for j in i.split(" "):
            if j[:2] == ">=" or j[:2] == "<=" or j[:1] == ">" or j[:1] == "<":
                yf.append(j)
            elif j[:1] == "^":
                yf.append(">="+j[1:])
                yf.append("<="+str(int(j[1:].split(".")[0])+1)+".0.0")
            elif j[:1] == "~":
                yf.append(">="+j[1:])
                yf.append("<="+j[1:].split(".")[0]+"."+str(int(j[1:].split(".")[1])+1)+".0")
            else:
                yf2 = ""
                yf3 = ""
                for k in j.split("."):#1.x.x, 1.1.x, x.x.x, 1.1.1
                    if k != "x":
                        yf2 += k+"."
                    else:
                        djwsx = len(yf2.split("."))# 1:x.x.x 2:1.x.x 3:1.1.x
                        for l in range(3-djwsx):
                            yf2 += "0."
                        yf2 += "0"
                        if djwsx == 2:
                            yf3 = str(int(yf2.split(".")[0])+1)+".0.0"
                        elif djwsx == 3:
                            yf3 = yf2.split(".")[0]+"."+str(int(yf2.split(".")[1])+1)+".0"
                        break
                if yf2[-1] == ".":
                    yf2 = yf2[:-1]
                    yf3 = str(yf2.split(".")[0])+"."+str(yf2.split(".")[1])+"."+str(int(yf2.split(".")[2])+1)
                if yf2 == "0.0.0":
                    yf.append("")
                else:
                    yf.append(">="+yf2)
                    yf.append("<"+yf3)
        status = True
        for j in yf:
            if (version in SpecifierSet(j)) == False:
                status = False
        if status == True:
            return True
    return False

def place_files(basedir,src,dest):
    if dest[-1] == "/":
        dest = dest[:-1]
    files = glob.glob(basedir+src)
    files2 = []
    if src[-1] == "*":
        if os.path.exists(dest):
            if not os.path.isdir(dest):
                return False
        else:
            os.makedirs(dest)
        for i in files:
            if os.path.isdir(i):
                shutil.copytree(i,dest+"/"+os.path.basename(i))
                for j in list_files(dest):
                    files2.append(j)
            else:
                shutil.copy(i,dest+"/"+os.path.basename(i))
                files2.append(dest+"/"+os.path.basename(i))
    else:
        if os.path.dirname(dest) != "" and not os.path.exists(os.path.dirname(dest)):
            os.makedirs(os.path.dirname(dest))
        for i in files:
            shutil.copy(i,dest)
            files2.append(dest)
    sha1_files = {}
    for i in files2:
        sha1_files[i] = sha1_file(i)
    return sha1_files

def list_files(directory):
    files2 = []
    for root,dirs,files in os.walk(directory):
        for j in files:
            files2.append(os.path.join(root,j))
    return files2


if sys.platform.startswith("linux"):
    GOOS = "linux"
elif sys.platform.startswith("win"):
    GOOS = "windows"
else:
    raise OSError("暂不支持你的系统："+sys.platform)

if platform.machine() == "AMD64" or platform.machine() == "x86_64":# AMD64: Windows, x86_64: Linux
    GOARCH = "amd64"
elif platform.machine() == "i386" or platform.machine() == "i686":
    GOARCH = "386"
elif platform.machine() == "aarch64" or platform.machine() == "armv8l":
    GOARCH = "arm64"
elif platform.machine() == "armv7l":
    GOARCH = "arm"
else:
    raise OSError("暂不支持你的系统的架构："+platform.machine())

if os.environ.get("GHPROXY") != None:
    GHPROXY = os.environ.get("GHPROXY")
else:
    GHPROXY = ""
