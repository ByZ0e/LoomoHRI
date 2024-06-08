# -*- encoding: utf-8 -*-
'''
@File    :   process.py
@Time    :   2024/06/08 12:10:47
@Author  :   ziyi 
@Desc    :   None
'''


from heapq import merge
import json
from ntpath import join
import numpy as np
from collections import defaultdict
import os
import shutil


work_dir = os.getcwd() # 获取绝对路径
print(work_dir)

SG_DIR = '../localmode_locobot_output-1'
FRAME_DIR = '../localmode_locobot_output-1/detection'
NUM_FRAME = len(os.listdir(os.path.join(SG_DIR, "det")))
ANNO_DIR = 'AnnoFiles'
SHOWTIME_FILE = 'showtime.json'
CAPTION_DIR = 'CaptionFiles'
DENSE_CAPTION_FILE = ['caption.json', 'query_list.json', 'caption_list.json']

if 'output' not in os.listdir(SG_DIR):
    os.mkdir(os.path.join(SG_DIR, 'output'))
if 'keyFrames' not in os.listdir(SG_DIR):
    os.mkdir(os.path.join(SG_DIR, 'keyFrames'))
if not os.path.exists(ANNO_DIR):
    os.mkdir(ANNO_DIR)
if not os.path.exists(CAPTION_DIR):
    os.mkdir(CAPTION_DIR)

def merge_dict(d1, d2):
    dd = defaultdict(list)
    for d in (d1, d2):
        for key, value in d.items():
            if isinstance(value, list):
                dd[key].extend(value)
            else:
                dd[key].append(value)
    return dict(dd)

def extract_keyframe(img_format='png'):
    '''
    合成视频用,从visualize文件夹获取关键帧,copy到keyFrames文件夹
    '''
    sg_frames = os.listdir(os.path.join(SG_DIR, "visualize"))
    keyframes = [x.split('_')[-1].replace('jpg', img_format) for x in sg_frames]
    # keyframes.sort(key=lambda x: int(x.split('.')[0]))
    # print(keyframes)
    for (idx, frame) in enumerate(keyframes):
        print(idx, frame)
        source = os.path.join(FRAME_DIR, 'detection_' + frame)
        target = os.path.join(SG_DIR, 'keyFrames', sg_frames[idx])
        # print(target)
        shutil.copy(source, target)

def convert():
    '''
    读取json及det文件夹的检测和SG,合并历史信息后,得到每一帧的global_SG结果,写入到output文件夹
    --output
        |--keyframe_index.json: bbox/bbox_scores/bbox_labels/rel_pairs/rel_labels/rel_scores/rel_all_scores
        |--keyframe_index.npz: bbox/num_bbox/image_h/image_w
    '''
    sg = {}
    bbox = {}
    for id in range(NUM_FRAME):
        sg_file = open(os.path.join(SG_DIR, "json/" + str(id) + ".json"), "r")
        bbox_file = open(os.path.join(SG_DIR, "det/" + str(id) + ".json"), "r")
        sg = merge_dict(sg, json.load(sg_file))
        bbox = merge_dict(bbox, json.load(bbox_file))

        global_ids = {}
        for node in sg["nodes"]:
            if (node["group_name"] == "object"):
                name = node["name"]
                global_ids[node["id"]] = int(name[name.find("_") + 1 : len(name)])

        res_json = {}

        res_json["bbox"] = []
        res_json["bbox_scores"] = []
        res_json["bbox_labels"] = []
        for node in sg["nodes"]:
            if (node["group_name"] == "object"):
                boxes = 0
                scores = 0
                labels = 0
                for j in range(0, len(bbox["global_ids"])):
                    if (global_ids[node["id"]] == bbox["global_ids"][j]):
                        boxes = bbox["obj_boxes"][j]
                        scores = bbox["obj_scores"][j]
                        labels = bbox["obj_labels"][j]
                res_json["bbox"].append(boxes)
                res_json["bbox_scores"].append(scores)
                res_json["bbox_labels"].append(labels)

        res_json["rel_pairs"] = []
        res_json["rel_labels"] = []
        for i in range(0, len(sg["links"]), 2):
            s = global_ids[sg["links"][i]["source"]]
            t = global_ids[sg["links"][i + 1]["target"]]
            rel = sg["nodes"][sg["links"][i]["target"]]["name"]
            res_json["rel_pairs"].append([s, t])
            res_json["rel_labels"].append(rel)

        res_json["rel_scores"] = []
        res_json["rel_all_scores"] = []

        res_json_file = open(os.path.join(SG_DIR, "output/" + str(id) + ".json"), "w")
        json.dump(res_json, res_json_file)

        tmp = []
        length = len(res_json["bbox"])
        for i in range(length):
            tmp.append((res_json["bbox_scores"][i], res_json["bbox"][i]))
        tmp.sort(reverse = True)
        np.savez(os.path.join(SG_DIR, "output/" + str(id) + ".npz"), bbox = np.array([i[1] for i in tmp], dtype = "float32"), num_bbox = np.array(length, dtype = "int64"), image_h = np.array(968, dtype = "int64"), image_w = np.array(1296, dtype = "int64"))

        sg_file.close()
        bbox_file.close()
        res_json_file.close()

