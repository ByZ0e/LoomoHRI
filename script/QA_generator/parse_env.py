# -*- encoding: utf-8 -*-
'''
@File    :   parse_env.py
@Time    :   2024/06/08 12:09:28
@Author  :   ziyi 
@Desc    :   parse the SG result into the environment dictionary
'''

import json

SG_DIR = '../localmode_locobot_output-1/'


# upper=queryExist,物体类,初始化一个不存在的物体
class objectEntity():
    translations = {
        # 'bread': 'food',
    }

    def __init__(self, name, bbox, score, obj_id):
        if name in self.translations:
            self.name = self.translations[name]
        else:
            self.name = name
        self.bbox = bbox
        self.score = score
        self.type = 'object'
        self.id = obj_id
        self.time_queue = None


# 关系类
class relationEntity():
    translations = {
        # 'close_to': 'near',
    }

    def __init__(self, name, sub, obj, rel_id):
        if name in self.translations:
            self.name = self.translations[name]
        else:
            self.name = name
        self.sub = sub
        self.obj = obj
        if name == 'near':
            self.sub_is_obj = True
        else:
            self.sub_is_obj = False
        self.score = None
        self.type = 'relation'
        self.id = rel_id
        self.time_queue = None


def parseEnv(file_idx=0):
    SG = json.load(open(SG_DIR + 'output/' + str(file_idx) + ".json", "r"))
    object_bbox = SG["bbox"]  # 标注框
    object_label = SG["bbox_labels"]  # 物体
    relation_label = SG["rel_labels"]  # 关系
    relation = SG["rel_pairs"]  # 关系对
    object_scores = SG["bbox_scores"]  # 置信度

    Env = {'objects': [], 'relations': []}
    for idx, obj in enumerate(object_label):
        Obj = objectEntity(obj + '_' + str(idx), object_bbox[idx], object_scores[idx], idx)
        Env['objects'].append(Obj)

    for idx, rel in enumerate(relation_label):
        rel_pair = relation[idx]
        Rel = relationEntity(rel, Env['objects'][rel_pair[0]], Env['objects'][rel_pair[1]], idx)
        Env['relations'].append(Rel)
    return Env
