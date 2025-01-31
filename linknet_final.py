# I have written this code in colab so the data was mounted from the drive

import os
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers
import pandas as pd
from PIL import Image
import matplotlib.pyplot as plt

df = pd.read_csv("/kaggale/detecting-crop-rows-from-image-data (1)/train and test ids.csv", dtype = 'str')
image_dir = '/kaggale/detecting-crop-rows-from-image-data (1)/Images/Images'
label_dir = '/kaggale/detecting-crop-rows-from-image-data (1)/train_labels/train_labels'

# Function to load and preprocess images
def load_and_preprocess_images(ids, image_dir):
    images = []

    for img_id in ids:
        img_id = int(img_id)  # Convert the ID to an integer to remove any decimal points
        img_path = os.path.join(image_dir, f'crop_row_{img_id:03d}.jpg')  # Use string formatting to pad with zeros
        img = Image.open(img_path)
        img_array = np.array(img) / 255.0  # Normalize pixel values between 0 and 1
        images.append(img_array)

    return np.array(images)
# Load and preprocess the train and test images
train_images = load_and_preprocess_images(df['train_ids'].dropna().values, image_dir)
test_images = load_and_preprocess_images(df['test_ids'].dropna().values, image_dir)

# Function to load the train labels
def load_train_labels(ids, label_dir):
    labels = []

    for img_id in ids:
        img_id = int(img_id)
        label_path = os.path.join(label_dir, f'crop_row_{img_id:03d}.npy')
        label = np.load(label_path)
        # Consider only one channel
        label = label[:, :, 0]
        # Normalize between 0 and 1
        label = label / 255.0
        labels.append(label)

    return np.array(labels)

# Load the train labels
train_labels = load_train_labels(df['train_ids'].dropna().values, label_dir)

import tensorflow as tf
from tensorflow.keras import layers

def encoder_block(input_tensor, filters):
    x = layers.Conv2D(filters, (3, 3), activation='relu', padding='same')(input_tensor)
    x = layers.BatchNormalization()(x)
    x = layers.Conv2D(filters, (3, 3), activation='relu', padding='same')(x)
    x = layers.BatchNormalization()(x)
    return x

def decoder_block(input_tensor, concat_tensor, filters):
    x = layers.Conv2DTranspose(filters, (2, 2), strides=(2, 2), padding='same')(input_tensor)
    x = layers.concatenate([x, concat_tensor])
    x = layers.Conv2D(filters, (3, 3), activation='relu', padding='same')(x)
    x = layers.BatchNormalization()(x)
    x = layers.Conv2D(filters, (3, 3), activation='relu', padding='same')(x)
    x = layers.BatchNormalization()(x)
    return x

def linknet(input_shape=(240, 320, 3)):
    inputs = layers.Input(input_shape)

    # Encoder
    e1 = encoder_block(inputs, 64)
    p1 = layers.MaxPooling2D((2, 2))(e1)

    e2 = encoder_block(p1, 128)
    p2 = layers.MaxPooling2D((2, 2))(e2)

    e3 = encoder_block(p2, 256)
    p3 = layers.MaxPooling2D((2, 2))(e3)

    e4 = encoder_block(p3, 512)
    p4 = layers.MaxPooling2D((2, 2))(e4)

    # Bridge
    bridge = encoder_block(p4, 1024)

    # Decoder
    d4 = decoder_block(bridge, e4, 512)
    d3 = decoder_block(d4, e3, 256)
    d2 = decoder_block(d3, e2, 128)
    d1 = decoder_block(d2, e1, 64)

    # Output
    outputs = layers.Conv2D(1, (1, 1), activation='sigmoid')(d1)

    # Create model
    model = tf.keras.Model(inputs=inputs, outputs=outputs)
    return model

train_labels = np.reshape(train_labels,(210,240,320,1))

train_labels.shape

model = linknet()
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

history = model.fit(train_images, train_labels, batch_size=6, epochs=110, validation_split=0.2)

plt.plot(history.history['loss'])
plt.plot(history.history['val_loss'])
plt.legend(['training loss','validation loss'])
plt.show()

plt.plot(history.history['accuracy'])
plt.plot(history.history['val_accuracy'])
plt.legend(['training accuracy','validation accuracy'])
plt.show()

