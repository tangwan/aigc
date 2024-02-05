#!/usr/bin/env python 
# -*- coding: utf-8 -*- 
"""
@Author: tangwan 
@License: Copyright © 2008-2023, Shanghai Greenshore Network Technology Co.,Ltd.All Rights Reserved. 
@Email: tangwan1114@gmail.com 
@Time: 2024/2/5 15:49
@Desc: 
"""
import os
import sys

from PIL import Image

args = sys.argv


def split_image(file_path, rows, cols):
    # 打开图片
    img = Image.open(file_path)
    # 计算每一份的尺寸
    w, h = img.size
    s_w, s_h = w // cols, h // rows

    imgs = []
    for i in range(rows):
        for j in range(cols):
            # 计算切片的坐标
            left, top = j * s_w, i * s_h
            right, bottom = left + s_w, top + s_h
            # 切割图片
            img_cropped = img.crop((left, top, right, bottom))
            imgs.append(img_cropped)

    return imgs


def merge_image(images, rows, cols, save_path, new_file_name):
    # 打开所有图片
    imgs = [Image.open(img).convert('RGBA') for img in images]

    if not imgs:
        raise ValueError("No images to merge.")

    # 假设所有图片的大小相同
    sample_width, sample_height = imgs[0].size

    # 计算新图片的总宽度和高度
    total_width = sample_width * cols
    total_height = sample_height * rows

    # 创建一个新的图片用于合并，使用RGBA模式以保留alpha通道
    new_img = Image.new('RGBA', (total_width, total_height), (0, 0, 0, 0))

    x_offset, y_offset = 0, 0
    img_iter = iter(imgs)
    for row in range(rows):
        for col in range(cols):
            try:
                img = next(img_iter)
            except StopIteration:
                break  # 没有更多的图片可以添加
            new_img.paste(img, (x_offset, y_offset), mask=img)
            x_offset += sample_width
        y_offset += sample_height
        x_offset = 0  # 重置x偏移量到开始位置

    # 保存或显示新的图片
    new_img.save(f'{save_path}/{new_file_name}')
    # new_img.show()


def get_sorted_files(directory, extension):
    """
    获取指定目录下所有指定扩展名的文件，并按文件名升序排序。

    参数:
    directory (str): 目录路径。
    extension (str): 文件扩展名（例如：'.txt'）。

    返回:
    list: 排序后的文件路径列表。
    """
    # 使用列表推导式获取所有指定扩展名的文件
    files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(extension)]

    # 按文件名升序排序
    files.sort()

    return files


# 获取子目录
def get_subdirectories(directory):
    subdirectories = []
    for root, dirs, files in os.walk(directory):
        for directory in dirs:
            subdirectory = os.path.join(root, directory)
            subdirectories.append(subdirectory)
    return subdirectories


def handle(operate):
    while 1:
        directory_path = input(f"输入图片完整路径[/opt/images|C:\games\images]:").lstrip().rstrip()
        if len(directory_path) == 0:
            print('图片完整路径未输入,程序终止!!!')
            break
        extension = input(f"请输入图片格式[.png]:").lstrip().rstrip()
        if len(extension) == 0:
            print('图片格式未输入,默认.png格式')
            extension = '.png'
        rows = input(f"请输入行数[>0整数]:").lstrip().rstrip()
        if len(rows) == 0 and int(rows) > 0:
            print('行数未输入,程序终止!!!')
            break
        cols = input(f"请输入列数[>0整数]:").lstrip().rstrip()
        if len(cols) == 0 and int(cols) > 0:
            print('列数未输入,程序终止!!!')
            break
        if 'cut' == operate:
            print("开始执行切图操作,请按提示输入参数...")
            images = get_sorted_files(directory_path, extension)
            for image in images:
                file_name = os.path.basename(image)
                file_base_name = file_name.split(".")[0]
                # 切分为4份（2x2）
                imgs = split_image(image, int(rows), int(cols))
                # 创建切图保存目录
                os.mkdir(f'{directory_path}/{file_base_name}')
                # 保存切分后的图片
                for i, img in enumerate(imgs):
                    img.save(f'{directory_path}/{file_base_name}/{file_base_name}__{i}.png')
        elif 'merge' == operate:
            print("开始执行合图操作,请按提示输入参数")
            # 获取所有子目录
            subdirectories = get_subdirectories(directory_path)
            for subdir in subdirectories:
                images = get_sorted_files(subdir, extension)
                # 合图
                new_file_name = os.path.basename(images[0]).split('__')[0] + '_new' + extension
                merge_image(images, int(rows), int(cols), directory_path, new_file_name)
        print(f"执行完成...")
        condition = input(f"是否继续切图[Y/N]:").lstrip().rstrip()
        condition = condition.lower()
        if condition == 'n':
            break


if __name__ == '__main__':
    operate_list = ['cut', 'merge']
    operate = args[1];
    if len(operate) == 0:
        print("请提供参数,支持参数[cut|merge]")
    elif operate not in operate_list:
        print("无效的参数")
    else:
        handle(operate)
