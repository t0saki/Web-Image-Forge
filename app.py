import os
import re
import time
from flask import Flask, request, send_file, jsonify, redirect, url_for
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import ImageTask, TaskStatus, init_db
from worker import ConversionWorker
from config import DATABASE_URL, WORKER_THREADS

app = Flask(__name__)

# 初始化数据库
init_db()

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


@app.route('/<path:image_url>')
def convert_image(image_url):
    # 提取原始URL
    original_url = extract_url(f"/{image_url}")
    if not original_url:
        return jsonify({"error": "Invalid URL format"}), 400
    
    # 获取转换格式参数
    output_format = request.args.get('format', 'webp')
    if output_format not in ['webp', 'avif']:
        return jsonify({"error": "Unsupported format"}), 400
    
    session = Session()
    try:
        # 计算URL哈希
        url_hash = ImageTask.url_to_hash(original_url)
        
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
            return jsonify({"error": "Image conversion failed"}), 500
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
        # 设置较长的缓存时间，因为图片hash是唯一的，内容变化时URL也会变化
        max_age = 31536000  # 1年（秒数）
        response.headers['Cache-Control'] = f'public, max-age={max_age}, immutable'
        response.headers['Expires'] = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(time.time() + max_age))
        
        # 添加ETag头，基于图片哈希
        response.headers['ETag'] = f'"{url_hash}"'
        
        return response
    except Exception as e:
        session.close()
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000))) 