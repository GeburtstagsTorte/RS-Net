#!/usr/bin/env python
from typing import Any
import tensorflow as tf
import tensorflow.keras as keras
import os
import inspect
import copy

# Create a Namespace class for hyperparameters
@keras.saving.register_keras_serializable() # is this even needed if no keras funcs are called here?
class HParams:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def update(self, **kwargs):
        self.__dict__.update(kwargs)

    def get_config(self):
        return {'__dict__', self.__dict__} # (self.__dict__)

    def as_string(self, delimiter=";", eq="=", stop_at=-1, skip_keys_list=[]) -> str:
        self_string = ""
        for key, value in self.__dict__.items():
            if key not in skip_keys_list:
                self_string += key + eq + str(value) + delimiter
        return self_string[:stop_at] # leaving out last delimiter

    def parse(self, params, delimiter=";"):
        param_list = params.strip("\"\'[] \n").split(delimiter)
        for param in param_list:
            key, value = param.split("=")
            if str(key) == "cls":  # parse cls strings
                try:
                    value = value.replace('\"', '').replace('\'', '').replace(' ', '')
                    value = value.strip('][')
                    try:
                        value = [int(i) for i in  value.split(',')] # for sparse categorical crossentropy
                    except ValueError:
                        value = [str(i) for i in  value.split(',')] # striping off <SPACE>, [, ], ', "
                    self.__dict__[key] = value
                    continue
                except ValueError as e:
                        print("value error: ", e)
                        pass
            try:
                value = int(value)
            except ValueError:
                try:
                    value = float(value)
                except ValueError:
                    #assuming input is supposed to be list format
                    # make list of value, only account for list of ints
                    try:
                        value = [int(i) for i in value.strip('][').split(',')]
                        self.__dict__[key] = value
                        continue
                    except ValueError:
                        pass
    
            if value == 'True':
                value = True
            elif value == 'False':
                value = False
            elif value == 'None':
                value = None
            self.__dict__[key] = value
    
    def __getitem__(self, item):
         # item is key
         return self.__dict__.get(item)
    
    def values(self):
        # naming is a bit off
        return self.__dict__
        # return self._hyperparameters.values()

    def keys(self):
        return self.__dict__.keys()
    


