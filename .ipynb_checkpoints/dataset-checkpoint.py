from albumentations.core.composition import OneOf
import torch
import numpy as np
from PIL import Image
from PIL import ImagePath
import random
import config
import albumentations as A
import cv2
import glob

class ImageTransform():
    def __init__(self, image_array):
        self.image_array = image_array

    def normalize(self, image):
        # normalise image with 0 mean, 1 std
        return (image - np.mean(image)) / (np.std(image)).astype(np.float32)
    
    def minmax_norm(self, image):
        # min-max to bring image in range 0,1. albumentations requires it.
        return ((image - np.min(image))/(np.max(image) - np.min(image)))
    
    def album(self):
        transform = A.Compose([
            A.OneOf([
                    A.RandomBrightnessContrast(brightness_limit = [-0.3,0.2], contrast_limit = [-0.3,0.2], p =0.75),
                    A.Sharpen(alpha = [0.1,0.4], lightness = [0.6, 1], p=0.75),
            ]),
            A.HorizontalFlip(p=0.6),
            A.ShiftScaleRotate(shift_limit_x=(-0.08, 0.08), scale_limit=0, rotate_limit=0,
                                p=1)
                    ])
       
        trans_image_array = transform(image = self.minmax_norm(np.copy(self.image_array)))['image']
        return self.normalize(trans_image_array)

    def swap_channels(self, p = 0.3, ):
        if np.random.uniform(0, 1) <= p:
            # init_shape = (t, f)
            final_shape = self.image_array.shape
            chnl_shape = (final_shape[0]//6, final_shape[1]//1) #will be approx to note.


            chnls = {'pos_chnls': [0,2,4], 'neg_chnls': [1,3,5]}
            chnls['pos_chnls'].remove(random.choice(chnls['pos_chnls']))
            chnls['neg_chnls'].remove(random.choice(chnls['neg_chnls']))
            swap_op = random.choice(['pos_chnls', 'neg_chnls', 'both_swap'])

            f = chnl_shape[1]
            t = chnl_shape[0]

            # image_patches = [self.image_array[c:(c+1)*t, : f]], c = 0, 1, 2 ,3, 4, 5
            trans_image_array = np.copy(self.image_array)
            if swap_op == 'pos_chnls' or swap_op == 'both_swap':
                c1 = chnls['pos_chnls'][0]
                c2 = chnls['pos_chnls'][1]
#                 print(f'swapping{c1}{c2}')
                trans_image_array[c1*t:(c1+1)*t, : f] = self.image_array[c2*t:(c2+1)*t, : f]
                trans_image_array[c2*t:(c2+1)*t, : f] = self.image_array[c1*t:(c1+1)*t, : f]

            if swap_op == 'neg_chnls' or swap_op == 'both_swap':
                c1 = chnls['neg_chnls'][0]
                c2 = chnls['neg_chnls'][1]
#                 print(f'swapping{c1}{c2}')
                trans_image_array[c1*t:(c1+1)*t, : f] = self.image_array[c2*t:(c2+1)*t, : f]
                trans_image_array[c2*t:(c2+1)*t, : f] = self.image_array[c1*t:(c1+1)*t, : f] 

            return self.normalize(trans_image_array)
        else:
            return self.image_array.astype(np.float32)

    def drop_channels(self, p = 0.3,):
        if np.random.uniform(0, 1) <= p:
            # init_shape = (t, f)
            final_shape = self.image_array.shape
            chnl_shape = (final_shape[0]//6, final_shape[1]//1) #will be approx to note.

            chnls = {'pos_chnls': [0,2,4], 'neg_chnls': [1,3,5]}
            chnls_to_remove = random.sample(chnls['neg_chnls'], random.choice([1,2]))

            f = chnl_shape[1]
            t = chnl_shape[0]

            # image_patches = [self.image_array[c:(c+1)*t, : f]], c = 0, 1, 2 ,3, 4, 5
            trans_image_array = np.copy(self.image_array)
            for c in chnls_to_remove:
                trans_image_array[c*t:(c+1)*t, : f] = np.min(trans_image_array)

            return self.normalize(trans_image_array)
        else:
            return self.image_array.astype(np.float32)
#     img - (6, 273, 256)

# function on one channel- add_needle(chl_img, needle_img): combime(chl_img, aug(needle_img))

# a sample - (256,256) define channels - 6
#  sample_type = random.choice(pos_sample or neg_sample)
#   if sample_type == pos_sample: add_needle to 0,2 or 4 channel
#    else: add_needle to 1,3 or 5 channel or add_needle to 0,1,2,3,4,5 channels
    
    def add_needle(self, chls_to_add_needle, needle_img, blend_prop = 0.5):
        fimg = np.copy(self.image_array)
        final_shape = fimg.shape
        chnl_shape = (final_shape[0]//6, final_shape[1]//1) #will be approx to note.
        f = chnl_shape[1]
        t = chnl_shape[0]
        needle_img = cv2.resize(needle_img, dsize = (f, t), interpolation=cv2.INTER_AREA)
        for chl in chls_to_add_needle:
            fimg[chl*t:(chl+1)*t, : f] = (1 - blend_prop)*fimg[chl*t:(chl+1)*t, : f] + blend_prop*needle_img
        return self.normalize(fimg).astype(np.float32)

    def apply_ext_needle(self):
        ftarget_type = random.choice([0, 1])
        needle_type = random.choice([
#             'nb/',
#             'nbd/',
#             'spnb/',
#             'squ/',
            'squigglesquarepulsednarrowband'
            ])
        needle_path = random.choice(glob.glob(f'{config.NEEDLE_PATH}*/{needle_type}/*.png'))
        needle_img = self.normalize(cv2.imread(needle_path, cv2.IMREAD_GRAYSCALE))

        if ftarget_type == 1:
            chls_to_add_needle = random.sample([0, 2, 4], random.choice([1, 2, 3]))
            trans_image_array = self.add_needle(chls_to_add_needle, needle_img)
        else:
            needle_img = np.amax(needle_img) - needle_img
            chls_to_add_needle = random.sample([1, 3, 5], random.choice([1, 2, 3]))
            trans_image_array = self.add_needle(chls_to_add_needle, needle_img)
        return trans_image_array

class SetiDataset:
    def __init__(self, image_paths, targets = None, ids = None, resize=None, augmentations = None):
        self.image_paths = image_paths
        self.targets = targets
        self.ids = ids
        self.resize = resize
        self.augmentations = augmentations

    def __len__(self):
        return len(self.image_paths)
        
    def __getitem__(self, item):
        # image = Image.open(self.image_paths[item])
        image = np.load(self.image_paths[item])
        
        id = self.ids[item]
        
        if config.ORIG_IMAGE:
#           converting 6 channels to 1 for original image, inverting off channels
            max_pix = np.amax(image)
            image[1] = max_pix - image[1]
            image[3] = max_pix - image[3]
            image[5] = max_pix - image[5]
            image = np.vstack(image)
            image = image.astype(np.float32)
            
        if self.targets is not None:
            target = self.targets[item]

        if self.resize is not None:
            image = image.resize(self.resize[1], self.resize[0], resample = Image.BILINEAR)

        imt = ImageTransform(image)
        image = imt.apply_ext_needle()
        if self.augmentations is not None:
            image = imt.album()
            image = imt.swap_channels(p = 0.7)
            image = imt.drop_channels(p = 0.3)
#         print('1ds', np.mean(image), np.std(image))
#         image =  imt.normalize(cv2.resize(image, dsize=(256, 256), interpolation=cv2.INTER_AREA))
        image = image.reshape(1,image.shape[0],image.shape[1])
        
        #pytorch expects channelHeightWidth instead of HeightWidthChannel
        # image = np.transpose(image, (2, 0, 1)).astype(np.float32)
    
        if self.targets is not None:
            return{'images': torch.tensor(image.copy(), dtype = torch.float), 
                    'targets': torch.tensor(target, dtype = torch.long),
                  'ids': torch.tensor(id, dtype = torch.int32)}
        else:
            return{'images': torch.tensor(image.copy(), dtype = torch.float),
                  'ids': torch.tensor(id, dtype = torch.int32)}

# i = SetiDataset([f'{config.DATA_PATH}train/1/1a0a41c753e1.npy'], targets = [1], ids =[0], resize=None, augmentations = None)[0]

# i = SetiDataset([f'/content/drive/MyDrive/SETI/resized_images/256256/train/1a0a41c753e1.npy'], targets = [1], ids =[0], resize=None, augmentations = None)[0]
# print(i)