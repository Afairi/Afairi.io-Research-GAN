from __future__ import print_function

import torch.nn as nn
import config.config as cc


class Discriminator(nn.Module):

    def __init__(self, input_size, hidden_sizes, bn_decay, critic, leaky_param):
        super(Discriminator, self).__init__()

        hidden_activation = nn.LeakyReLU(leaky_param)

        previous_layer_size = input_size
        layers = []

        for layer_number, layer_size in enumerate(hidden_sizes):
            layers.append(nn.Linear(previous_layer_size, layer_size))
            if layer_number > 0 and bn_decay > 0:
                layers.append(nn.BatchNorm1d(layer_size, momentum=(1 - bn_decay)))
            layers.append(hidden_activation)
            previous_layer_size = layer_size

        layers.append(nn.Linear(previous_layer_size, 1))

        # the critic has a linear output
        if not critic:
            layers.append(nn.Sigmoid())

        self.model = nn.Sequential(*layers)

    def forward(self, inputs):
        return self.model(inputs).view(-1)

