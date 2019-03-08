# Copyright (c) 2019 Zijun Wei.
# Licensed under the MIT License.
# Author: Zijun Wei
# Usage(TODO):
# Email: hzwzijun@gmail.com
# Created: 12/Feb/2019 10:10


from PyUtils.pickle_utils import loadpickle, save2pickle
from PyUtils.dict_utils import get_value_sorted_dict
import random
import os
from PyUtils.json_utils import load_json_list
import glob
import tqdm
from AdobeStockTools.TagUtils import remove_hat
from PyUtils.file_utils import get_stem
annotation_directory = '/home/zwei/Dev/AttributeNet3/AdobeStockSelection/RetrieveSelected778/selected_keywords_retrieve'
raw_annotation_files = glob.glob(os.path.join(annotation_directory, '*.json'))

collectedCIDs = loadpickle('/home/zwei/Dev/AttributeNet3/AdobeStockSelection/RetrieveSelected778/data/dataset_CIDs_661_val.pkl')
collectedCIDs = set(collectedCIDs)
processedCIDs = set()
CIDtagstrings = set()
CIDs_similar_tag_removal = []
for s_raw_idx, s_raw_file in enumerate(tqdm.tqdm(raw_annotation_files, desc="Processing Files")):
    keyword = get_stem(s_raw_file)
    s_annotations = load_json_list(s_raw_file)
    for s_annotaiton in s_annotations:
        cid = s_annotaiton['cid']
        if cid not in collectedCIDs or cid in processedCIDs:
            continue
        else:
            processedCIDs.add(cid)
            s_tags = remove_hat(s_annotaiton['tags'])
            s_tags = set(s_tags)
            if keyword in s_tags:
                continue
            else:
                print("{}\t{} not in \t{}".format(cid, keyword, ', '.join(list(s_tags))))
            # n_tags = max(20, len(s_tags))
            # s_tags = s_tags[:n_tags]
            # s_tag_string = ''.join(s_tags)
            # if s_tag_string in CIDtagstrings:
            #     continue
            # else:
            #     CIDtagstrings.add(s_tag_string)
            #     CIDs_similar_tag_removal.append(cid)


print("preivous: {}, after repeat tag removal: {}".format(len(collectedCIDs), len(CIDs_similar_tag_removal)))