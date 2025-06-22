# -*- coding: utf-8 -*-
"""
集中配置管理系统
"""
import os
import json
import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, field
from .interfaces import IConfigService
from .exceptions import ConfigurationError

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """数据库配置"""
    url: str = ""
    pool_size: int = 10
    max_overflow: int = 20
    pool_recycle: int = 3600
    echo: bool = False
    
    def __post_init__(self):
        if not self.url:
            # 根据环境自动生成数据库URL
            if os.environ.get('FLASK_ENV') == 'production':
                # 生产环境使用PostgreSQL
                host = os.environ.get('POSTGRES_HOST', 'localhost')
                port = os.environ.get('POSTGRES_PORT', '5432')
                db = os.environ.get('POSTGRES_DB', 'chat_ai')
                user = os.environ.get('POSTGRES_USER', 'postgres')
                password = os.environ.get('POSTGRES_PASSWORD', '')
                
                if password:
                    self.url = f"postgresql://{user}:{password}@{host}:{port}/{db}"
                else:
                    # 生产环境必须有密码
                    raise ConfigurationError("生产环境必须设置数据库密码")
            else:
                # 开发环境使用SQLite
                db_path = Path.cwd() / 'data' / 'chat_ai.db'
                db_path.parent.mkdir(exist_ok=True)
                self.url = f"sqlite:///{db_path}"


@dataclass
class RedisConfig:
    """Redis配置"""
    url: str = "redis://localhost:6379/0"
    decode_responses: bool = True
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    retry_on_timeout: bool = True
    health_check_interval: int = 30
    
    def __post_init__(self):
        if not self.url or self.url == "redis://localhost:6379/0":
            # 从环境变量获取Redis配置
            self.url = os.environ.get('REDIS_URL', self.url)


@dataclass
class SecurityConfig:
    """安全配置"""
    secret_key: str = ""
    session_timeout: int = 3600
    max_login_attempts: int = 5
    login_attempt_timeout: int = 900
    password_min_length: int = 8
    password_require_special: bool = True
    allowed_origins: list = field(default_factory=list)
    
    def __post_init__(self):
        if not self.secret_key:
            self.secret_key = os.environ.get('SECRET_KEY')
            if not self.secret_key:
                if os.environ.get('FLASK_ENV') == 'production':
                    raise ConfigurationError("生产环境必须设置SECRET_KEY")
                else:
                    # 开发环境生成临时密钥
                    import secrets
                    self.secret_key = secrets.token_urlsafe(32)
                    logger.warning("使用临时生成的密钥，生产环境请设置SECRET_KEY环境变量")
        
        if not self.allowed_origins:
            origins = os.environ.get('ALLOWED_ORIGINS', 'http://localhost:3000,http://localhost:5000')
            self.allowed_origins = [origin.strip() for origin in origins.split(',') if origin.strip()]


@dataclass
class LLMConfig:
    """LLM配置"""
    api_key: str = ""
    api_url: str = "https://llm.chutes.ai/v1/chat/completions"
    model: str = "deepseek-ai/DeepSeek-V3-0324"
    temperature: float = 0.7
    max_tokens: int = 1000
    timeout: int = 30
    
    def __post_init__(self):
        if not self.api_key:
            self.api_key = os.environ.get('LLM_API_KEY')
            if not self.api_key:
                raise ConfigurationError("必须设置LLM_API_KEY环境变量")
        
        # 从环境变量覆盖默认值
        self.api_url = os.environ.get('LLM_API_URL', self.api_url)
        self.model = os.environ.get('LLM_MODEL', self.model)
        self.temperature = float(os.environ.get('LLM_TEMPERATURE', self.temperature))
        self.max_tokens = int(os.environ.get('LLM_MAX_TOKENS', self.max_tokens))


@dataclass
class CacheConfig:
    """缓存配置"""
    default_timeout: int = 300
    search_timeout: int = 600
    product_timeout: int = 600
    enabled: bool = True
    
    def __post_init__(self):
        self.default_timeout = int(os.environ.get('CACHE_TIMEOUT', self.default_timeout))
        self.search_timeout = int(os.environ.get('SEARCH_CACHE_TIMEOUT', self.search_timeout))


@dataclass
class FileConfig:
    """文件配置"""
    upload_folder: str = "static/uploads"
    barcode_folder: str = "static/barcodes"
    max_upload_size: int = 5242880  # 5MB
    allowed_extensions: list = field(default_factory=lambda: ['png', 'jpg', 'jpeg', 'gif', 'pdf'])
    
    def __post_init__(self):
        self.upload_folder = os.environ.get('UPLOAD_FOLDER', self.upload_folder)
        self.barcode_folder = os.environ.get('BARCODE_FOLDER', self.barcode_folder)
        self.max_upload_size = int(os.environ.get('MAX_UPLOAD_SIZE', self.max_upload_size))
        
        # 确保目录存在
        Path(self.upload_folder).mkdir(parents=True, exist_ok=True)
        Path(self.barcode_folder).mkdir(parents=True, exist_ok=True)


