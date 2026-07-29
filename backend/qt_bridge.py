# -*- coding: utf-8 -*-
"""PyQt5 与前端 QWebChannel 通信的桥接层 (Qt Bridge)

符合 Google 编程规范，包含详细的中文注释。
提供统一的 JSON-RPC 路由分发槽方法 call()，以及页面重载槽方法 trigger_refresh()。
"""

import json
import logging
from typing import Any, Optional, cast

try:
    from PySide6.QtCore import QObject, Slot as pyqtSlot, Signal as pyqtSignal, QUrl
except ImportError:
    try:
        from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal, QUrl
    except ImportError:
        # 为静态类型检查器及无 GUI 依赖的环境提供标准 Stub
        class QObject:  # type: ignore
            pass

        def pyqtSlot(*args: Any, **kwargs: Any) -> Any:  # type: ignore
            return lambda f: f

        class pyqtSignal:  # type: ignore
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                pass

            def emit(self, *args: Any, **kwargs: Any) -> None:
                pass

        class QUrl:  # type: ignore
            @staticmethod
            def fromLocalFile(path: str) -> Any:
                return path

# 载入 SQLAlchemy 局部会话
from app.database import SessionLocal

# 载入供应商 CRUD 逻辑
from crud.supplier import (
    get_suppliers,
    create_supplier,
    update_supplier,
    delete_supplier,
    find_or_create_supplier_by_name,
)

# 载入数据验证 Schema
from schemas.supplier import SupplierCreate, SupplierUpdate, SupplierResponse

# 载入地区数据解析方法
from region_data import get_all_provinces, get_cities_by_province

logger = logging.getLogger("qt_bridge")


