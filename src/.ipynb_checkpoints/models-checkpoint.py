import timm

import torch
import torch.nn as nn
from torch.nn import functional as F

import math

import config
import utils

def get_model(pretrained=True, net_out_features=1):
    if config.NET == 'Net_ArcFace':
        net = Net_ArcFace(pretrained=pretrained, net_out_features=net_out_features)
    elif config.NET == 'Net_Simple':
        net = Net_Simple(pretrained=pretrained, net_out_features=net_out_features)
    elif config.NET == 'Net_SimpleBN':
        net = Net_SimpleBN(pretrained=pretrained, net_out_features=net_out_features)
    return net

class Backbone(nn.Module):
    def __init__(self, pretrained=True):
        super().__init__()
        self.model = timm.create_model(config.MODEL_NAME,
                                            pretrained=pretrained, in_chans=config.CHANNELS)

        if config.MODEL_NAME in ['resnet18', 'resnet18d']:
            self.in_features = self.model.fc.in_features
        else:
            self.in_features = self.model.classifier.out_features
        
        print(f'\n Using {config.MODEL_NAME} as backbone, backbone head: {self.model.fc}\n')

    def forward(self, x):
        logits = self.model(x)
        return logits


class ArcMarginProduct(nn.Module):
    def __init__(self, in_features, out_features):
        super().__init__()
        self.weight = nn.Parameter(torch.FloatTensor(out_features, in_features))
        self.reset_parameters()

    def reset_parameters(self):
        nn.init.xavier_uniform(self.weight)

    def forward(self, features):
        '''
        logits = cosine, as:
        W = Weight at last layer
        x = last layer feature
        Z = logits
        logits = Z = W*x = |W||x|cos(theta)
        theta = angle between W and x
        normalised weights W and normalised features x, |W|=1 |x|=1
        thus logits become cos(theta)
        '''
        logits = F.linear(F.normalize(features), F.normalize(self.weight))
        return logits

class Net_ArcFace(nn.Module):
    def __init__(self, pretrained=True, net_out_features=1):
        super().__init__()
        self.net_out_features = net_out_features
        self.backbone = Backbone(pretrained=pretrained)
        self.net_head = nn.Linear(self.backbone.model.fc.out_features, self.net_out_features)
        
        
        
        self.linear_layer = nn.Linear(self.backbone.model.fc.out_features, 4096)
        self.batch_norm_layer = nn.BatchNorm1d(4096)
        self.prelu = nn.PReLU()
        self.arcface_logits = ArcMarginProduct(4096, self.net_out_features+1)

    def forward(self, x):
        x = self.backbone(x)
#         x = self.net_head(x)
        x = self.linear_layer(x)
        x = self.batch_norm_layer(x)
        x = self.prelu(x)
        x = self.arcface_logits(x)
        
        if config.DROPOUT:
            for i, dropout in enumerate(self.dropouts):
                if i == 0:
                    logits = self.output_layer(dropout(x))
                else:
                    logits += self.output_layer(dropout(x))
            logits /= len(self.dropouts)
            return logits
        else:
            return x

class Net_SimpleBN(nn.Module):
    def __init__(self, pretrained=True, net_out_features=1):
        super().__init__()
        self.net_out_features = net_out_features
        self.backbone = Backbone(pretrained=pretrained)
        self.linear_layer = nn.Linear(self.backbone.model.fc.out_features, 4096)
        self.batch_norm_layer = nn.BatchNorm1d(4096)
        self.prelu = nn.PReLU()
        self.net_head = nn.Linear(4096, self.net_out_features)
        
    def forward(self, x):
        x = self.backbone(x)
        x = self.linear_layer(x)
        x = self.batch_norm_layer(x)
        x = self.prelu(x)
        x = self.net_head(x)
        
        if config.DROPOUT:
            for i, dropout in enumerate(self.dropouts):
                if i == 0:
                    logits = self.output_layer(dropout(x))
                else:
                    logits += self.output_layer(dropout(x))
            logits /= len(self.dropouts)
            return logits
        else:
            return x
        
class Net_Simple(nn.Module):
    def __init__(self, pretrained=True, net_out_features=1):
        super().__init__()
        self.net_out_features = net_out_features
        self.backbone = Backbone(pretrained=pretrained)
        self.batch_norm_layer = nn.BatchNorm1d(self.backbone.model.fc.out_features)
        self.net_head = nn.Linear(self.backbone.model.fc.out_features, self.net_out_features)

    def forward(self, x):
        x = self.backbone(x)
#         x = self.batch_norm_layer(x)
        x = self.net_head(x)
        
        if config.DROPOUT:
            for i, dropout in enumerate(self.dropouts):
                if i == 0:
                    logits = self.output_layer(dropout(x))
                else:
                    logits += self.output_layer(dropout(x))
            logits /= len(self.dropouts)
            return logits
        else:
            return x
# class Model(nn.Module):
#     def __init__(self, pretrained=True ):
#         super().__init__()
#         self.base_model = timm.create_model(config.MODEL_NAME,
#                                             pretrained=pretrained, in_chans=config.CHANNELS)
#         if config.MODEL_NAME in ['resnet18', 'resnet18d']:
#             self.in_features = self.base_model.fc.in_features
#         else:
#             self.in_features = self.base_model.classifier.out_features
            
            
#         if config.DROPOUT:
#             self.base_model_out_features = 1024*10
#             self.base_model.fc = nn.Linear(self.in_features, self.base_model_out_features)
#             self.output_layer = nn.Linear(self.base_model_out_features, config.TARGET_SIZE)
#         else:
#             self.base_model_out_features = config.TARGET_SIZE
#             self.base_model.fc = nn.Linear(self.in_features, self.base_model_out_features)
#             self.output_layer = self.base_model.fc
        
        
#         self.dropouts = nn.ModuleList([
#             nn.Dropout(0.7) for _ in range(16)
#         ])
# #         print(self.model)
#         print(f'\nUsing {config.MODEL_NAME}, model output layer: {self.output_layer} with DROPOUT {config.DROPOUT}\n')

#     def forward(self, x):
#         base_model_logits = self.base_model(x)
#         if config.DROPOUT:
#             for i, dropout in enumerate(self.dropouts):
#                 if i == 0:
#                     logits = self.output_layer(dropout(base_model_out))
#                 else:
#                     logits += self.output_layer(dropout(base_model_out))
#             logits /= len(self.dropouts)
#             return logits
#         else:
#             return base_model_logits
        