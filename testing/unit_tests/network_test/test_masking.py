import os

#import matplotlib.pyplot as plt
import numpy as np
import time
import unittest
import random
import math

import torch

from PIL import Image

from torchvision import transforms
from configs import g_conf

from torch.nn import functional as F

import input
import reference

from coil_core.train import select_balancing_strategy
from network import CoILModel


from network.loss import compute_attention_map_L2, compute_attention_map_L1


class testMasking(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(testMasking, self).__init__(*args, **kwargs)
        self.root_test_dir = 'testing/unit_tests/data'
        self.test_images_write_path = 'testing/unit_tests/_test_images_'


    def test_masking(self):

        if not os.path.exists(self.test_images_write_path + 'central'):
            os.mkdir(self.test_images_write_path + 'central')

        full_dataset = os.path.join(os.environ["COIL_DATASET_PATH"], 'ValTraining')
        # This depends on the number of fused frames. A image could have
        # A certain number of fused frames
        g_conf.TRAIN_DATASET_NAME = 'ValTraining'
        g_conf.NUMBER_OF_ITERATIONS = 10000
        g_conf.NUMBER_OF_HOURS = 50
        g_conf.DATA_USED = 'all'




        augmenter = input.Augmenter(None)
        dataset = input.CoILDataset(full_dataset, transform=augmenter,
                              preload_name=str(g_conf.NUMBER_OF_HOURS) +
                                           'hours_' + g_conf.TRAIN_DATASET_NAME)



        model = CoILModel(g_conf.MODEL_TYPE, g_conf.MODEL_CONFIGURATION)
        model.cuda()


        # data_loader = torch.utils.data.DataLoader(dataset, batch_size=120,
        #                                          shuffle=True, num_workers=12, pin_memory=True)
        # capture_time = time.time()
        data_loader = select_balancing_strategy(dataset, 0, 12)
        print('len ', len(data_loader))

        count = 0
        for data in data_loader:


            branches = model(torch.squeeze(data['rgb'].cuda()),
                             dataset.extract_inputs(data).cuda())

            inter_layers = [model.intermediate_layers[ula] for ula in g_conf.USED_LAYERS_ATT]
            # here we call a function to get the wanted attention leyer

            # We reshape the labels input to be the same size as the inter_layer
            layer_count = 0
            for il in inter_layers:

                # Down sample does not exist. But maybe upsample does the same.
                labels_reshaped = F.downsample(data['labels'], size_new=(il.shape[1], il.shape[2]),
                                               mode='bilinear')


                # Try to convert this to a label image.
                image_to_save = transforms.ToPILImage()(
                    (data['rgb'][0].cpu() * 255).type(torch.ByteTensor))
                b, g, r = image_to_save.split()
                image_to_save = Image.merge("RGB", (r, g, b))
                image_to_save.save(
                    os.path.join(self.test_images_write_path + 'central', str(count) + 'label.png'))

                att = compute_attention_map_L1(il)

                image_to_save = transforms.ToPILImage()(
                    (data['rgb'][0].cpu() * 255).type(torch.ByteTensor))
                b, g, r = image_to_save.split()
                image_to_save = Image.merge("RGB", (r, g, b))
                image_to_save.save(
                    os.path.join(self.test_images_write_path + 'central', str(count) + 'att'
                                 + str(layer_count) + '.png'))

                layer_count += 1

                # Lets get the attention for CAR

                print (" Amount of attention for cars ", sum(att[np.where(labels_reshaped==10)]))

                # Lets get the attention on pedestrian labels


                #inter_layers = where(labels_reshaped==4)

                # Lets get the attention on road markings labels

                #inter_layers = where(labels_reshaped==6)



                # Labels is equal the traffic signs

                #inter_layers = where(labels_reshaped==12)



            image_to_save = transforms.ToPILImage()((data['rgb'][0].cpu()*255).type(torch.ByteTensor))
            b, g, r = image_to_save.split()
            image_to_save = Image.merge("RGB", (r, g, b))
            image_to_save.save(os.path.join(self.test_images_write_path + 'central', str(count)+'rgb.png'))



            # Test steerings after augmentation
            #print("steer: ", data['steer'][0], "angle: ", data['angle'][0])
            #print ("directions", data['directions'], " speed_module", data['speed_module'])
            count += 1
