# Copyright (c) 2019 Zijun Wei.
# Licensed under the MIT License.
# Author: Zijun Wei
# Usage(TODO):
# Email: hzwzijun@gmail.com
# Created: 11/Feb/2019 12:50
from PyUtils.pickle_utils import loadpickle


from PyUtils.file_utils import get_dir
import os

image_annotations = loadpickle('/home/zwei/Dev/AttributeNet3/MtrukPrepData/EmotionTagging_1000x10x5_v3/selected_list_10000.pkl')
save_directory = get_dir('emotiontagging-1000x10x5_v3')
# save_directory = get_dir('tmp')



total_examples = 10000
n_per_hit = 10

count = 0
for s_item in image_annotations:
    if count % n_per_hit == 0:
        of_ = open(os.path.join(save_directory, 'sample_{:02d}.csv'.format(count//n_per_hit)), 'w')
        of_.write('image_url,image_tags,emotion_label\n')
    count += 1



    of_.write('{},{},{}\n'.format(s_item[0], ';'.join(s_item[1]), s_item[2][0]))

    if count % n_per_hit == 0:
        of_.close()

of_.close()

print("DB, {}".format(count))