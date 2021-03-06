# encoding: utf-8
import os
import time
from compiler.ast import flatten

import cv2
import numpy as np
import scipy.sparse as sp
from sklearn.metrics import f1_score
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score

from com.constant.constant import RESOURCE_BASE_URL, EMOTION_CLASS
from com.image.feature.color_moment import ColorMoment
from com.image.feature.texture_glcm import TextureGLCM
from com.image.pnn import PNN
from com.image.utils.common_util import CommonUtil
from com.text import collect
from com.text.classification_util import get_objective_classification, get_emotion_classification
from com.text.feature.chi_feature import CHIFeature
from com.utils.fileutil import FileUtil

__author__ = 'root'
__date__ = '2016/06/14'


class ImageClassification:
    weibo_path = os.path.join(RESOURCE_BASE_URL, "collect")
    image_train_path = os.path.join(RESOURCE_BASE_URL, "image")

    def __init__(self, nn=PNN()):
        self.nn = nn

    def get_classificator(self):
        sentences = self.read_train(ImageClassification.image_train_path)
        if not sentences:
            # 读取微博数据
            sentences = collect.read_weibo(ImageClassification.weibo_path, isreadimg=True)
            pure_sentences = [sentence.get("sentence") for sentence in sentences]

            # predict
            c_pred = self.__classifict(CHIFeature(), pure_sentences, incr=True)

            # reconstruct sentences
            sentences = self.__reconstruct(sentences, c_pred)

            # save
            self.__save_result(sentences)

        texts, imgs, labels = self.split(sentences)
        img_feature = self.__get_feature_from_img(imgs)
        self.nn.get_classificator(img_feature, labels)
        return self

    def predict(self, imgs):
        img_feature = self.__get_feature_from_img(imgs)
        return self.nn.predict(img_feature)

    def metrics_precision(self, c_true, c_pred):
        classes = self.getclasses()
        pos_label, average = self.__get_label_average(classes)
        return precision_score(c_true, c_pred, labels=classes, pos_label=pos_label, average=None)

    def metrics_recall(self, c_true, c_pred):
        classes = self.getclasses()
        pos_label, average = self.__get_label_average(classes)
        return recall_score(c_true, c_pred, labels=classes, pos_label=pos_label, average=None)

    def metrics_f1(self, c_true, c_pred):
        classes = self.getclasses()
        pos_label, average = self.__get_label_average(classes)
        return f1_score(c_true, c_pred, labels=classes, pos_label=pos_label, average=None)

    def getclasses(self):
        return EMOTION_CLASS.keys()

    def __get_label_average(self, classes):
        if len(classes) <= 1:
            raise ValueError("must two classes")
        elif len(classes) <= 2:
            return "Y", "binary"
        else:
            return 1, "None"

    def __classifict(self, feature, sentences, incr=False):
        if isinstance(sentences, basestring):
            sentences = [sentences]

        # 获得主客观分类器
        feature.subjective = False
        objective_clf = get_objective_classification(feature)

        # 主客观部分
        test_datas_objective, c_true_objective, danger_index_objective = feature.get_key_words(sentences)

        test_objective = test_datas_objective
        if not sp.issparse(test_datas_objective):
            test_objective = feature.cal_weight_improve(test_datas_objective, c_true_objective)

        c_pred_objective = objective_clf.predict(test_objective)

        # 获得情绪分类器
        feature.subjective = True
        emotion_clf = get_emotion_classification(feature, incr=incr)

        # 情绪部分
        test_datas, c_true, danger_index = feature.get_key_words(sentences)

        test = test_datas
        if not sp.issparse(test_datas):
            test = feature.cal_weight_improve(test_datas, c_true)

        c_pred = []
        for i in range(len(sentences)):
            if i not in danger_index_objective and i not in danger_index:
                before_i_in_danger_obj = np.sum(np.asarray(danger_index_objective) < i)
                before_i_in_danger_ = np.sum(np.asarray(danger_index) < i)

                c = emotion_clf.predict(test[i - before_i_in_danger_])[0] if c_pred_objective[i - before_i_in_danger_obj] == "Y" \
                    else c_pred_objective[i - before_i_in_danger_obj]
                c_pred.append(c)
            else:
                c_pred.append("none(insufficient key_words)")

        return c_pred

    def __reconstruct(self, sentences, c_pred):
        l = []
        for i, sentence in enumerate(sentences):
            if not c_pred[i] == "N" and not c_pred[i].startswith("none")\
                    and sentence.get("img") and self.__has_fit_image(sentence.get("img")):
                img_urls = self.__process_img(sentence.get("img"))
                d = dict(sentence)
                d["img"] = img_urls
                d["label"] = c_pred[i]
                l.append(d)
        return l

    def __process_img(self, img_urls):
        dir_ = os.path.join(ImageClassification.image_train_path, "img")
        FileUtil.mkdirs(dir_)

        def copy_img(img_url):
            filename = os.path.split(img_url)[1]
            filepath = os.path.join(dir_, filename)
            cv2.imwrite(filepath, cv2.imread(img_url))
            return filepath

        return [copy_img(img_url) for img_url in img_urls]

    def __has_fit_image(self, img_urls):
        fit_bool = [os.path.split(img_url)[1].endswith("jpg") for img_url in img_urls]
        return sum(fit_bool) == len(img_urls)

    def read_train(self, path):
        def handle_read(datas):
            l = []
            d = dict()
            for data in datas:
                if data.startswith("sentence"):
                    d = dict()
                    d["sentence"] = data[data.find(":") + 1:]
                    l.append(d)
                elif data.startswith("img"):
                    d["img"] = filter(lambda x: x, data[data.find(":") + 1:].split(","))
                elif data.startswith("label"):
                    d["label"] = data[data.find(":") + 1:]
            return l

        path = path if path.startswith(RESOURCE_BASE_URL) else os.path.join(RESOURCE_BASE_URL, path)
        filenames = FileUtil.listdir(path, isrecursion=False)
        return flatten([CommonUtil.read_from_file(filename, handle_read) for filename in filenames])

    def __save_result(self, sentences):
        FileUtil.mkdirs(ImageClassification.image_train_path)
        current = time.strftime('%Y-%m-%d %H:%M:%S')
        out = os.path.join(ImageClassification.image_train_path, current + ".txt")

        with open(out, "w") as fp:
            for sentence in sentences:
                s = ("sentence:" + sentence.get("sentence") + "\n" +
                     "img:" + ",".join(sentence.get("img")) + "\n" +
                     "label:" + sentence.get("label")) + "\n"
                fp.write(s)

    def split(self, sentences):
        texts = []
        imgs = []
        labels = []
        for sentence in sentences:
            for img in sentence.get("img"):
                texts.append(sentence.get("sentence"))
                imgs.append(img)
                labels.append(sentence.get("label"))
        return texts, imgs, labels

    def __get_feature_from_img(self, imgs):
        res = []
        for i, img in enumerate(imgs):
            if (i + 1) % 5 == 0:
                print "%s: has done %s" % (time.strftime('%Y-%m-%d %H:%M:%S'), i + 1)
            color_feature = ColorMoment(img).cal_feature()
            texture_feature = TextureGLCM(img).cal_feature()
            res.append(color_feature + texture_feature)
        print "%s: has done %s" % (time.strftime('%Y-%m-%d %H:%M:%S'), i + 1)
        return res
#        return [ColorMoment(img).cal_feature() + TextureGLCM(img).cal_feature() for img in imgs]

if __name__ == "__main__":
    clf = ImageClassification()
    clf.get_classificator()

    test_path = os.path.join(ImageClassification.image_train_path, "test")
    test_sentences = clf.read_train(test_path)
    _, imgs, c_true = clf.split(test_sentences)
    c_pred = clf.predict(imgs)
    print clf.metrics_precision(c_true, c_pred)
    print clf.metrics_recall(c_true, c_pred)
    print clf.metrics_f1(c_true, c_pred)

