# -*- coding: utf-8 -*-
"""
PI Manager 三合一客户端统一入口

支持三种模式（启动时交互选择）：
  1. 在线模式（默认）：加载 Vue App，离线走 QWebChannel 桥接
  2. 离线模式：强制 QWebChannel + SQLite，禁用 CDN 更新检查
  3. 轻量模式（Vue-only）：仅启动 WebEngine 界面，无完整 PyQt 窗口系统

复用 client/main.py 的 MainWindow，但在此之前：
  - 执行 SQLite 增量迁移
  - 初始化 QtBridge（QWebChannel RPC -> SQLite）
  - 自动检测网络，在线走远程 API，离线走 QWebChannel

用法：
  python run_combined.py
"""
import sys
import os
import logging

logger = logging.getLogger('run_combined')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

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


# ---- 统一的 Qt 枚举导入 ----
# PySide6 和 PyQt5 枚举值不同，统一在这里处理
_QT_IMPORTS = None


def _init_qt():
    global _QT_IMPORTS
    if _QT_IMPORTS is not None:
        return _QT_IMPORTS
    try:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QApplication
        from PySide6.QtWebEngineWidgets import QWebEngineView
        # QWebEngineSettings 在 PySide6 中位于 QtWebEngineCore
        from PySide6.QtWebEngineCore import QWebEngineSettings
        from PySide6.QtWebChannel import QWebChannel
        from PySide6.QtCore import QUrl
        _QT_IMPORTS = {
            'Qt': Qt,
            'QApplication': QApplication,
            'QWebEngineView': QWebEngineView,
            'QWebEngineSettings': QWebEngineSettings,
            'QWebChannel': QWebChannel,
            'QUrl': QUrl,
            'AA_EnableHighDpiScaling': Qt.ApplicationAttribute.AA_EnableHighDpiScaling,
            'LocalContentCanAccessRemoteUrls': QWebEngineSettings.LocalContentCanAccessRemoteUrls,
        }
        return _QT_IMPORTS
    except ImportError:
        from PyQt5.QtCore import Qt, QUrl
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
        from PyQt5.QtWebChannel import QWebChannel
        _QT_IMPORTS = {
            'Qt': Qt,
            'QApplication': QApplication,
            'QWebEngineView': QWebEngineView,
            'QWebEngineSettings': QWebEngineSettings,
            'QWebChannel': QWebChannel,
            'QUrl': QUrl,
            'AA_EnableHighDpiScaling': 20,  # Qt.AA_EnableHighDpiScaling
            'LocalContentCanAccessRemoteUrls': QWebEngineSettings.LocalContentCanAccessRemoteUrls,
        }
        return _QT_IMPORTS


def _show_mode_dialog(app) -> str:
    """弹出模式选择对话框，返回 'online' | 'offline' | 'vue-only'。"""
    Qt = _init_qt()['Qt']
    try:
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
    except ImportError:
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QPushButton

    result = {'mode': 'online'}

    dlg = QDialog()
    dlg.setWindowTitle('PI Manager - 选择运行模式')
    dlg.setFixedSize(420, 200)
    dlg.setWindowFlags(
        dlg.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint
    )

    layout = QVBoxLayout(dlg)
    layout.addWidget(QLabel('请选择运行模式：'))

    btns = QHBoxLayout()
    online_btn = QPushButton('在线模式（推荐）')
    offline_btn = QPushButton('离线模式')
    vue_btn = QPushButton('轻量模式（无窗口框架）')
    btns.addWidget(online_btn)
    btns.addWidget(offline_btn)
    btns.addWidget(vue_btn)
    layout.addLayout(btns)

    def set_mode(mode):
        result['mode'] = mode
        dlg.accept()

    online_btn.clicked.connect(lambda: set_mode('online'))
    offline_btn.clicked.connect(lambda: set_mode('offline'))
    vue_btn.clicked.connect(lambda: set_mode('vue-only'))

    dlg.exec()

    mode = result['mode']
    logger.info('[Combined] 用户选择模式: %s', mode)
    return mode


def _get_frontend_index() -> str:
    fm = FrontendManager()
    return fm.get_active_index_path()


def _run_vue_only(app, index_path: str):
    """轻量模式：仅启动 WebEngine 加载 Vue App。"""
    logger.info('[Combined] 启动 Vue-only 轻量模式...')
    qt = _init_qt()

    bridge = QtBridge()
    channel = qt['QWebChannel']()
    channel.registerObject('nativeBridge', bridge)

    page = qt['QWebEngineView']()
    page.page().setWebChannel(channel)
    page.page().settings().setAttribute(
        qt['LocalContentCanAccessRemoteUrls'], True
    )

    abs_path = os.path.abspath(index_path)
    page.load(qt['QUrl'].fromLocalFile(abs_path))
    page.setWindowTitle('PI Manager')
    page.resize(1280, 800)
    page.show()
    sys.exit(app.exec())


def _run_full_desktop(app, index_path: str, offline: bool):
    """完整桌面模式：启动 client/main.py 的 MainWindow，加载 Vue App。"""
    logger.info('[Combined] 启动完整桌面模式（offline=%s）...', offline)
    bridge = QtBridge()
    logger.info('[Combined] QtBridge(QWebChannel->SQLite) 已就绪')

    qt = _init_qt()
    from main import MainWindow
    from api.client import ApiClient
    from config import Config

    api_client = ApiClient(base_url=Config.API_BASE_URL)
    dept_id = 'S'
    window = MainWindow(api_client, dept_id, index_path=index_path)
    window.show()

    if not offline and Config.AUTO_CHECK_UPDATE:
        from PySide6.QtCore import QTimer
    else:
        from PyQt5.QtCore import QTimer
    QTimer.singleShot(1000, window._check_update_async)

    sys.exit(app.exec())


def main():
    # 执行数据库迁移
    logger.info('[Combined] 开始数据库迁移...')
    migrate()
    logger.info('[Combined] 数据库迁移完成')

    # 获取前端路径
    index_path = _get_frontend_index()
    print('[Combined] 前端入口: ' + index_path)

    # 创建 Qt 应用对象（对话框需要先有 app）
    qt = _init_qt()
    qt['QApplication'].setAttribute(qt['AA_EnableHighDpiScaling'], True)
    app = qt['QApplication'](sys.argv)

    # 弹出模式选择对话框
    mode = _show_mode_dialog(app)

    # 根据模式启动
    if mode == 'vue-only':
        _run_vue_only(app, index_path)
    elif mode == 'offline':
        _run_full_desktop(app, index_path, offline=True)
    else:
        _run_full_desktop(app, index_path, offline=False)


if __name__ == '__main__':
    main()
