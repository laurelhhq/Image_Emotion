# encoding: utf-8
import os

import numpy as np
import scipy.sparse as sp
import time
from sklearn import cross_validation
from sklearn.feature_extraction import FeatureHasher
from sklearn.metrics import precision_score, recall_score, f1_score, zero_one_loss, accuracy_score

from com import EMOTION_CLASS, OBJECTIVE_CLASS, RESOURCE_BASE_URL
from com.text.bayes import Bayes
from com.text.feature.chi_feature import CHIFeature
from com.text.load_sample import Load
from com.text.utils.fileutil import FileUtil

__author__ = 'root'
__date__ = '15-12-13'


class Classification:
    """
    分类
    """
    def __init__(self, f=False, bayes=Bayes(), subjective=True):
        # f 开关，将分词后的结果写入到文本中
        #   若资源有更新，可以打开开关，强制写入新的分词后的结果
        self.f = f
        self.bayes = bayes
        self.subjective = subjective
        # 特征词 Hash 散列器
        self.feature_hasher = FeatureHasher(n_features=600000, non_negative=True)

    def get_classificator(self, train_datas, class_label, iscrossvalidate=False):
        """
        获取分类器
        :param train_datas
        :param class_label
        :param iscrossvalidate 是否需要读取交叉验证后的结果来获得训练器
        :return:
        """
        out = os.path.join(RESOURCE_BASE_URL, "best_train_test_index/train_index.txt")
        if iscrossvalidate and (not FileUtil.isexist(out) or FileUtil.isempty(out)):
            raise ValueError("please use cross_validation() firstly")

        # fit data
        fit_train_datas = self.fit_data(train_datas)
        class_label = np.array(class_label)

        if iscrossvalidate:
            train_index = np.loadtxt(out, dtype=int)
        else:
            train_index = np.array(range(fit_train_datas.shape[0]))

        # 训练模型
        self.bayes.fit(fit_train_datas[train_index], class_label[train_index])
        return self

    def get_incr_classificator(self, incr_datas, test_datas, test_class_label):
        """
        对增量式贝叶斯的增量集部分进行处理
        :param incr_datas: [{"emorion-1-type": value, "sentence": {}},...]
                            (emotion-1-type and sentence are optional)
        :param test_datas:
        :param test_class_label:
        :return:
        """
        print "Begin Increment Classification: ", time.strftime('%Y-%m-%d %H:%M:%S')
        # 将参数写入/读取
        dir_ = os.path.join(RESOURCE_BASE_URL, "bayes_args")
        FileUtil.mkdirs(dir_)

        class_count_out = os.path.join(dir_, "class_count.txt")
        class_log_prob_out = os.path.join(dir_, "class_log_prob.txt")
        feature_count_out = os.path.join(dir_, "feature_count.txt")
        feature_log_prob_out = os.path.join(dir_, "feature_log_prob.txt")

        out = (class_count_out, class_log_prob_out, feature_count_out, feature_log_prob_out)

        if self.f or not FileUtil.isexist(out) or FileUtil.isempty(out):
            if not hasattr(self.bayes, "feature_log_prob_") or not hasattr(self.bayes, "class_log_prior_"):
                raise ValueError("please use get_classificator() to get classificator firstly")

            for i in range(len(incr_datas)):
                if i % 5 == 0:
                    print "Begin Increment Classification_%d: %s" % (i / 5, time.strftime('%Y-%m-%d %H:%M:%S'))
                # 分类损失，求最大值的处理方式
                loss = 0
                # 增量集中优先选择更改分类器参数的文本
                text = None
                # 增量集中优先选择更改分类器参数的文本所对应的类别
                c_pred = None
                # 增量集中优先选择更改分类器参数的文本所对应的下标
                index = 0

                origin_class_log_prob_ = self.bayes.class_log_prior_
                origin_feature_log_prob_ = self.bayes.feature_log_prob_
                for i0, data in enumerate(incr_datas):
                    c_true0 = data.get("emotion-1-type", "unknow")
                    text0 = [data.get("sentence") if "sentence" in data else data]
                    # todo
                    # predict 接受的参数是计算过权重后，而这里的 text0 是未计算权重的，这里是否有影响？
                    c_pred0 = self.predict(text0)[0]
                    text0 = text0[0]
                    if c_true0 == c_pred0:
                        text = text0
                        c_pred = c_pred0
                        index = i0
                        break
                    else:
                        self.bayes.class_log_prior_, self.bayes.feature_log_prob_ = self.bayes.update(c_pred0, text0, copy=True)
                        loss0 = self.metrics_my_zero_one_loss(test_datas)
                        if loss0 > loss:
                            loss = loss0
                            text = text0
                            c_pred = c_pred0
                            index = i0

                    self.bayes.class_log_prior_ = origin_class_log_prob_
                    self.bayes.feature_log_prob_ = origin_feature_log_prob_

                self.bayes.update(c_pred, text)
                del incr_datas[index]

            bayes_args = (self.bayes.class_count_, self.bayes.class_log_prior_,
                          self.bayes.feature_count_, self.bayes.feature_log_prob_)
            map(lambda x: np.savetxt(x[0], x[1]), zip(out, bayes_args))
        else:
            self.bayes.class_count_ = np.loadtxt(out[0])
            self.bayes.class_log_prior_ = np.loadtxt(out[1])
            self.bayes.feature_count_ = np.loadtxt(out[2])
            self.bayes.feature_log_prob_ = np.loadtxt(out[3])

        print "Increment Classification Done: ", time.strftime('%Y-%m-%d %H:%M:%S')
        return self

    def predict(self, test_datas):
        """
        预测
        :param test_datas:
        :return: [n_samples,]
        """
        # fit data
        fit_test_datas = self.fit_data(test_datas)

        # 预测
        return self.bayes.predict(fit_test_datas)

    def predict_proba(self, test_datas):
        """
        预测每个样本属于每个类别的概率
        :param test_datas:
        :return: [n_samples, n_class]
        """
        # fit data
        fit_test_datas = self.fit_data(test_datas)

        return self.bayes.predict_proba(fit_test_datas)

    def predict_unknow(self, test_datas):
        """
        预测，若预测的概率小于一定的阖值，则输出 unknow
        :param test_datas:
        :return:
        """
        _max = 0.3

        # proba: [n_samples, n_class]
        proba = self.predict_proba(test_datas)
        max_proba_index = np.argmax(proba, axis=1)

        rowid = 0
        res = []
        for row in proba:
            index = max_proba_index[rowid]
            c = self.bayes.classes_[index] if row[index] > _max else "unknow"
            res.append(c)
            rowid += 1
        return res

    def cross_validation(self, train_datas, class_label, score='precision'):
        """
        K-Fold Cross Validation
        采用交叉验证的方式来优化贝叶斯参数
        选出具有最佳 score 的训练集和测试集
        此时训练集和测试集就不需要事先选好，交给交叉验证来完成
        :param train_datas:
        :param class_label:
        :param score:
        :return:
        """
        score_options = ('precision', 'recall', 'f1', 'accuracy')
        if score not in score_options:
            raise ValueError('score has to be one of ' +
                             str(score_options))

        # fit data
        fit_train_datas = self.fit_data(train_datas)

        n_samples = fit_train_datas.shape[0]
        class_label = np.array(class_label)

        max_result = []
        max_index = []
        max_ = 0
        i = 0
        while(max_ < 0.6 and i <= 200):
            i += 1
            print "Seeking %d; max: %f; %s" % (i, max_, time.strftime('%Y-%m-%d %H:%M:%S'))

            result = []
            index = []
            cv = cross_validation.KFold(n_samples, n_folds=10, shuffle=True)

            for train_index, test_index in cv:
                train0, train0_label = fit_train_datas[train_index], class_label[train_index]
                test0, test0_label = fit_train_datas[test_index], class_label[test_index]
                self.get_classificator(train0, train0_label)
                c_pred0 = self.predict(test0)

                if score == "precision":
                    result.append(self.metrics_precision(test0_label, c_pred0))
                    index.append((train_index, test_index))
                elif score == "recall":
                    result.append(self.metrics_recall(test0_label, c_pred0))
                    index.append((train_index, test_index))
                elif score == "f1":
                    result.append(self.metrics_f1(test0_label, c_pred0))
                    index.append((train_index, test_index))
                else:
                    result.append(self.metrics_accuracy(test0_label, c_pred0))
                    index.append((train_index, test_index))

            max_ = max(result)
            max_result.append(max_)
            max_index.append(index[np.argmax(result)])

        argmax = np.argmax(max_result)
        print "Seeking Done; max: %f; %s" % (max_result[argmax], time.strftime('%Y-%m-%d %H:%M:%S'))

        # 对最大值再训练一次，得到最优的参数
        self.get_classificator(fit_train_datas[max_index[argmax][0]], class_label[max_index[argmax][0]])

        dir_ = os.path.join(RESOURCE_BASE_URL, "best_train_test_index")
        FileUtil.mkdirs(dir_)
        current = time.strftime('%Y-%m-%d %H:%M:%S')
        train_index_out = os.path.join(dir_, current + "train_index.txt")
        test_index_out = os.path.join(dir_, current + "test_index.txt")

        map(lambda x: np.savetxt(x[0], x[1], fmt="%d"),
            zip(
                    (train_index_out, test_index_out),
                    (max_index[argmax])
                )
            )

    def metrics_precision(self, c_true, c_pred):
        fit_true_pred = self.__del_unknow(c_true, c_pred)
        c_true_0 = fit_true_pred[0]
        c_pred_0 = fit_true_pred[1]
        classes = self.getclasses()
        pos_label, average = self.__get_label_average(classes)
        return precision_score(c_true_0, c_pred_0, labels=classes, pos_label=pos_label, average=average)

    def metrics_recall(self, c_true, c_pred):
        fit_true_pred = self.__del_unknow(c_true, c_pred)
        c_true_0 = fit_true_pred[0]
        c_pred_0 = fit_true_pred[1]
        classes = self.getclasses()
        pos_label, average = self.__get_label_average(classes)
        return recall_score(c_true_0, c_pred_0, labels=classes, pos_label=pos_label, average=average)

    def metrics_f1(self, c_true, c_pred):
        fit_true_pred = self.__del_unknow(c_true, c_pred)
        c_true_0 = fit_true_pred[0]
        c_pred_0 = fit_true_pred[1]
        classes = self.getclasses()
        pos_label, average = self.__get_label_average(classes)
        return f1_score(c_true_0, c_pred_0, labels=classes, pos_label=pos_label, average=average)

    def metrics_accuracy(self, c_true, c_pred):
        fit_true_pred = self.__del_unknow(c_true, c_pred)
        c_true_0 = fit_true_pred[0]
        c_pred_0 = fit_true_pred[1]
        return accuracy_score(c_true_0, c_pred_0)

    def metrics_zero_one_loss(self, c_true, c_pred):
        fit_true_pred = self.__del_unknow(c_true, c_pred)
        c_true_0 = fit_true_pred[0]
        c_pred_0 = fit_true_pred[1]
        return zero_one_loss(c_true_0, c_pred_0)

    def metrics_my_zero_one_loss(self, test_datas):
        """
        依据增量式贝叶斯论文所提供的分类损失度的计算方式
        :param test_datas:
        :return:
        """
        # fit data
        fit_test_datas = self.fit_data(test_datas)

        n_samples = fit_test_datas.shape[0]
        proba = self.predict_proba(test_datas)
        # 计算每个样本最大的概率，即每个样本最应该属于某个类别的概率
        max_proba = np.max(proba, axis=1)
        return np.sum(1 - max_proba) / (n_samples - 1)

    def metrics_correct(self, c_true, c_pred):
        # 不能过滤 unknow 部分，因统计时需要
        self._correct(c_true, c_pred, labels=self.getclasses())

    def _correct(self, c_true, c_pred, labels=None):
        def _diff(label_tuple):
            """
            if label0 == label1:
                return the (index + 1) of label0 in labels
            if label0 != label1 and label1 == 'unknow':
                return the (-1) * (index + 1) of label0 in labels
            else:
                return 0

            :param label0:
            :param label1:
            :return:
            """
            label0, label1 = label_tuple

            if label0 == label1:
                return labels.index(label0) + 1
            elif label1 == "unknow":
                return (labels.index(label0) + 1) * (-1)
            else:
                return 0

        if len(c_true) != len(c_pred):
            raise ValueError("the two lists have different size!")

        present_labels = set(c_true)
        if labels is None:
            labels = list(present_labels)

        # 每个类别共有的样本数
        true_sum = [c_true.count(c) for c in labels]

        # 每个类别预测的样本数
        pred = c_pred if isinstance(c_pred, list) else c_pred.tolist()
        pred_sum = [pred.count(c) for c in labels]

        # 每个类别下预测的正确数
        diff = map(_diff, zip(c_true, c_pred))
        tp_sum = [diff.count(i + 1) for i, c in enumerate(labels)]

        # 每个类别 unknow 数
        unknow_sum = [diff.count(-i - 1) for i, c in enumerate(labels)]

        # print
        for i, c in enumerate(labels):
            print(c)
            print("total samples: %d" % true_sum[i])
            print("predict correct: %d" % tp_sum[i])
            print("predict others into this class: %d" % (pred_sum[i] - tp_sum[i]))
            print("predict unknow: %d" % unknow_sum[i])
            print("predict incorrect: %d" % (true_sum[i] - tp_sum[i] - unknow_sum[i]))
            print

    def getclasses(self):
        if self.subjective:
            classes = EMOTION_CLASS.keys()
        else:
            classes = OBJECTIVE_CLASS.keys()
        return classes

    def __get_label_average(self, classes):
        if len(classes) <= 1:
            raise ValueError("must two classes")
        elif len(classes) <= 2:
            return "Y", "binary"
        else:
            return 1, "macro"

    def fit_data(self, datas):
        fit_datas = datas
        if not sp.issparse(datas):
            datas = [d.get("sentence") if "sentence" in d else d for d in datas]
            fit_datas = self.feature_hasher.transform(datas)
        return fit_datas

    @staticmethod
    def __del_unknow(c_true, c_pred):
        """
        过滤 c_pred 中 unknow 部分
        :param c_true:
        :param c_pred:
        :return:
        """
        if len(c_true) != len(c_pred):
            raise ValueError("the two lists have different size!")

        l = filter(lambda x: x[1] != "unknow", zip(c_true, c_pred))
        return zip(*l)

