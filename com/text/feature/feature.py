# encoding: utf-8
from __future__ import division

import copy
import math
import os
import time
from compiler.ast import flatten

from sklearn.feature_extraction.text import TfidfTransformer

from com.constant.constant import TEXT_OUT, EMOTION_CLASS, OBJECTIVE_CLASS
from com.text import Feature_Hasher
from com.text.feature.vectorize.another_improve_tf_idf import TfidfImproveSec
from com.text.feature.vectorize.improve_tf_idf import TfidfImprove
from com.text.load_sample import Load
from com.text.split_words_nlpir import SplitWords
from com.utils.fileutil import FileUtil

__author__ = 'zql'
__date__ = '2015/11/12'


class Feature(object):
    """
    文本特征词抽取
    """
    def __init__(self, f=False, subjective=True):
        # f 开关，将分词后的结果写入到文本中
        #   若资源有更新，可以打开开关，强制写入新的分词后的结果
        self.f = f
        self.istrain = False
        self.subjective = subjective

    def get_key_words(self, sentences=None):
        """
        获取关键词
        如果 sentences 为 None，则获取训练集中的关键词
        否则获取 sentences 中的关键词
        :param sentences
        :return:
        """
        if sentences is None:
            self.istrain = True
        else:
            self.istrain = False

        print "%s/%s/%s" % ("emotion" if self.subjective else "subjective",
                            "train" if self.istrain else "test",
                            self.__class__.__name__)
        splited_words_list, sentence_size = self._split(sentences)

        return self._collect(splited_words_list, sentence_size)
