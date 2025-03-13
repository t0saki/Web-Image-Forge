import os
import requests
from wand.image import Image
import tempfile
import re
from urllib.parse import urlparse
from config import (
    STORAGE_PATH, 
    WEBP_QUALITY, 
    WEBP_METHOD, 
    AVIF_QUALITY, 
    AVIF_SPEED
)

def ensure_dirs():
    """确保存储目录存在"""
    if not os.path.exists(STORAGE_PATH):
        os.makedirs(STORAGE_PATH)

def download_image(url):
    """下载原始图片并提取文件名"""
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    # 从响应头中提取文件名
    original_filename = None
    content_disposition = response.headers.get('Content-Disposition')
    if content_disposition:
        # 尝试从Content-Disposition获取文件名
        matches = re.findall(r'filename="(.+?)"', content_disposition)
        if matches:
            original_filename = matches[0]
    
    # 如果响应头中没有文件名，则从URL中提取
    if not original_filename:
        parsed_url = urlparse(url)
        path = parsed_url.path
        # 获取路径的最后部分
        if path and '/' in path:
            original_filename = path.split('/')[-1]
            # 移除可能的查询参数
            if '?' in original_filename:
                original_filename = original_filename.split('?')[0]
    
    # 如果没有扩展名或文件名为空，使用默认文件名
    if not original_filename or '.' not in original_filename:
        original_filename = "image.jpg"
    
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    for chunk in response.iter_content(chunk_size=8192):
        temp_file.write(chunk)
    temp_file.close()
    
    return temp_file.name, original_filename

def convert_image(image_path, output_format, task_id):
    """转换图片到指定格式"""
    ensure_dirs()
    
    # 创建输出路径
    output_dir = os.path.join(STORAGE_PATH, str(task_id))
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    output_path = os.path.join(output_dir, f"converted.{output_format}")
    
    with Image(filename=image_path) as img:
        if output_format == 'webp':
            img.format = 'webp'
            img.options['webp:method'] = str(WEBP_METHOD)
            img.options['webp:lossless'] = 'false'
            img.compression_quality = WEBP_QUALITY
        elif output_format == 'avif':
            img.format = 'avif'
            img.options['avif:speed'] = str(AVIF_SPEED)
            img.compression_quality = AVIF_QUALITY
        
        img.save(filename=output_path)
        
    return output_path

def process_image(url, output_format, task_id):
    """处理图片转换的完整流程"""
    try:
        temp_file, original_filename = download_image(url)
        output_path = convert_image(temp_file, output_format, task_id)
        os.unlink(temp_file)  # 删除临时文件
        return output_path, original_filename
    except Exception as e:
        if 'temp_file' in locals() and os.path.exists(temp_file):
            os.unlink(temp_file)  # 确保临时文件被删除
        raise e 