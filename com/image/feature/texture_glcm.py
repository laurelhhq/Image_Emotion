# encoding: utf-8
import math
import os
import numpy as np

from com.constant.constant import TEST_RESOURCE
from com.image.feature.texture_feature import TextureFeature

__author__ = 'root'
__date__ = '15-11-8'


class TextureGLCM(TextureFeature):
    """
    灰度共生矩阵，一般只取 0, 45, 90, 135度 四种情况
    """
    GLCM_ANGLE_0 = 0                # 0度方向
    GLCM_ANGLE_45 = 1               # 45度方向
    GLCM_ANGLE_90 = 2               # 90度方向
    GLCM_ANGLE_135 = 3              # 135度方向

    GLCM_PROPERTY_ENERGY = 0        # 角二阶矩
    GLCM_PROPERTY_ENTROPY = 1       # 熵
    GLCM_PROPERTY_CONTRAST = 2      # 对比度
    GLCM_PROPERTY_MEAN = 3          # 均匀度

    def __init__(self, image):
        super(TextureGLCM, self).__init__(image)

    def cal_feature(self):
        """
        灰度共生矩阵，只计算 d = 1 的情况
        :return:
        """
        src_img = super(TextureGLCM, self).bgr2gray()

        # 为减少计算量，将灰度图量化成16级
        # opencv将16位即256个灰度等级的图像变换成4位即16个灰度等级的图像
        # 直接将每个像素的灰度值除于16，再取整就是你要得到的4位灰度级。
        for index, value in np.ndenumerate(src_img):
            src_img[index] = value / 16

        glcm0 = self.cal_glcm(src_img, TextureGLCM.GLCM_ANGLE_0, True)
        glcm45 = self.cal_glcm(src_img, TextureGLCM.GLCM_ANGLE_45, True)
        glcm90 = self.cal_glcm(src_img, TextureGLCM.GLCM_ANGLE_90, True)
        glcm135 = self.cal_glcm(src_img, TextureGLCM.GLCM_ANGLE_135, True)

        res = []
        for index, glcm in enumerate((glcm0, glcm45, glcm90, glcm135)):
            res.append(self.cal_property(glcm, TextureGLCM.GLCM_PROPERTY_CONTRAST))
            res.append(self.cal_property(glcm, TextureGLCM.GLCM_PROPERTY_ENTROPY))
            res.append(self.cal_property(glcm, TextureGLCM.GLCM_PROPERTY_ENERGY))
            res.append(self.cal_property(glcm, TextureGLCM.GLCM_PROPERTY_MEAN))
