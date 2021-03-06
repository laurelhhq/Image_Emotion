# encoding: utf-8
import os

import jieba
import jieba.posseg as pseg
import regex
import time

from com.constant.constant import TEXT_RESOURCE
from com.text.third_part.langconv import Converter

__author__ = 'zql'
__date__ = '2015/11/10'


class SplitWords:
    """
    结巴中文分词
    """
    @staticmethod
    def __init__():
        # 添加用户词典
        SplitWords.add_user_word("netword.txt")
        SplitWords.add_user_word("ntusd.txt")
        SplitWords.add_user_word("hownet.txt")
        SplitWords.import_user_dict("dict-jieba.txt")

    @staticmethod
    def split_words(s):
        # 繁体转简体
        s = SplitWords.__convert(s)

        # 去除标签
        s = SplitWords.__del_non_tag(s)

        # 去除标点符号
        s = SplitWords.__del_punctuation(s)

        # 去除数字
        s = SplitWords.__del_digit(s)

        # 分词 带有词性
        words = pseg.lcut(s, HMM=True)
        # 重新编码 UTF-8
        words = SplitWords.__reencoding(words)

        # 去掉中文停用词
        words = SplitWords.__del_stop(words, SplitWords.__read_chinese_stoplist())

        # 去掉英文停用词
        words = SplitWords.__del_stop(words, SplitWords.__read_english_stoplist())

        # 去掉多余的空格
        words = SplitWords.__del_blank(words)

        # 去掉无用的词性词汇，并将剩下的词汇的词性删除
        words = SplitWords.__del_non_pos(words)

        return words

    @staticmethod
    def close():
        pass

    @staticmethod
    def add_user_word(path):
        # 添加用户词典
        [jieba.add_word(line.strip("\n"))
         for line in open(os.path.join(TEXT_RESOURCE, path))]

    @staticmethod
    def import_user_dict(path):
        print "Before Import User Dict: ", time.strftime('%Y-%m-%d %H:%M:%S')
        jieba.load_userdict(os.path.join(TEXT_RESOURCE, path))
        print "Done: ", time.strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def __convert(s):
        # 将繁体转化成简体
        return Converter("zh-hans").convert(s.decode("utf_8"))

    @staticmethod
    def __del_non_tag(s):
        # 去除微博中无用的标签
        def theme_tag():
            # 主题标签
            return regex.sub(r"#.*?#", "", s)

        def tran_tag():
            # //@__: 转发标签
            return regex.sub(r"//@.*?:", "", s)

        def url_tag():
            # url 标签
            return regex.sub(r"(http|https)?://([a-zA-Z|\d]+\.)+[a-zA-Z|\d]+(/[a-zA-Z|\d|\-|\+|_./?%=]*)?", "", s)

        def alt_tag():
            # @提醒标签
            return regex.sub(ur"@[\u4e00-\u9fa5\w-]{1,30}(?=\s|:)", "",
                             s if isinstance(s, unicode) else s.decode("utf_8"))

        s = theme_tag()
        s = tran_tag()
        s = url_tag()
        s = alt_tag()
        return s.encode("utf_8")

    @staticmethod
    def __del_punctuation(s):
        # todo
        # 不要删除表情和表情符号
        # 表情符号暂时不考虑 *^_^*
        """
        去除标点符号，不管是英文标点还是中文标点
        暂时删除英文单词，即暂时不对英文进行处理
        :return:
        """
        """
        Unicode 编码并不只是为某个字符简单定义了一个编码，而且还将其进行了归类。
        \pP 其中的小写 p 是 property 的意思，表示 Unicode 属性，用于 Unicode 正表达式的前缀。
        大写 P 表示 Unicode 字符集七个字符属性之一：标点字符。
        其他六个是
        L：字母；
        M：标记符号（一般不会单独出现）；
        Z：分隔符（比如空格、换行等）；
        S：符号（比如数学符号、货币符号等）；
        N：数字（比如阿拉伯数字、罗马数字等）；
        C：其他字符

        Python 自带的 re 模块貌似不支持 unicode 属性，因此需要安装 regex 模块
        这样就可以使用 \p{} 这样的 unicode 属性
        使用时，正则表达式和字符串都必须经过 unicode 编码
        """
        s = regex.sub(ur"\p{P}|\p{S}|\p{Ll}|\p{Lu}", "", s if isinstance(s, unicode) else s.decode("utf_8"))
        return s.encode("utf_8")

    @staticmethod
    def __del_digit(s):
        return regex.sub(r"\d", "", s)

    @staticmethod
    def __del_stop(words, stoplist):
        return filter(lambda x: x.word not in stoplist, words)

    @staticmethod
    def __del_blank(words):
        return [word for word in words if word.word != " "]

    @staticmethod
    def __read_chinese_stoplist():
        url_0 = os.path.join(TEXT_RESOURCE, "chinese_stoplist_0.txt")
        url_1 = os.path.join(TEXT_RESOURCE, "chinese_stoplist_1.txt")
        # 下面这行使用方便，但觉得会不会不会关闭打开文件后的资源
        # return [line.strip("\n") for line in open(url).readlines()]
        url = (url_0, url_1)
        stoplist = []
        for u in url:
            with open(u) as fp:
                stoplist += [line.strip("\n") for line in fp]
        return set(stoplist)

    @staticmethod
    def __read_english_stoplist():
        url_0 = os.path.join(TEXT_RESOURCE, "english_stoplist.txt")
        url = (url_0,)
        stoplist = []
        for u in url:
            with open(u) as fp:
                stoplist += [line.strip("\n") for line in fp]
        return set(stoplist)

    @staticmethod
    def __del_non_pos(words):
        def is_use_pos(s):
            non_pos = ("nr", "ns", "nt", "s", "f", "t", "m", "q", "p", "c", "u")
            return not s.flag.startswith(non_pos)

        # 删除无用的词性的词
        words = filter(is_use_pos, words)
        # 删除词性
        return map(lambda x: x.word, words)

    @staticmethod
    def __reencoding(words):
        return [pseg.pair(word.word.encode("utf_8"), word.flag) for word in words]

    @staticmethod
    def __ispair(word):
        return isinstance(word, pseg.pair)

if __name__ == "__main__":
    string1 = r'//@王久辛:@王久辛 @王久辛 留大量[愤怒] 预习与@王久辛:作业,让家长@hj 给孩子' \
              r'报游动轮换辅导班作死妖娆佳丽微博铺导班#辅导班#,他们再#《》赚一把钱~~美特伺邦威周成健: ' \
              r'做 ME AND CITY是非常有价值的。' \
              r'群众的呼声VERY very importantly！！！[大笑] [大笑] *^_^*'
    string2 = "给孩子辅导班我媽話你們宿捨怎麼這麼失敗的?"
    string3 = r"想做微博如果中国黄山的我们一个说今年高考作文题a AaBb披露，巨无聊。虚假、做做、装逼，一无是处。能不能出点富于新意、能多少融入个人生活的题目？" \
              r"我记得大约15年前，台湾的高考作文题是《生活中的苦涩与甘美》。" \
              r"譬如，《我在马勒戈壁的青春放浪》、《动物凶猛的饮食生活》啥的。" \
              r"里屋"
    string4 = r"他来到了网易的杭研大厦"
    SplitWords.__init__()
    splited_words = SplitWords.split_words(string3)
    SplitWords.close()
    print len(splited_words)
    for splited_word in splited_words:
        if isinstance(splited_word, unicode):
            print splited_word
        else:
            print splited_word.decode("utf_8")

