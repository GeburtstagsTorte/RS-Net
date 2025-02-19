import keras as k
import numpy as np
from keras.models import Model
from keras import layers
from keras.layers import Input, Conv2D, MaxPooling2D, UpSampling2D, Concatenate, Dropout, Cropping2D, Activation, BatchNormalization
from keras import utils
import keras.utils
from keras.models import Model
from keras import regularizers
from keras.metrics import Precision, Recall
from keras.initializers import GlorotNormal, HeNormal
from keras.layers import Input, Conv2D, MaxPooling2D, UpSampling2D, Concatenate, Dropout, Cropping2D, Activation, BatchNormalization
from keras.optimizers import AdamW

from keras.models import Model
from keras.layers import *
import keras
from tensorflow.keras.optimizers import *
import tensorflow as tf

from keras import backend as K

smooth = 0.0000001
activation_func = "relu"
initialization = "glorot_uniform"
l2_reg = 1e-3
overlap = 40
last_layer_activation_func="softmax"
batch_norm_momentum = 0.99
dropout=0.15


def get_model():
    model = model_arch_256(input_rows=256,
        input_cols=256, 
        num_of_channels=7, 
        num_of_classes=5, 
        conv2d_kernel_shape=(7,7))
    
    model.input.set_shape((batch_size,) + model.input.shape[1:])


    return model


def aspp(x,out_shape):
    b0=SeparableConv2D(256,(1,1),padding="same",use_bias=False, depthwise_regularizer=regularizers.l2(l2_reg), depthwise_initializer=initialization)(x)
    b0=BatchNormalization()(b0)
    b0=Activation(activation_func)(b0)

    #b5=DepthwiseConv2D((3,3),dilation_rate=(3,3),padding="same",use_bias=False)(x)
    #b5=BatchNormalization()(b5)
    #b5=Activation(activation_func)(b5)
    #b5=SeparableConv2D(256,(1,1),padding="same",use_bias=False)(b5)
    #b5=BatchNormalization()(b5)
    #b5=Activation(activation_func)(b5)
    
    b1=DepthwiseConv2D((3,3),dilation_rate=(6,6),padding="same",use_bias=False, depthwise_regularizer=regularizers.l2(l2_reg), depthwise_initializer=initialization)(x)
    b1=BatchNormalization()(b1)
    b1=Activation(activation_func)(b1)
    b1=SeparableConv2D(256,(1,1),padding="same",use_bias=False, depthwise_regularizer=regularizers.l2(l2_reg), depthwise_initializer=initialization)(b1)
    b1=BatchNormalization()(b1)
    b1=Activation(activation_func)(b1)
    
    b2=DepthwiseConv2D((3,3),dilation_rate=(12,12),padding="same",use_bias=False, depthwise_regularizer=regularizers.l2(l2_reg), depthwise_initializer=initialization)(x)
    b2=BatchNormalization()(b2)
    b2=Activation(activation_func)(b2)
    b2=SeparableConv2D(256,(1,1),padding="same",use_bias=False, depthwise_regularizer=regularizers.l2(l2_reg), depthwise_initializer=initialization)(b2)
    b2=BatchNormalization()(b2)
    b2=Activation(activation_func)(b2)	
    
    b3=DepthwiseConv2D((3,3),dilation_rate=(18,18),padding="same",use_bias=False, depthwise_regularizer=regularizers.l2(l2_reg), depthwise_initializer=initialization)(x)
    b3=BatchNormalization()(b3)
    b3=Activation(activation_func)(b3)
    b3=SeparableConv2D(256,(1,1),padding="same",use_bias=False, depthwise_regularizer=regularizers.l2(l2_reg), depthwise_initializer=initialization)(b3)
    b3=BatchNormalization()(b3)
    b3=Activation(activation_func)(b3)
    
    b4=AveragePooling2D(pool_size=(out_shape,out_shape))(x)
    b4=SeparableConv2D(256,(1,1),padding="same",use_bias=False, depthwise_regularizer=regularizers.l2(l2_reg), depthwise_initializer=initialization)(b4)
    b4=BatchNormalization()(b4)
    b4=Activation(activation_func)(b4)
    b4=UpSampling2D((out_shape,out_shape), interpolation='bilinear')(b4)
    x=Concatenate()([b4,b0,b1,b2,b3])
    return x



