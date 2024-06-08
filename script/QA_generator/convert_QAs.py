# -*- encoding: utf-8 -*-
'''
@File    :   convert_QAs.py
@Time    :   2024/06/08 12:09:52
@Author  :   ziyi 
@Desc    :   convert the QA result into the total QA json classified with query objects
'''

import json
import os
from parse_env import parseEnv
QA_path = "./QA/"
SG_DIR = '../localmode_locobot_output-1/'
QA_DIR = 'QAFiles'
if not os.path.exists(QA_DIR):
    os.mkdir(QA_DIR)
object_QA_save_file = './QAs.json'
room_QA_save_file = ['./questions.json', './answers.json']

Env = parseEnv(file_idx=105)
objects = Env['objects']
object_dict = {}
object_QAs = []
questions = []
answers = []
for obj in objects:
    # QAs.append = {"type": obj.name, "qas":[]}
    object_dict[obj.name] = []

files = os.listdir(QA_path)
# files.remove('.DS_Store')
for file in files:
    print(file)
    QA_list = json.load(open(os.path.join(QA_path, file), 'r'))
    for QA_dict in QA_list:
        query_object = QA_dict['query_object']
        if query_object in object_dict.keys():
            object_dict[query_object].append({"value": QA_dict['answer'], "text": QA_dict['question']})
        else:
            questions.append(QA_dict['question'])
            answers.append(QA_dict['answer'])

for type, qa in object_dict.items():
    object_QAs.append({"type": type, "qas": qa})

json.dump(questions, open(os.path.join(QA_DIR, room_QA_save_file[0]), 'w'))
json.dump(answers, open(os.path.join(QA_DIR, room_QA_save_file[1]), 'w'))
json.dump(object_QAs, open(os.path.join(QA_DIR, object_QA_save_file), 'w'))

