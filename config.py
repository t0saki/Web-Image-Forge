import os

# 数据库配置
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/image_optimizer')

# 图片存储路径
STORAGE_PATH = os.getenv('STORAGE_PATH', './images')

# ImageMagick 转换参数
WEBP_QUALITY = int(os.getenv('WEBP_QUALITY', '80'))
WEBP_METHOD = int(os.getenv('WEBP_METHOD', '4'))  # 压缩速度 (0-6)

AVIF_QUALITY = int(os.getenv('AVIF_QUALITY', '65'))
AVIF_SPEED = int(os.getenv('AVIF_SPEED', '6'))  # 压缩速度 (0-10)

# 工作线程数量
WORKER_THREADS = int(os.getenv('WORKER_THREADS', '2'))

# 轮询间隔 (秒)
POLL_INTERVAL = int(os.getenv('POLL_INTERVAL', '1')) 