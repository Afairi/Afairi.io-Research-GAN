from __future__ import print_function

import argparse

import pandas as pd
import torch

import numpy as np

from torch.autograd.variable import Variable

from Functions.original.methods.general.generator import Generator

from Functions.original.utils.categorical import load_variable_sizes_from_metadata
from Functions.original.utils.commandline import parse_int_list
from Functions.original.utils.cuda import to_cuda_if_available, to_cpu_if_available, load_without_cuda


def sample(generator, num_samples, num_features, batch_size=100, noise_size=128):
    generator = to_cuda_if_available(generator)

    generator.train(mode=False)

    samples = np.zeros((num_samples, num_features), dtype=np.float32)

    start = 0
    while start < num_samples:
        with torch.no_grad():
            noise = Variable(torch.FloatTensor(batch_size, noise_size).normal_())
            noise = to_cuda_if_available(noise)
            batch_samples = generator(noise, training=False)
        batch_samples = to_cpu_if_available(batch_samples)
        batch_samples = batch_samples.data.numpy()

        # do not go further than the desired number of samples
        end = min(start + batch_size, num_samples)
        # limit the samples taken from the batch based on what is missing
        samples[start:end, :] = batch_samples[:min(batch_size, end - start), :]

        # move to next batch
        start = end

    return samples


def generate_data():
    options_parser = argparse.ArgumentParser(description="Sample data with MedGAN.")

    # options_parser.add_argument("generator", type=str, help="Generator input file.")
    #
    # options_parser.add_argument("metadata", type=str,
    #                             help="Information about the categorical variables in json format.")
    #
    # options_parser.add_argument("num_samples", type=int, help="Number of output samples.")
    # options_parser.add_argument("num_features", type=int, help="Number of output features.")
    # options_parser.add_argument("data", type=str, help="Output data.")

    options_parser.add_argument(
        "--noise_size",
        type=int,
        default=128,
        help="Dimension of the generator input noise."
    )

    options_parser.add_argument(
        "--batch_size",
        type=int,
        default=100,
        help="Amount of samples per batch."
    )

    options_parser.add_argument(
        "--generator_hidden_sizes",
        type=str,
        default="128,128,128",
        help="Size of each hidden layer in the generator separated by commas (no spaces)."
    )

    options_parser.add_argument(
        "--generator_bn_decay",
        type=float,
        default=0.01,
        help="Generator batch normalization decay."
    )

    options = options_parser.parse_args()

    options.generator = 'data/generators/generator_2023_05_11_23.pt'
    options.metadata = 'config/metadata.json'
    options.num_samples = 500000
    options.num_features = 52
    options.data = 'data/gan_generated/sample_no_ei.pickle'

    generator = Generator(
        options.noise_size,
        load_variable_sizes_from_metadata(options.metadata),
        hidden_sizes=parse_int_list(options.generator_hidden_sizes),
        bn_decay=options.generator_bn_decay
    )

    load_without_cuda(generator, options.generator)

    data = sample(
        generator,
        options.num_samples,
        options.num_features,
        batch_size=options.batch_size,
        noise_size=options.noise_size
    )

    print('Saving sample')
    data = pd.DataFrame(data)
    return data