def rle_encode(mask):
    '''
    mask: numpy array binary mask
    255 - mask
    0 - background
    Returns encoded run length
    '''
    pixels = mask.flatten()
    pixels = np.concatenate([[0], pixels, [0]])
    runs = np.where(pixels[1:] != pixels[:-1])[0] + 1
    runs[1::2] -= runs[::2]

    return ' '.join(str(x) for x in runs)

import matplotlib.pyplot as plt

# Load and preprocess the image
def load_and_preprocess_image(image_path):
    img = Image.open(image_path)
    #img = img.resize(target_size)
    img_array = np.array(img) / 255.0  # Normalize pixel values between 0 and 1
    return np.expand_dims(img_array, axis=0)  # Add a batch dimension

# Load the image you want to predict
image_path = "/content/drive/MyDrive/DL kaggale/detecting-crop-rows-from-image-data (1)/Images/Images/crop_row_001.jpg"
label_path = "/content/drive/MyDrive/DL kaggale/detecting-crop-rows-from-image-data (1)/train_labels/train_labels/crop_row_001.npy"
image = load_and_preprocess_image(image_path)

# Predict the segmentation using the trained model
segmentation = model.predict(image)

# Remove the batch dimension and convert the segmentation to binary values (0 or 255)
segmentation = (segmentation.squeeze() * 255).astype(np.uint8)
threshold = 0.20
output = (segmentation/np.max(segmentation) > threshold).astype(np.uint8)


label = np.load(label_path)[:, :, 0] // 255

# Plot the input image, label, and predicted mask
fig, axs = plt.subplots(1, 3, figsize=(10, 5))
axs[0].imshow(image.squeeze())
axs[0].set_title('Input Image')
axs[1].imshow(label, cmap='gray')
axs[1].set_title('Ground Truth Label')
axs[2].imshow(output, cmap='gray')
axs[2].set_title('Predicted Label')
plt.show()

output

def IOU(output,label):
  overlap = label*output
  union = label+output
  IOU = overlap.sum()/float(union.sum())
  return(IOU)

train_ids = df['train_ids'].dropna().values
test_ids = df['test_ids'].dropna().values

import matplotlib.pyplot as plt

# Load and preprocess the image
def load_and_preprocess_image(image_path):
    img = Image.open(image_path)
    img_array = np.array(img) / 255.0  # Normalize pixel values between 0 and 1
    return np.expand_dims(img_array, axis=0)  # Add a batch dimension

# Function to load the train labels
def load_and_preprocess_label(label_path):
    label = np.load(label_path)
    # Consider only one channel
    label = label[:, :, 0]
    # Normalize between 0 and 1
    label = label / 255.0
    return (label)

IOU_total = []
for img in train_ids:
  img_id = int(img)
  # Load the image you want to predict
  image_path = os.path.join(image_dir, f'crop_row_{img_id:03d}.jpg')
  label_path = os.path.join(label_dir, f'crop_row_{img_id:03d}.npy')
  image = load_and_preprocess_image(image_path)
  label = load_and_preprocess_label(label_path)

  # Predict the segmentation using the trained model
  segmentation = model.predict(image)

  # Remove the batch dimension and convert the segmentation to binary values (0 or 255)
  segmentation = (segmentation.squeeze() * 255).astype(np.uint8)

  threshold = 0.5
  output = (segmentation/np.max(segmentation) > threshold).astype(np.uint8)
  IOU_total.append(IOU(output,label))

sum(IOU_total)/len(IOU_total)

#-----------------------------------Testing------------------------------------------#
rle_enconde_list = []
for img in test_ids:
  img_id = int(img)
  # Load the image you want to predict
  image_path = os.path.join(image_dir, f'crop_row_{img_id:03d}.jpg')
  image = load_and_preprocess_image(image_path)

  # Predict the segmentation using the trained model
  segmentation = model.predict(image)

  # Remove the batch dimension and convert the segmentation to binary values (0 or 255)
  segmentation = (segmentation.squeeze() * 255).astype(np.uint8)

  threshold = 0.5
  output = (segmentation/np.max(segmentation) > threshold).astype(np.uint8)
  rle_enconde_list.append(rle_encode(output))

d = {}
d['ids'] = list(test_ids)
d['labels'] = rle_enconde_list
df_test = pd.DataFrame(d)

df_test

df_test.to_csv('unet_results.csv', index=False)

df_test.to_csv('RaviTeja_Seera_finalattempt1.csv')

from google.colab import files
files.download('RaviTeja_Seera_finalattempt1.csv')

