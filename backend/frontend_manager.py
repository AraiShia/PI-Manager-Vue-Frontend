# -*- coding: utf-8 -*-
"""前端包热更新与安全管理器 (Frontend Manager)

符合 Google 编程规范，包含详细的中文注释。
提供安全的文件下载、ECDSA 签名校验、SHA-256 完整性检验、临时目录原子替换以及损坏回滚能力。
"""

import os
import sys
import json
import hashlib
import zipfile
import shutil
import logging
import urllib.request
from typing import Dict, List, Optional

# 使用 cryptography 进行签名验证
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.exceptions import InvalidSignature

# 将项目根目录添加到 sys.path 以加载 app.database 等模块
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.database import get_data_dir

logger = logging.getLogger("frontend_manager")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ECDSA 公钥：优先从环境变量读取，避免硬编码在代码中
# 用法：set PI_MANAGER_PUBLIC_KEY_PEM=-----BEGIN PUBLIC KEY-----\nMFkw...\n-----END PUBLIC KEY-----
# Windows PowerShell: $env:PI_MANAGER_PUBLIC_KEY_PEM="-----BEGIN PUBLIC KEY-----`nMFkw...`n-----END PUBLIC KEY-----"
_PUBLIC_KEY_PEM_ENV = os.getenv("PI_MANAGER_PUBLIC_KEY_PEM", "").replace("\\n", "\n")
if _PUBLIC_KEY_PEM_ENV:
    PUBLIC_KEY_PEM = _PUBLIC_KEY_PEM_ENV.encode("utf-8")
else:
    # 测试/开发环境使用默认密钥，但明确警告不安全
    import warnings
    warnings.warn(
        "[安全警告] PI_MANAGER_PUBLIC_KEY_PEM 未设置，使用测试公钥！"
        "生产部署必须通过环境变量配置正式的 ECDSA 公钥。",
        UserWarning,
    )
    PUBLIC_KEY_PEM = b"""-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE+smxcuJhzpE1i/5oxPAa5BmwefHr
2sX4o59kyVA+ZlH+/2NeU0llzDxKc0I5zi8vgNaC3IIKITyhPoHabJW52w==
-----END PUBLIC KEY-----"""

# 基线/初始版本号
BASELINE_VERSION = "1.0.0.0"