def jacc_coef(y_true, y_pred):
    y_true_f = K.flatten(y_true)
    y_pred_f = K.flatten(y_pred)
    intersection = K.sum(y_true_f * y_pred_f)
    return 1 - ((intersection + smooth) / (K.sum(y_true_f) + K.sum(y_pred_f) - intersection + smooth))

def bn_relu(input_tensor):
    """It adds a Batch_normalization layer before a Relu
    """
    input_tensor = BatchNormalization(axis=3)(input_tensor)
    return Activation(activation_func)(input_tensor)

def contr_arm(input_tensor, filters, kernel_size):
    """It adds a feedforward signal to the output of two following conv layers in contracting path
    TO DO: remove keras.layers.add and replace it with add only
    """

    x = SeparableConv2D(filters, kernel_size, padding='same', depthwise_regularizer=regularizers.l2(l2_reg), depthwise_initializer=initialization)(input_tensor)
    x = bn_relu(x)

    x = SeparableConv2D(filters, kernel_size, padding='same', depthwise_regularizer=regularizers.l2(l2_reg), depthwise_initializer=initialization)(x)
    x = bn_relu(x)

    filters_b = filters // 2
    kernel_size_b = (kernel_size[0]-2, kernel_size[0]-2)  # creates a kernl size of (1,1) out of (3,3)

    x1 = SeparableConv2D(filters_b, kernel_size_b, padding='same', depthwise_regularizer=regularizers.l2(l2_reg), depthwise_initializer=initialization)(input_tensor)
    x1 = bn_relu(x1)

    x1 = concatenate([input_tensor, x1], axis=3)
    x = keras.layers.add([x, x1])
    x = Activation(activation_func)(x)
    return x
    



def imprv_contr_arm(input_tensor, filters, kernel_size):
    """It adds a feedforward signal to the output of two following conv layers in contracting path
    """

    x = SeparableConv2D(filters, kernel_size, padding='same', depthwise_regularizer=regularizers.l2(l2_reg), depthwise_initializer=initialization)(input_tensor)
    x = bn_relu(x)

    x0 = SeparableConv2D(filters, kernel_size, padding='same', depthwise_regularizer=regularizers.l2(l2_reg), depthwise_initializer=initialization)(x)
    x0 = bn_relu(x0)

    x = SeparableConv2D(filters, kernel_size, padding='same', depthwise_regularizer=regularizers.l2(l2_reg), depthwise_initializer=initialization)(x0)
    x = bn_relu(x)

    filters_b = filters // 2
    kernel_size_b = (kernel_size[0]-2, kernel_size[0]-2)  # creates a kernl size of (1,1) out of (3,3)

    x1 = SeparableConv2D(filters_b, kernel_size_b, padding='same', depthwise_regularizer=regularizers.l2(l2_reg), depthwise_initializer=initialization)(input_tensor)
    x1 =bn_relu(x1)

    x1 = concatenate([input_tensor, x1], axis=3)

    x2 = SeparableConv2D(filters, kernel_size_b, padding='same', depthwise_regularizer=regularizers.l2(l2_reg), depthwise_initializer=initialization)(x0)
    x2 = bn_relu(x2)

    x = keras.layers.add([x, x1, x2])
    x = Activation(activation_func)(x)
    return x


def bridge(input_tensor, filters, kernel_size, dropout):
    """It is exactly like the identity_block plus a dropout layer. This block only uses in the valley of the UNet
    """

    x = SeparableConv2D(filters, kernel_size, padding='same', depthwise_regularizer=regularizers.l2(l2_reg), bias_regularizer=regularizers.l2(l2_reg),
                            depthwise_initializer=initialization)(input_tensor)
    x = bn_relu(x)

    x = SeparableConv2D(filters, kernel_size, padding='same', depthwise_regularizer=regularizers.l2(l2_reg), bias_regularizer=regularizers.l2(l2_reg),
                            depthwise_initializer=initialization)(x)
    # x = Dropout(.15)(x)
    x = Dropout(dropout)(x)
    x = bn_relu(x)

    filters_b = filters // 2
    kernel_size_b = (kernel_size[0]-2, kernel_size[0]-2)  # creates a kernl size of (1,1) out of (3,3)

    x1 =SeparableConv2D(filters_b, kernel_size_b, padding='same', depthwise_regularizer=regularizers.l2(l2_reg), bias_regularizer=regularizers.l2(l2_reg),
                            depthwise_initializer=initialization)(input_tensor)
    x1 = bn_relu(x1)

    x1 = concatenate([input_tensor, x1], axis=3)
    x = keras.layers.add([x, x1])
    x = Activation(activation_func)(x)
    return x