@dataclass
class BusinessConfig:
    """业务配置"""
    default_stock_quantity: int = 100
    min_stock_warning_threshold: int = 10
    max_conversation_history: int = 20
    default_page_size: int = 50
    max_page_size: int = 200
    
    def __post_init__(self):
        self.default_stock_quantity = int(os.environ.get('DEFAULT_STOCK_QUANTITY', self.default_stock_quantity))
        self.min_stock_warning_threshold = int(os.environ.get('MIN_STOCK_WARNING_THRESHOLD', self.min_stock_warning_threshold))
        self.max_conversation_history = int(os.environ.get('MAX_CONVERSATION_HISTORY', self.max_conversation_history))
        self.default_page_size = int(os.environ.get('DEFAULT_PAGE_SIZE', self.default_page_size))
        self.max_page_size = int(os.environ.get('MAX_PAGE_SIZE', self.max_page_size))


@dataclass
class AppConfig:
    """应用配置"""
    debug: bool = False
    testing: bool = False
    environment: str = "development"
    port: int = 5000
    host: str = "0.0.0.0"
    
    # 子配置
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    file: FileConfig = field(default_factory=FileConfig)
    business: BusinessConfig = field(default_factory=BusinessConfig)
    
    def __post_init__(self):
        self.environment = os.environ.get('FLASK_ENV', self.environment)
        self.debug = self.environment == 'development'
        self.testing = os.environ.get('TESTING', '').lower() == 'true'
        self.port = int(os.environ.get('PORT', self.port))
        self.host = os.environ.get('HOST', self.host)


class ConfigService(IConfigService):
    """配置服务实现"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config = AppConfig()
        self.config_file = config_file
        self._load_config()
        self._validate_config()
    
    def _load_config(self):
        """加载配置"""
        # 加载.env文件
        self._load_env_file()
        
        # 加载环境特定的JSON配置文件
        if not self.config_file:
            config_dir = Path.cwd() / 'config'
            env_config_file = config_dir / f'{self.config.environment}.json'
            if env_config_file.exists():
                self.config_file = str(env_config_file)
        
        # 加载JSON配置文件
        if self.config_file and os.path.exists(self.config_file):
            self._load_json_config()
        
        logger.info(f"配置加载完成，环境: {self.config.environment}, 配置文件: {self.config_file or 'None'}")
    
    def _load_env_file(self):
        """加载环境变量文件"""
        env_file = Path.cwd() / '.env'
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ.setdefault(key.strip(), value.strip().strip('"\''))
    
    def _load_json_config(self):
        """加载JSON配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                json_config = json.load(f)
                self._merge_config(json_config)
        except Exception as e:
            logger.error(f"加载配置文件失败 {self.config_file}: {e}")
    
    def _merge_config(self, json_config: Dict[str, Any]):
        """合并JSON配置"""
        for section, values in json_config.items():
            if hasattr(self.config, section) and isinstance(values, dict):
                section_config = getattr(self.config, section)
                for key, value in values.items():
                    if hasattr(section_config, key):
                        setattr(section_config, key, value)
    
    def _validate_config(self):
        """验证配置"""
        errors = []
        
        # 验证必需的配置
        if not self.config.security.secret_key:
            errors.append("SECRET_KEY is required")
        
        if not self.config.llm.api_key:
            errors.append("LLM_API_KEY is required")
        
        # 验证数据库配置
        if not self.config.database.url:
            errors.append("Database URL is required")
        
        # 验证文件路径
        if not os.path.exists(self.config.file.upload_folder):
            try:
                os.makedirs(self.config.file.upload_folder, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create upload folder: {e}")
        
        if errors:
            raise ConfigurationError(f"配置验证失败: {'; '.join(errors)}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        try:
            parts = key.split('.')
            value = self.config
            for part in parts:
                value = getattr(value, part)
            return value
        except AttributeError:
            return default
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """获取配置节"""
        try:
            section_config = getattr(self.config, section)
            if hasattr(section_config, '__dict__'):
                return section_config.__dict__
            return {}
        except AttributeError:
            return {}
    
    def set(self, key: str, value: Any) -> bool:
        """设置配置值"""
        try:
            parts = key.split('.')
            target = self.config
            for part in parts[:-1]:
                target = getattr(target, part)
            setattr(target, parts[-1], value)
            return True
        except AttributeError:
            return False
    
    def reload(self) -> bool:
        """重新加载配置"""
        try:
            self.config = AppConfig()
            self._load_config()
            self._validate_config()
            return True
        except Exception as e:
            logger.error(f"重新加载配置失败: {e}")
            return False
    
    def validate(self) -> Dict[str, Any]:
        """验证配置"""
        try:
            self._validate_config()
            return {'valid': True, 'errors': []}
        except ConfigurationError as e:
            return {'valid': False, 'errors': [str(e)]}


# 全局配置服务实例
config_service = ConfigService()