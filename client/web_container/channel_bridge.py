"""QWebChannel Python 端：暴露 Native API 给 Vue"""
from PySide6.QtCore import QObject, Slot, Signal
from .native_api import NativeAPI


class NativeBridge(QObject):
    """通过 QWebChannel 暴露给 Vue 的 Python 对象"""

    # --- 文件操作 ---
    @Slot(str, result=str)
    def selectFile(self, filter_str: str) -> str:
        return self._api.select_file(filter_str)

    @Slot(str, result=str)
    def saveFile(self, default_name: str) -> str:
        return self._api.save_file(default_name)

    # --- Excel 操作（异步）---
    # 旧 readExcel 是阻塞调用，10w+ 行会冻结 WebChannel 线程。
    # 新 readExcel 立即返回 task_id，结果通过 excelReadComplete 信号回调。
    @Slot(str, result=str)
    def readExcel(self, file_path: str) -> str:
        """异步读取 Excel，立即返回 task_id。结果通过 excelReadComplete 信号返回。"""
        return self._api.read_excel_async(file_path)

    @Slot(str, list, result=bool)
    def writeExcel(self, file_path: str, data: list) -> bool:
        return self._api.write_excel(file_path, data)

    # --- 系统能力 ---
    @Slot(str)
    def showNotification(self, message: str):
        self._api.show_notification(message)

    @Slot(result=str)
    def getAppVersion(self) -> str:
        return self._api.get_app_version()

    @Slot(result=str)
    def getAppVersionName(self) -> str:
        return self._api.get_app_name()

    # --- 信号（Python → Vue） ---
    versionAvailable = Signal(str)
    fileSelected = Signal(str)
    # Excel 异步读取完成信号，参数为 dict: {task_id, ok, data, error}
    excelReadComplete = Signal('QVariant')

    def __init__(self, api: NativeAPI):
        super().__init__()
        self._api = api
        api.set_bridge(self)

    def emit_version_available(self, version: str):
        self.versionAvailable.emit(version)

    def emit_excel_read_complete(self, result: dict):
        self.excelReadComplete.emit(result)