#            print ("Contrast: %f" % self.cal_property(glcm, TextureGLCM.GLCM_PROPERTY_CONTRAST))
#            print ("Entropy: %f" % self.cal_property(glcm, TextureGLCM.GLCM_PROPERTY_ENTROPY))
#            print ("Energy: %f" % self.cal_property(glcm, TextureGLCM.GLCM_PROPERTY_ENERGY))
#            print ("Homogeneity: %f" % self.cal_property(glcm, TextureGLCM.GLCM_PROPERTY_MEAN))
#            print
        return res

    def cal_glcm(self, src_img, angle_direction, normalization=False):

        def myreduce(arg1, arg2):
            glcm[(arg1 - glcm_min, arg2 - glcm_min)] += 1
            return arg2

        def is_outofarray(array, index):
            """
            判断数组是否越界
            :param array:
            :param index: (rows, columns)
            :return:
            """
            rows = array.shape[0] - 1
            columns = array.shape[1] - 1
            if index[0] > rows or index[0] < 0 or index[1] > columns or index[1] < 0:
                return True
            return False

        def get_direction_seq(array, direction):
            """
            获取 array 数组中 direction 方向上的序列
            如 0 度方向，就是获取行数据；
            90 度方向，就是获取列数据
            """
            if direction == TextureGLCM.GLCM_ANGLE_0:
                for row in array:
                    yield row

            if direction == TextureGLCM.GLCM_ANGLE_45:
                for j in range(array.shape[1]):
                    result = list()
                    i = 0
                    while not is_outofarray(array, (i, j)):
                        result.append(array[(i, j)])
                        j += 1
                        i += 1
                    yield result

                for i in range(1, array.shape[0]):
                    result = list()
                    j = 0
                    while not is_outofarray(array, (i, j)):
                        result.append(array[(i, j)])
                        j += 1
                        i += 1
                    yield result

            if direction == TextureGLCM.GLCM_ANGLE_90:
                for j in range(array.shape[1]):
                    result = list()
                    for i in range(array.shape[0]):
                        result.append(array[(i, j)])
                    yield result

            if direction == TextureGLCM.GLCM_ANGLE_135:
                for j in range(array.shape[1] - 1, -1, -1):
                    result = list()
                    i = 0
                    while not is_outofarray(array, (i, j)):
                        result.append(array[(i, j)])
                        j -= 1
                        i += 1
                    yield result

                for i in range(1, array.shape[0]):
                    result = list()
                    j = array.shape[1] - 1
                    while not is_outofarray(array, (i, j)):
                        result.append(array[(i, j)])
                        j -= 1
                        i += 1
                    yield result

        def norm(array):
            # 归一化
            array_sum = np.sum(array)
            for index, value in np.ndenumerate(array):
                array[index] = value / array_sum * 1.0
            return array

        # 平坦化数组，方便求取最大值和最小值
        # glcm_max - glcm_min + 1 灰度共生矩阵的阶数
        glcm_max = max(src_img.flat)
        glcm_min = min(src_img.flat)
        glcm_n = glcm_max - glcm_min + 1

        # 创建空的 glcm_n * glcm_n 的共生矩阵
        glcm = np.zeros((glcm_n, glcm_n), dtype="float32")

        datas = get_direction_seq(src_img, angle_direction)
        for data in datas:
            reduce(myreduce, data)

        if normalization is True:
            return norm(glcm)

        return glcm

    def cal_property(self, glcm, prop):
        """
        计算共生矩阵的几个参数
        :param glcm: 共生矩阵
        :param prop: 参数
        :return:
        """
        def cal_energy():
            # 角二阶矩（能量）
            s = 0
            for index, value in np.ndenumerate(glcm):
                s += math.pow(value, 2)
            return s

        def cal_entropy():
            # 熵
            s = 0
            for index, value in np.ndenumerate(glcm):
                if value == 0:
                    continue
                s += math.log(value, 2) * value
            return s * (-1.0)

        def cal_contrast():
            # 对比度
            s = 0
            for index, value in np.ndenumerate(glcm):
                s += value * math.pow((index[0] - index[1]), 2)
            return s

        def cal_homogeneity():
            # 均匀度
            s = 0
            for index, value in np.ndenumerate(glcm):
                s += value / (math.fabs(index[0] - index[1]) + 1)
            return s

        if prop == TextureGLCM.GLCM_PROPERTY_ENERGY:
            return cal_energy()

        if prop == TextureGLCM.GLCM_PROPERTY_ENTROPY:
            return cal_entropy()

        if prop == TextureGLCM.GLCM_PROPERTY_CONTRAST:
            return cal_contrast()

        if prop == TextureGLCM.GLCM_PROPERTY_MEAN:
            return cal_homogeneity()

if __name__ == "__main__":
    """imgname = np.array([
        [0, 0, 0, 1, 2],
        [0, 0, 1, 1, 2],
        [0, 1, 1, 1, 1],
        [1, 1, 2, 2, 1],
        [1, 2, 2, 1, 0]
    ], dtype="int32")"""
    """imgname = np.array([
        [1, 1, 5, 6, 8],
        [2, 3, 5, 7, 1],
        [4, 5, 7, 1, 2],
        [8, 5, 1, 2, 5]
    ], dtype="int32")"""
    """imgname = np.array([
        [0,1,2,3,0,1,2],
        [1,2,3,0,1,2,3],
        [2,3,0,1,2,3,0],
        [3,0,1,2,3,0,1],
        [0,1,2,3,0,1,2],
        [1,2,3,0,1,2,3],
        [2,3,0,1,2,3,0]
    ], dtype="int32")"""
    imgname = os.path.join(TEST_RESOURCE, "photo.png")
    textureFeature = TextureGLCM(imgname).cal_feature()
    print textureFeature


