import datetime
import pytz
import os


tz_NY = pytz.timezone('Asia/Kolkata')
datetime_NY = datetime.datetime.now(tz_NY)
DATETIME = datetime_NY.strftime('%m%d')

i = 0
input_path = ['/mnt/gfs/gv1/project_sonar_data/seti/', '/content/drive/MyDrive/SETI/input/']
DATA_PATH = input_path[i]


IMAGE_SIZE = (256,256)
resize_image_path = [f'/home/asajw/resized_images_seti/{IMAGE_SIZE[0]}{IMAGE_SIZE[1]}/',
                     f'/content/drive/MyDrive/SETI/resized_images/{IMAGE_SIZE[0]}{IMAGE_SIZE[1]}/']

RESIZED_IMAGE_PATH = resize_image_path[i]
try:
    os.makedirs(RESIZED_IMAGE_PATH[:-1])
except:
    print(f'error creating {RESIZED_IMAGE_PATH[:-1]}')
SAVE_IMAGE = True


DEBUG = False
MIXED_PRECISION = True

DEVICE = 'cuda'
EPOCHS = 7
BATCH_SIZE = 32
TARGET_SIZE = 1
FOLDS = 4

MODEL_NAME = 'efficientnet_b0'
CHANNELS = 1

LEARNING_RATE = 5e-5
FACTOR = 0.1
PATIENCE = 2
EPS = 1e-8


SEED = 42

out_path = ['/home/asajw/seti_models/', '/content/drive/MyDrive/SETI/output/']
MODEL_OUTPUT_PATH = out_path[i]

log_path = ['/home/asajw/SETI/output/', '/content/SETI/output/']
foldername = f'{MODEL_NAME}_dt{DATETIME}'
LOG_DIR = f'{os.path.join(log_path[i], foldername)}/'
try:
    os.mkdir(LOG_DIR[:-1])
except:
    print('folder exists, make sure this call is from inference.py')

INFER = False
