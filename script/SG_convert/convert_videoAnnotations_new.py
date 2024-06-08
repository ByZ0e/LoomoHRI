# -*- encoding: utf-8 -*-
'''
@File    :   convert_videoAnnotations_new.py
@Time    :   2024/06/08 12:10:26
@Author  :   ziyi 
@Desc    :   None
'''

import json
import os
import numpy as np
import random

SG_DIR = '../localmode_locobot_output-1/'
ANNO_DIR = 'AnnoFiles'
SHOWTIME_FILE = 'showtime.json'
CAPTION_DIR = 'CaptionFiles'
ANNO_FILE = 'videoAnnotations.json'

image_width = 1280.0  # 原始视频帧
image_height = 720.0
display_width = 650.0  # 网页canvas
display_height = 371.63
width_ratio = display_width / image_width
height_ratio = display_height / image_height
num_frames = 106  # 当前展示视频帧数
time_interval = 1/num_frames # 帧时间间隔


anno_files = os.listdir(os.path.join(SG_DIR, 'det'))
# anno_files.remove('.DS_Store')
anno_files.sort(key=lambda x: int(x.split('.')[0]))
time_files = json.load(open(os.path.join(ANNO_DIR, SHOWTIME_FILE)))
caption_file = json.load(open(os.path.join(CAPTION_DIR, 'caption.json')))

highContrastingColors = ['rgba(0,255,81,1)', 'rgba(255,219,0,1)', 'rgba(255,0,0,1)', 'rgba(0,4,255,1)',
                         'rgba(227,0,255,1)']

def rename_frames():
    keyFrame_path = os.path.join(SG_DIR, 'keyFrames')
    frame_files = os.listdir(keyFrame_path)
    frame_files.sort(key=lambda x: int(x.split('_')[0]))
    # 遍历更改文件名
    num = 1
    for i, file in enumerate(frame_files):
        os.rename(os.path.join(keyFrame_path, file), os.path.join(keyFrame_path, 'keyframe_%03d.jpg' % i))
        num = num + 1


def getColor():
    return highContrastingColors[np.random.randint(0, len(highContrastingColors))]


def make_anno_file():
    '''
    根据SG生成前端展示文件videoAnnotations.json
    --obj_dic
        |--incident
            |--incident info in each keyframe(xy, time, show or hide)
    '''
    anno_files.sort(key=lambda x: int(x.split('.')[0]))
    id_list = []
    obj_list, obj_set_tmp = [], []
    bbox_list = []
    for file in anno_files:
        anno = json.load(open(os.path.join(SG_DIR, 'det', file)))
        ids = anno['global_ids']
        objs = anno['obj_labels']
        obj_ids = []
        for i, obj in zip(ids, objs):
            obj_ids.append(obj + "_" + str(i))
        bbox = anno['obj_boxes']
        # obj_list.append(obj_ids)
        obj_list.append(obj_ids)
        obj_set_tmp += obj_ids
        id_list.append(ids)
        bbox_list.append(bbox)

    obj_set = list(set(obj_set_tmp))
    obj_set.sort(key=obj_set_tmp.index)

    # obj_set = ['chair', 'desk']
    videoAnnotations = []
    length = len(obj_set)
    for i, obj in enumerate(obj_set):
        print(obj)
        obj_dic = {
            "id": obj,
            "name": obj,
            "showtime": time_files[i],
            "label": str(length - i),
            "classLable": obj,
            "color": getColor(),
            "incidents": [],
            "childrenNames": [],
            "parentName": '',
            "caption": caption_file[obj][-1]
        }
        for frame_id, objs in enumerate(obj_list):
            if obj in objs:
                idx = objs.index(obj)
                x1, y1, x2, y2 = bbox_list[frame_id][idx]
                incident = {
                    "x": x1 * width_ratio,
                    "y": y1 * height_ratio,
                    "width": (x2 - x1) * width_ratio,
                    "height": (y2 - y1) * height_ratio,
                    "time": time_interval * frame_id,
                    "status": "Show",
                    "id": obj,
                    "name": obj,
                    "label": ""
                    ""
                }
                obj_dic['incidents'].append(incident)
            else:
                incident = {
                    "x": x1 * width_ratio,
                    "y": y1 * height_ratio,
                    "width": (x2 - x1) * width_ratio,
                    "height": (y2 - y1) * height_ratio,
                    "time": time_interval * frame_id,
                    "status": "Hide",
                    "id": obj,
                    "name": obj,
                    "label": ""
                }
                obj_dic['incidents'].append(incident)
        videoAnnotations.append(obj_dic)

    # videoAnnotations.reverse()
    json.dump(videoAnnotations, open(os.path.join(ANNO_DIR, ANNO_FILE), 'w'))


if __name__ == '__main__':
    rename_frames()
    make_anno_file()