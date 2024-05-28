import random
from flask import Flask, jsonify, make_response, render_template, send_from_directory, request, redirect, url_for
import os
import shutil
import json

# 读取配置文件
with open('config.json', 'r') as f:
    config = json.load(f)

app = Flask(__name__)

# 获取图片目录
IMAGE_FOLDER = config["image_folder"]
OPT_IMAGE_FOLDER = config["opt_image_folder"]

images = os.listdir(IMAGE_FOLDER)
random.shuffle(images) # 打乱

def count_files_in_directory(directory):
    """计算指定目录中的文件总数（不包括子目录中的文件）"""
    return len([name for name in os.listdir(directory) if os.path.isfile(os.path.join(directory, name))])


@app.route('/')
def index():
    return redirect(url_for('view_image', image_index=0))

# 根据list索引图片
@app.route('/images/<int:image_index>')
def view_image(image_index):
    # 设定cookies user_var为用户当前标注数量
    user_specific_var = request.cookies.get('user_var')

    if image_index < 0 or image_index >= len(images):
        return redirect(url_for('view_image', image_index=0))
    
    image_name = images[image_index]
    next_index = (image_index + 1) % len(images)
    prev_index = (image_index - 1) % len(images)
    
    saved_num = count_files_in_directory(OPT_IMAGE_FOLDER)
    
    html = render_template('index.html', 
                           image_name = image_name, 
                           next_index = next_index, 
                           prev_index = prev_index, 
                           total_num = len(images), 
                           saved_img = saved_num, 
                           get_user_cnt = user_specific_var,
                           usr_task = config["usr_task"],
                           total_task = config["total_task"])
    
    if user_specific_var is None:
        # 用户第一次访问，设置 Cookie
        resp = make_response(html)
        resp.set_cookie('user_var', '0', max_age=60*60*24*365)  # Cookie 有效期为一年
        return resp
    else:
        # Cookie 已存在，用户非首次访问
        return html

@app.route('/static/images/<filename>')
def get_image(filename):
    return send_from_directory(IMAGE_FOLDER, filename)

# 保存图，在保存同时将cookies + 1
@app.route('/save_image/<image_name>/<next_index>', methods=['POST'])
def save_image(image_name, next_index):
    user_var = request.cookies.get('user_var')

    new_user_var = str(int(user_var) + 1)  
    response = make_response(redirect(url_for('view_image', image_index=int(next_index)-1)))
    response.set_cookie('user_var', new_user_var, max_age=60*60*24*30)
   
    source_path = IMAGE_FOLDER + image_name  # 源文件路径
    target_path = OPT_IMAGE_FOLDER  + image_name # 目标路径，确保目录已存在
    shutil.copy(source_path, target_path)  # 复制文件
    return response  # 返回 重定向


if __name__ == '__main__':
    # 在大装置网页端可以打开公网端口
    app.run(debug=False, host=config["host"],port=config["port"])
