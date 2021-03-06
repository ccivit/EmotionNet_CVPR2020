# Copyright (c) 2019 Zijun Wei.
# Licensed under the MIT License.
# Author: Zijun Wei
# Usage(TODO):
# Email: hzwzijun@gmail.com
# Created: 04/Mar/2019 10:11

from PyUtils.pickle_utils import loadpickle, save2pickle
import torch
from torch.autograd import Variable
from CNNs.models.resnet import load_state_dict
from TextClassification.model_DAN_2constraints import CNN_Embed_v2
import tqdm



text_data = torch.load('/home/zwei/Dev/AttributeNet3/TextClassification/models/model_feature_regularization.pth.tar')

pretrained_model = text_data['model']
tag2idx = text_data['tag2idx']


text_params = {
    # "Learning_SCHEDULE": [int(i) for i in args.lr_schedule.split(',')],
    # "LEARNING_RATE": args.learning_rate,
    "MAX_SENT_LEN": 1,
    "BATCH_SIZE": 1,
    "WORD_DIM": pretrained_model.WORD_DIM,
    "FILTER_NUM": pretrained_model.FILTER_NUM,
    "VOCAB_SIZE": len(text_data['tag2idx']),  # FIXME: check here!
    "CLASS_SIZE": pretrained_model.CLASS_SIZE,
    "tag2idx": text_data['tag2idx'],
    "idx2tag": text_data['idx2tag'],
}
text_model = CNN_Embed_v2(**text_params)
load_state_dict(text_model, pretrained_model.state_dict())
# text_model.load_state_dict(pretrained_model.state_dict(), strict=False)
# Not training Text Model, set to eval to freeze BN
text_model.eval()

tag_embeddings = {}
for s_key in tqdm.tqdm(tag2idx, total=len(tag2idx)):
    input_id = [[tag2idx[s_key]]]

    input_id = Variable(torch.LongTensor(input_id))
    output_feat = text_model(input_id)
    tag_embeddings[s_key] = output_feat.cpu().data.numpy()

save2pickle('Embeddings/FullVocab_BN_transformed_l2_regularization.pkl', tag_embeddings)

print("Done")
