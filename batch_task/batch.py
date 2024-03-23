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

import requests

# 读取配置
config = configparser.ConfigParser()
config.read('config.ini')
sections = config.sections()
print(sections)

comfyui_url = 'http://192.168.28.118:8188/prompt'
headers = {
    'Host': '192.168.28.118:8188',
    'Connection': 'keep-alive',
    'Comfy-User': 'undefined',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6266.199 Safari/537.36 Edg/121.0.2260.62',
    'Accept': '*/*',
    'Origin': 'http://192.168.28.118:8188',
    'Referer': 'http://192.168.28.118:8188/',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'Content-Type': 'application/json'
}


def load_api_json(json_file):
    with open(json_file, 'r') as file:
        data = json.load(file)
    return data


def handle():
    for section in sections:
        print(f"开始执行任务: {section}")
        batch_size = int(config.get(section, 'batch_size'))
        sleep_time = config.get(section, 'sleep_time')
        workflow_api_json_file = config.get(section, 'workflow_api_json')
        json_data = load_api_json(workflow_api_json_file)
        # 读取所选目录
        for key in json_data.keys():
            class_type_value = json_data[key]['class_type']
            if 'LoadImageListFromDir' not in class_type_value:
                continue
            base_dir = json_data[key]['inputs']['directory']
            print("按照批次数把图片分批次复制到新目录")
            files = os.listdir(base_dir)
            image_files = [file for file in files if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
            batch_total = (len(image_files) - 1) // batch_size + 1
            # 目录结构
            new_base_dir = base_dir
            if not base_dir.endswith(os.sep):
                new_base_dir = new_base_dir + os.sep
            for i in range(0, batch_total):
                # 创建目录
                target_dir = new_base_dir + "batch_" + str(i)
                shutil.rmtree(target_dir)
                os.makedirs(target_dir, exist_ok=True)
                # 复制图片到新目录
                end_idx = min((i + 1) * batch_size, len(image_files))
                for image_file in image_files[i * batch_size:end_idx]:
                    shutil.copy(new_base_dir + image_file, target_dir)
            # 调用ComfyUI Api提交任务
            for i in range(0, batch_total):
                target_dir = new_base_dir + "batch_" + str(i)
                json_data[key]['inputs']['directory'] = target_dir
                batch_json_data = json.dumps(json_data, ensure_ascii=False)
                print(batch_json_data)
                response = requests.request("POST", comfyui_url, headers=headers, data=batch_json_data)
                print(response.text)

    return


if __name__ == '__main__':
    handle()
