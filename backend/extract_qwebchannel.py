# -*- coding: utf-8 -*-
"""通过 Qt 资源系统提取官方内置的 qwebchannel.js 文件"""

import os
import sys

# 将根目录添加到 sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

def extract():
    print("=== 正在通过 Qt 资源系统提取 qwebchannel.js ===")
    
    # 尝试加载 PySide6 或 PyQt5，并实例化 QCoreApplication 以激活 QRC 资源引擎
    try:
        from PySide6.QtCore import QCoreApplication, QFile, QIODevice
        import PySide6.QtWebChannel
        app = QCoreApplication([])
        print("成功载入 PySide6 并初始化资源引擎")
    except ImportError:
        try:
            from PyQt5.QtCore import QCoreApplication, QFile, QIODevice
            import PyQt5.QtWebChannel
            app = QCoreApplication([])
            print("成功载入 PyQt5 并初始化资源引擎")
        except ImportError:
            print("[错误] 运行环境中未安装 PySide6 或 PyQt5，无法提取 qwebchannel.js")
            sys.exit(1)

    # 从内建的 Qt 虚拟资源路径中读取脚本内容
    f = QFile(":/qtwebchannel/qwebchannel.js")
    if f.open(QIODevice.ReadOnly):
        content = f.readAll().data()
        dest_path = os.path.join(os.path.dirname(BASE_DIR), "frontend", "public", "qwebchannel.js")
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        
        with open(dest_path, "wb") as out:
            out.write(content)
            
        print(f"[成功] 已成功提取并保存至: {dest_path} (大小: {len(content)} 字节)")
    else:
        print(f"[错误] 无法打开 Qt 内置资源文件: {f.errorString()}")
        sys.exit(1)

if __name__ == "__main__":
    extract()
