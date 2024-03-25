#!/usr/bin/env python 
# -*- coding: utf-8 -*- 
"""
批量图生图任务处理
@Author: tangwan 
@License: Copyright © 2008-2023, Shanghai Greenshore Network Technology Co.,Ltd.All Rights Reserved. 
@Email: tangwan1114@gmail.com 
@Time: 2024/3/20 17:01
@Desc: 
"""

import json
import configparser
import os
import time
import shutil
import uuid
import logging

import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('batch_task')
# 读取配置
config = configparser.ConfigParser()
config.read('config.ini')
sections = config.sections()

# comfyui_post_url = 'http://192.168.23.52:8188/prompt'
# comfyui_get_url = 'http://192.168.23.52:8188/history'

comfyui_post_url = 'http://127.0.0.1:8188/prompt'
comfyui_get_url = 'http://127.0.0.1:8188/history'

headers = {
    'Content-Type': 'application/json'
}


def load_api_json(json_file):
    with open(json_file, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data


def handle():
    for section in sections:
        logger.info(f'开始执行任务: %s', section)
        # 每批图片数量
        batch_size = int(config.get(section, 'batch_size'))
        # 每批次执行玩后休眠时间(秒)
        sleep_time = int(config.get(section, 'sleep_time'))
        # comfyui api json
        workflow_api_json_file = config.get(section, 'workflow_api_json')
        json_data = load_api_json(workflow_api_json_file)
        # 从json中读取所选目录
        base_dir = ''
        node = ''
        for key in json_data.keys():
            class_type_value = json_data[key]['class_type']
            if 'LoadImageListFromDir' not in class_type_value:
                continue
            node = key
            base_dir = json_data[key]['inputs']['directory']

        if len(base_dir) == 0 or not os.path.exists(base_dir):
            logger.error(f'comfyui中未设置[加载图像列表的路径],任务停止执行')
            continue

        logger.info(f'按照每批次图片数量拆分任务,batch_size: %s,base_dir: %s', batch_size, base_dir)
        image_files = [file for file in os.listdir(base_dir) if
                       file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
        if len(image_files) == 0:
            logger.warning(f'comfyui中设置的[加载图像列表的路径]中没有图片,任务停止执行')
        batch_total = (len(image_files) - 1) // batch_size + 1
        # 目录结构
        new_base_dir = base_dir
        if not base_dir.endswith(os.sep):
            new_base_dir = new_base_dir + os.sep
        # 切分任务
        split_task(batch_size, batch_total, image_files, new_base_dir)
        # 调用ComfyUI Api提交任务
        for i in range(0, batch_total):
            target_dir = new_base_dir + "batch_" + str(i)
            json_data[node]['inputs']['directory'] = target_dir
            req = {
                "client_id": str(uuid.uuid4()).replace('-', ''),
                "prompt": json_data
            }
            payload = json.dumps(req, ensure_ascii=False)
            logger.info(f'请求comfyui api 提交任务 req: %s', payload)
            response = requests.post(comfyui_post_url, json=req)
            logger.info(f'请求comfyui api 提交任务 resp: %s', response.text)
            prompt_id = json.loads(response.text)['prompt_id']
            while True:
                time.sleep(5)
                task_status_resp = requests.get(comfyui_get_url + "/" + prompt_id)
                logger.info(f'请求comfyui api 获取任务状态 resp: %s', task_status_resp.text)
                prompt_result = json.loads(task_status_resp.text)[prompt_id]
                if prompt_result is None:
                    continue
                task_status = prompt_result['status']
                if task_status['status_str'] == 'success' and task_status['completed']:
                    break
            logger.info(f'总批次: %s,当前批次执行完成: %s', batch_total, i + 1)
            if (i + 1) == batch_total:
                logger.info(f'所有批次任务都执行完成')
                return
            time.sleep(sleep_time)


def split_task(batch_size, batch_total, image_files, new_base_dir):
    for i in range(0, batch_total):
        # 创建目录
        target_dir = new_base_dir + "batch_" + str(i)
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        os.makedirs(target_dir, exist_ok=True)
        # 复制图片到新目录
        end_idx = min((i + 1) * batch_size, len(image_files))
        for image_file in image_files[i * batch_size:end_idx]:
            shutil.copy(new_base_dir + image_file, target_dir)


if __name__ == '__main__':
    handle()