if __name__ == "__main__":
    print
    # 加载情绪分类数据集
    feature = CHIFeature()
    train_datas, class_label = feature.get_key_words()
    train = train_datas
    if not sp.issparse(train_datas):
        train = feature.cal_weight(train_datas)

    test = Load.load_test_balance()
    test_datas, test_label = feature.get_key_words(test)
    test = test_datas
    # 构建适合 bayes 分类的数据集
    if not sp.issparse(train_datas):
        test = feature.cal_weight(test_datas)

    clf = Classification()
    # clf.cross_validation(train, class_label, score="f1")
    clf.get_classificator(train, class_label, iscrossvalidate=True)
    pred = clf.predict(test)
    pred_unknow = clf.predict_unknow(test)
    print pred
    print "precision:", clf.metrics_precision(test_label, pred_unknow)
    print "recall:", clf.metrics_recall(test_label, pred_unknow)
    print "f1:", clf.metrics_f1(test_label, pred_unknow)
    print "accuracy:", clf.metrics_accuracy(test_label, pred_unknow)
    print "zero_one_loss:", clf.metrics_zero_one_loss(test_label, pred_unknow)
    print
    clf.metrics_correct(test_label, pred_unknow)

    # 加载主客观分类数据集
#    feature = CHIFeature(subjective=False)
#    train_datas, class_label = feature.get_key_words()
#    train = train_datas
#    if not sp.issparse(train_datas):
#        train = feature.cal_weight(train_datas)
#
#    test = Load.load_test_objective_balance()
#    test_datas, test_label = feature.get_key_words(test)
#    test = test_datas
#    # 构建适合 bayes 分类的数据集
#    if not sp.issparse(train_datas):
#        test = feature.cal_weight(test_datas)
#
#    clf = Classification(subjective=False)
#    clf.get_classificator(train, class_label)
#    pred = clf.predict(test)
#    pred_unknow = clf.predict_unknow(test)
#    print pred
#    print "precision:", clf.metrics_precision(test_label, pred_unknow)
#    print "recall:", clf.metrics_recall(test_label, pred_unknow)
#    print "f1:", clf.metrics_f1(test_label, pred_unknow)
#    print "accuracy:", clf.metrics_accuracy(test_label, pred_unknow)
#    print "zero_one_loss:", clf.metrics_zero_one_loss(test_label, pred_unknow)
#    print
#    clf.metrics_correct(test_label, pred_unknow)
