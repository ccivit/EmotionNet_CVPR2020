# Copyright (c) 2019 Zijun Wei.
# Licensed under the MIT License.
# Author: Zijun Wei
# Usage(TODO):
# Email: hzwzijun@gmail.com
# Created: 07/Mar/2019 21:45


from PyUtils.pickle_utils import loadpickle, save2pickle
import tqdm, os
from collections import Counter
from PyUtils.json_utils import load_json_list
from PyUtils.file_utils import get_stem
dataset_directory = '/home/zwei/datasets/PublicEmotion/EMOTIC'





data_split = 'test'
text_annotation_file = os.path.join(dataset_directory, 'annotations/samples', '{}.txt'.format(data_split))

annotaitons_person_crop = []
annotaitons_whole_image = []
raw_annotation_list = load_json_list(text_annotation_file)[0]

for s_annotation in tqdm.tqdm(raw_annotation_list, desc="Processing data"):
    s_file_name = os.path.join(s_annotation['folder'],  s_annotation['filename'])
    s_file_name_stem = get_stem(s_file_name)
    s_file_extension = s_file_name.split('.')[-1]
    if isinstance(s_annotation['person'], list):
        pass
    else:
        s_annotation['person'] = [s_annotation['person']]


    for s_person_idx, s_person in enumerate(s_annotation['person']):
        s_bbox = s_person['body_bbox']

        annotated_categories = []
        if not isinstance(s_person['annotations_categories'], list):
            s_person['annotations_categories'] = [s_person['annotations_categories']]
            s_person['combined_continuous'] = s_person['annotations_continuous']
        for s_single_annotation in s_person['annotations_categories']:
            annotated_categories.extend(s_single_annotation['categories'])

        average_continuous_emotion = s_person['combined_continuous']
        category_emotion_counter = Counter(annotated_categories)
        s_person_file_name = os.path.join(s_annotation['folder'], '{}_{:03d}.{}'.format(s_file_name_stem, s_person_idx, s_file_extension))
        annotaitons_person_crop.append([s_person_file_name, category_emotion_counter, average_continuous_emotion, s_bbox])
        annotaitons_whole_image.append([s_file_name, category_emotion_counter, average_continuous_emotion, s_bbox])

print("D")
save2pickle(os.path.join(dataset_directory, 'new_z_data', '{}_person_crop.pkl'.format(data_split)), annotaitons_person_crop)
save2pickle(os.path.join(dataset_directory, 'new_z_data', '{}_whole_image.pkl'.format(data_split)), annotaitons_whole_image)
