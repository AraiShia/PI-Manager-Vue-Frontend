# 数据库连接和会话管理模块
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base  # SQLAlchemy 2.0+ 推荐的导入方式
import os
import sys

def get_data_dir():
    """获取数据目录 - 统一使用 APPDATA 下的目录，避免权限限制"""
    env_data_dir = os.environ.get('PI_MANAGER_DATA_DIR')
    if env_data_dir:
        os.makedirs(env_data_dir, exist_ok=True)
        return env_data_dir
        
    # 获取 Windows AppData 目录，若非 Windows 则回退至用户家目录
    app_data = os.environ.get('APPDATA')
    if not app_data:
        app_data = os.path.expanduser('~')
        
    data_dir = os.path.join(app_data, 'PIManager', 'data')
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

data_dir = get_data_dir()

# 使用 SQLite 本地文件数据库
SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(data_dir, 'pimain.db')}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """FastAPI 依赖注入，用于获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()