def get_showtime():
    '''
    获取showtime.json文件
    记录每个global_entity首次出现的keyframe_index (list)
    '''
    showtime = []
    json_files = os.listdir(os.path.join(SG_DIR, 'json'))
    # json_files.remove('.DS_Store')
    json_files.sort(key=lambda x: int(x.split('.')[0]))
    for file in json_files:   
        result = json.load(open(os.path.join(SG_DIR, 'json', file), 'r'))
        nodes = result['nodes']
        objects = [x for x in nodes if x['group_name'] == 'object']
        for obj in objects:
            showtime.append(file.split('.')[0])
    json.dump(showtime, open(os.path.join(ANNO_DIR, SHOWTIME_FILE), 'w'))

def get_dense_caption(json_idx=24):
    caption_dict = {}
    result = json.load(open(os.path.join(SG_DIR, 'output', '{}.json'.format(json_idx)), 'r'))
    rel_pairs = result['rel_pairs']
    rel_labels = result['rel_labels']
    bbox_labels = result['bbox_labels']
    for idx, rel in enumerate(rel_pairs):
        sub, obj = bbox_labels[rel[0]], bbox_labels[rel[1]]
        # sub, obj = bbox_labels[rel[0]] + '_' + str(rel[0]), bbox_labels[rel[1]] + '_' + str(rel[1])
        dic_key = sub + '_' + str(rel[0])
        rel_name = rel_labels[idx]
        if dic_key in caption_dict.keys():
            # caption_dict[sub].append(sub + ' ' + rel_name + ' ' + obj)
            caption_dict[dic_key].append('a ' + sub + ' ' + rel_name + ' a ' + obj)
        else:
            # caption_dict[sub].append(sub + ' ' + rel_name + ' ' + obj)
            caption_dict[dic_key] = ['a ' + sub + ' ' + rel_name + ' a ' + obj]
    for idx, obj in enumerate(bbox_labels):
        dic_key = obj + '_' + str(idx)
        if dic_key not in caption_dict.keys():
            caption_dict[dic_key] = ['This is a ' + obj + '.']
        elif len(caption_dict[dic_key]) > 1:
            caption_dict[dic_key].append('This is ' + ', '.join(caption_dict[dic_key]) + '.')
        else:
            caption_dict[dic_key][0] = 'This is ' + caption_dict[dic_key][0] + '.'
    
    caption_dict = dict(sorted(caption_dict.items(), key=lambda d: int(d[0].split('_')[-1])))
    json.dump(caption_dict, open(os.path.join(CAPTION_DIR, DENSE_CAPTION_FILE[0]), 'w'))

    query_list = []
    caption_list = {}
    for obj, captions in caption_dict.items():
        query_list.append({
            "value": obj,
            "label": obj
        })
        caption_list[obj] = captions[-1]
    json.dump(query_list, open(os.path.join(CAPTION_DIR, DENSE_CAPTION_FILE[1]), 'w'))
    json.dump(caption_list, open(os.path.join(CAPTION_DIR, DENSE_CAPTION_FILE[2]), 'w'))

if __name__ == '__main__':
    convert()
    extract_keyframe('jpg')
    get_showtime()
    get_dense_caption(json_idx=105)
