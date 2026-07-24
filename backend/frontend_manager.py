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

# ECDSA 公钥：优先从受保护文件路径读取（环境变量只能传文件路径，不能直接传 PEM 内容）。
# 生产环境：
#   1. 优先：PI_MANAGER_PUBLIC_KEY_FILE 环境变量指向磁盘上的受保护密钥文件
#   2. 兜底（同目录）：exe 同级 keys/public_key.pem（PyInstaller 打包后指向 _MEIPASS）
#   3. 以上均不存在时：抛出异常，阻止启动（生产环境必须有正式公钥）
#
# ⚠️ 不再支持 PI_MANAGER_PUBLIC_KEY_PEM 环境变量直接传 PEM 内容。
#    因为环境变量可被普通用户修改，攻击者可替换为自己的公钥从而签发恶意前端包。

def _load_public_key() -> bytes:
    import warnings

    # 优先从文件路径加载
    key_file = os.getenv("PI_MANAGER_PUBLIC_KEY_FILE", "").strip()
    if key_file:
        key_file = os.path.expandvars(key_file)  # 支持 %APPDATA%\xxx 或 $HOME/xxx
        if os.path.isfile(key_file):
            with open(key_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
            if "BEGIN PUBLIC KEY" in content:
                logger.info(f"[FrontendManager] ECDSA 公钥从文件加载: {key_file}")
                return content.encode("utf-8")
            else:
                raise ValueError(f"PI_MANAGER_PUBLIC_KEY_FILE 不是有效的公钥文件: {key_file}")

    # 兜底：exe 同级 keys/public_key.pem（PyInstaller 环境指向 _MEIPASS）
    base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
    fallback_key_file = os.path.join(base_dir, "keys", "public_key.pem")
    if os.path.isfile(fallback_key_file):
        with open(fallback_key_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if "BEGIN PUBLIC KEY" in content:
            logger.info(f"[FrontendManager] ECDSA 公钥从兜底文件加载: {fallback_key_file}")
            return content.encode("utf-8")

    # 以上均无：生产环境必须拒绝启动，开发/测试环境发警告
    import sys as _sys
    frozen = getattr(sys, 'frozen', False)
    if frozen:
        raise FileNotFoundError(
            "[安全错误] 生产环境缺少 ECDSA 公钥文件。"
            "请在 exe 同级创建 keys/public_key.pem，或设置 "
            "PI_MANAGER_PUBLIC_KEY_FILE 环境变量指向受保护路径。"
        )
    else:
        warnings.warn(
            "[安全警告] 未配置 ECDSA 公钥，使用测试公钥（不安全，勿用于生产）。"
            "请在 exe 同级创建 keys/public_key.pem，或设置 "
            "PI_MANAGER_PUBLIC_KEY_FILE 环境变量。",
            UserWarning,
        )
        return b"""-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE+smxcuJhzpE1i/5oxPAa5BmwefHr
2sX4o59kyVA+ZlH+/2NeU0llzDxKc0I5zi8vgNaC3IIKITyhPoHabJW52w==
-----END PUBLIC KEY-----"""


PUBLIC_KEY_PEM = _load_public_key()

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

    def _compare_versions(self, v1: str, v2: str) -> int:
        """比较两个语义化版本号，返回 -1/0/1。"""
        def normalize(ver: str) -> list:
            return [int(x) if x.isdigit() else 0 for x in ver.lstrip("v").split(".")]
        p1, p2 = normalize(v1), normalize(v2)
        max_len = max(len(p1), len(p2))
        p1 += [0] * (max_len - len(p1))
        p2 += [0] * (max_len - len(p2))
        for a, b in zip(p1, p2):
            if a < b:
                return -1
            if a > b:
                return 1
        return 0

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

    def update_frontend(self, manifest: Dict, current_app_version: str = "") -> bool:
        """从 Manifest 下载前端包，校验数字签名与包完整性后原子更新。

        Args:
            manifest: CDN version.json 内容（包含 version/dist_url/sha256/min_app_version/signature）。
            current_app_version: 当前 exe 版本号（如 "1.0.0.28"）。若不满足 min_app_version 则拒绝更新。
        """
        # 1. 安全验签
        if not self.verify_manifest_signature(manifest):
            logger.error("数字签名校验失败，停止下载更新")
            return False

        # 2. min_app_version 兼容性校验
        min_app_version = manifest.get("min_app_version", "")
        if current_app_version and min_app_version:
            if self._compare_versions(current_app_version, min_app_version) < 0:
                logger.error(
                    f"前端包要求最低 exe 版本 {min_app_version}，"
                    f"当前 exe 版本 {current_app_version} 不满足，拒绝激活。"
                )
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

            # 4. 解压至临时目录（路径穿越防护：逐成员校验路径合法性）
            logger.info("解压缩文件并验证完整性...")
            os.makedirs(temp_extract_dir, exist_ok=True)
            with zipfile.ZipFile(target_zip, "r") as zf:
                for member in zf.infolist():
                    member_path = os.path.abspath(os.path.join(temp_extract_dir, member.filename))
                    # 拒绝绝对路径或包含 .. 的成员，防止路径穿越攻击
                    if not member_path.startswith(os.path.abspath(temp_extract_dir) + os.sep):
                        raise ValueError(
                            f"ZIP 成员包含非法路径（路径穿越风险）: {member.filename}"
                        )
                    # 拒绝符号链接（S_IFLNK == 0o120000），防止解压后劫持路径
                    if (member.external_attr >> 28) == 0o12:
                        raise ValueError(f"ZIP 成员包含符号链接（不安全）: {member.filename}")
                    zf.extract(member, temp_extract_dir)

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