class QtBridge(QObject):
    """QWebChannel 桥接类，供前端进行安全调用与数据交互"""

    # 信号定义：用于主动通知前端
    version_available = pyqtSignal(str)          # 新版本可用信号
    network_status_changed = pyqtSignal(bool)   # 联网状态变更信号

    def __init__(self, view=None, frontend_manager=None):
        """构造函数
        
        Args:
            view: PyQt5 中的 QWebEngineView 实例，用于页面跳转
            frontend_manager: FrontendManager 实例，用于读取最新前端入口路径
        """
        super().__init__()
        self.view = view
        self.frontend_manager = frontend_manager

    @pyqtSlot(str, str, result=str)
    def call(self, method: str, params_json: str) -> str:
        """统一 JSON-RPC 通信终结点。
        
        解析方法名和 JSON 参数串，执行相应业务逻辑，并返回统一的 JSON 结构。
        
        Args:
            method: 远程方法标识符，如 "suppliers.list"
            params_json: 客户端传参经过 JSON 序列化后的字符串
            
        Returns:
            str: 格式为 {"success": bool, "data": any, "error": str} 的 JSON 串
        """
        logger.info(f"[RPC Call] Method={method}, Params={params_json}")
        
        try:
            params: dict[str, Any] = json.loads(params_json) if params_json else {}
        except Exception as e:
            logger.error(f"解析参数 JSON 失败: {e}")
            return json.dumps({
                "success": False,
                "data": None,
                "error": f"JSON 参数解析失败: {str(e)}"
            }, ensure_ascii=False)

        db = SessionLocal()
        try:
            # 1. 查询供应商列表
            if method == "suppliers.list":
                skip = int(params.get("skip", 0))
                limit = int(params.get("limit", 20))
                raw_kw = params.get("keyword")
                keyword: Optional[str] = str(raw_kw) if raw_kw is not None else None
                
                suppliers_list = get_suppliers(db, skip=skip, limit=limit, keyword=keyword)
                return json.dumps({
                    "success": True,
                    "data": suppliers_list,
                    "error": None
                }, ensure_ascii=False)

            # 2. 新增供应商
            elif method == "suppliers.create":
                payload = SupplierCreate.model_validate(params)
                dept_id = str(params.get("dept_id") or "S")
                db_supplier = create_supplier(db, payload, dept_id=dept_id)
                if not db_supplier:
                    return json.dumps({
                        "success": False,
                        "data": None,
                        "error": "创建供应商失败"
                    }, ensure_ascii=False)
                
                # 使用 Pydantic SupplierResponse 完整序列化，包含联系人与扩展属性
                data = SupplierResponse.model_validate(db_supplier).model_dump(mode="json")
                return json.dumps({
                    "success": True,
                    "data": data,
                    "error": None
                }, ensure_ascii=False)

            # 3. 采购自动创建或关联供应商
            elif method == "suppliers.findOrCreate":
                supplier_name_val = params.get("supplier_name")
                platform_val = params.get("platform")
                dept_id_val = str(params.get("dept_id") or "S")
                
                if not supplier_name_val or not str(supplier_name_val).strip():
                    return json.dumps({
                        "success": False,
                        "data": None,
                        "error": "供应商名称（supplier_name）不能为空"
                    }, ensure_ascii=False)
                
                supplier_name = str(supplier_name_val).strip()
                platform = str(platform_val).strip() if platform_val else ""

                if platform not in ("1688", "wechat", "offline"):
                    return json.dumps({
                        "success": False,
                        "data": None,
                        "error": "无效的供应商平台分类（platform）"
                    }, ensure_ascii=False)

                contact_person = str(params.get("contact_person")) if params.get("contact_person") is not None else None
                phone = str(params.get("phone")) if params.get("phone") is not None else None
                address = str(params.get("address")) if params.get("address") is not None else None
                wechat_id = str(params.get("wechat_id")) if params.get("wechat_id") is not None else None
                wechat_nickname = str(params.get("wechat_nickname")) if params.get("wechat_nickname") is not None else None
                is_dropship = bool(params.get("is_dropship")) if params.get("is_dropship") is not None else None

                result = find_or_create_supplier_by_name(
                    db,
                    supplier_name=supplier_name,
                    platform=platform,
                    dept_id=dept_id_val,
                    contact_person=contact_person,
                    phone=phone,
                    address=address,
                    wechat_id=wechat_id,
                    wechat_nickname=wechat_nickname,
                    is_dropship=is_dropship,
                )
                if not result:
                    return json.dumps({
                        "success": False,
                        "data": None,
                        "error": "查找或创建供应商数据层失败"
                    }, ensure_ascii=False)

                new_supplier, created = result
                supplier_dict = SupplierResponse.model_validate(new_supplier).model_dump(mode="json")
                supplier_dict["created"] = created
                return json.dumps({
                    "success": True,
                    "data": supplier_dict,
                    "error": None
                }, ensure_ascii=False)

            # 4. 获取省份清单
            elif method == "suppliers.getProvinces":
                provinces = get_all_provinces()
                return json.dumps({
                    "success": True,
                    "data": provinces,
                    "error": None
                }, ensure_ascii=False)

            # 5. 获取城市清单
            elif method == "suppliers.getCities":
                raw_province = params.get("province", "")
                province = str(raw_province) if raw_province is not None else ""
                cities = get_cities_by_province(province)
                return json.dumps({
                    "success": True,
                    "data": cities,
                    "error": None
                }, ensure_ascii=False)

            # 6. 更新供应商
            elif method == "suppliers.update":
                id_val = params.get("id")
                if not id_val:
                    return json.dumps({
                        "success": False,
                        "data": None,
                        "error": "缺失要更新的供应商 ID"
                    }, ensure_ascii=False)

                # 将 ID 过滤后，其余参数打包成 Schema 校验
                update_params = {k: v for k, v in params.items() if k != "id"}
                payload = SupplierUpdate.model_validate(update_params)
                db_supplier = update_supplier(db, int(id_val), payload)
                
                if not db_supplier:
                    return json.dumps({
                        "success": False,
                        "data": None,
                        "error": f"未找到 ID 为 {id_val} 的供应商"
                    }, ensure_ascii=False)
                
                # 使用 Pydantic SupplierResponse 完整序列化，包含联系人与扩展属性
                data = SupplierResponse.model_validate(db_supplier).model_dump(mode="json")
                return json.dumps({
                    "success": True,
                    "data": data,
                    "error": None
                }, ensure_ascii=False)

            # 7. 删除供应商
            elif method == "suppliers.delete":
                id_val = params.get("id")
                if not id_val:
                    return json.dumps({
                        "success": False,
                        "data": None,
                        "error": "缺失要删除的供应商 ID"
                    }, ensure_ascii=False)

                success = delete_supplier(db, int(id_val))
                return json.dumps({
                    "success": True,
                    "data": success,
                    "error": None
                }, ensure_ascii=False)

            # 8. 产品-供应商-URL 列表
            elif method == "productSupplierUrls.list":
                from crud.product_supplier_url import list_urls
                product_id = params.get("product_id")
                supplier_id = params.get("supplier_id")
                raw_supplier_name = params.get("supplier_name")
                supplier_name = str(raw_supplier_name) if raw_supplier_name is not None else None

                if not product_id:
                    return json.dumps({
                        "success": False,
                        "data": None,
                        "error": "product_id 为必填参数"
                    }, ensure_ascii=False)
                urls = list_urls(
                    db,
                    product_id=int(product_id),
                    supplier_id=int(supplier_id) if supplier_id else None,
                    supplier_name=supplier_name,
                )
                return json.dumps({
                    "success": True,
                    "data": [{
                        "id": u.id,
                        "product_id": u.product_id,
                        "supplier_id": u.supplier_id,
                        "supplier_name": u.supplier_name,
                        "url": u.url,
                        "display_name": u.display_name,
                        "is_default": u.is_default,
                        "created_at": str(u.created_at) if u.created_at else None
                    } for u in urls],
                    "error": None
                }, ensure_ascii=False)

            # 9. 产品-供应商-URL 新增
            elif method == "productSupplierUrls.create":
                from schemas.product_supplier_url import ProductSupplierUrlCreate
                from crud.product_supplier_url import create_url
                payload = ProductSupplierUrlCreate.model_validate(params)
                url_obj, created = create_url(db, payload)
                db.commit()
                data = {
                    "id": url_obj.id,
                    "product_id": url_obj.product_id,
                    "supplier_id": url_obj.supplier_id,
                    "supplier_name": url_obj.supplier_name,
                    "url": url_obj.url,
                    "display_name": url_obj.display_name,
                    "is_default": url_obj.is_default,
                    "created_at": str(url_obj.created_at) if url_obj.created_at else None,
                }
                return json.dumps({
                    "success": True,
                    "data": data,
                    "error": None,
                    "created": created
                }, ensure_ascii=False)

            # 10. PI 发票列表
            elif method == "pi.list":
                from crud.pi import get_pi_invoices_with_customer
                skip = params.get("skip", 0)
                limit = params.get("limit", 20)
                raw_status = params.get("status")
                status = int(raw_status) if raw_status is not None else None
                records = get_pi_invoices_with_customer(
                    db,
                    skip=int(skip),
                    limit=int(limit),
                    status=status
                )
                return json.dumps({
                    "success": True,
                    "data": records,
                    "error": None
                }, ensure_ascii=False)

            # 11. 1688 线上采购创建桩 (Stub)
            elif method == "purchase.createOnline":
                return json.dumps({
                    "success": False,
                    "data": None,
                    "error": "线上采购功能需要在 local-online 或 remote-web 模式下使用远程 API 执行"
                }, ensure_ascii=False)

            # 12. 客户列表
            elif method == "customer.list":
                from crud.customer import get_customers
                skip = params.get("skip", 0)
                limit = params.get("limit", 20)
                customers = get_customers(db, skip=int(skip), limit=int(limit))
                return json.dumps({
                    "success": True,
                    "data": [{
                        "id": c.id,
                        "customer_code": c.customer_code,
                        "customer_name": c.customer_name,
                        "country": c.country,
                        "dept_id": c.dept_id,
                        "created_at": str(c.created_at) if hasattr(c, "created_at") else None
                    } for c in customers],
                    "error": None
                }, ensure_ascii=False)

            else:
                logger.error(f"未知的 RPC 方法调用: {method}")
                return json.dumps({
                    "success": False,
                    "data": None,
                    "error": f"未定义此端点的离线桥接映射: {method}"
                }, ensure_ascii=False)

        except Exception as e:
            logger.exception(f"执行 RPC 发生异常: {str(e)}")
            return json.dumps({
                "success": False,
                "data": None,
                "error": f"内部异常错误: {str(e)}"
            }, ensure_ascii=False)
        finally:
            db.close()

    @pyqtSlot(result=str)
    def get_app_version(self) -> str:
        """获取本地 exe 版本号"""
        return "1.0.0.0"

    def emit_version_available(self, version: str):
        """向前端发射新版本可用信号
        
        Args:
            version: 可用的前端新版本号
        """
        logger.info(f"[QtBridge] 发现前端新版本: {version}，准备发射信号给 JS")
        if hasattr(self.version_available, "emit"):
            self.version_available.emit(version)

    @pyqtSlot(result=str)
    def trigger_refresh(self) -> str:
        """前端检测到更新后，主动通知 PyQt5 壳子重新加载新版本的 index.html"""
        logger.info("[QtBridge] trigger_refresh 槽函数被触发")
        if self.view and self.frontend_manager:
            try:
                new_index_path = self.frontend_manager.get_active_index_path()
                logger.info(f"[QtBridge] 重新加载目标 file 路径: {new_index_path}")
                # 使用 QUrl.fromLocalFile 加载本地物理文件，规避 file:// 路径名转义问题
                self.view.setUrl(QUrl.fromLocalFile(new_index_path))
                return json.dumps({
                    "success": True,
                    "data": "ok",
                    "error": None
                })
            except Exception as e:
                logger.error(f"[QtBridge] 重新加载失败: {e}")
                return json.dumps({
                    "success": False,
                    "data": None,
                    "error": f"重新定向失败: {str(e)}"
                })
        return json.dumps({
            "success": False,
            "data": None,
            "error": "PyQt5 QWebEngineView 视图未注入"
        })
