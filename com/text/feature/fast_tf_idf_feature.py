# encoding: utf-8
import time
from sklearn.feature_extraction.text import TfidfTransformer

from com.text import Feature_Hasher
from com.text.feature.feature import Feature

__author__ = 'root'
__date__ = '15-12-14'


class FastTFIDFFeature(Feature):
    """
    文本的 TFIDF 特征，速度快
    """
    def __init__(self, f=False, subjective=True):
        # 特征 Hash 散列器
        super(FastTFIDFFeature, self).__init__(f, subjective)

    def _collect(self, splited_words_list, sentence_size):
        print "Collection datas: ", time.strftime('%Y-%m-%d %H:%M:%S')
        data = [d.get("sentence") for d in splited_words_list[: sentence_size]]
        class_label = [d.get("emotion-1-type") for d in splited_words_list[: sentence_size]]
        fit_data = Feature_Hasher.transform(data)
        tfidf = TfidfTransformer()
        tfidf.fit(fit_data)
        a = tfidf.transform(fit_data)
        print "Done: ", time.strftime('%Y-%m-%d %H:%M:%S')
        return a, class_label, []

    def get_dict(self, l):
        d = {}
        for l1 in set(l):
            d[l1] = l.count(l1)
        return d

if __name__ == "__main__":
    FastTFIDFFeature().get_key_words()