#        if self.istrain:
#            return self._collect(splited_words_list, sentence_size)
#        else:
#            class_label = [d.get("emotion-1-type") for d in splited_words_list[: sentence_size]]
#            return splited_words_list[: sentence_size], class_label

    def cal_weight(self, key_words):
        """
        计算获取特征词后的权重信息
        :param key_words: [{'sentence': {}}, ...] or [{}, ...] 有可能是测试集数据有可能是训练集数据
        :return:
        """
        print "Cal Weight: ", time.strftime('%Y-%m-%d %H:%M:%S')
        if not self.istrain:
            dir_ = os.path.join(TEXT_OUT, "key_words")
            filename = self.__class__.__name__ + ".txt" if self.subjective else self.__class__.__name__ + "_objective.txt"
            url = os.path.join(dir_, filename)
            train_key_words = FileUtil.read(url)
        else:
            train_key_words = key_words
        train_key_words = [d.get("sentence") if "sentence" in d else d for d in train_key_words]
        key_words = [d.get("sentence") if "sentence" in d else d for d in key_words]
        # 获得 tf
        key_words = [{k: v / sum(d.values()) for k, v in d.items()} for d in key_words]
        fit_train_key_words = Feature_Hasher.transform(train_key_words)
        fit_key_words = Feature_Hasher.transform(key_words)
        tfidf = TfidfTransformer()
        # 训练 idf
        tfidf.fit(fit_train_key_words)
        weight_matrix = tfidf.transform(fit_key_words)
        print "Cal Weight Done: ", time.strftime('%Y-%m-%d %H:%M:%S')
        print
        return weight_matrix

    def cal_weight_improve(self, key_words, class_label):
        """
        计算获取特征词后的权重信息
        :param key_words: [{'sentence': {}}, ...] or [{}, ...] 有可能是测试集数据有可能是训练集数据
        :return:
        """
        print "Cal Improve Weight: ", time.strftime('%Y-%m-%d %H:%M:%S')
        if not self.istrain:
            dir_ = os.path.join(TEXT_OUT, "key_words")
            filename = self.__class__.__name__ + ".txt" if self.subjective else self.__class__.__name__ + "_objective.txt"
            url = os.path.join(dir_, filename)
            train_key_words = FileUtil.read(url)
            train_class_label = [d.get("emotion-1-type") for d in train_key_words]
        else:
            train_key_words = key_words
            train_class_label = class_label
        train_key_words = [d.get("sentence") if "sentence" in d else d for d in train_key_words]
        key_words = [d.get("sentence") if "sentence" in d else d for d in key_words]
        # 获得 tf
        key_words = [{k: v / sum(d.values()) for k, v in d.items()} for d in key_words]
        fit_train_key_words = Feature_Hasher.transform(train_key_words)
        fit_key_words = Feature_Hasher.transform(key_words)
        tfidf = TfidfImprove()
        # 训练 idf
        tfidf.fit(fit_train_key_words, train_class_label)
        weight_matrix = tfidf.transform(fit_key_words, class_label)
        print "Cal Weight Done: ", time.strftime('%Y-%m-%d %H:%M:%S')
        print
        return weight_matrix

    def cal_weight_improve_sec(self, key_words, class_label):
        """
        计算获取特征词后的权重信息
        :param key_words: [{'sentence': {}}, ...] or [{}, ...] 有可能是测试集数据有可能是训练集数据
        :return:
        """
        print "Cal Improve Second Weight: ", time.strftime('%Y-%m-%d %H:%M:%S')
        if not self.istrain:
            dir_ = os.path.join(TEXT_OUT, "key_words")
            filename = self.__class__.__name__ + ".txt" if self.subjective else self.__class__.__name__ + "_objective.txt"
            url = os.path.join(dir_, filename)
            train_key_words = FileUtil.read(url)
            train_class_label = [d.get("emotion-1-type") for d in train_key_words]
        else:
            train_key_words = key_words
            train_class_label = class_label
        train_key_words = [d.get("sentence") if "sentence" in d else d for d in train_key_words]
        key_words = [d.get("sentence") if "sentence" in d else d for d in key_words]

        fit_train_key_words = Feature_Hasher.transform(train_key_words)
        fit_key_words = Feature_Hasher.transform(key_words)
        tfidf = TfidfImproveSec()
        # 训练 idf
        tfidf.fit(fit_train_key_words, train_class_label)
        weight_matrix = tfidf.transform(fit_key_words, class_label)
        print "Cal Weight Done: ", time.strftime('%Y-%m-%d %H:%M:%S')
        print
        return weight_matrix

    def cal_score(self, t, sentence, label, class_sentences, sentences):
        """
        计算特征词 t 的得分
        :param t: 特征词
        :param sentence: 特征词所在的句子，分词后
        :param label: 类别
        :param class_sentences: 带有类别信息的句子集，即类别 c 下的句子集，最好也是分词后（不分词貌似也不影响）
        :param sentences: 句子集，最好也是分词后（不分词貌似也不影响）
        :return:
        """
        pass

    def _split(self, sentences):
        # 加载分词后的训练集
        print "Before Split: ", time.strftime('%Y-%m-%d %H:%M:%S')
        splited_words_list = self._get_splited_train()
        sentence_size = len(splited_words_list)

        if sentences is not None:
            l = Feature.__pre_process(sentences)

            splited_sentence_list = Feature.__split(flatten(l))
#            splited_sentence_list = Feature.__del_low_frequency_word(splited_sentence_list)

            splited_words_list = splited_sentence_list + splited_words_list
            sentence_size = len(splited_sentence_list)

        print "Split Done: ", time.strftime('%Y-%m-%d %H:%M:%S')

        return splited_words_list, sentence_size

    def _collect(self, splited_words_list, sentence_size):
        dir_ = os.path.join(TEXT_OUT, "key_words")
        if self.subjective:
            key_words_txt = os.path.join(dir_, self.__class__.__name__ + ".txt")
        else:
            key_words_txt = os.path.join(dir_, self.__class__.__name__ + "_objective.txt")
#        def norm(word_scores):
#            """
#            以样本为单位正则化
#            归一化（正则化）
#            Normalization 主要思想是对每个样本计算其p-范数，然后对该样本中每个元素除以该范数，
#            这样处理的结果是使得每个处理后样本的p-范数（l1-norm,l2-norm）等于1。
#
#            p-范数的计算公式：||X||p=(|x1|^p+|x2|^p+...+|xn|^p)^1/p
#
#            该方法主要应用于文本分类和聚类中。
#
#            :param word_scores: a dict {word: score}
#            """
#            p = 0.0
#            for v in word_scores.values():
#                p += math.pow(math.fabs(v), 2)
#            p = math.pow(p, 1.0 / 2)
#
#            for k, v in word_scores.items():
#                word_scores[k] = v / p

