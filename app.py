import os
import re
import time
from flask import Flask, request, send_file, jsonify, redirect, url_for
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import ImageTask, TaskStatus, init_db
from config import DATABASE_URL, DOMAIN_WHITELIST, API_KEY
from functools import wraps

app = Flask(__name__)

# 初始化数据库
init_db()

# API鉴权装饰器
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 如果API_KEY未设置，则不进行鉴权
        if not API_KEY:
            return f(*args, **kwargs)
        
        # 从请求头中获取API KEY
        api_key = request.headers.get('X-API-Key')
        
        # 验证API KEY
        if not api_key or api_key != API_KEY:
            return jsonify({"error": "Unauthorized. Invalid or missing API key"}), 401
            
        return f(*args, **kwargs)
    return decorated_function

# 创建数据库连接
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def extract_url(path):
    """从路径中提取URL"""
    if path.startswith(('/http://', '/https://')):
        return path[1:]
    if path.startswith('http://') or path.startswith('https://'):
        return path
    if path.startswith('/'):
        return f"http://{path[1:]}"
    return None

def is_domain_allowed(url):
    """检查URL的域名是否在白名单中"""
    if not DOMAIN_WHITELIST:  # 白名单为空，允许所有域名
        return True
        
    try:
        # 提取域名部分
        domain_match = re.search(r'^https?://([^/]+)', url)
        if not domain_match:
            return False
            
        domain = domain_match.group(1)
        # 移除可能的端口号
        domain = domain.split(':')[0]
        
        # 检查域名或子域名是否在白名单中
        for allowed_domain in DOMAIN_WHITELIST:
            allowed_domain = allowed_domain.strip()
            if not allowed_domain:
                continue
                
            # 完全匹配
            if domain == allowed_domain:
                return True
                
            # 子域名匹配（确保是子域名而不是部分字符串匹配）
            if domain.endswith('.' + allowed_domain):
                return True
                
        return False
    except:
        return False


@app.route('/<path:image_url>')
@require_api_key
def convert_image(image_url):
    # 提取原始URL
    original_url = extract_url(f"/{image_url}")
    if not original_url:
        return jsonify({"error": "Invalid URL format"}), 400
    
    # 检查域名是否在白名单中
    if not is_domain_allowed(original_url):
        return jsonify({"error": "Domain not allowed"}), 403
    
    # 获取转换格式参数 - 首先检查查询参数
    output_format = request.args.get('format')
    
    # 如果查询参数中没有指定格式，则检查Accept头部来确定浏览器支持的格式
    if not output_format:
        accept_header = request.headers.get('Accept', '')
        # 按优先级检查支持的格式
        supported_formats = ['avif', 'webp']
        for fmt in supported_formats:
            if f'image/{fmt}' in accept_header:
                output_format = fmt
                break
    
    # 如果无法确定格式，直接重定向到原始URL
    if not output_format:
        return redirect(original_url)
    
    # 验证格式支持
    if output_format not in ['webp', 'avif']:
        return jsonify({"error": "Unsupported format"}), 400
    
    session = Session()
    try:
        # 计算URL哈希 (包含格式参数)
        url_hash = ImageTask.url_to_hash(original_url, output_format)
        
        # 查找或创建任务
        task = session.query(ImageTask).filter_by(
            original_url_hash=url_hash,
            format=output_format
        ).first()
        
        if not task:
            task = ImageTask(
                original_url=original_url,
                original_url_hash=url_hash,
                format=output_format,
                status=TaskStatus.PENDING
            )
            session.add(task)
            session.commit()
        task.query_count += 1
        session.commit()
        
        # Wait until task reaches a terminal state (SUCCEED or FAILED)
        while task.status not in (TaskStatus.SUCCEED, TaskStatus.FAILED):
            session.refresh(task)
            time.sleep(0.5)

        if task.status == TaskStatus.SUCCEED:
            session.close()
            # 重定向到哈希URL
            return redirect(url_for('serve_optimized_image', url_hash=url_hash, format=output_format))
        else:
            session.close()
            # 如果转换失败，直接重定向到原始URL
            return redirect(original_url)
    except Exception as e:
        session.rollback()
        session.close()
        return jsonify({"error": str(e)}), 500


@app.route('/img/<url_hash>.<format>')
def serve_optimized_image(url_hash, format):
    if format not in ['webp', 'avif']:
        return jsonify({"error": "Unsupported format"}), 400
    
    session = Session()
    try:
        # 查找任务
        task = session.query(ImageTask).filter_by(
            original_url_hash=url_hash,
            format=format
        ).first()
        
        if not task or task.status != TaskStatus.SUCCEED:
            session.close()
            # 如果任务不存在或转换失败，尝试获取原始URL并重定向
            if task and task.original_url:
                return redirect(task.original_url)
            return jsonify({"error": "Image not found or conversion failed"}), 404
        
        # 获取用于Content-Disposition的文件名
        filename = task.original_filename
        print(f"filename: {filename}")
        if filename:
            # 替换文件扩展名
            if '.' in filename:
                base_name = filename.rsplit('.', 1)[0]
                filename = f"{base_name}.{format}"
            else:
                filename = f"{filename}.{format}"
        else:
            filename = f"image.{format}"
        
        # 关闭会话
        session.close()
        
        # 使用send_file并设置Content-Disposition
        response = send_file(task.result_path, mimetype=f'image/{format}')
        response.headers['Content-Disposition'] = f'inline; filename="{filename}"'
        
        # 添加缓存控制头，使响应能被CDN有效缓存
        # 设置较长的缓存时间，因为图片hash是唯一的（包含URL和格式），内容变化时URL也会变化
        max_age = 31536000  # 1年（秒数）
        response.headers['Cache-Control'] = f'public, max-age={max_age}, immutable'
        response.headers['Expires'] = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(time.time() + max_age))
        
        # 添加ETag头，基于图片哈希（包含URL和格式）
        response.headers['ETag'] = f'"{url_hash}"'
        
        return response
    except Exception as e:
        session.close()
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000))) 