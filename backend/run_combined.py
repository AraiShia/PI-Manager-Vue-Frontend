# -*- coding: utf-8 -*-
"""
PI Manager 三合一客户端统一入口

支持三种启动模式：
  1. 纯桌面（默认）：启动 PyQt 主窗口，加载 Vue App（WebEngine）
  2. --offline：强制离线模式（不检查远程更新）
  3. --vue-only：仅启动 WebEngine Vue 界面（无完整 PyQt 窗口系统）
     用于交付给最终用户的轻量桌面客户端。

复用 client/main.py 的 MainWindow，但在此之前：
  - 执行 SQLite 增量迁移
  - 初始化 QtBridge（QWebChannel RPC -> SQLite）
  - 配置前端路径（exe 同级 dist/）
  - 自动检测网络，在线走远程 API，离线走 QWebChannel

用法：
  python run_combined.py [--offline] [--vue-only]
"""
import sys
import os
import argparse
import logging

# 将 backend 和 client 都加入 sys.path
if getattr(sys, 'frozen', False):
    _BACKEND_DIR = os.path.dirname(sys.executable)
else:
    _BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_CLIENT_DIR = os.path.join(os.path.dirname(_BACKEND_DIR), 'client')
for p in (_BACKEND_DIR, _CLIENT_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

from app.migration_manager import migrate
from frontend_manager import FrontendManager
from qt_bridge import QtBridge

logger = logging.getLogger('run_combined')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)


def get_frontend_index() -> str:
    fm = FrontendManager()
    return fm.get_active_index_path()


def main():
    parser = argparse.ArgumentParser(description='PI Manager 三合一客户端')
    parser.add_argument('--offline', action='store_true',
                        help='强制离线模式，跳过 CDN 版本检查')
    parser.add_argument('--vue-only', action='store_true',
                        help='仅启动 WebEngine Vue 界面（轻量模式）')
    args = parser.parse_args(sys.argv[1:])

    logger.info('[Combined] 开始数据库迁移...')
    migrate()
    logger.info('[Combined] 数据库迁移完成')

    index_path = get_frontend_index()
    print('[Combined] 前端入口: ' + index_path)

    if args.vue_only:
        _run_vue_only(index_path, args.offline)
    else:
        _run_full_desktop(index_path, args.offline)


def _run_vue_only(index_path: str, offline: bool):
    logger.info('[Combined] 启动 Vue-only 轻量模式...')
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
        from PySide6.QtWebChannel import QWebChannel
        from PySide6.QtCore import QUrl
    except ImportError:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
        from PyQt5.QtWebChannel import QWebChannel
        from PyQt5.QtCore import QUrl

    QApplication.setAttribute(20, True)
    app = QApplication(sys.argv)

    bridge = QtBridge()
    channel = QWebChannel()
    channel.registerObject('nativeBridge', bridge)
    page = QWebEngineView()
    page.page().setWebChannel(channel)

    settings = page.page().settings()
    settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)

    abs_path = os.path.abspath(index_path)
    page.load(QUrl.fromLocalFile(abs_path))
    page.setWindowTitle('PI Manager')
    page.resize(1280, 800)
    page.show()

    sys.exit(app.exec())


def _run_full_desktop(index_path: str, offline: bool):
    logger.info('[Combined] 启动完整桌面模式...')
    bridge = QtBridge()
    logger.info('[Combined] QtBridge(QWebChannel->SQLite) 已就绪')

    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QTimer
    except ImportError:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import QTimer

    QApplication.setAttribute(20, True)
    app = QApplication(sys.argv)

    from main import MainWindow
    from api.client import ApiClient
    from config import Config

    api_client = ApiClient(base_url=Config.API_BASE_URL)
    dept_id = 'S'
    window = MainWindow(api_client, dept_id, index_path=index_path)
    window.show()

    if not offline and Config.AUTO_CHECK_UPDATE:
        QTimer.singleShot(1000, window._check_update_async)

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