@keras.saving.register_keras_serializable()
def get_params(model, satellite):
    # TODO: convert all this to objects of HParam
    if model == 'U-net' and satellite == 'Sentinel-2':
        hparams = {
            'learning_rate': 0.001,
            'decay': 1e-1,
            'dropout': 0.5,
            'L2reg': 1e-2,
            'threshold': 0.5,
            'patch_size': 320,
            'overlap': 40,
            'batch_size': 32,
            'steps_per_epoch': 40,
            'epochs': 10,
            'norm_threshold': 12000,
            'initial_model': 'sen2cor',
            'cls': 'cloud',
            'collapse_cls': True,
            'bands': [2, 3, 4, 8],
            'tile_size': 10980,
            'project_path': '/home/mxh/RS-Net/',
            'satellite': 'Sentinel-2'
        }
        
        return HParams(**hparams)
    
    elif model == 'U-net' and satellite == 'Landsat8':
        """old hparams
        elif model == 'U-net' and satellite == 'Landsat8':
        hparams = {
            'modelNick': 'Unet-L8',
            'modelID': '180609113138',
            'num_gpus': 1,
            'optimizer': 'Adam',
            'loss_func': 'binary_crossentropy',
            'activation_func': 'elu',
            'initialization': 'glorot_uniform',
            'use_batch_norm': True,
            'dropout_on_last_layer_only': True,
            'early_stopping': False,
            'reduce_lr': False,
            'save_best_only': False,
            'use_ensemble_learning': False,
            'ensemble_method': 'Bagging',
            'learning_rate': 1e-4,
            'dropout': 0.2,
            'L1reg': 0.0,
            'L2reg': 1e-4,
            'L1L2reg': 0.0,
            'decay': 0.0,
            'batch_norm_momentum': 0.7,
            'threshold': 0.5,
            'patch_size': 256,
            'overlap': 40,
            'overlap_train_set': 40, # 0, trying 40 for train dataset (npy) generation
            'batch_size': 40,
            'steps_per_epoch': None,
            'epochs': 5,
            'norm_method': 'enhance_contrast',
            'norm_threshold': 65535,
            'cls': ['cloud', 'thin'],
            'collapse_cls': False,
            'affine_transformation': True,
            'brightness_augmentation': False,
            'bands': [1, 2, 3, 4, 5, 6, 7],
            'project_path': "/home/mxh/RS-Net/",
            'toa_path': "data/processed/Biome_TOA/",
            'data_path': 'data/raw/Biome_dataset/',
            'satellite': 'Landsat8',
            'train_dataset': 'Biome_fmask',
            'test_dataset': 'Biome_gt',
            'split_dataset': True,
            'test_tiles': __data_split__('Biome_gt')
        }
        return HParams(**hparams)"""
        hparams = HParams(
            modelNick= 'Unet',
            plateau_patience = 12,
            early_patience = 100,
        )
        hparams_dict = {
            'modelID': '_',
            'random':False,
            'shuffle':False,
            'num_gpus': 1,
            'optimizer': 'Adam',
            'loss_func': 'binary_crossentropy',
            'activation_func': 'elu',
            'random': True,
            'last_layer_activation_func': 'softmax',
            'initialization': 'glorot_uniform',
            'use_batch_norm': True,
            'dropout_on_last_layer_only': True,
            'early_stopping': False,
            #'use_cyclical_lr_scheduler':False,
            #'use_factorial_cyclical_lr_scheduler':False,
            #'use_round_cyclical_lr_scheduler':False,
            'reduce_lr': False,
            'replace_fill_values': True,
            'dataset_fill_cls':None, # if set to any number, fill values will be replaced by it and it will be ignored by loss calculation. 
                # If set to None, fill values will be replaced by most probable cls and not ignored by sparse categorical crossentropy.
            'patience': 12,
            'save_best_only': False,
            'use_ensemble_learning': False,
            'ensemble_method': 'Bagging',
            'learning_rate': 1e-4,
            'dropout': 0.2,
            'L1reg': 0.0,
            'L2reg': 1e-4,
            'L1L2reg': 0.0,
            'decay': 0.0,
            'batch_norm_momentum': 0.7,
            'threshold': 0.5,
            'patch_size': 256,
            'overlap': 40,
            'overlap_train_set': 0,
            'batch_size': 40,
            'steps_per_epoch': None,
            'epochs': 5,
            'norm_method': None, # 'enhance_contrast'
            'norm_threshold': 65535,
            'cls': ['cloud', 'thin'],
            'collapse_cls': False,
            'affine_transformation': True,
            'brightness_augmentation': False,
            'bands': [1, 2, 3, 4, 5, 6, 7],
            'project_path': "/home/mxh/RS-Net/",
            'toa_path': "data/processed/Biome_TOA/",
            'data_path': 'data/raw/Biome_dataset/',
            'satellite': 'Landsat8',
            'usecase': 'MOD09GA',
            'train_dataset': 'Biome_gt',  # train on ground truth by default # Choose Biome_gt, Biome_fmask, SPARCS_gt, or SPARCS_fmask
            'test_dataset': 'Biome_gt', # Biome_gt # Choose Biome_gt, Biome_fmask, SPARCS_gt, or SPARCS_fmask
            'split_dataset': True,
            'test_tiles': __data_split__('Biome_gt') # Biome_gt # Chose test_dataset value
        }
        hparams.update(**hparams_dict)
        return hparams
    elif model == 'U-net-v2' and (satellite == 'Landsat8' or satellite =='MODIS'):
        hparams = HParams(
            modelNick= 'Unet-v2-MOD09GA',
            plateau_patience = 2,
            early_patience = 3,
        )
        hparams_dict = {
            'modelID': '_',
            'random':False,
            'shuffle':False,
            'num_gpus': 1,
            'optimizer': 'Adam',
            'loss_func': 'sparse_categorical_crossentropy',
            'activation_func': 'elu',
            'random': True,
            'last_layer_activation_func': 'softmax',
            'initialization': 'glorot_uniform',
            'use_batch_norm': True,
            'dropout_on_last_layer_only': True,
            'early_stopping': False,
            #'use_cyclical_lr_scheduler':False,
            #'use_factorial_cyclical_lr_scheduler':False,
            #'use_round_cyclical_lr_scheduler':False,
            'reduce_lr': False,
            'replace_fill_values': True,
            'dataset_fill_cls':None, # if set to any number, fill values will be replaced by it and it will be ignored by loss calculation. 
                # If set to None, fill values will be replaced by most probable cls and not ignored by sparse categorical crossentropy.
            'patience': 12,
            'save_best_only': False,
            'use_ensemble_learning': False,
            'ensemble_method': 'Bagging',
            'learning_rate': 1e-4,
            'dropout': 0.2,
            'L1reg': 0.0,
            'L2reg': 1e-4,
            'L1L2reg': 0.0,
            'decay': 0.0,
            'batch_norm_momentum': 0.7,
            'threshold': 0.5,
            'patch_size': 256,
            'overlap': 40,
            'overlap_train_set': 0,
            'batch_size': 40,
            'steps_per_epoch': None,
            'epochs': 5,
            'norm_method': None, # 'enhance_contrast'
            'norm_threshold': 65535,
            'cls': ['cloud', 'thin'],
            'collapse_cls': False,
            'affine_transformation': True,
            'brightness_augmentation': False,
            'bands': [1, 2, 3, 4, 5, 6, 7],
            'project_path': "/home/mxh/RS-Net/",
            'toa_path': "data/processed/Biome_TOA/",
            'data_path': 'data/raw/Biome_dataset/',
            'satellite': 'Landsat8',
            'usecase': 'MOD09GA',
            'train_dataset': 'Biome_gt',  # train on ground truth by default # Choose Biome_gt, Biome_fmask, SPARCS_gt, or SPARCS_fmask
            'test_dataset': 'Biome_gt', # Biome_gt # Choose Biome_gt, Biome_fmask, SPARCS_gt, or SPARCS_fmask
            'split_dataset': True,
            'test_tiles': __data_split__('Biome_gt') # Biome_gt # Chose test_dataset value
        }
        hparams.update(**hparams_dict)
        return hparams
    elif model =="U-net-v3":
        hparams = HParams(
            modelNick= 'Unet-v3',
            plateau_patience = 2,
            early_patience = 3,
        )
        hparams_dict = {
            'modelID': '_',
            'random':False,
            'shuffle':False,
            'num_gpus': 1,
            'optimizer': 'AdamW',
            'loss_func': 'sparse_categorical_crossentropy',
            'activation_func': 'relu',
            'random': True,
            'last_layer_activation_func': 'softmax',
            'initialization': 'he_normal',
            'use_batch_norm': True,
            'dropout_on_last_layer_only': True,
            'early_stopping': False,
            #'use_cyclical_lr_scheduler':False,
            #'use_factorial_cyclical_lr_scheduler':False,
            #'use_round_cyclical_lr_scheduler':False,
            "lr_scheduler":False,
            'reduce_lr': False,
            'replace_fill_values': True,
            'dataset_fill_cls':None, # if set to any number, fill values will be replaced by it and it will be ignored by loss calculation. 
                # If set to None, fill values will be replaced by most probable cls and not ignored by sparse categorical crossentropy.
            'patience': 12,
            'save_best_only': False,
            'use_ensemble_learning': False,
            'ensemble_method': 'Bagging',
            'learning_rate': 1e-4,
            'dropout': 0.2,
            'L1reg': 0.0,
            'L2reg': 1e-4,
            'L1L2reg': 0.0,
            'decay': 0.0,
            'batch_norm_momentum': 0.7,
            'threshold': 0.5,
            'patch_size': 256,
            'overlap': 40,
            'overlap_train_set': 0,
            'batch_size': 40,
            'steps_per_epoch': None,
            'epochs': 5,
            'norm_method': None, # 'enhance_contrast'
            'norm_threshold': 65535,
            'cls': ['cloud', 'thin'],
            'collapse_cls': False,
            'affine_transformation': True,
            'brightness_augmentation': False,
            'bands': [1, 2, 3, 4, 5, 6, 7],
            'project_path': "/home/mxh/RS-Net/",
            'toa_path': "data/processed/Biome_TOA/",
            'data_path': 'data/raw/Biome_dataset/',
            'satellite': 'Landsat8',
            'usecase': 'MOD09GA',
            'train_dataset': 'Biome_gt',  # train on ground truth by default # Choose Biome_gt, Biome_fmask, SPARCS_gt, or SPARCS_fmask
            'test_dataset': 'Biome_gt', # Biome_gt # Choose Biome_gt, Biome_fmask, SPARCS_gt, or SPARCS_fmask
            'split_dataset': True,
            'which_scheduler': "unknown",
            'test_tiles': __data_split__('Biome_gt') # Biome_gt # Chose test_dataset value
        }
        hparams.update(**hparams_dict)
        return hparams
    elif model =="U-net-v4-CXN":
        hparams = HParams(
            modelNick= 'Unet-v4-CXN',
            plateau_patience = 2,
            early_patience = 3,
        )
        hparams_dict = {
            'modelID': '_',
            'random':False,
            'shuffle':False,
            'num_gpus': 1,
            'optimizer': 'AdamW',
            'loss_func': 'sparse_categorical_crossentropy',
            'activation_func': 'relu',
            'random': True,
            'last_layer_activation_func': 'softmax',
            'initialization': 'he_normal',
            'use_batch_norm': True,
            'dropout_on_last_layer_only': True,
            'early_stopping': False,
            #'use_cyclical_lr_scheduler':False,
            #'use_factorial_cyclical_lr_scheduler':False,
            #'use_round_cyclical_lr_scheduler':False,
            "lr_scheduler":True,
            'reduce_lr': False,
            'learning_rate':1e-5,
            'base_lr':1e-7,
            'cyclical_lr_step_size':2*6600, # number iterations per epoch = number batches in epoch ? # for training on full dataset, double?
            'cyclical_lr_mode':"exp_range", 
            'cyclical_lr_gamma': 0.99994,
            'replace_fill_values': True,
            'dataset_fill_cls':None, # if set to any number, fill values will be replaced by it and it will be ignored by loss calculation. 
                # If set to None, fill values will be replaced by most probable cls and not ignored by sparse categorical crossentropy.
            'patience': 12,
            'save_best_only': False,
            'use_ensemble_learning': False,
            'ensemble_method': 'Bagging',
            'conv_kernel':7,
            'depth_kernel':7,
            'dropout': 0.15,
            'L1reg': 0.0,
            'L2reg': 1e-4,
            'L1L2reg': 0.0,
            'decay': 0.99,
            'batch_norm_momentum': 0.7,
            'threshold': 0.5,
            'patch_size': 256,
            'overlap': 40,
            'overlap_train_set': 0,
            'batch_size': 40,
            'steps_per_epoch': None,
            'epochs': 5,
            'norm_method': None, # 'enhance_contrast'
            'norm_threshold': 65535,
            'cls': ['shadow', 'clear', 'thin', 'cloud'],
            'collapse_cls': False,
            'affine_transformation': True,
            'brightness_augmentation': False,
            'bands': [1, 2, 3, 4, 5, 6, 7],
            'project_path': "/home/mxh/RS-Net/",
            'toa_path': "data/processed/Biome_TOA/",
            'data_path': 'data/raw/Biome_dataset/',
            'satellite': 'Landsat8',
            'usecase': 'MOD09GA',
            'train_dataset': 'Biome_gt',  # train on ground truth by default # Choose Biome_gt, Biome_fmask, SPARCS_gt, or SPARCS_fmask
            'test_dataset': 'Biome_gt', # Biome_gt # Choose Biome_gt, Biome_fmask, SPARCS_gt, or SPARCS_fmask
            'split_dataset': True,
            'which_scheduler': "unknown",
            'test_tiles': __data_split__('Biome_gt') # Biome_gt # Chose test_dataset value
        }
        hparams.update(**hparams_dict)
        return hparams