class FrontendManager:
    """管理前端资源文件的下载、校验、原子解压及版本控制"""

    def __init__(self):
        # 统一存放在 APPDATA 路径下，避免权限限制
        self.app_dir = os.path.dirname(get_data_dir()) # 获取 PIManager 目录
        self.frontend_dir = os.path.join(self.app_dir, "frontend")
        self.config_path = os.path.join(self.app_dir, "config.json")
        
        # 创建前端管理根目录
        os.makedirs(self.frontend_dir, exist_ok=True)
        self._init_config()

    def _init_config(self):
        """初始化配置文件 config.json"""
        if not os.path.exists(self.config_path):
            default_config = {
                "active_version": BASELINE_VERSION,
                "installed_versions": [BASELINE_VERSION]
            }
            self._write_config_atomic(default_config)

    def _read_config(self) -> Dict:
        """安全读取配置文件"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"读取 config.json 失败，返回默认配置: {e}")
            return {
                "active_version": BASELINE_VERSION,
                "installed_versions": [BASELINE_VERSION]
            }

    def _write_config_atomic(self, config_data: Dict):
        """原子写入配置文件，防止半路写入断电/崩溃损坏文件"""
        temp_path = self.config_path + ".tmp"
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            # 原子替换文件
            os.replace(temp_path, self.config_path)
        except Exception as e:
            logger.error(f"原子写入 config.json 失败: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def get_active_version(self) -> str:
        """获取当前配置的主动生效版本"""
        config = self._read_config()
        return config.get("active_version", BASELINE_VERSION)

    def get_active_index_path(self) -> str:
        """获取当前应当被加载的前端 index.html 绝对路径，如果不存在则退回内置兜底"""
        active_ver = self.get_active_version()
        index_path = os.path.join(self.frontend_dir, f"dist-v{active_ver}", "index.html")

        if os.path.exists(index_path):
            return index_path

        # 损坏回滚：当前 active_version 对应的目录不存在或损坏，扫描本地已有版本
        logger.warning(f"当前版本目录 dist-v{active_ver} 损坏或不存在，执行自动恢复扫描...")
        valid_version = self.recover_valid_version()
        if valid_version:
            logger.info(f"成功恢复至可用的本地最高版本: {valid_version}")
            return os.path.join(self.frontend_dir, f"dist-v{valid_version}", "index.html")

        # 最终兜底：如果是 PyInstaller 打包状态，使用内置的 frontend_dist 兜底
        if getattr(sys, "frozen", False):
            meipass_dist = os.path.join(sys._MEIPASS, "frontend_dist", "index.html")
            if os.path.exists(meipass_dist):
                logger.info("加载 EXE 内置兜底前端资源")
                return meipass_dist

        # 源码运行状态下，返回本地开发的 index.html
        source_dist = os.path.join(os.path.dirname(self.app_dir), "frontend", "dist", "index.html")
        if os.path.exists(source_dist):
            return source_dist

        raise FileNotFoundError("无法定位任何有效的前端 index.html 文件！")

    def recover_valid_version(self) -> Optional[str]:
        """扫描本地所有 dist-v* 文件夹，选出包含 valid index.html 的最新版本并更新 config"""
        installed = []
        if os.path.exists(self.frontend_dir):
            for name in os.listdir(self.frontend_dir):
                if name.startswith("dist-v"):
                    ver = name[6:]
                    idx_path = os.path.join(self.frontend_dir, name, "index.html")
                    if os.path.exists(idx_path):
                        installed.append(ver)

        if not installed:
            return None

        # 简单的按版本号字符串排序，选出最新的一个
        installed.sort(key=lambda s: list(map(int, s.split('.'))) if s.replace('.', '').isdigit() else s)
        newest_ver = installed[-1]

        # 更新配置
        config = self._read_config()
        config["active_version"] = newest_ver
        config["installed_versions"] = installed
        self._write_config_atomic(config)
        return newest_ver

    def verify_manifest_signature(self, manifest: Dict) -> bool:
        """验证自 CDN 下载的 version.json 的数字签名是否合法"""
        try:
            # 提取参与签名的核心字段
            version = manifest.get("version")
            dist_url = manifest.get("dist_url")
            sha256 = manifest.get("sha256")
            min_app_version = manifest.get("min_app_version")
            signature = manifest.get("signature")

            if not all([version, dist_url, sha256, min_app_version, signature]):
                logger.error("Manifest 校验字段缺失")
                return False

            # 重组待签名字节数组，必须与签署端算法严格保持一致
            message = f"{version}:{dist_url}:{sha256}:{min_app_version}".encode("utf-8")
            sig_bytes = bytes.fromhex(signature)

            # 加载硬编码公钥并执行 ECDSA-SHA256 验签
            public_key = serialization.load_pem_public_key(PUBLIC_KEY_PEM)
            public_key.verify(sig_bytes, message, ec.ECDSA(hashes.SHA256()))
            return True
        except InvalidSignature:
            logger.error("数字签名非法，Manifest 被篡改或源不可信！")
            return False
        except Exception as e:
            logger.error(f"Manifest 数字签名验证异常: {e}")
            return False

    def verify_file_sha256(self, file_path: str, expected_sha256: str) -> bool:
        """验证下载的 ZIP 包的 SHA-256 完整性"""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            calc_hash = sha256_hash.hexdigest()
            if calc_hash.lower() == expected_sha256.lower():
                return True
            logger.error(f"SHA-256 校验失败: 计算={calc_hash}, 预期={expected_sha256}")
            return False
        except Exception as e:
            logger.error(f"计算 SHA-256 时发生异常: {e}")
            return False

    def ensure_baseline_frontend(self):
        """若 APPDATA 中没有任何前端包，且为打包状态，将内置前端包释放到本地作为基线版本"""
        baseline_path = os.path.join(self.frontend_dir, f"dist-v{BASELINE_VERSION}")
        if not os.path.exists(os.path.join(baseline_path, "index.html")):
            if getattr(sys, "frozen", False):
                meipass_dist = os.path.join(sys._MEIPASS, "frontend_dist")
                if os.path.exists(meipass_dist):
                    logger.info("初始化释放内置前端资源到 AppData 基线版本...")
                    try:
                        shutil.copytree(meipass_dist, baseline_path, dirs_exist_ok=True)
                        logger.info("基线前端资源释放成功")
                    except Exception as e:
                        logger.error(f"释放基线前端资源失败: {e}")

    def update_frontend(self, manifest: Dict) -> bool:
        """从 Manifest 下载前端包，校验数字签名与包完整性后原子更新"""
        # 1. 安全验签
        if not self.verify_manifest_signature(manifest):
            logger.error("数字签名校验失败，停止下载更新")
            return False

        version = manifest["version"]
        dist_url = manifest["dist_url"]
        expected_sha256 = manifest["sha256"]

        # 如果已经是当前版本，跳过下载
        if version == self.get_active_version():
            logger.info("本地已运行最新版本，无需下载")
            return True

        target_zip = os.path.join(self.app_dir, "temp_download.zip")
        temp_extract_dir = os.path.join(self.frontend_dir, f"temp_extract_{version}")
        final_dir = os.path.join(self.frontend_dir, f"dist-v{version}")

        # 清除残留文件/目录
        if os.path.exists(target_zip):
            os.remove(target_zip)
        if os.path.exists(temp_extract_dir):
            shutil.rmtree(temp_extract_dir)

        try:
            # 2. 下载 ZIP 包
            logger.info(f"正在从 {dist_url} 下载新版本前端包...")
            urllib.request.urlretrieve(dist_url, target_zip)

            # 3. 校验包完整性
            if not self.verify_file_sha256(target_zip, expected_sha256):
                raise RuntimeError("下载包 SHA-256 校验失败")

            # 4. 解压至临时目录
            logger.info("解压缩文件并验证完整性...")
            with zipfile.ZipFile(target_zip, "r") as zf:
                zf.extractall(temp_extract_dir)

            # 验证解压产物中是否包含 index.html 核心入口
            if not os.path.exists(os.path.join(temp_extract_dir, "index.html")):
                raise RuntimeError("解压文件损坏，未找到 index.html 入口")

            # 5. 原子替换：将临时解压目录重命名为正式版本目录
            if os.path.exists(final_dir):
                shutil.rmtree(final_dir)
            os.rename(temp_extract_dir, final_dir)

            # 6. 原子更新 config.json
            config = self._read_config()
            config["active_version"] = version
            if version not in config["installed_versions"]:
                config["installed_versions"].append(version)
            self._write_config_atomic(config)

            logger.info(f"前端包已成功安全更新至版本: {version}")

            # 7. 异步/延迟清理旧版本目录，保留最新 3 个版本
            self._cleanup_old_versions()
            return True

        except Exception as e:
            logger.error(f"下载/更新前端包发生错误: {e}")
            # 清理垃圾
            if os.path.exists(temp_extract_dir):
                shutil.rmtree(temp_extract_dir)
            if os.path.exists(final_dir) and not os.path.exists(os.path.join(final_dir, "index.html")):
                shutil.rmtree(final_dir)
            return False
        finally:
            if os.path.exists(target_zip):
                os.remove(target_zip)

    def _cleanup_old_versions(self):
        """自动清理旧版本包，仅保留最新的 3 个已安装版本，防硬盘过度膨胀"""
        config = self._read_config()
        installed: List[str] = config.get("installed_versions", [])
        active_ver = config.get("active_version", BASELINE_VERSION)

        if len(installed) <= 3:
            return

        # 排序版本
        installed.sort(key=lambda s: list(map(int, s.split('.'))) if s.replace('.', '').isdigit() else s)
        
        # 找出需要删除的版本（但绝不能删除当前激活的版本）
        to_remove = []
        for v in installed:
            if v != active_ver and v != BASELINE_VERSION: # 保留基线和当前激活的
                to_remove.append(v)
                if len(installed) - len(to_remove) <= 3:
                    break

        for v in to_remove:
            logger.info(f"清理旧版本前端包: dist-v{v}")
            dir_path = os.path.join(self.frontend_dir, f"dist-v{v}")
            if os.path.exists(dir_path):
                try:
                    shutil.rmtree(dir_path)
                except Exception as e:
                    logger.error(f"清理文件夹 {dir_path} 失败: {e}")
            
            if v in installed:
                installed.remove(v)

        config["installed_versions"] = installed
        self._write_config_atomic(config)
