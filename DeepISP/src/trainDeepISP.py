## Train DeepISP

import tensorflow as tf
from model import create_complete_model
from tensorflow.keras.utils import plot_model
from dataImportHelper import parse_image_S7_X,parse_image_S7_Y,parse_image, random_crop_joint,horizontal_flip_joint
from customLossesAndMetrics import MSSSIM, HL_loss
import os
import glob
from numpy import savetxt
import matplotlib.pyplot as plt

S7_DATA_PATH ='S7-ISP-Dataset-Sorted/S7-ISP-Short-Exposure'
DATAX_PATH = os.path.join(os.getcwd(),S7_DATA_PATH,'X_dem_cropped') 
DATAY_PATH = os.path.join(os.getcwd(),S7_DATA_PATH,'Y_cropped') 


BATCH_SIZE = 1 # In the paper, they use BATCH_SIZE=1. Here, if it is >1 there is a bug. To be fixed

tf.random.set_seed(1234)

AUTOTUNE = tf.data.experimental.AUTOTUNE

# ## Dataset

names = [x.split('/')[-1].split('.')[0] for x in glob.glob(os.path.join(DATAX_PATH,'*.png'))]
train_names = names[:90]
val_names = names[90:99]
test_names = names[99:]
savetxt('test_names.txt',[int(test_name) for test_name in test_names],fmt='%d') #will use at test time

X_train_paths = tf.constant([os.path.join(DATAX_PATH,name+'.png') for name in train_names])
Y_train_paths = tf.constant([os.path.join(DATAY_PATH,name+'.jpg') for name in train_names])
X_val_paths = tf.constant([os.path.join(DATAX_PATH,name+'.png') for name in val_names])
Y_val_paths = tf.constant([os.path.join(DATAY_PATH,name+'.jpg') for name in val_names])


# Training set
list_ds_train_X = tf.data.Dataset.list_files(X_train_paths, seed=42) # seed for random but consistent shuffling #TODO: vs ds.shuffle(buffer)  ??
list_ds_train_Y = tf.data.Dataset.list_files(Y_train_paths, seed=42)
trainX = list_ds_train_X.map(parse_image_S7_X,num_parallel_calls=AUTOTUNE)  
trainY = list_ds_train_Y.map(parse_image_S7_Y,num_parallel_calls=AUTOTUNE)

#ds_crop_flipped = tf.data.Dataset.zip((trainX,trainY)).repeat(2).map(random_crop_joint,num_parallel_calls=AUTOTUNE).map(horizontal_flip_joint,num_parallel_calls=AUTOTUNE)
ds_train = (tf.data.Dataset.zip((trainX,trainY))
             .batch(BATCH_SIZE)
             .prefetch(AUTOTUNE)
             .cache(filename='TODO')
           )

#.map(random_crop_joint,num_parallel_calls=AUTOTUNE)
#shuffle(100)

# Validation set
'''list_ds_val_X = tf.data.Dataset.list_files(X_val_paths, seed=42) # seed for random but consistent shuffling #TODO: vs ds.shuffle(buffer)  ??
list_ds_val_Y = tf.data.Dataset.list_files(Y_val_paths, seed=42)
valX = list_ds_val_X.map(parse_image_S7_X,num_parallel_calls=AUTOTUNE)
valY = list_ds_val_Y.map(parse_image_S7_Y,num_parallel_calls=AUTOTUNE)

ds_val = tf.data.Dataset.zip((valX,valY)).map(random_crop_joint,num_parallel_calls=AUTOTUNE).batch(BATCH_SIZE)'''


# ## Training

## Dir to save model progress
checkpoint_path = "training_DeepISP_1/cp.ckpt"
checkpoint_dir = os.path.dirname(checkpoint_path)

## All S7 images have same H*W (3024x4032). Assume all images in dataset have same orientation (use enforce_S7_orientation)
#dim1 = 1024  # training on 1024x1024 patches
#dim2 = 1024
#
dim1 = 200
dim2 = 200
N_ll=15
N_hl=3


ISP_model = create_complete_model(dim1,dim2,N_ll,N_hl)

# Create a callback that saves the model's weights
cp_callback = tf.keras.callbacks.ModelCheckpoint(filepath=checkpoint_path,
                                                 save_weights_only=True,
                                                 verbose=1)

# Callback that logs training epoch info to csv
csv_logger = tf.keras.callbacks.CSVLogger('DeepISP_training.log')

optimizer = tf.keras.optimizers.Adam(learning_rate=0.00005,
                                    beta_1=0.9,
                                    beta_2=0.999,
                                    epsilon=1e-08)


ISP_model.compile(optimizer=optimizer,  # Optimizer
              # Loss function to minimize
              loss=HL_loss,
              # List of metrics to monitor
              metrics=[])

history =  ISP_model.fit(x= ds_train,
              epochs=200,
              validation_data=None, # won't be used, not metric passed in compile()
              validation_freq=None,
              validation_steps=None, 
              verbose=1,
              callbacks=[cp_callback, csv_logger])  # Pass callback to training




