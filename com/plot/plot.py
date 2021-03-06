# encoding: utf-8
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc
from sklearn.preprocessing import label_binarize
from scipy import interp

__author__ = 'zql'
__date__ = '16-04-26'


def get_instance():
    plt.figure()


def show():
    plt.show()


def plot_roc(y_true, y_score, text='', linestyle='-', classes=None, detail=False):
    """
    plot roc, support for multi-class
    detail for : http://scikit-learn.org/stable/auto_examples/model_selection/plot_roc.html

    :param y_true: shape=[n_samples]
    :param y_score: shape=[n_samples, n_classes]
    :param classes: list
    :return:
    """
    unique_classes = set(y_true)
    if not classes:
        classes = unique_classes

    # Binarize the output
    y_true = label_binarize(y_true, classes=classes)
    n_classes = y_true.shape[1]

    # Compute ROC curve and ROC area for each class
    fpr = dict()
    tpr = dict()
    roc_auc = dict()
    for i in range(n_classes):
        fpr[i], tpr[i], _ = roc_curve(y_true[:, i], y_score[:, i])
        roc_auc[i] = auc(fpr[i], tpr[i])

    # Compute micro-average ROC curve and ROC area
    fpr["micro"], tpr["micro"], _ = roc_curve(y_true.ravel(), y_score.ravel())
    roc_auc["micro"] = auc(fpr["micro"], tpr["micro"])

    ##############################################################################
    # Plot ROC curves for the multiclass problem

    # Compute macro-average ROC curve and ROC area

    # First aggregate all false positive rates
    all_fpr = np.unique(np.concatenate([fpr[i] for i in range(n_classes)]))

    # Then interpolate all ROC curves at this points
    mean_tpr = np.zeros_like(all_fpr)
    for i in range(n_classes):
        mean_tpr += interp(all_fpr, fpr[i], tpr[i])

    # Finally average it and compute AUC
    mean_tpr /= n_classes

    fpr["macro"] = all_fpr
    tpr["macro"] = mean_tpr
    roc_auc["macro"] = auc(fpr["macro"], tpr["macro"])

    # Plot all ROC curves
#    plt.figure()
#    plt.plot(fpr["micro"], tpr["micro"],
#             label=text + ' micro-average ROC curve (area = {0:0.8f})'
#                          ''.format(roc_auc["micro"]),
#             linewidth=2)

    plt.plot(fpr["macro"], tpr["macro"], linestyle,
             label=text + ' (area = {0:0.8f})'
                          ''.format(roc_auc["macro"]),
             linewidth=2)

    plt.plot([0, 1], [0, 1], 'k--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Some extension of Receiver operating characteristic to multi-class')
    plt.legend(loc="lower right")
#    plt.show()

    if detail:
        for i in range(n_classes):
            plt.plot(fpr[i], tpr[i], label='ROC curve of class {0} (area = {1:0.8f})'
                                           ''.format(classes[i], roc_auc[i]))

        plt.plot([0, 1], [0, 1], 'k--')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('Some extension of Receiver operating characteristic to multi-class')
        plt.legend(loc="lower right")
        plt.show()

