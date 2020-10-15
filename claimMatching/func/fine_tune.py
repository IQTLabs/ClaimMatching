"""
Created on Fri Aug 28 14:08:16 2020
This file allows for funetuning the weights provided by SBERT
with Infodemic-specific data.
@author: brocklin
"""

from sentence_transformers import SentencesDataset, SentenceTransformer, losses
from torch.utils.data import DataLoader

# note: nothing in this file is finished, it simply outlines how we might begin finetuning
# full example here: https://github.com/UKPLab/sentence-transformers/blob/master/examples/training/sts/training_stsbenchmark_continue_training.py
def fine_tune(cfg):
    """
    Function to finetune a model with Infodemic-specific data.

    :param cfg: configuration dictionary
    :return: none
    """
    model = SentenceTransformer(cfg['model'])
    # data reading dependent on data format, see https://github.com/UKPLab/sentence-transformers/blob/master/examples/training/sts/training_stsbenchmark_continue_training.py
    # for an example at lines 48-62
    train_samples = None
    train_ds = SentencesDataset(train_samples, model)
    train_dl = DataLoader(train_ds)
    train_loss = losses.SoftmaxLoss(model, num_labels=3)

    evaluator = None # list of evaluators at https://github.com/UKPLab/sentence-transformers/tree/master/sentence_transformers/evaluation
    model.fit(train_objectives=[(train_dl, train_loss)],
              evaluator=evaluator,
              epochs=30,
              evaluation_steps=1000,
              output_path=cfg['model_output'])
