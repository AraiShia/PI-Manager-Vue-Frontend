# -*- coding: utf-8 -*-
"""数据库增量迁移管理器 (Migration Manager)

符合 Google 编程规范，包含详细的中文注释。
提供基于文件排他锁的防多进程重入锁，支持增量迁移、事务回滚与首次启动初始化。
"""

import os
import sys
import time
import logging
import importlib
from datetime import datetime
from sqlalchemy import text

# 将项目根目录添加到 sys.path 以方便加载 migrations 和 app 模块
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.database import engine, Base
import models  # 确保所有 SQLAlchemy 模型都被导入注册

# 设定日志输出
logger = logging.getLogger("migration_manager")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# 按时间/依赖顺序排列的增量迁移文件清单
MIGRATIONS = [
    ("1.0.0.1", "add_product_short_name"),
    ("1.0.0.2", "add_supplier_platform_fields"),
    ("1.0.0.3", "add_product_supplier_url"),
    ("1.0.0.4", "add_audit_log_table"),
    ("1.0.0.5", "add_pi_item_color"),
    ("1.0.0.6", "add_pi_item_company_code"),
    ("1.0.0.7", "add_pi_item_units_per_carton"),
    ("1.0.0.8", "add_pi_item_cartons_per_unit"),
    ("1.0.0.9", "add_pi_item_extra_fields"),
    ("1.0.0.10", "add_pi_item_labeling_fee"),
    ("1.0.0.11", "add_pi_item_profit_exchange"),
    ("1.0.0.12", "add_pi_item_inbound_records"),
    ("1.0.0.13", "add_purchase_snapshot_fields"),
    ("1.0.0.14", "sync_pi_payment_stages_to_receivables"),
    ("1.0.0.15", "repair_sup_supplier_primary_key"),
    ("1.0.0.16", "add_customer_reply_fields"),
    ("1.0.0.17", "expand_product_supplier_url_fields"),
]

# 最新代码版本对应的数据库版本
LATEST_VERSION = "1.0.0.17"