#        def reduce_dim(word_scores):
#            """
#            降维：选取累加权重信息占比超过 0.9 的特征词
#            """
#            _size = len(word_scores)
#            _max = math.pow(_size, 1.0 / 2) * 0.85
#            res = {}
#            # 降序排序
#            sort = sorted(word_scores.items(), key=lambda x: x[1], reverse=True)
#            _sum = 0.0
#            for k, v in sort:
#                if(_sum > _max):
#                    break
#                res[k] = v
#                _sum += v
#            return res

        if not self.istrain or self.f or not FileUtil.isexist(key_words_txt) or FileUtil.isempty(key_words_txt):
            print "Cal Scores: ", time.strftime('%Y-%m-%d %H:%M:%S')
            if len(splited_words_list) == sentence_size:
                train_range = slice(sentence_size)
            else:
                train_range = slice(sentence_size, len(splited_words_list))

            # 获取所有类别下的文本
            all_class_datas = Feature.all_class_text(splited_words_list[train_range], self.getclasses())

            # 获取类别标签
            class_label = [d.get("emotion-1-type") for d in splited_words_list[: sentence_size]]

            # return term/frequency or term/score
            res = []
            for splited_words_dict in splited_words_list[0: sentence_size]:
                splited_words = splited_words_dict.get("sentence")
                label = splited_words_dict.get("emotion-1-type")
                # 计算每个单词的得分 scores: {word: [score, frequency], ...}
                scores = {splited_word: [self.cal_score(splited_word, splited_words, label, all_class_datas,
                                                        [d.get("sentence") for d in splited_words_list[train_range]]),
                                         frequency]
                          for splited_word, frequency in splited_words.items()}
                # 归一化
                # norm(scores)
                # 降维处理
                sorted_words = scores
#                if not self.istrain:
#                    sorted_words = reduce_dim(scores)

                # Collection
                # if False return term/score
                # if True  return term/frequency
#                if False:
#                    for k in sorted_words.keys():
#                        sorted_words[k] = splited_words.count(k)

                res.append({"sentence": sorted_words,
                            "emotion-1-type": splited_words_dict.get("emotion-1-type")})
            print "Cal Scores Done: ", time.strftime('%Y-%m-%d %H:%M:%S')
            # FileUtil.write(TEST_BASE_URL + "scores.txt", res)
            print "Begin Normalization: ", time.strftime('%Y-%m-%d %H:%M:%S')
            # 归一化
            self.norm(res)
            # FileUtil.write(TEST_BASE_URL + "norm.txt", res)
            print "Normalization Done: ", time.strftime('%Y-%m-%d %H:%M:%S')

            print "Begin Reduce: ", time.strftime('%Y-%m-%d %H:%M:%S')
            # 降维
            self.reduce_dim(res)
            print "Reduce Done: ", time.strftime('%Y-%m-%d %H:%M:%S')

            # Try Convert term/score to term/frequency
            # if False return term/score
            # if True  return term/frequency
            for d in res:
                ws = d.get("sentence")
                for k, v in ws.items():
                    ws[k] = v[0]
                    if True:
                        ws[k] = v[1]

            # 由于分词或降维的过程中，有可能因为样本的信息关键词不够，
            # 使得该样本经过上诉步骤后为空，返回这类样本的索引
            danger_index = []
            res = filter(lambda x: danger_index.append(x[0]) if not x[1].get("sentence") else x,
                         enumerate(res))
            res = list(zip(*res)[1])

            class_label = [c for i, c in enumerate(class_label)
                           if i not in danger_index]

            # 写入文件
            if self.istrain:
                FileUtil.write(key_words_txt, res)
        else:
            res = FileUtil.read(key_words_txt)
            class_label = [r["emotion-1-type"] for r in res]
            danger_index = []

        # 输出统计信息
        if False:
            self.__print_top_key_word(res)
        return res, class_label, danger_index

    def _get_splited_train(self):
        """
        优先从文件中读取训练集分词后的结果
        :return:
        """
        dir_ = os.path.join(TEXT_OUT, "split")
        if self.subjective:
            split_txt = os.path.join(dir_, self.__class__.__name__ + ".txt")
            training_datas = Load.load_training_balance()
        else:
            split_txt = os.path.join(dir_, self.__class__.__name__ + "_objective.txt")
            training_datas = Load.load_training_objective_balance()

        if self.f or not FileUtil.isexist(split_txt) or FileUtil.isempty(split_txt):
            # 加载训练集
            # 每个句子还包含类别信息
            splited_words_list = Feature.__split(flatten(training_datas))
