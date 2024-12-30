# minecraft-package-manager
---
## 这是什么？
这是一个基于Python开发的《Minecraft》服务端的包管理器，简称mpm，目前还处于早期开发阶段，基本不可用

---
## 已实现
* [x] 安装，搜寻，卸载modrinth插件、模组  
* [x] 列出已安装的软件包  
* [x] 功能模块化，可自行开发适用于其他站点的模块  
* [x] 安装tooth包（[lip](https://lip.futrime.com/zh/)的软件包）  
## 待实现
* [ ] 更新modrinth插件、模组  
* [ ] 卸载、更新tooth包（[lip](https://lip.futrime.com/zh/)的软件包）
---
## 特点
目前已经实现功能模块化，可以自己写功能，然后把写好功能的py文件放进modules文件夹  
[不是很详细的模块开发文档](docs/write_module.md)  

## 编译成二进制文件
```bash
# 首先安装pyinstaller
pip install pyinstaller

# 编译程序
pyinstaller -F --add-data modules:modules --hidden-import packaging main.py

# 编译好的程序在dist文件夹下
```