class FileLock:
    """基于操作系统原生文件描述符的排他锁，规避多进程并发执行冲突"""

    def __init__(self, lock_path: str):
        self.lock_path = lock_path
        self.handle = None

    def acquire(self) -> bool:
        """尝试获取锁，不阻塞，成功返回 True，被占用返回 False"""
        try:
            if os.name == "nt":
                import msvcrt
                # Windows 下打开文件并申请非阻塞排他锁
                self.handle = open(self.lock_path, "w")
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                # Unix/Mac 下申请非阻塞排他锁
                self.handle = open(self.lock_path, "w")
                fcntl.flock(self.handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except (IOError, OSError):
            if self.handle:
                try:
                    self.handle.close()
                except Exception:
                    pass
                self.handle = None
            return False

    def release(self):
        """释放文件锁并清理锁文件"""
        if self.handle:
            try:
                self.handle.close()
            except Exception:
                pass
            try:
                if os.path.exists(self.lock_path):
                    os.remove(self.lock_path)
            except Exception:
                pass
            self.handle = None


def parse_version(v_str: str) -> tuple[int, ...]:
    """将版本号字符串 (如 '1.0.0.16') 解析为整数元组 (如 (1, 0, 0, 16)) 用于精确比较"""
    try:
        return tuple(int(x) for x in v_str.split("."))
    except ValueError:
        return (0, 0, 0, 0)


class MigrationManager:
    """管理 SQLite 数据库迁移的核心类"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.lock_path = db_path + ".lock"
        self.lock = FileLock(self.lock_path)

    def table_exists(self, table_name: str) -> bool:
        """检查 SQLite 数据库中是否存在某张表"""
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name=:name"
        with engine.connect() as conn:
            result = conn.execute(text(query), {"name": table_name}).fetchone()
            return result is not None

    def has_any_tables(self) -> bool:
        """数据库是否已经存在任何业务表"""
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        with engine.connect() as conn:
            result = conn.execute(text(query)).fetchall()
            return len(result) > 0

    def init_schema_version_table(self):
        """初始化 schema 版本记录表"""
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS sys_schema_version (
                    version VARCHAR(50) PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

    def get_current_version(self) -> str:
        """获取当前数据库存储的 schema 版本号"""
        if not self.table_exists("sys_schema_version"):
            # 若不存在版本表，但存在其他业务表，说明是历史遗留的旧版数据库，基线设为 1.0.0.0
            if self.has_any_tables():
                logger.info("检测到旧版数据库但无版本记录表，设定基线版本为 1.0.0.0")
                self.init_schema_version_table()
                with engine.begin() as conn:
                    conn.execute(text(
                        "INSERT INTO sys_schema_version (version) VALUES ('1.0.0.0')"
                    ))
                return "1.0.0.0"
            else:
                # 纯新数据库，尚未创建任何表
                return "0.0.0.0"

        # 存在版本表，读取最新应用的版本
        query = "SELECT version FROM sys_schema_version ORDER BY applied_at DESC LIMIT 1"
        with engine.connect() as conn:
            result = conn.execute(text(query)).fetchone()
            return result[0] if result else "1.0.0.0"

    def update_version(self, version: str):
        """原子更新数据库的版本号"""
        with engine.begin() as conn:
            # 写入最新版本号
            conn.execute(
                text("INSERT OR REPLACE INTO sys_schema_version (version) VALUES (:v)"),
                {"v": version}
            )

    def run_migration_script(self, script_name: str) -> bool:
        """动态加载并执行迁移脚本的 upgrade 方法"""
        try:
            logger.info(f"正在执行迁移脚本: {script_name} ...")
            module = importlib.import_module(f"migrations.{script_name}")
            if hasattr(module, "upgrade"):
                module.upgrade()
                logger.info(f"迁移脚本 {script_name} 执行成功")
                return True
            else:
                logger.error(f"迁移脚本 {script_name} 中未找到 upgrade 方法")
                return False
        except Exception as e:
            logger.exception(f"执行迁移脚本 {script_name} 时发生异常: {str(e)}")
            return False

    def check_and_migrate(self):
        """执行检查并进行数据库升级的主函数 (防重入)"""
        # 1. 尝试获取跨进程文件锁，防并发重入
        max_retries = 5
        acquired = False
        for attempt in range(max_retries):
            if self.lock.acquire():
                acquired = True
                break
            logger.warning(f"数据库正在由其他进程执行迁移，等待 1 秒... (尝试 {attempt + 1}/{max_retries})")
            time.sleep(1.0)

        if not acquired:
            logger.error("无法获取数据库迁移排他锁，可能另一个进程正在迁移，跳过本次迁移。")
            return

        try:
            current_ver = self.get_current_version()
            logger.info(f"当前数据库版本: {current_ver}, 目标最新版本: {LATEST_VERSION}")

            # 2. 如果是全新安装（版本号为 0.0.0.0 且无任何表）
            if current_ver == "0.0.0.0":
                logger.info("检测到新数据库，开始首次安装建表...")
                # 创建所有模型定义的数据表
                Base.metadata.create_all(bind=engine)
                # 初始化版本记录表并直接设定为最新版本
                self.init_schema_version_table()
                self.update_version(LATEST_VERSION)
                logger.info(f"数据库初始化建表完成，当前版本标记为 {LATEST_VERSION}")
                return

            # 3. 增量迁移升级逻辑
            current_tuple = parse_version(current_ver)
            latest_tuple = parse_version(LATEST_VERSION)

            if current_tuple == latest_tuple:
                logger.info("数据库已是最新版本，无需升级。")
                return

            # 按照版本顺序寻找需执行的迁移
            for version, script in MIGRATIONS:
                version_tuple = parse_version(version)
                if version_tuple > current_tuple:
                    logger.info(f"开始升级至版本 {version} ({script})")
                    # 每个升级文件有其自身的 engine.begin() 事务保障
                    success = self.run_migration_script(script)
                    if success:
                        self.update_version(version)
                        logger.info(f"成功升级至版本 {version}")
                    else:
                        logger.error(f"升级至版本 {version} 失败，中断后续升级流程")
                        # 触发错误时应当退出，防止脏数据后续执行
                        raise RuntimeError(f"数据库迁移在 {version} 发生故障中断")

            logger.info("数据库所有增量迁移执行完毕")

        finally:
            # 释放排他锁
            self.lock.release()


def migrate():
    """外置调用接口"""
    # 提取 AppData 下的 pimain.db 绝对路径
    from app.database import get_data_dir
    db_path = os.path.join(get_data_dir(), "pimain.db")
    manager = MigrationManager(db_path)
    manager.check_and_migrate()


if __name__ == "__main__":
    migrate()