def conv_block_exp_path(input_tensor, filters, kernel_size):
    """It Is only the convolution part inside each expanding path's block
    """

    x = Conv2D(filters, kernel_size, padding='same', kernel_regularizer=regularizers.l2(l2_reg),
                    kernel_initializer=initialization)(input_tensor)
    x = bn_relu(x)

    x = Conv2D(filters, kernel_size, padding='same', kernel_regularizer=regularizers.l2(l2_reg),
                    kernel_initializer=initialization)(x)
    x = bn_relu(x)
    return x


def conv_block_exp_path3(input_tensor, filters, kernel_size):
    """It Is only the convolution part inside each expanding path's block
    """

    x = Conv2D(filters, kernel_size, padding='same', kernel_regularizer=regularizers.l2(l2_reg),
                    kernel_initializer=initialization)(input_tensor)
    x = bn_relu(x)

    x = Conv2D(filters, kernel_size, padding='same', kernel_regularizer=regularizers.l2(l2_reg),
                    kernel_initializer=initialization)(x)
    x = bn_relu(x)

    x = Conv2D(filters, kernel_size, padding='same', kernel_regularizer=regularizers.l2(l2_reg),
                    kernel_initializer=initialization)(x)
    x = bn_relu(x)
    return x


def add_block_exp_path(input_tensor1, input_tensor2, input_tensor3):
    """It is for adding two feed forwards to the output of the two following conv layers in expanding path
    """

    x = keras.layers.add([input_tensor1, input_tensor2, input_tensor3])
    x = Activation(activation_func)(x)
    return x


def improve_ff_block4(input_tensor1, input_tensor2 ,input_tensor3, input_tensor4, pure_ff):
    """It improves the skip connection by using previous layers feature maps
    TO DO: shrink all of ff blocks in one function/class
    """

    for ix in range(1):
        if ix == 0:
            x1 = input_tensor1
        x1 = concatenate([x1, input_tensor1], axis=3)
        x1 = MaxPooling2D(pool_size=(2, 2))(x1)

    for ix in range(3):
        if ix == 0:
            x2 = input_tensor2
        x2 = concatenate([x2, input_tensor2], axis=3)
    x2 = MaxPooling2D(pool_size=(4, 4))(x2)

    for ix in range(7):
        if ix == 0:
            x3 = input_tensor3
        x3 = concatenate([x3, input_tensor3], axis=3)
    x3 = MaxPooling2D(pool_size=(8, 8))(x3)

    for ix in range(15):
        if ix == 0:
            x4 = input_tensor4
        x4 = concatenate([x4, input_tensor4], axis=3)
    x4 = MaxPooling2D(pool_size=(16, 16))(x4)

    x = keras.layers.add([x1, x2, x3, x4, pure_ff])
    x = Activation(activation_func)(x)
    return x


def improve_ff_block3(input_tensor1, input_tensor2, input_tensor3, pure_ff):
    """It improves the skip connection by using previous layers feature maps
    """

    for ix in range(1):
        if ix == 0:
            x1 = input_tensor1
        x1 = concatenate([x1, input_tensor1], axis=3)
    x1 = MaxPooling2D(pool_size=(2, 2))(x1)

    for ix in range(3):
        if ix == 0:
            x2 = input_tensor2
        x2 = concatenate([x2, input_tensor2], axis=3)
    x2 = MaxPooling2D(pool_size=(4, 4))(x2)

    for ix in range(7):
        if ix == 0:
            x3 = input_tensor3
        x3 = concatenate([x3, input_tensor3], axis=3)
    x3 = MaxPooling2D(pool_size=(8, 8))(x3)

    x = keras.layers.add([x1, x2, x3, pure_ff])
    x = Activation(activation_func)(x)
    return x


def improve_ff_block2(input_tensor1, input_tensor2, pure_ff):
    """It improves the skip connection by using previous layers feature maps
    """

    for ix in range(1):
        if ix == 0:
            x1 = input_tensor1
        x1 = concatenate([x1, input_tensor1], axis=3)
    x1 = MaxPooling2D(pool_size=(2, 2))(x1)

    for ix in range(3):
        if ix == 0:
            x2 = input_tensor2
        x2 = concatenate([x2, input_tensor2], axis=3)
    x2 = MaxPooling2D(pool_size=(4, 4))(x2)

    x = keras.layers.add([x1, x2, pure_ff])
    x = Activation(activation_func)(x)
    return x