#            splited_words_list = Feature.__del_low_frequency_word(splited_words_list)

            FileUtil.write(split_txt, splited_words_list)
        else:
            splited_words_list = FileUtil.read(split_txt)

        return splited_words_list

    def norm(self, word_scores):
        """
        以类别为单位正则化
        归一化（正则化）
        Normalization 主要思想是对每个样本计算其p-范数，然后对该样本中每个元素除以该范数，
        这样处理的结果是使得每个处理后样本的p-范数（l1-norm,l2-norm）等于1。

        p-范数的计算公式：||X||p=(|x1|^p+|x2|^p+...+|xn|^p)^1/p

        该方法主要应用于文本分类和聚类中。

        :param word_scores: a list [{emotion-1-type: "like", sentence: {word: score}}, ...]
        """
        def norm_0(c0):
            word_score = reduce(Feature.union, all_class.get(c), {})
            p = 0.0
            for k, v in word_score.items():
                p += math.pow(math.fabs(v[0]), 2)
            p = math.pow(p, 1.0 / 2)

            for d in word_scores:
                if d.get("emotion-1-type") == c0:
                    ws = d.get("sentence")
                    for k, v in ws.items():
                        ws[k][0] = v[0] / p

        all_class = Feature.all_class_text(word_scores, self.getclasses() + ["unknow"])
        for c in all_class.keys():
            norm_0(c)

    def reduce_dim(self, word_scores):
        """
        降维：选取累加权重信息占比超过 0.9 的特征词
        :param word_scores
        """
        def reduce_dim_0(c0):
            word_score = reduce(Feature.union, all_class.get(c0), {})
#            _sum = 0.0
#            for k, v in word_score.items():
#                _sum += v[0]
#            _max = _sum * 0.85
            _size = len(word_score)
            _max = math.pow(_size, 1.0 / 2) * 0.85

            res = []
            # 降序排序
            sort = sorted(word_score.items(), key=lambda x: x[1][0], reverse=True)
            _sum = 0.0
            for k, v in sort:
                if(_sum > _max):
                    break
                res.append(k)
                _sum += v[0]

            for d in word_scores:
                if d.get("emotion-1-type") == c0:
                    ws = d.get("sentence")
                    for k, v in ws.items():
                        if k in res:
                            ws[k][2] = 1

        # 初始化 word_scores, 为每个单词增加一个标记 mark
        # 初始值 0, 若这个单词允许保留，则改为 1
        for d in word_scores:
            ws = d.get("sentence")
            for k, v in ws.items():
                ws[k].append(0)

        all_class = Feature.all_class_text(word_scores, self.getclasses() + ["unknow"])

        [reduce_dim_0(c) for c in all_class.keys()]

        # 保持 word_scores 的形式不变，删除 mark 标记
        # 若 1, 则只需要删除 mark 标记；若 0，则删除单词
        for d in word_scores:
            ws = d.get("sentence")
            ws_0 = copy.deepcopy(ws)
            for k, v in ws_0.items():
                if v[2] == 1:
                    ws[k].pop()
                else:
                    del ws[k]

    def getclasses(self):
        if self.subjective:
            classes = EMOTION_CLASS.keys()
        else:
            classes = OBJECTIVE_CLASS.keys()
        return classes

    @staticmethod
    def tf(word, words):
        """
        计算词频
        :param word:
        :param words: is a list
        :return:
        """
        return words.count(word) / len(words)

    @staticmethod
    def n_contains(word, wordslist):
        # 计算特征词 word 在文档集 wordslist 中出现的文档数
        return sum(1 for words in wordslist if word in words)

    @staticmethod
    def all_class_text(datas, classes):
        def each_class_text(c):
            # 获取 datas 下，类别 c 的文本
            return [data.get("sentence") for data in datas if data.get("emotion-1-type") == c]
        # 将 datas 下的数据以 {类别 ：[文档]} 的形式返回
        return {c: each_class_text(c) for c in classes}

    @staticmethod
    @DeprecationWarning
    def __each_class_text(datas, c):
        # 获取 datas 下，类别 c 的文本
        if c not in EMOTION_CLASS.keys():
            raise ValueError("have no emotion class")
        return [data.get("sentence") for data in datas if data.get("emotion-1-type") == c]

    @staticmethod
    def __pre_process(sentences):
        def process_str(s):
            return {"emotion-1-type": "unknow", "sentence": s}

        def process_dict(s):
            if not s.has_key("emotion-1-type") or not s.has_key("sentence"):
                raise AttributeError("dict has no emotion-1-type or sentence key")
            return s

        res = list()
        l = list()
        l.append(sentences)
        sentence_list = flatten(l)
        for sentence in sentence_list:
            if isinstance(sentence, basestring):
                res.append(process_str(sentence))
            if isinstance(sentence, dict):
                res.append(process_dict(sentence))
        return res

    @staticmethod
    def __split(sentence_list):
        SplitWords.__init__()

        l = []
        for sentence in sentence_list:
            splited_words = SplitWords.split_words(sentence.get("sentence"))
