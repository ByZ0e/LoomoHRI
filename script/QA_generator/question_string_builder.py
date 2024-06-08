# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

# -*- encoding: utf-8 -*-
'''
@File    :   question_string_builder.py
@Time    :   2024/06/08 12:10:08
@Author  :   ziyi 
@Desc    :   Generates the question string, given the template and filler objects and rooms
'''

from nltk.stem import WordNetLemmatizer


class QuestionStringBuilder():
    def __init__(self):
        self.wnl = WordNetLemmatizer()
        self.articleMap = {'utensil': 'a', 'utensil holder': 'a'}
        """
        Keeps track of all the rooms+objs from where questions have been generated
        """
        self.objects = set()

    """
    Checks if a noun is plural or not; requires nltk
    from https://stackoverflow.com/questions/18911589/how-to-test-whether-a-word-is-in-singular-form-or-not-in-python
    """

    def isPlural(self, word):
        lemma = self.wnl.lemmatize(word, 'n')
        plural = True if word is not lemma else False
        return plural

    """
    Handles auxiliary verbs, articles and plurals
    """

    # upper=questionObjectBuilder template:问题模板 obj:实体名
    def prepareString(self, template, obj, isSplit):
        qString = template

        self.objects.add(obj)

        if isSplit:
            obj = obj.split('_')[0]  # 去掉_

        # 替换
        if '<AUX>' in qString or '<AUX-plural>' in qString:  # 助动词替换
            qString = self.replaceAux(qString, obj)
        if '<ARTICLE>' in qString or '<ARTICLE-sure>' in qString:  # 冠词替换
            qString = self.replaceArticle(qString, obj)
        if '<OBJ>' in qString or '<OBJ-plural>' in qString:  # 物体替换
            qString = self.replaceObj(qString, obj)
        return qString

    def prepareStringForLogic1(self, template, obj, op, isSplit):
        qString = template
        self.objects.add(obj)

        if isSplit:
            obj = obj.split('_')[0]

        if '<AUX>' in qString or '<AUX-plural>' in qString:  # 助动词替换
            qString = self.replaceAux(qString, obj)
        if '<ARTICLE>' in qString or '<ARTICLE-sure>' in qString:  # 冠词替换
            qString = self.replaceArticle(qString, obj)
        if '<OBJ>' in qString:  # 物体替换
            qString = self.replaceObjForLogic(qString, obj, None)
        if '<LOGIC>' in qString:  # 关系替换
            qString = self.replaceOp1(qString, op)
        return qString

    def prepareStringForLogic2(self, template, obj1, obj2, op1, op2, isSplit):
        qString = template

        self.objects.add(obj1)
        self.objects.add(obj2)

        if isSplit:
            obj1 = obj1.split('_')[0]
            obj2 = obj2.split('_')[0]

        if '<AUX>' in qString or '<AUX-plural>' in qString:  # 助动词替换
            qString = self.replaceAux(qString, obj1)

        if '<ARTICLE>' in qString or '<ARTICLE-sure>' in qString:  # 冠词替换
            qString = self.replaceArticle(qString, obj1)
            if '<ARTICLE>' in qString or '<ARTICLE-sure>' in qString:
                qString = self.replaceArticle(qString, obj2)

        if '<OBJ1>' in qString or '<OBJ2>' in qString:  # 物体替换
            qString = self.replaceObjForLogic(qString, obj1, obj2)

        if '<LOGIC>' in qString:  # 关系替换
            qString = self.replaceOp1(qString, op1)
        if '<LOGIC1>' in qString and '<LOGIC2>' in qString:  # 关系替换
            qString = self.replaceOp2(qString, op1, op2)
        return qString

    def replaceOp1(self, template, op):
        template = template.replace('<LOGIC>', op)
        return template

    def replaceOp2(self, template, op1, op2):
        template = template.replace('<LOGIC1>', op1)
        template = template.replace('<LOGIC2>', op2)

        return template

    def replaceAux(self, template, obj):
        if '<AUX>' in template:
            if self.isPlural(obj):
                return template.replace('<AUX>', 'are')
            else:
                return template.replace('<AUX>', 'is')
        elif '<AUX-plural>' in template:
            return template.replace('<AUX-plural>', 'are')

    def replaceArticle(self, template, obj):
        if '<ARTICLE>' in template:
            if self.isPlural(obj):
                return template.replace(' <ARTICLE>', '', 1)
            else:
                if obj in self.articleMap:
                    return template.replace('<ARTICLE>', self.articleMap[obj], 1)
                elif obj[0] in ['a', 'e', 'i', 'o', 'u']:
                    return template.replace('<ARTICLE>', 'an', 1)
                else:
                    return template.replace('<ARTICLE>', 'a', 1)
        if '<ARTICLE-sure>' in template:
            return template.replace('<ARTICLE-sure>', 'the', 1)

    def replaceObj(self, template, obj):
        if '<OBJ>' in template:
            return template.replace('<OBJ>', obj, 1)
        elif '<OBJ-plural>' in template:
            if self.isPlural(obj):
                return template.replace('<OBJ-plural>', obj)
            else:
                return template.replace('<OBJ-plural>', obj + 's')

    def replaceObjForLogic(self, template, obj1, obj2):
        template = template.replace('<OBJ>', obj1)
        if obj2 is not None:
            template = template.replace('<OBJ1>', obj1)
            template = template.replace('<OBJ2>', obj2)
        return template


if __name__ == '__main__':
    q_str_builder = QuestionStringBuilder()
    q_string = q_str_builder.prepareString(
        "is there a <OBJ> in the room?",
        "ceiling_fan",
        True
    )
    q_string_for_logic = q_str_builder.prepareStringForLogic2(
        "<AUX> there <ARTICLE> <OBJ1> <LOGIC> <ARTICLE> <OBJ2> in the room",
        "ottoman", "chairs", "and", True)

    print(q_string_for_logic)
    print(q_string)
    print(q_str_builder.objects)
