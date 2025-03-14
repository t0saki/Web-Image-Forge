import os

# 数据库配置
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/image_optimizer')

# 图片存储路径
STORAGE_PATH = os.getenv('STORAGE_PATH', './images')

# API鉴权密钥
API_KEY = os.getenv('API_KEY', '')

# ImageMagick 转换参数
WEBP_QUALITY = int(os.getenv('WEBP_QUALITY', '80'))
WEBP_METHOD = int(os.getenv('WEBP_METHOD', '4'))  # 压缩速度 (0-6)

AVIF_QUALITY = int(os.getenv('AVIF_QUALITY', '65'))
AVIF_SPEED = int(os.getenv('AVIF_SPEED', '6'))  # 压缩速度 (0-10)

# 工作线程数量
WORKER_THREADS = int(os.getenv('WORKER_THREADS', '2'))

# 轮询间隔 (秒)
POLL_INTERVAL = int(os.getenv('POLL_INTERVAL', '1'))

# 域名白名单 - 仅允许这些域名的图片进行处理
# 从环境变量获取，多个域名用逗号分隔，例如：example.com,example.org
# 为空时表示允许所有域名（不启用白名单）
DOMAIN_WHITELIST = os.getenv('DOMAIN_WHITELIST', '').split(',') if os.getenv('DOMAIN_WHITELIST') else [] 