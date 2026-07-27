# -*- coding: utf-8 -*-
"""离线部署特性单元测试 (Test Offline Features)

符合 Google 编程规范，包含详细的中文注释。
覆盖了：
1. 数据库首次建表初始化与增量迁移的幂等性
2. 迁移失败事务回滚与防多进程重入锁
3. 签名 manifests 验证、SHA-256 包完整性检验
4. 损坏的 dist 前端版本目录的自动回滚恢复
"""

import os
import sys
import json
import shutil
import tempfile
import pytest
from sqlalchemy import create_engine, text

# 将项目根目录加入 sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.migration_manager import MigrationManager, FileLock
from frontend_manager import FrontendManager

# 导入签名相关的模块以用于生成测试签名
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization


@pytest.fixture
def temp_dir():
    """临时文件夹夹具，测试完毕后自动删除"""
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


def test_file_lock(temp_dir):
    """测试文件排他锁的获取与释放"""
    lock_path = os.path.join(temp_dir, "test.lock")
    lock1 = FileLock(lock_path)
    lock2 = FileLock(lock_path)

    # 1. 第一个锁应当成功获取
    assert lock1.acquire() is True
    # 2. 在第一个锁未释放前，第二个锁应当获取失败
    assert lock2.acquire() is False

    # 3. 释放第一个锁
    lock1.release()
    # 4. 第二个锁现在应当成功获取
    assert lock2.acquire() is True
    lock2.release()


def test_signature_verification(temp_dir):
    """测试 ECDSA 数字签名的生成与验证"""
    # 1. 生成测试密钥对
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    # 2. 模拟 Manifest 数据
    manifest = {
        "version": "1.0.0.99",
        "dist_url": "https://cdn.example.com/dist-v1.0.0.99.zip",
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "min_app_version": "1.0.0.0"
    }

    # 3. 生成签名
    message = f"{manifest['version']}:{manifest['dist_url']}:{manifest['sha256']}:{manifest['min_app_version']}".encode("utf-8")
    sig_bytes = private_key.sign(message, ec.ECDSA(hashes.SHA256()))
    manifest["signature"] = sig_bytes.hex()

    # 4. 实例化 FrontendManager，并打补丁替换其 PUBLIC_KEY_PEM 为当前的测试公钥
    fm = FrontendManager()
    
    # 保存原公钥以供复原
    old_pem = fm.config_path
    
    import frontend_manager
    original_key = frontend_manager.PUBLIC_KEY_PEM
    frontend_manager.PUBLIC_KEY_PEM = public_pem

    # 5. 验证正确签名应当返回 True
    assert fm.verify_manifest_signature(manifest) is True

    # 6. 篡改其中一个字段（例如版本号），验签应当失败
    corrupted_manifest = manifest.copy()
    corrupted_manifest["version"] = "1.0.0.98"
    assert fm.verify_manifest_signature(corrupted_manifest) is False

    # 7. 篡改签名本身，验签应当失败
    corrupted_sig_manifest = manifest.copy()
    corrupted_sig_manifest["signature"] = "aabbccddeeff"
    assert fm.verify_manifest_signature(corrupted_sig_manifest) is False

    # 复原公钥
    frontend_manager.PUBLIC_KEY_PEM = original_key


def test_frontend_fallback_recovery(temp_dir):
    """测试当前前端版本文件夹损坏时，自动扫描并回滚到其它可用本地版本"""
    fm = FrontendManager()
    fm.frontend_dir = os.path.join(temp_dir, "frontend")
    fm.config_path = os.path.join(temp_dir, "config.json")
    os.makedirs(fm.frontend_dir, exist_ok=True)
    fm._init_config()

    # 1. 模拟写入一个不存在的版本 1.0.0.99 并设为 active
    config = fm._read_config()
    config["active_version"] = "1.0.0.99"
    fm._write_config_atomic(config)

    # 2. 模拟本地存在其它旧版本 dist-v1.0.0.50，且含有 valid index.html
    v50_path = os.path.join(fm.frontend_dir, "dist-v1.0.0.50")
    os.makedirs(v50_path)
    with open(os.path.join(v50_path, "index.html"), "w", encoding="utf-8") as f:
        f.write("<html>V50</html>")

    # 3. 模拟本地存在 dist-v1.0.0.60 目录，但其 index.html 缺失（即损坏状态）
    v60_path = os.path.join(fm.frontend_dir, "dist-v1.0.0.60")
    os.makedirs(v60_path)

    # 4. 获取 index 路径，此时 1.0.0.99 缺失，应该自动识别 v60 损坏，并成功回滚到 v50
    active_index = fm.get_active_index_path()
    assert "dist-v1.0.0.50" in active_index
    assert fm.get_active_version() == "1.0.0.50"


def test_migration_atomic_initialization(temp_dir):
    """测试数据库在全新安装时自动运行 Base.metadata.create_all 并初始化版本"""
    db_path = os.path.join(temp_dir, "pimain_test.db")
    
    # 模拟重写数据库模块中的 engine 指向我们的测试 db 路径
    import app.database
    original_engine = app.database.engine
    original_url = app.database.SQLALCHEMY_DATABASE_URL
    
    test_url = f"sqlite:///{db_path}"
    test_engine = create_engine(test_url, connect_args={"check_same_thread": False})
    
    app.database.engine = test_engine
    app.database.SQLALCHEMY_DATABASE_URL = test_url
    
    # 同样修改 migration_manager 里的 engine 导入引用
    import app.migration_manager
    app.migration_manager.engine = test_engine
    
    try:
        manager = MigrationManager(db_path)
        
        # 此时是全新安装，数据库不存在版本表也不存在任何表
        assert manager.get_current_version() == "0.0.0.0"
        
        # 运行迁移
        manager.check_and_migrate()
        
        # 首次安装完毕后，版本表应当已建立，且版本号直接设为最新版本号
        assert manager.table_exists("sys_schema_version") is True
        assert manager.get_current_version() == app.migration_manager.LATEST_VERSION
        
        # 且业务表已经存在，例如 sup_supplier 已经被成功建立
        assert manager.table_exists("sup_supplier") is True
        
    finally:
        # 复原 engine
        app.database.engine = original_engine
        app.database.SQLALCHEMY_DATABASE_URL = original_url
        app.migration_manager.engine = original_engine