def improve_ff_block1(input_tensor1, pure_ff):
    """It improves the skip connection by using previous layers feature maps
    """

    for ix in range(1):
        if ix == 0:
            x1 = input_tensor1
        x1 = concatenate([x1, input_tensor1], axis=3)
    x1 = MaxPooling2D(pool_size=(2, 2))(x1)

    x = keras.layers.add([x1, pure_ff])
    x = Activation(activation_func)(x)
    return x
    
def model_arch_128_v2(input_rows=256, input_cols=256, num_of_channels=7, num_of_classes=4, conv2d_kernel_shape=(3,3)):
    inputs = Input((input_rows, input_cols, num_of_channels))
    conv1 = Conv2D(16, conv2d_kernel_shape, activation='relu', padding='same', kernel_regularizer=regularizers.l2(l2_reg),
                    kernel_initializer=initialization)(inputs)

    conv1 = contr_arm(conv1, 32, conv2d_kernel_shape)
    bn1 = BatchNormalization(momentum=batch_norm_momentum)(conv1)
    pool1 = MaxPooling2D(pool_size=(2, 2))(bn1)

    conv2 = contr_arm(pool1, 64, conv2d_kernel_shape)
    bn2 = BatchNormalization(momentum=batch_norm_momentum)(conv2)
    pool2 = MaxPooling2D(pool_size=(2, 2))(bn2)

    conv3 = imprv_contr_arm(pool2, 128, conv2d_kernel_shape)
    bn3 = BatchNormalization(momentum=batch_norm_momentum)(conv3)
    pool3 = MaxPooling2D(pool_size=(2, 2))(bn3)

    conv4 = bridge(pool3, 256, conv2d_kernel_shape, dropout=dropout)
    
    conv6  = aspp(conv4,input_rows//32)

    convT9 = Conv2DTranspose(128, (2, 2), strides=(2, 2), padding='same', kernel_regularizer=regularizers.l2(l2_reg), kernel_initializer=initialization)(conv6)
    prevup9 = improve_ff_block2(input_tensor1=conv2, input_tensor2=conv1, pure_ff=conv3)
    up9 = concatenate([convT9, prevup9], axis=3)
    conv9 = conv_block_exp_path(input_tensor=up9, filters=128, kernel_size=conv2d_kernel_shape)
    conv9 = add_block_exp_path(input_tensor1=conv9, input_tensor2=conv3, input_tensor3=convT9)

    convT10 = Conv2DTranspose(64, (2, 2), strides=(2, 2), padding='same', kernel_regularizer=regularizers.l2(l2_reg), kernel_initializer=initialization)(conv9)
    prevup10 = improve_ff_block1(input_tensor1=conv1, pure_ff=conv2)
    up10 = concatenate([convT10, prevup10], axis=3)
    conv10 = conv_block_exp_path(input_tensor=up10, filters=64, kernel_size=conv2d_kernel_shape)
    conv10 = add_block_exp_path(input_tensor1=conv10, input_tensor2=conv2, input_tensor3=convT10)

    convT11 = Conv2DTranspose(32, (2, 2), strides=(2, 2), padding='same', kernel_regularizer=regularizers.l2(l2_reg), kernel_initializer=initialization)(conv10)
    up11 = concatenate([convT11, conv1], axis=3)
    conv11 = conv_block_exp_path(input_tensor=up11, filters=32, kernel_size=conv2d_kernel_shape)
    conv11 = add_block_exp_path(input_tensor1=conv11, input_tensor2=conv1, input_tensor3=convT11)

    # -----------------------------------------------------------------------
    # add cropping from RS-Net
    clip_pixels = np.int32(overlap / 2)  #(overlap) / 2  # Only used for input in Cropping2D function on next line
    crop9 = Cropping2D(cropping=((clip_pixels, clip_pixels), (clip_pixels, clip_pixels)))(conv11)
    # -----------------------------------------------------------------------
    
    conv12 = Conv2D(num_of_classes, (1, 1), activation=last_layer_activation_func)(crop9)
    #conv12 = Conv2D(num_of_classes, (1, 1), activation='softmax')(conv11) # sigmoid

    return Model(inputs=[inputs], outputs=[conv12])

def model_arch_128(input_rows=256, input_cols=256, num_of_channels=7, num_of_classes=4, conv2d_kernel_shape=(3,3)):
    inputs = Input((input_rows, input_cols, num_of_channels))
    conv1 = Conv2D(16, conv2d_kernel_shape, activation='relu', padding='same', kernel_regularizer=regularizers.l2(l2_reg),
                    kernel_initializer=initialization)(inputs)

    conv1 = contr_arm(conv1, 32, conv2d_kernel_shape)
    pool1 = MaxPooling2D(pool_size=(2, 2))(conv1)

    conv2 = contr_arm(pool1, 64, conv2d_kernel_shape)
    pool2 = MaxPooling2D(pool_size=(2, 2))(conv2)

    conv3 = imprv_contr_arm(pool2, 128, conv2d_kernel_shape)
    pool3 = MaxPooling2D(pool_size=(2, 2))(conv3)

    conv4 = bridge(pool3, 256, conv2d_kernel_shape, dropout=dropout)
    
    conv6  = aspp(conv4,input_rows//32)

    convT9 = Conv2DTranspose(128, (2, 2), strides=(2, 2), padding='same', kernel_regularizer=regularizers.l2(l2_reg), kernel_initializer=initialization)(conv6)
    prevup9 = improve_ff_block2(input_tensor1=conv2, input_tensor2=conv1, pure_ff=conv3)
    up9 = concatenate([convT9, prevup9], axis=3)
    conv9 = conv_block_exp_path(input_tensor=up9, filters=128, kernel_size=conv2d_kernel_shape)
    conv9 = add_block_exp_path(input_tensor1=conv9, input_tensor2=conv3, input_tensor3=convT9)

    convT10 = Conv2DTranspose(64, (2, 2), strides=(2, 2), padding='same', kernel_regularizer=regularizers.l2(l2_reg), kernel_initializer=initialization)(conv9)
    prevup10 = improve_ff_block1(input_tensor1=conv1, pure_ff=conv2)
    up10 = concatenate([convT10, prevup10], axis=3)
    conv10 = conv_block_exp_path(input_tensor=up10, filters=64, kernel_size=conv2d_kernel_shape)
    conv10 = add_block_exp_path(input_tensor1=conv10, input_tensor2=conv2, input_tensor3=convT10)

    convT11 = Conv2DTranspose(32, (2, 2), strides=(2, 2), padding='same', kernel_regularizer=regularizers.l2(l2_reg), kernel_initializer=initialization)(conv10)
    up11 = concatenate([convT11, conv1], axis=3)
    conv11 = conv_block_exp_path(input_tensor=up11, filters=32, kernel_size=conv2d_kernel_shape)
    conv11 = add_block_exp_path(input_tensor1=conv11, input_tensor2=conv1, input_tensor3=convT11)

    # -----------------------------------------------------------------------
    # add cropping from RS-Net
    clip_pixels = np.int32(overlap / 2)  #(overlap) / 2  # Only used for input in Cropping2D function on next line
    crop9 = Cropping2D(cropping=((clip_pixels, clip_pixels), (clip_pixels, clip_pixels)))(conv11)
    # -----------------------------------------------------------------------
    
    conv12 = Conv2D(num_of_classes, (1, 1), activation=last_layer_activation_func)(crop9)
    #conv12 = Conv2D(num_of_classes, (1, 1), activation='softmax')(conv11) # sigmoid

    return Model(inputs=[inputs], outputs=[conv12])

def model_arch_256_bn(input_rows=256, input_cols=256, num_of_channels=7, num_of_classes=4, conv2d_kernel_shape=(3,3)):
    inputs = Input((input_rows, input_cols, num_of_channels))
    conv1 = Conv2D(16, conv2d_kernel_shape, activation=activation_func, padding='same',
                    kernel_regularizer=regularizers.l2(l2_reg),
                    kernel_initializer=initialization)(inputs)

    conv1 = contr_arm(conv1, 32, conv2d_kernel_shape)
    bn1 = BatchNormalization(momentum=batch_norm_momentum)(conv1)
    pool1 = MaxPooling2D(pool_size=(2, 2))(bn1)

    conv2 = contr_arm(pool1, 64, conv2d_kernel_shape)
    bn2 = BatchNormalization(momentum=batch_norm_momentum)(conv2)
    pool2 = MaxPooling2D(pool_size=(2, 2))(bn2)

    conv3 = contr_arm(pool2, 128, conv2d_kernel_shape)
    bn3 = BatchNormalization(momentum=batch_norm_momentum)(conv3)
    pool3 = MaxPooling2D(pool_size=(2, 2))(bn3)

    conv4 = imprv_contr_arm(pool3, 256, conv2d_kernel_shape)
    bn4 = BatchNormalization(momentum=batch_norm_momentum)(conv4)
    pool4 = MaxPooling2D(pool_size=(2, 2))(bn4)

    conv5 = bridge(pool4, 512, conv2d_kernel_shape, dropout)
    
    conv6  = aspp(conv5,input_rows//32)

    convT8 = Conv2DTranspose(256, (2, 2), strides=(2, 2), padding='same', kernel_regularizer=regularizers.l2(l2_reg),
                    kernel_initializer=initialization)(conv6)
    prevup8 = improve_ff_block3(input_tensor1=conv3, input_tensor2=conv2, input_tensor3=conv1, pure_ff=conv4)
    up8 = concatenate([convT8, prevup8], axis=3)
    conv8 = conv_block_exp_path(input_tensor=up8, filters=256, kernel_size=conv2d_kernel_shape)
    conv8 = add_block_exp_path(input_tensor1=conv8, input_tensor2=conv4, input_tensor3=convT8)

    convT9 = Conv2DTranspose(128, (2, 2), strides=(2, 2), padding='same', kernel_regularizer=regularizers.l2(l2_reg),
                    kernel_initializer=initialization)(conv8)
    prevup9 = improve_ff_block2(input_tensor1=conv2, input_tensor2=conv1, pure_ff=conv3)
    up9 = concatenate([convT9, prevup9], axis=3)
    conv9 = conv_block_exp_path(input_tensor=up9, filters=128, kernel_size=conv2d_kernel_shape)
    conv9 = add_block_exp_path(input_tensor1=conv9, input_tensor2=conv3, input_tensor3=convT9)

    convT10 = Conv2DTranspose(64, (2, 2), strides=(2, 2), padding='same', kernel_regularizer=regularizers.l2(l2_reg),
                    kernel_initializer=initialization)(conv9)
    prevup10 = improve_ff_block1(input_tensor1=conv1, pure_ff=conv2)
    up10 = concatenate([convT10, prevup10], axis=3)
    conv10 = conv_block_exp_path(input_tensor=up10, filters=64, kernel_size=conv2d_kernel_shape)
    conv10 = add_block_exp_path(input_tensor1=conv10, input_tensor2=conv2, input_tensor3=convT10)

    convT11 = Conv2DTranspose(32, (2, 2), strides=(2, 2), padding='same', kernel_regularizer=regularizers.l2(l2_reg),
                    kernel_initializer=initialization)(conv10)
    up11 = concatenate([convT11, conv1], axis=3)
    conv11 = conv_block_exp_path(input_tensor=up11, filters=32, kernel_size=conv2d_kernel_shape)
    conv11 = add_block_exp_path(input_tensor1=conv11, input_tensor2=conv1, input_tensor3=convT11)

    # -----------------------------------------------------------------------
    # add cropping from RS-Net
    clip_pixels = np.int32(overlap / 2)  #(overlap) / 2  # Only used for input in Cropping2D function on next line
    crop9 = Cropping2D(cropping=((clip_pixels, clip_pixels), (clip_pixels, clip_pixels)))(conv11)
    # -----------------------------------------------------------------------
    
    conv12 = Conv2D(num_of_classes, (1, 1), activation='softmax')(crop9) # sigmoid

    #conv12 = Conv2D(num_of_classes, (1, 1), activation='softmax')(conv11) # sigmoid

    return Model(inputs=[inputs], outputs=[conv12])

def model_arch_256( input_rows=256, input_cols=256, num_of_channels=7, num_of_classes=4, conv2d_kernel_shape=(3,3)):
    inputs = Input((input_rows, input_cols, num_of_channels))
    conv1 = Conv2D(16, conv2d_kernel_shape, activation='relu', padding='same',
                    kernel_regularizer=regularizers.l2(l2_reg),
                    kernel_initializer=initialization)(inputs)

    conv1 = contr_arm(conv1, 32, conv2d_kernel_shape)
    pool1 = MaxPooling2D(pool_size=(2, 2))(conv1)

    conv2 = contr_arm(pool1, 64, conv2d_kernel_shape)
    pool2 = MaxPooling2D(pool_size=(2, 2))(conv2)

    conv3 = contr_arm(pool2, 128, conv2d_kernel_shape)
    pool3 = MaxPooling2D(pool_size=(2, 2))(conv3)

    conv4 = imprv_contr_arm(pool3, 256, conv2d_kernel_shape)
    pool4 = MaxPooling2D(pool_size=(2, 2))(conv4)

    conv5 = bridge(pool4, 512, conv2d_kernel_shape, dropout)
    
    conv6  = aspp(conv5,input_rows//32)

    convT8 = Conv2DTranspose(256, (2, 2), strides=(2, 2), padding='same', kernel_regularizer=regularizers.l2(l2_reg),
                    kernel_initializer=initialization)(conv6)
    prevup8 = improve_ff_block3(input_tensor1=conv3, input_tensor2=conv2, input_tensor3=conv1, pure_ff=conv4)
    up8 = concatenate([convT8, prevup8], axis=3)
    conv8 = conv_block_exp_path(input_tensor=up8, filters=256, kernel_size=conv2d_kernel_shape)
    conv8 = add_block_exp_path(input_tensor1=conv8, input_tensor2=conv4, input_tensor3=convT8)

    convT9 = Conv2DTranspose(128, (2, 2), strides=(2, 2), padding='same', kernel_regularizer=regularizers.l2(l2_reg),
                    kernel_initializer=initialization)(conv8)
    prevup9 = improve_ff_block2(input_tensor1=conv2, input_tensor2=conv1, pure_ff=conv3)
    up9 = concatenate([convT9, prevup9], axis=3)
    conv9 = conv_block_exp_path(input_tensor=up9, filters=128, kernel_size=conv2d_kernel_shape)
    conv9 = add_block_exp_path(input_tensor1=conv9, input_tensor2=conv3, input_tensor3=convT9)

    convT10 = Conv2DTranspose(64, (2, 2), strides=(2, 2), padding='same', kernel_regularizer=regularizers.l2(l2_reg),
                    kernel_initializer=initialization)(conv9)
    prevup10 = improve_ff_block1(input_tensor1=conv1, pure_ff=conv2)
    up10 = concatenate([convT10, prevup10], axis=3)
    conv10 = conv_block_exp_path(input_tensor=up10, filters=64, kernel_size=conv2d_kernel_shape)
    conv10 = add_block_exp_path(input_tensor1=conv10, input_tensor2=conv2, input_tensor3=convT10)

    convT11 = Conv2DTranspose(32, (2, 2), strides=(2, 2), padding='same', kernel_regularizer=regularizers.l2(l2_reg),
                    kernel_initializer=initialization)(conv10)
    up11 = concatenate([convT11, conv1], axis=3)
    conv11 = conv_block_exp_path(input_tensor=up11, filters=32, kernel_size=conv2d_kernel_shape)
    conv11 = add_block_exp_path(input_tensor1=conv11, input_tensor2=conv1, input_tensor3=convT11)

    # -----------------------------------------------------------------------
    # add cropping from RS-Net
    clip_pixels = np.int32(overlap / 2)  #(overlap) / 2  # Only used for input in Cropping2D function on next line
    crop9 = Cropping2D(cropping=((clip_pixels, clip_pixels), (clip_pixels, clip_pixels)))(conv11)
    # -----------------------------------------------------------------------
    
    conv12 = Conv2D(num_of_classes, (1, 1), activation='softmax')(crop9) # sigmoid

    #conv12 = Conv2D(num_of_classes, (1, 1), activation='softmax')(conv11) # sigmoid

    return Model(inputs=[inputs], outputs=[conv12])


def model_arch(input_rows=256, input_cols=256, num_of_channels=7, num_of_classes=4, conv2d_kernel_shape=(3,3)):
    inputs = Input((input_rows, input_cols, num_of_channels))
    conv1 = Conv2D(16, conv2d_kernel_shape, activation='relu', padding='same')(inputs)

    conv1 = contr_arm(conv1, 32, conv2d_kernel_shape)
    pool1 = MaxPooling2D(pool_size=(2, 2))(conv1)

    conv2 = contr_arm(pool1, 64, conv2d_kernel_shape)
    pool2 = MaxPooling2D(pool_size=(2, 2))(conv2)

    conv3 = contr_arm(pool2, 128, conv2d_kernel_shape)
    pool3 = MaxPooling2D(pool_size=(2, 2))(conv3)

    conv4 = contr_arm(pool3, 256, conv2d_kernel_shape)
    pool4 = MaxPooling2D(pool_size=(2, 2))(conv4)

    conv5 = imprv_contr_arm(pool4, 512, conv2d_kernel_shape)
    pool5 = MaxPooling2D(pool_size=(2, 2))(conv5)

    conv6 = bridge(pool5, 1024, conv2d_kernel_shape, dropout=dropout)
    
    conv6  = aspp(conv6,input_rows//32)

    convT7 = Conv2DTranspose(512, (2, 2), strides=(2, 2), padding='same', kernel_regularizer=regularizers.l2(l2_reg), kernel_initializer=initialization)(conv6)
    prevup7 = improve_ff_block4(input_tensor1=conv4, input_tensor2=conv3, input_tensor3=conv2, input_tensor4=conv1, pure_ff=conv5)
    up7 = concatenate([convT7, prevup7], axis=3)
    conv7 = conv_block_exp_path3(input_tensor=up7, filters=512, kernel_size=conv2d_kernel_shape)
    conv7 = add_block_exp_path(conv7, conv5, convT7)

    convT8 = Conv2DTranspose(256, (2, 2), strides=(2, 2), padding='same', kernel_regularizer=regularizers.l2(l2_reg), kernel_initializer=initialization)(conv7)
    prevup8 = improve_ff_block3(input_tensor1=conv3, input_tensor2=conv2, input_tensor3=conv1, pure_ff=conv4)
    up8 = concatenate([convT8, prevup8], axis=3)
    conv8 = conv_block_exp_path(input_tensor=up8, filters=256, kernel_size=conv2d_kernel_shape)
    conv8 = add_block_exp_path(input_tensor1=conv8, input_tensor2=conv4, input_tensor3=convT8)

    convT9 = Conv2DTranspose(128, (2, 2), strides=(2, 2), padding='same', kernel_regularizer=regularizers.l2(l2_reg), kernel_initializer=initialization)(conv8)
    prevup9 = improve_ff_block2(input_tensor1=conv2, input_tensor2=conv1, pure_ff=conv3)
    up9 = concatenate([convT9, prevup9], axis=3)
    conv9 = conv_block_exp_path(input_tensor=up9, filters=128, kernel_size=conv2d_kernel_shape)
    conv9 = add_block_exp_path(input_tensor1=conv9, input_tensor2=conv3, input_tensor3=convT9)

    convT10 = Conv2DTranspose(64, (2, 2), strides=(2, 2), padding='same', kernel_regularizer=regularizers.l2(l2_reg), kernel_initializer=initialization)(conv9)
    prevup10 = improve_ff_block1(input_tensor1=conv1, pure_ff=conv2)
    up10 = concatenate([convT10, prevup10], axis=3)
    conv10 = conv_block_exp_path(input_tensor=up10, filters=64, kernel_size=conv2d_kernel_shape)
    conv10 = add_block_exp_path(input_tensor1=conv10, input_tensor2=conv2, input_tensor3=convT10)

    convT11 = Conv2DTranspose(32, (2, 2), strides=(2, 2), padding='same', kernel_regularizer=regularizers.l2(l2_reg), kernel_initializer=initialization)(conv10)
    up11 = concatenate([convT11, conv1], axis=3)
    conv11 = conv_block_exp_path(input_tensor=up11, filters=32, kernel_size=conv2d_kernel_shape)
    conv11 = add_block_exp_path(input_tensor1=conv11, input_tensor2=conv1, input_tensor3=convT11)

    # -----------------------------------------------------------------------
    # add cropping from RS-Net
    clip_pixels = np.int32(overlap / 2)  #(overlap) / 2  # Only used for input in Cropping2D function on next line
    crop9 = Cropping2D(cropping=((clip_pixels, clip_pixels), (clip_pixels, clip_pixels)))(conv11)
    # -----------------------------------------------------------------------
    
    conv12 = Conv2D(num_of_classes, (1, 1), activation='softmax')(crop9) # sigmoid

    #conv12 = Conv2D(num_of_classes, (1, 1), activation='softmax')(conv11) # sigmoid

    return Model(inputs=[inputs], outputs=[conv12])
