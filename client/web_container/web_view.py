"""QWebEngineView 封装：Vue SPA 容器"""
import urllib.parse
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtCore import QUrl
from PySide6.QtGui import QContextMenuEvent
from .channel_bridge import NativeBridge
from .native_api import NativeAPI

# 允许加载的前端域名白名单
ALLOWED_HOSTS = (
    'piapi.wakabashia.tj.cn',
    'localhost',
    '127.0.0.1',
)


def _validate_host(url: str) -> str:
    """校验 URL 是否在白名单内，防止配置被社工劫持。

    Args:
        url: 候选 URL。
    Returns:
        规范化后的 URL（去掉末尾斜杠）。
    Raises:
        ValueError: 当 URL 协议或域名不在白名单内时抛出。
    """
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ('http', 'https'):
        raise ValueError(f'不允许的协议: {parsed.scheme}（仅允许 http/https）')
    if parsed.hostname is None or parsed.hostname not in ALLOWED_HOSTS:
        raise ValueError(f'不允许的远程地址: {parsed.hostname}')
    # 显式去除末尾斜杠并重建
    return f"{parsed.scheme}://{parsed.netloc}".rstrip('/')


def build_web_url(remote_url: str, path: str) -> str:
    """构建 Web 容器 URL，自动去除重复斜杠并拒绝外部跳转。"""
    if path.startswith('//') or not path.startswith('/'):
        raise ValueError('Web 容器只允许站内路径')
    validated = _validate_host(remote_url)
    return f"{validated}{path}"


class WebContainerView(QWebEngineView):
    """Vue SPA 容器，通过 QWebChannel 与 Vue 通信"""

    def __init__(self, remote_url: str = None, parent=None):
        super().__init__(parent)
        if remote_url:
            # 显式传入的地址也走白名单校验
            try:
                self.remote_url = _validate_host(remote_url.rstrip('/'))
            except ValueError as e:
                raise ValueError(f'WebContainer 启动失败: {e}') from e
        else:
            # 从本地配置读取前端地址
            try:
                from config.local_settings_manager import get_frontend_url
                self.remote_url = _validate_host(get_frontend_url().rstrip('/'))
            except ValueError as e:
                raise ValueError(
                    f'WebContainer 配置非法: {e}。'
                    f'请在 local_settings.json 中将 frontend_url 设置为白名单内的地址。'
                ) from e
            except Exception as e:
                print(f"[WebContainer] 读取前端地址失败: {e}")
                # 兜底默认地址也走白名单校验（piapi.wakabashia.tj.cn 已在白名单内）
                self.remote_url = "https://piapi.wakabashia.tj.cn"

        print("[WebContainer] custom contextMenuEvent will suppress native menu")

        # 保留默认 page，但安装自定义 channel
        self.channel = QWebChannel(self)
        self.page().setWebChannel(self.channel)

        self._native_api = NativeAPI(self)
        self._native_bridge = NativeBridge(self._native_api)
        self.channel.registerObject('nativeBridge', self._native_bridge)

        self.load(QUrl(self.remote_url))

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        """吞掉 QWebEngineView 默认的 Chromium 右键菜单。

        不调用 super().contextMenuEvent()，从而不会弹出原生菜单，
        也不会阻止事件继续派发到 Chromium；Chromium 仍会在页面 JS 中
        触发 contextmenu 事件，前端 addEventListener('contextmenu', ...) 即可收到。
        """
        print(
            f"[WebContainer] contextMenuEvent suppressed at "
            f"{event.globalPos().x()},{event.globalPos().y()} reason={event.reason()}"
        )
        event.accept()

    def navigate_to(self, path: str):
        """路由跳转"""
        self.load(QUrl(build_web_url(self.remote_url, path)))

    def reload_current(self):
        """刷新当前页面"""
        self.reload()

    @property
    def native_bridge(self) -> NativeBridge:
        return self._native_bridge
