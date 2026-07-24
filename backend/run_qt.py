# -*- coding: utf-8 -*-
"""Qt 离线客户端启动入口 (Run Qt App)

符合 Google 编程规范，包含详细的中文注释。
负责在启动时自动执行 SQLite 增量数据库迁移、初始化并校验本地 AppData 前端资源包、
绑定 QWebChannel 通信桥梁，并拉起 PyQt5 消息循环。不启动本地 HTTP 端口服务。
"""

import os
import sys
import logging
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

# 将项目根目录加入 sys.path 以方便载入 app 依赖
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.migration_manager import migrate
from frontend_manager import FrontendManager
from qt_bridge import QtBridge

# 设定日志输出
logger = logging.getLogger("run_qt")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# 读取当前 exe 版本（与 frontend_manager.BASELINE_VERSION 对齐）
_EXE_VERSION = "1.0.0.28"  # TODO: 与 backend/version.json 同步，打包时由 CI 注入


def main():
    logger.info("=== PI Manager 离线客户端启动 ===")

    # 1. 自动执行 SQLite 增量数据库迁移 (防多进程并发锁)
    try:
        logger.info("开始检查并执行数据库迁移与结构补建...")
        migrate()
        logger.info("数据库迁移与表验证已顺利完成")
    except Exception as e:
        logger.error(f"数据库迁移阶段发生致命错误，启动被拦截终止: {e}")
        # 弹窗提示或直接打印并异常退出
        sys.exit(1)

    # 2. 实例化前端管理器并准备前端基线物理资源包
    logger.info("检查 AppData 本地缓存前端包资源...")
    frontend_manager = FrontendManager()
    frontend_manager.ensure_baseline_frontend()

    # 3. 初始化并配置 PyQt5 应用对象
    # 开启高 DPI 缩放支持
    QApplication.setAttribute(20, True)  # Qt.AA_EnableHighDpiScaling
    app = QApplication(sys.argv)

    # 4. 实例化 QWebEngineView 窗口
    view = QWebEngineView()
    view.setWindowTitle("PI Manager 订单管理系统")
    view.resize(1280, 800)

    # 5. 安全性与跨域配置配置
    settings = view.page().settings()
    # 核心安全放开：允许本地加载的 file:// 前端通过 Ajax 请求 https:// 远程 API（在线模式必需）
    settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
    # 允许使用控制台与检查元素进行调试 (开发验证辅助)
    settings.setAttribute(QWebEngineSettings.DeveloperExtrasEnabled, True)

    # 6. 配置 QWebChannel 桥接，并在全局注册 nativeBridge 对象
    channel = QWebChannel()
    # 注入 View 视图和资源管理器以备 trigger_refresh 重定向及版本比对
    bridge = QtBridge(view=view, frontend_manager=frontend_manager)
    
    # 必须在 JS 端通过 channel.objects.nativeBridge 进行同名匹配调用
    channel.registerObject("nativeBridge", bridge)
    view.page().setWebChannel(channel)

    # 7. 读取当前配置的可用前端 index.html 路径并引导加载
    index_path = frontend_manager.get_active_index_path()
    logger.info(f"前端加载路径选定为: {index_path}")
    
    # 使用 QUrl.fromLocalFile 避免物理绝对路径的反斜杠转义失败导致无法加载
    view.setUrl(QUrl.fromLocalFile(index_path))

    # 8. 启动异步线程检查 CDN 前端包热更新 (不阻塞 UI 展示)
    import threading
    import json
    import urllib.request

    def _async_check_update():
        try:
            cdn_version_url = os.environ.get(
                "PI_CDN_VERSION_URL",
                "https://cdn.example.com/pi-manager/version.json"
            )
            logger.info(f"正在异步发起 CDN 前端更新比对: {cdn_version_url}")
            req = urllib.request.Request(cdn_version_url, headers={"User-Agent": "PIManager-Desktop/1.0"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    manifest = json.loads(resp.read().decode("utf-8"))
                    if frontend_manager.verify_manifest_signature(manifest):
                        if frontend_manager.update_frontend(manifest, current_app_version=_EXE_VERSION):
                            new_ver = manifest.get("version", "")
                            logger.info(f"CDN 前端包已安全下载完成，通知前端刷新: {new_ver}")
                            bridge.emit_version_available(new_ver)
                    else:
                        logger.warning("CDN Manifest 签名校验未通过，放弃热更新")
        except Exception as e:
            logger.debug(f"异步 CDN 更新检查跳过或联网超时 (离线状态正常): {e}")

    threading.Thread(target=_async_check_update, daemon=True).start()

    # 9. 窗口展示并进入 Qt 循环
    view.show()
    # 兼容 PySide6 exec() 与 PyQt5 exec_()
    sys.exit(app.exec() if hasattr(app, "exec") else app.exec_())


if __name__ == "__main__":
    main()
