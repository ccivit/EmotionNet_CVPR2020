# Copyright (c) 2018 Zijun Wei.
# Licensed under the MIT License.
# Author: Zijun Wei
# Usage(TODO): modified from https://github.com/pytorch/examples/blob/master/imagenet/main.py
# TODO: this is modified from main_mclass_corss_entropy_v2.py
# Email: hzwzijun@gmail.com
# Created: 07/Oct/2018 11:09
import os, sys
project_root = os.path.join(os.path.expanduser('~'), 'Dev/AttributeNet3')
sys.path.append(project_root)
from sklearn.metrics.pairwise import cosine_similarity
# import argparse
import random
import shutil
import time
import warnings

import torch
import torch.nn as nn
import torch.nn.parallel
import torch.backends.cudnn as cudnn
import torch.distributed as dist
import torch.optim
import torch.utils.data
import torch.utils.data.distributed
import CNNs.models as models
import CNNs.utils.util as CNN_utils
from torch.optim import lr_scheduler
from CNNs.dataloaders.utils import none_collate
from PyUtils.file_utils import get_date_str, get_dir, get_stem
from PyUtils import log_utils
import CNNs.datasets as custom_datasets
from CNNs.utils.config import parse_config
from CNNs.models.resnet import load_state_dict
import torch.nn.functional as F
from TextClassificationV2.models.TextCNN import TextCNN_NLT
model_names = sorted(name for name in models.__dict__
    if name.islower() and not name.startswith("__")
    and callable(models.__dict__[name]))


def get_instance(module, name, args):
    return getattr(module, name)(args)


