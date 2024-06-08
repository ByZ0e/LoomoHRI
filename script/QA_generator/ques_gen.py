# -*- encoding: utf-8 -*-
'''
@File    :   ques_gen.py
@Time    :   2024/06/08 12:08:43
@Author  :   ziyi 
@Desc    :   generate question files with 13 templates
'''

import copy
import os
import numpy as np
import random
import json
from parse_env import parseEnv, objectEntity, relationEntity
from question_string_builder import QuestionStringBuilder


# 问题引擎：模板和执行方式
class Engine:
    '''
        Templates and functional forms.
    '''

    # 函数模板
    template_defs = {
        'exist': [
            'filter.objects', 'query.exist'
        ],
        'obj_exist': [
            'filter.relations', 'query.exist'
        ],
        'global': [
            'filter.objects', 'query.global'
        ],
        'query_what': [
            'filter.relations', 'query.query'
        ],
        'query_which': [
            'filter.relations', 'query.query'
        ],
        'query_where': [
            'filter.relations', 'query.query'
        ],
        'count': [
            'non_filter.objects', 'query.count'
        ],
        'obj_count': [
            'filter.objects', 'query.count'
        ],
        'rel_count': [
            'filter.relations', 'query.count'
        ],
        'global_choose': ['filter.objects', 'query.global'],
        'choose_what': [
            'filter.relations', 'query.choose'
        ],
        'choose_which': [
            'filter.relations', 'query.choose'
        ],
        'choose_where': [
            'filter.relations', 'query.choose'
        ]
    }

    # 问题模板
    templates = {
        'exist': '<AUX> there <ARTICLE> <OBJ> in the room?',
        'obj_exist': '<AUX> <ARTICLE-sure> <OBJ1> <LOGIC> <ARTICLE-sure> <OBJ2>?',
        'global': 'what objects <AUX> in the room?',
        'query_what': 'What <AUX> <LOGIC> <ARTICLE-sure> <OBJ>?',
        'query_which': 'Which object <AUX> <LOGIC> <ARTICLE-sure> <OBJ>?',
        'query_where': 'Where <AUX> <ARTICLE-sure> <OBJ>?',
        'count': 'how many objects <AUX> there in the room?',
        'obj_count': 'how many <OBJ-plural> <AUX-plural> there in the room?',
        'rel_count': 'how many objects <AUX> <LOGIC> <ARTICLE-sure> <OBJ>?',
        'global_choose': 'what object <AUX> in the room, <OBJ> or <OBJ>?',
        'choose_what': 'What <AUX> <LOGIC> <ARTICLE-sure> <OBJ>, <OBJ1> or <OBJ2>?',
        'choose_which': 'Which object <AUX> <LOGIC> <ARTICLE-sure> <OBJ>, <OBJ1> or <OBJ2>?',
        'choose_where': 'Where <AUX> <ARTICLE-sure> <OBJ>, <LOGIC1> <ARTICLE-sure> <OBJ1> or <LOGIC2> <ARTICLE-sure> <OBJ2>?'
    }

    use_threshold_size = True
    use_threshold_score = True
    neg_prob = 1

    # 初始化
    def __init__(
            self,
            Env,
            debug=False,
            object_counts_by_room_file="data/obj_counts_by_room.json"
    ):
        self.template_fns = {
            'filter': self.filter,
            'non_filter': self.non_filter,
            'query': self.query,
        }
        self.query_fns = {
            'query_exist': self.queryExist,
            'query_global': self.queryGlobal,
            'query_count': self.queryCount,
            'query_query': self.queryQuery,
            'query_choose': self.queryChoose,
        }

        self.debug = debug
        self.ent_queue = None
        self.threshold = 0.3
        self.entities = Env
        self.entities_no_filter = copy.deepcopy(self.entities)
        self.global_obj_list = [
            'container', 'books', 'switch',
            'grill', 'shelving', 'person', 'pet',
            'decoration','fan','stand', 'cabinet'
        ]  # decoy object list
        self.negative_exists = []
        self.q_str_builder = QuestionStringBuilder()
        self.q_obj_builder = self.questionObjectBuilder

    # 分离参数，产生问题
    def executeFn(self, template_def, template):
        self.entities = copy.deepcopy(self.entities_no_filter)
        for i in template_def:
            if '.' in i:
                _ = i.split('.')
                fn = _[0]  # 分开函数和参数
                param = _[1]
            else:
                fn = i
                param = None

            res = self.template_fns[fn](param, template)  # 调用模板函数生成问题

        if isinstance(res, dict):
            return res
        else:
            return list({x['question']: x for x in res}.values())

    def clearQueue(self):
        self.ent_queue = None

    def thresholdSize(self, *args):
        def getSize(bbox):
            try:
                return (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
            except:
                return np.prod(bbox['radii']) * 8

        assert self.ent_queue != None
        assert self.ent_queue['type'] == 'objects'

        ent = self.ent_queue
        sizes = [getSize(x.bbox) for x in ent['elements']]
        idx = [i for i, v in enumerate(sizes) if v < 0.0005]

        for i in idx[::-1]:
            del ent['elements'][i]

        self.ent_queue = ent
        return self.ent_queue

    # upper=filter,根据置信度过滤掉物体
    def thresholdScore(self, *args):
        assert self.ent_queue != None
        ent = self.ent_queue
        scores = [x.score for x in ent['elements']]  # 获取置信度分数
        idx = [i for i, v in enumerate(scores) if v < self.threshold]  # 因为置信度过低被过滤掉的物体编号

        # 删除置信度过低的物体
        for i in idx[::-1]:
            del ent['elements'][i]

        self.ent_queue = ent
        return self.ent_queue

    # upper=executeFn,过滤器
    def filter(self, *args):
        self.ent_queue = {
            'type': args[0],  # objects,relations
            'elements': self.entities[args[0]]  # type对应的Env
        }
        if self.ent_queue['type'] == 'objects' and self.use_threshold_score == True:
            self.ent_queue = self.thresholdScore()
        return self.ent_queue

    # upper=executeFn,不过滤
    def non_filter(self, *args):
        self.ent_queue = {
            'type': args[0],  # objects,relations
            'elements': self.entities[args[0]]  # type对应的Env
        }

    # upper=executeFn,问题生成
    def query(self, *args):
        assert self.ent_queue != None
        ent = self.ent_queue  # ent:entities

        return self.query_fns['query_' + args[0]](ent, args[1])  # 调用query_args[0]指向的函数

    # upper=query,当函数模板为exist时调用
    def queryExist(self, ent, template):
        type = ''
        child_list = []
        qns = []
        if template == 'exist':
            type = 'exist'
        elif template == 'obj_exist':
            type = 'obj_exist'

        for i in ent['elements']:  # ent:entities

            if type == 'exist':
                child_list = [i]

            elif type == 'obj_exist':
                child_list = [i]
                name = self.searchEntity(i)
                child_list.append(name)

            # 调用questionObjectBuilder,产生一个答案为yes的QA
            # 得到问题-答案-类型字典，加到qns列表中
            qns.append(self.q_obj_builder(type, child_list, 'yes', q_type=type + '_positive'))

            # 出现的物体(去掉重复)
            obj_present = list(set([x.name.split('_')[0] for x in ent['elements']]))

            # 未出现的物体（既不在已出现的物体中也未生成过问题）
            obj_not_present = [
                x for x in self.global_obj_list
                if x not in obj_present and x not in self.negative_exists
            ]

            # 产生一个答案为no的QA，产生过问题的加入negative_exists
            if len(obj_not_present) == 0:  # 没有不存在的物体
                continue
            self.negative_exists.append(obj_not_present[0])

            # 调用objectEntity函数，产生一个不存在的物体
            sampled_obj = objectEntity(obj_not_present[0], bbox=[], score=0.0, obj_id=None)

            # 产生一个答案为no的QA，产生过问题的加入negative_exists
            if type == 'exist':
                child_list = [sampled_obj]

            elif type == 'obj_exist':
                child_list = [i]
                name = [sampled_obj.name, random.choice(self.searchEntity(i))]
                child_list.append(name)

            # 调用questionObjectBuilder,产生一个答案为no的QA
            if random.random() < self.neg_prob:  # 控制问题分布
                qns.append(self.q_obj_builder(type, child_list, 'no', q_type=type + '_negative'))

        self.negative_exists = []
        return qns

    # upper=query,当函数模板为global时调用
    def queryGlobal(self, ent, template):
        qns = []
        if template == 'global':
            qns.append(self.q_obj_builder('global', 'null', 'objects', q_type='global'))
        elif template == 'global_choose':
            for i in ent['elements']:  # ent:entities

                # 调用questionObjectBuilder,产生一个答案为both的QA
                # 得到问题-答案-类型字典，加到qns列表中
                while 1:
                    j = random.choice(ent['elements'])
                    if j != i and j.name.split('_')[0] != i.name.split('_')[0]:
                        break
                qns.append(self.q_obj_builder('global_choose', [(i, j)], 'both', q_type='global_choose_both'))

                # 调用questionObjectBuilder,产生一个答案为object的QA
                obj_present = list(set([x.name.split('_')[0] for x in ent['elements']]))
                obj_not_present = [
                    x for x in self.global_obj_list
                    if x not in obj_present and x not in self.negative_exists
                ]
                if len(obj_not_present) == 0:  # 没有不存在的物体
                    continue

                jj = random.choice(obj_not_present)
                self.negative_exists.append(jj)
                sampled_obj = objectEntity(jj, bbox=[], score=0.0, obj_id=None)
                qns.append(self.q_obj_builder('global_choose', [(i, sampled_obj)], i.name.split('_')[0],
                                              q_type='global_choose_single'))

            self.negative_exists = []

            for i in ent['elements']:  # ent:entities
                # 调用questionObjectBuilder,产生一个答案为none的QA
                obj_present = list(set([x.name.split('_')[0] for x in ent['elements']]))
                obj_not_present = [
                    x for x in self.global_obj_list
                    if x not in obj_present and x not in self.negative_exists
                ]
                while len(obj_not_present) > 1:
                    j1 = random.choice(obj_not_present)
                    j2 = random.choice(obj_not_present)
                    if j1 != j2:
                        break
                self.negative_exists.append(j1)
                self.negative_exists.append(j2)
                sampled_obj1 = objectEntity(j1, bbox=[], score=0.0, obj_id=None)
                sampled_obj2 = objectEntity(j2, bbox=[], score=0.0, obj_id=None)
                qns.append(self.q_obj_builder('global_choose', [(sampled_obj1, sampled_obj2)], 'none',
                                              q_type='global_choose_none'))

        return qns

    # upper=query,当函数模板为count时调用
    def queryCount(self, ent, template):
        qns = []
        if template == 'count':
            qns.append(self.q_obj_builder(template, 'null', len(self.ent_queue['elements']), q_type='count'))
        elif template == 'obj_count':
            # 出现的物体
            obj_present = [x.name.split('_')[0] for x in ent['elements']]
            # 出现的物体（去除重复）
            obj_present_set = list(set(obj_present))  #所有出现过的物体类别
            obj = None
            for i in obj_present_set:
                for j in ent['elements']:
                    if i == j.name.split('_')[0]:
                        obj = j
                        break
                qns.append(
                    self.q_obj_builder(template, [obj], obj_present.count(i), q_type='obj_count')
                )
        elif template == 'rel_count':
            answer_list = self.countEntity(ent)
            for i in answer_list:
                qns.append(self.q_obj_builder(template, i, i[2], q_type='rel_count'))

        return qns

    def queryQuery(self, ent, template):
        qns = []
        answer_list = self.countEntity(ent)
        obj_present = []
        for i in self.entities['objects']:
            obj_present.append(i.name)
        for i in answer_list:
            if i[1] in obj_present:
                obj_present.remove(i[1])

        if template == 'query_what' or template == 'query_which':
            for i in answer_list:
                qns.append(self.q_obj_builder(template, i, i[3], q_type=template + '_positive'))
                if len(obj_present) > 0:  # obj_present could be null
                    j = random.choice(obj_present)
                    obj_present.remove(j)
                    qns.append(self.q_obj_builder(template, [i[0], j], 'nothing', q_type=template + '_negative'))

        if template == 'query_where':
            for i in answer_list:
                for ii in i[3]:
                    qns.append(self.q_obj_builder(template, [i[0], ii], i[0] + ' the ' + i[1], q_type=template))

        return qns

    def queryChoose(self, ent, template):
        qns = []
        answer_list = self.countEntity(ent)

        if template == 'choose_what' or template == 'choose_which':
            for i in answer_list:
                # 产生答案为both的问题
                if i[2] > 1:
                    while 1:
                        j = random.choice(i[3])
                        k = random.choice(i[3])
                        if j != k:
                            break
                    qns.append(self.q_obj_builder(template, [i, (j, k)], 'both', q_type=template + '_both'))

                # 产生答案为object的问题
                obj_present = []
                for ii in self.entities['objects']:
                    obj_present.append(ii.name)
                for ii in i[3]:
                    if ii in obj_present:
                        obj_present.remove(ii)
                for ii in i[3]:
                    j = random.choice(obj_present)
                    obj_present.remove(j)
                    qns.append(self.q_obj_builder(template, [i, (ii, j)], ii, q_type=template + '_single'))

                # 产生答案为none的问题
                j = random.choice(obj_present)
                obj_present.remove(j)
                k = random.choice(obj_present)
                qns.append(self.q_obj_builder(template, [i, (j, k)], 'none', q_type=template + '_none'))

        if template == 'choose_where':
            obj_present = []
            rel_present = []
            for ii in self.entities['objects']:
                obj_present.append(ii.name)
            for ii in self.entities['relations']:
                rel_present.append(ii.name)
            rel_present = list(set(rel_present))

            for i in answer_list:
                while (1):
                    j = random.choice(obj_present)
                    k = random.choice(rel_present)
                    if j != i[1] and k != i[0]:
                        break

                for ii in i[3]:
                    qns.append(
                        self.q_obj_builder(template, [i[0], i[1], k, j, ii], i[0] + ' the ' + i[1], q_type=template))

        return qns

    # upper=queryExists，每个实体调用一次，生成一个QA对
    # template:问题类型 q_ent:第i个实体 a_str:答案字符串 q_type:问题类型
    def questionObjectBuilder(self, template, q_ent, a_str, q_type=None):
        if q_type == None:
            q_type = template

        q_str = self.templates[template]  # 获取问题模板字符串
        query_object = None
        if self.ent_queue['type'] == 'objects':

            # 只能生成一个问题
            if q_ent == 'null':
                if a_str == 'objects':
                    answer = []
                    for ent in self.ent_queue['elements']:
                        answer.append(ent.name.split('_')[0])
                    a_str = list(set(answer))
                    q_str = self.q_str_builder.prepareString(q_str, 'objects', True)
                elif isinstance(a_str, int):
                    a_str = len(self.ent_queue['elements'])
                    q_str = self.q_str_builder.prepareString(q_str, 'objects', True)

            else:
                for ent in q_ent:
                    # 判断ent是否是tuple，如果是，则是二选一的问题
                    if isinstance(ent, tuple):
                        q_str = self.q_str_builder.prepareString(q_str, ent[0].name, True)
                        q_str = self.q_str_builder.prepareString(q_str, ent[1].name, True)
                        query_object = random.choice([ent[0].name, ent[1].name])

                    # 调用prepareString q_str:问题模板 ent.name:实体名
                    else:
                        q_str = self.q_str_builder.prepareString(q_str, ent.name, True)
                        # query_object = ent.name
                        # if q_type == 'obj_count':
                        #     query_object = None

        elif self.ent_queue['type'] == 'relations':
            if template == 'obj_exist':
                q_str = self.q_str_builder.prepareStringForLogic2(q_str, q_ent[1][0], q_ent[1][1], q_ent[0].name, None,
                                                                  True)
                query_object = q_ent[1][0]
            elif template == 'rel_count' or template.find('query') != -1:
                q_str = self.q_str_builder.prepareStringForLogic1(q_str, q_ent[1], q_ent[0], False)
                query_object = q_ent[1]
            elif template == 'choose_what' or template == 'choose_which':
                q_str = self.q_str_builder.prepareStringForLogic1(q_str, q_ent[0][1], q_ent[0][0], False)
                q_str = self.q_str_builder.prepareStringForLogic2(q_str, q_ent[1][0], q_ent[1][1], q_ent[0][0], None,
                                                                  False)
                query_object = q_ent[0][1]
            elif template == 'choose_where':
                q_str = self.q_str_builder.prepareStringForLogic1(q_str, q_ent[4], None, False)
                q_str = self.q_str_builder.prepareStringForLogic2(q_str, q_ent[1], q_ent[3], q_ent[0], q_ent[2],
                                                                  False)
                query_object = q_ent[4]

        # 返回问题、答案、类型的字典
        return {
            'question': q_str,
            'answer': a_str,
            'type': q_type,
            'query_object': query_object
            # 'bbox': bbox
        }

    def searchEntity(self, ent):
        name = [ent.obj.name, ent.sub.name]
        return name

    def countEntity(self, ent):
        answer_list = []
        for i in ent['elements']:  # ent:entities
            answer_list.append([i.name, i.obj.name])
            if i.sub_is_obj:
                answer_list.append([i.name, i.sub.name])
        answer_list = list(set(([tuple(t) for t in answer_list])))

        for i, answer in enumerate(answer_list):
            answer_list[i] = list(answer_list[i])
            answer_list[i].append(0)
            answer_list[i].append([])
            for e in ent['elements']:
                if e.name == answer_list[i][0] and e.obj.name == answer_list[i][1]:
                    answer_list[i][2] += 1
                    answer_list[i][3].append(e.sub.name)
                elif e.name == answer_list[i][0] and e.obj.name == answer_list[i][1] and e.sub_is_obj == True:
                    answer_list[i][2] += 1
                    answer_list[i][3].append(e.obj.name)

        return answer_list


if __name__ == '__main__':
    """
        Env:objects、relations
        objects:该帧的所有物体
        relations:该帧的所有关系
        objects:bbox,id,name,score,time_queue,translations,type
        relations:id,name,obj,score,sub,time_queue,translations,type
    """
    last_frame_idx = 105  # 当前展示视频帧数
    Env = parseEnv(file_idx=last_frame_idx)

    """
        E:问题引擎
        debug
        ent_queue:all entities->根据置信度去除一些实体
        entities:objects and relations
        global_obj_list:decoy
        negative_exists:不存在物体列表
        q_str_builder:articleMap,objects,wnl
        query_fns
        template_defs:模板函数
        template_fns:filter,queues
        threshold:置信度阈值
        use_threshold_score
        use_threshold_size
    """
    E = Engine(Env)

    # res = E.executeFn(['filter.objects'])
    QA_path = "./QA/"
    if not os.path.exists(QA_path):
        os.makedirs(QA_path)
    for i, j in enumerate(E.template_defs):
        QA = open(os.path.join(QA_path, str(i) + ".json"), "w")
        num_qns_for_house = 0
        qns = E.executeFn(E.template_defs[j], j)  # 生成问答对
        num_qns_for_house += len(qns)  # 统计问答对数量
        print('generate {} QAs with {} type'.format(num_qns_for_house, j))
        print([q for q in qns])
        json.dump([q for q in qns], QA)
    E.clearQueue()

    
