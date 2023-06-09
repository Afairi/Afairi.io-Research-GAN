import sys

import torch
from tqdm import tqdm
from Functions.rcamino_functions import utils
from Functions.rcamino_functions.methods.general.generator import Generator

modelkey = 3
sys.argv = [f"--modelversion {modelkey}"]

import pandas as pd
from sklearn import utils

import config.config as cc
from Functions import metrics
import xgboost as xgb
from Functions.sampler import sample
import numpy as np
import scipy.stats as stats

def run_xgboost(train, test, version=1):
    if version == 1:
        xgb_model = xgb.XGBRegressor(objective='count:poisson',
                                     n_estimators=1200,
                                     max_depth=7,
                                     eta=0.025,
                                     colsample_bytree=0.8,
                                     subsample=0.9,
                                     min_child_weight=10,
                                     tree_method="hist",
                                     random_state=1)
    elif version == 2:
        xgb_model = xgb.XGBRegressor(objective='count:poisson',
                                     n_estimators=500,
                                     max_depth=5,
                                     eta=0.02,
                                     colsample_bytree=0.8,
                                     subsample=0.9,
                                     min_child_weight=10,
                                     tree_method="hist",
                                     random_state=1)

    train = train[test.columns]
    xgb_model.fit(train.drop(labels='ClaimNb', axis=1), train['ClaimNb'])

    preds1 = xgb_model.predict(test.drop(labels='ClaimNb', axis=1))

    return preds1

def summaries(x, rounding = 3):
    return np.round(np.mean(x), rounding), \
           np.round(np.std(x), rounding),\
           np.round(stats.t.interval(alpha=0.95, df=len(x)-1, loc=np.mean(x), scale=stats.sem(x))[0], rounding),\
           np.round(stats.t.interval(alpha=0.95, df=len(x) - 1, loc=np.mean(x), scale=stats.sem(x))[1],rounding)


def get_model(modelversion, datasets, ganruns=pd.read_csv('./config/ganruns.csv', sep=';'), bestmodel=True):
    key = modelversion
    value = ganruns.loc[ganruns['sim_num'] == int(key)].iloc[0].to_dict()

    if value['has_ei']:
        transformer = datasets['ei']['transformer']
        metadata = cc.metadata_ei
    else:
        transformer = datasets['noei']['transformer']
        metadata = cc.metadata_noei

    value['losses'] = pd.read_csv(value['output_loss'])

    model_best = Generator(
        noise_size=int(value['z_size']),
        output_size=metadata['variable_sizes'],
        hidden_sizes=[int(x) for x in value['generator_hidden_sizes'].split(',')],
        bn_decay=value['gen_bn_decay']
    )

    weightspath = f"{value['output_generator']}"

    if bestmodel:
        weightspath += "_inbetween"

    weights = torch.load(weightspath, map_location=lambda storage, loc: storage)
    model_best.load_state_dict(weights)
    value['generator'] = model_best
    value['transformer'] = pd.read_pickle(value['output_scaler'])
    return value


def gan_bootstraped(value, testset, datasets, bootstraps, postprocess=False, version=1, seed=1):
    if value['has_ei']:
        metadata = cc.metadata_ei
        transformer = datasets['ei']['transformer']
    else:
        metadata = cc.metadata_noei
        transformer = datasets['noei']['transformer']

    devs = []

    for i in tqdm(range(0, bootstraps)):  # WARNING: Seed = i in this case (not as usual = 1)
        torch.manual_seed(seed)
        seed += 1
        testset = utils.resample(testset.copy(deep=True), replace=True, n_samples=len(testset), random_state=i,
                              stratify=None)
        preds1 = gan_xgb(metadata, postprocess, testset, transformer, value, version)
        dev1 = metrics.poisson_deviance(preds1, testset['ClaimNb'])
        devs += [dev1]

    return devs


def gan_xgb(metadata, postprocess, testset, transformer, value, version=1):
    train = sample(
        generator=value['generator'],
        num_features=metadata['num_features'],
        num_samples=100000,
        batch_size=100000,
        noise_size=int(value['z_size'])
    )
    train = pd.DataFrame(train)
    try:
        train = value['transformer'].inverse_transform(train)
    except AttributeError:
        train = transformer.inverse_transform(train)
    train[['VehPower', 'VehAge', 'DrivAge', 'BonusMalus']] = train[
        ['VehPower', 'VehAge', 'DrivAge', 'BonusMalus']].astype(int)
    # Data postprocessing
    if postprocess:
        train['ClaimNb'] = train['ClaimNb'].apply(lambda x: 4 if x > 4 else x)
        train['VehAge'] = train['VehAge'].apply(lambda x: 20 if x > 20 else x)
        train['DrivAge'] = train['DrivAge'].apply(lambda x: 90 if x > 90 else x)
        train['BonusMalus'] = train['BonusMalus'].apply(lambda x: 150 if x > 150 else int(x))
        train['VehPower'] = train['VehPower'].apply(lambda x: 9 if x > 9 else x)
    trainset = train.drop(train.filter(like="EI_", axis=1).columns, axis=1)

    # Fixing non-existent columns in the model
    missed_cols = [col for col in testset.columns if col not in train.columns]
    trainset[missed_cols] = 0
    preds1 = run_xgboost(trainset, testset, version=version)

    return preds1


def xgb_bootstraped(trainset, testset, bootstraps, samplesize, version=1):
    devs = []

    for i in tqdm(range(0, bootstraps)):  # WARNING: Seed = i in this case (not as usual = 1)
        if samplesize > len(trainset):
            samplesize = len(trainset)
        train = utils.resample(trainset, replace=True, n_samples=samplesize, random_state=i, stratify=None)
        test = utils.resample(testset, replace=True, n_samples=len(testset), random_state=i, stratify=None)
        preds1 = run_xgboost(train, test, version=version)

        dev1 = metrics.poisson_deviance(preds1, testset['ClaimNb'])

        devs += [dev1]

    return devs