def main():

    import argparse
    parser = argparse.ArgumentParser(description="Pytorch Image CNN training from Configure Files")
    parser.add_argument('--config_file', required=True, help="This scripts only accepts parameters from Json files")
    input_args = parser.parse_args()

    config_file = input_args.config_file

    args = parse_config(config_file)
    if args.name is None:
        args.name = get_stem(config_file)

    torch.set_default_tensor_type('torch.FloatTensor')
    # best_prec1 = 0

    args.script_name = get_stem(__file__)
    # current_time_str = get_date_str()





    print_func = print


    if args.device:
        os.environ["CUDA_VISIBLE_DEVICES"]=args.device


    if args.seed is not None:
        random.seed(args.seed)
        torch.manual_seed(args.seed)
        cudnn.deterministic = True
        warnings.warn('You have chosen to seed training. '
                      'This will turn on the CUDNN deterministic setting, '
                      'which can slow down your training considerably! '
                      'You may see unexpected behavior when restarting '
                      'from checkpoints.')

    if args.gpu is not None:
        warnings.warn('You have chosen a specific GPU. This will completely '
                      'disable data parallelism.')

    args.distributed = args.world_size > 1

    if args.distributed:
        dist.init_process_group(backend=args.dist_backend, init_method=args.dist_url,
                                world_size=args.world_size)

    if args.pretrained:
        print_func("=> using pre-trained model '{}'".format(args.arch))
        model = models.__dict__[args.arch](pretrained=True, num_classes=args.num_classes)
    else:
        print_func("=> creating model '{}'".format(args.arch))
        model = models.__dict__[args.arch](pretrained=False, num_classes=args.num_classes)



    if args.gpu is not None:
        model = model.cuda(args.gpu)
    elif args.distributed:
        model.cuda()
        model = torch.nn.parallel.DistributedDataParallel(model)
    else:
        if args.arch.startswith('alexnet') or args.arch.startswith('vgg'):
            model.features = torch.nn.DataParallel(model.features)
            model.cuda()
        else:
            model = torch.nn.DataParallel(model).cuda()
            # model = model.cuda()



    if args.visual_model:
        if os.path.isfile(args.visual_model):
            print_func("=> loading checkpoint '{}'".format(args.visual_model))
            checkpoint = torch.load(args.visual_model)
            model.load_state_dict(checkpoint['state_dict'], strict=True)
            # import collections
            # if isinstance(checkpoint, collections.OrderedDict):
            #     load_state_dict(model, checkpoint, exclude_layers=['fc.weight', 'fc.bias'])
            #
            #
            # else:
            #     load_state_dict(model, checkpoint['state_dict'], exclude_layers=['module.fc.weight', 'module.fc.bias'])
            #     print_func("=> loaded checkpoint '{}' (epoch {})"
            #           .format(args.visual_model, checkpoint['epoch']))
        else:
            print_func("=> no checkpoint found at '{}'".format(args.visual_model))
            return
    else:
        print_func("=> This script is for fine-tuning only, please double check '{}'".format(args.visual_model))
        print_func("Now using randomly initialized parameters!")

    cudnn.benchmark = True




    from PyUtils.pickle_utils import loadpickle

    import numpy as np
    from PublicEmotionDatasets.Emotic.constants import emotion_full_words_690 as emotion_self_words

    from torchvision.datasets.folder import default_loader
    # tag_wordvectors = loadpickle(args.text_embed)
    text_ckpt = torch.load(args.text_ckpt)
    args_textmodel = text_ckpt['args_model']
    args_textdata = text_ckpt['args_data']
    text_model = TextCNN_NLT(args_textmodel)
    text_model.load_state_dict(text_ckpt['state_dict'], strict=True)
    text_model.eval()
    idx2tag = args_textdata.idx2tag
    tag2idx = args_textdata.tag2idx
    print_func(" => loading word2vec parameters: {}".format(args.text_ckpt))



    emotic_emotion_explaintations = {}

    for x_key in emotion_self_words:
        x_words = emotion_self_words[x_key].split(',')
        x_id = [tag2idx[x] if x in tag2idx else args_textmodel.vocab_size+2 for x in x_words]
        x_id_padded = x_id + [args_textmodel.vocab_size + 1] * (args_textmodel.max_len - len(x_id))
        x_id_padded = torch.LongTensor(x_id_padded).unsqueeze(0)

        item = {}
        item ['pred'] = []
        item ['label'] = []
        item ['target_matrix'] = text_model(x_id_padded)[-2].squeeze(0).cpu().data.numpy()[:len(x_id)]
        item ['description'] = x_words
        emotic_emotion_explaintations[x_key] = item

    val_list = loadpickle(args.val_file)
    image_directory = args.data_dir
    from CNNs.datasets.multilabel import get_val_simple_transform
    val_transform = get_val_simple_transform()
    model.eval()

    import tqdm
    for i, (input_image_file, target, _, _) in tqdm.tqdm(enumerate(val_list), desc="Evaluating Peace",
                                                         total=len(val_list)):
        # measure data loading time

        image_path = os.path.join(image_directory, input_image_file)
        input_image = default_loader(image_path)
        input_image = val_transform(input_image)

        if args.gpu is not None:
            input_image = input_image.cuda(args.gpu, non_blocking=True)
        input_image = input_image.unsqueeze(0).cuda()

        # target_idx = target.nonzero() [:,1]

        # compute output
        output, output_proj = model(input_image)

        output_proj = output_proj.cpu().data.numpy()
        target_labels = set([x[0] for x in target.most_common()])

        for x_key in emotic_emotion_explaintations:

            dot_product_label = cosine_similarity(output_proj, emotic_emotion_explaintations[x_key]['target_matrix'])[0]
            pred_score = np.average(dot_product_label)
            emotic_emotion_explaintations[x_key]['pred'].append(pred_score)
            if x_key in target_labels:
                emotic_emotion_explaintations[x_key]['label'].append(1)
            else:
                emotic_emotion_explaintations[x_key]['label'].append(0)

    from sklearn.metrics import average_precision_score
    full_AP = []
    for x_key in emotic_emotion_explaintations:
        full_pred = np.array(emotic_emotion_explaintations[x_key]['pred'])
        full_label = np.array(emotic_emotion_explaintations[x_key]['label'])
        AP = average_precision_score(full_label, full_pred)
        if np.isnan(AP):
            print("{} is Nan".format(x_key))
            continue
        full_AP.append(AP)
        print("{}\t{:.4f}".format(x_key, AP * 100))
    AvgAP = np.mean(full_AP)
    print("Avg AP: {:.2f}".format(AvgAP * 100))

    # print("* {} Image: {} GT label: {}, predicted label: {}".format(i, input_image_file, idx2emotion[target], idx2label[output_label]))
        # print(" == closest tags: {}".format(', '.join(['{}({:.02f})'.format(idx2tag[x], dot_product_tag[x]) for x in out_tags])))
    # print("Accuracy {:.4f}".format(correct/total))








if __name__ == '__main__':
    main()