#            if splited_words:
            d = {}
            d["emotion-1-type"] = sentence.get("emotion-1-type")
            d["sentence"] = {splited_word: splited_words.count(splited_word)
                             for splited_word in set(splited_words)}
            l.append(d)

        SplitWords.close()
        return l

    @staticmethod
    def __del_low_frequency_word(splited_words_list):
        """
        删除频率 <= 3 的词汇，因这些词汇有可能是生僻词或表意能力比较差的词
        :return:
        """
        def fun(splited_words):
            splited_words_0 = splited_words.get("sentence")
            aa = filter(lambda x: x[0] in leave, splited_words_0.items())
            splited_words["sentence"] = {a[0]: a[1] for a in aa}

        final = reduce(Feature.union, [d.get("sentence") for d in splited_words_list])
        # 单词总数
        words_sum = sum(final.values())
        # words_sum = sum([sum(d.get("sentence").values()) for d in current_splited_words])
        # 阖值, 词频小于等于该阖值将删除
        max_ = min(0.0001 * words_sum, 1)
        leave = filter(lambda x: x[1] > max_, final.items())
        leave = {d[0]: d[1] for d in leave}
        leave_words_sum = sum(leave.values())
        map(fun, splited_words_list)
        return [d for d in splited_words_list if d.get("sentence")]

    @staticmethod
    def union(dict1, dict2):
        """
        合并两个字典
        if has the same key, then add value
        else append {key: value}
        :param dict1: {key: [weight, frequency]} or {key: frequency}
        :param dict2: {key: [weight, frequency]} or {key: frequency}
        :return: d
        """
        d = dict(dict1)
        for k, v in dict2.items():
            if k in dict1:
                if hasattr(v, "__getitem__"):
                    d[k] = [(d[k][0] + v[0]) / 2, d[k][1] + v[1]]
                    # d[k][0] = (d[k][0] + v[0]) / 2
                    # d[k][1] += v[1]
                else:
                    d[k] = d[k] + v
            else:
                d[k] = v
        return d

    def __print_top_key_word(self, res):
        all_class = Feature.all_class_text(res, self.getclasses())
        for c in all_class.keys():
            each_class = reduce(Feature.union, all_class.get(c))
            sort = sorted(each_class.items(), key=lambda x: x[1], reverse=True)
            sort = sort[0:50]
            print c
            for k, v in sort:
                print k.decode("utf-8") + ":" + str(v)
            print
        print

if __name__ == "__main__":
    ss = "我在高楼高楼上高楼"
    s = "高楼"
    print ss.count(s)
    print len(ss)
    print Feature.tf(s, ss)
    if s in ss:
        print "Yes"