def __data_split__(dataset):
    if 'Biome' in dataset:
        # For each biome, the top two tiles are 'Clear', then two 'MidClouds', and then two 'Cloudy'
        # NOTE: IT IS IMPORTANT TO KEEP THE ORDER THE SAME, AS IT IS USED WHEN EVALUATING THE 'MIDCLOUDS',
        #       'CLOUDY', AND 'CLEAR' GROUPS
        train_tiles = ['LC80420082013220LGN00',  # Barren
                       'LC81640502013179LGN01',
                       'LC81330312013202LGN00',
                       'LC81570452014213LGN00',
                       'LC81360302014162LGN00',
                       'LC81550082014263LGN00',
                       'LC80070662014234LGN00',  # Forest
                       'LC81310182013108LGN01',
                       'LC80160502014041LGN00',
                       'LC82290572014141LGN00',
                       'LC81170272014189LGN00',
                       'LC81800662014230LGN00',
                       'LC81220312014208LGN00',  # Grass/Crops
                       'LC81490432014141LGN00',
                       'LC80290372013257LGN00',
                       'LC81750512013208LGN00',
                       'LC81220422014096LGN00',
                       'LC81510262014139LGN00',
                       'LC80010732013109LGN00',  # Shrubland
                       'LC80750172013163LGN00',
                       'LC80350192014190LGN00',
                       'LC80760182013170LGN00',
                       'LC81020802014100LGN00',
                       'LC81600462013215LGN00',
                       'LC80841202014309LGN00',  # Snow/Ice
                       'LC82271192014287LGN00',
                       'LC80060102014147LGN00',
                       'LC82171112014297LGN00',
                       'LC80250022014232LGN00',
                       'LC82320072014226LGN00',
                       'LC80410372013357LGN00',  # Urban
                       'LC81770262013254LGN00',
                       'LC80460282014171LGN00',
                       'LC81620432014072LGN00',
                       'LC80170312013157LGN00',
                       'LC81920192013103LGN01',
                       'LC80180082014215LGN00',  # Water
                       'LC81130632014241LGN00',
                       'LC80430122014214LGN00',
                       'LC82150712013152LGN00',
                       'LC80120552013202LGN00',
                       'LC81240462014238LGN00',
                       'LC80340192014167LGN00',  # Wetlands
                       'LC81030162014107LGN00',
                       'LC80310202013223LGN00',
                       'LC81080182014238LGN00',
                       'LC81080162013171LGN00',
                       'LC81020152014036LGN00']

        test_tiles = ['LC80530022014156LGN00',  # Barren
                      'LC81750432013144LGN00',
                      'LC81390292014135LGN00',
                      'LC81990402014267LGN00',
                      'LC80500092014231LGN00',
                      'LC81930452013126LGN01',
                      'LC80200462014005LGN00',  # Forest
                      'LC81750622013304LGN00',
                      'LC80500172014247LGN00',
                      'LC81330182013186LGN00',
                      'LC81720192013331LGN00',
                      'LC82310592014139LGN00',
                      'LC81820302014180LGN00',  # Grass/Crops
                      'LC82020522013141LGN01',
                      'LC80980712014024LGN00',
                      'LC81320352013243LGN00',
                      'LC80290292014132LGN00',
                      'LC81440462014250LGN00',
                      'LC80320382013278LGN00',  # Shrubland
                      'LC80980762014216LGN00',
                      'LC80630152013207LGN00',
                      'LC81590362014051LGN00',
                      'LC80670172014206LGN00',
                      'LC81490122013218LGN00',
                      'LC80441162013330LGN00',  # Snow/Ice
                      'LC81001082014022LGN00',
                      'LC80211222013361LGN00',
                      'LC81321192014054LGN00',
                      'LC80010112014080LGN00',
                      'LC82001192013335LGN00',
                      'LC80640452014041LGN00',  # Urban
                      'LC81660432014020LGN00',
                      'LC80150312014226LGN00',
                      'LC81970242013218LGN00',
                      'LC81180382014244LGN00',
                      'LC81940222013245LGN00',
                      'LC80210072014236LGN00',  # Water
                      'LC81910182013240LGN00',
                      'LC80650182013237LGN00',
                      'LC81620582014104LGN00',
                      'LC81040622014066LGN00',
                      'LC81660032014196LGN00',
                      'LC81460162014168LGN00',  # Wetlands
                      'LC81580172013201LGN00',
                      'LC81010142014189LGN00',
                      'LC81750732014035LGN00',
                      'LC81070152013260LGN00',
                      'LC81500152013225LGN00']

        #test_tiles = ['LC82290572014141LGN00',
        #              'LC81080162013171LGN00']
        return [train_tiles, test_tiles]
    elif "SPARCS" in dataset:
        # TODO: split SPARCS by hand
        train_tiles = []
        test_tiles = []

        return [train_tiles, test_tiles]
