# Copyright (c) 2019 Zijun Wei.
# Licensed under the MIT License.
# Author: Zijun Wei
# Usage(TODO):
# Email: hzwzijun@gmail.com
# Created: 23/Feb/2019 11:56
import glob, os
import tqdm
from PyUtils.pickle_utils import loadpickle, save2pickle
from AdobeStockTools.AdobeStockUnitls import get_image_cid_from_url
from PyUtils.dict_utils import get_key_sorted_dict
from AdobeStockTools.TagUtils import remove_hat
from PyUtils.json_utils import load_json_list
datasplit = 'train'
image_cid_list = loadpickle('/home/zwei/Dev/AttributeNet3/AdobeStockSelection/RetrieveSelected778/data_v6_690_xmas/CNNsplit_key_labels_train.pkl')
pretrained_vocabulary = loadpickle('/home/zwei/Dev/TextClassifications/z_implementations/pre_extract_w2v/params/googlenews_extracted_w2v_wordnet_synsets_py3.pl')
image_cids = []
for s_image_annotation in tqdm.tqdm(image_cid_list, desc="Create CID set"):
    image_cids.append(int(get_image_cid_from_url(s_image_annotation[0], location=1)))

image_cids = set(image_cids)

raw_annotation_files = glob.glob(os.path.join('/home/zwei/Dev/AttributeNet3/AdobeStockSelection/RetrieveSelected778/selected_keywords_retrieve_v2', '*.json'))
processed_images = {}
tag_counts = {}
for s_raw_annotation_file in tqdm.tqdm(raw_annotation_files):
    s_raw_annotations = load_json_list(s_raw_annotation_file)
    for s_raw_annotation in s_raw_annotations:
        s_cid = s_raw_annotation['cid']
        if s_cid in processed_images or s_cid not in image_cids:
            continue
        else:

            s_tags = remove_hat(s_raw_annotation['tags'])
            updated_tags = []
            for s_tag in s_tags:
                if s_tag in pretrained_vocabulary:
                    if s_tag in tag_counts:
                        tag_counts[s_tag] += 1
                    else:
                        tag_counts[s_tag] = 1

                    updated_tags.append(s_tag)
            processed_images[s_cid] = updated_tags

tag_counts = get_key_sorted_dict(tag_counts, reverse=False)
save2pickle('train_cids_tags.pkl', processed_images)
save2pickle('train_tag_counts.pkl', tag_counts)

