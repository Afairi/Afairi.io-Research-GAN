import pickle
import pandas as pd
from sklearn.datasets import fetch_openml

from Functions.dataprep import CommonPrep, SpecificPrep
import config.config as cc
from Functions.trainer import run_training


def main():
    try:
        df = pd.read_pickle(cc.original_data)
    except FileNotFoundError:
        df = fetch_openml(data_id=41214, as_frame=True).data
        df.to_pickle(cc.original_data)

    # GAN without expert input
    common = CommonPrep()
    train, val, test = common.fit_transform(df)

    # Saving datasets
    train.to_pickle(cc.train_common)
    val.to_pickle(cc.val_common)
    test.to_pickle(cc.test_common)

    specific_dataprepper = SpecificPrep(gan_cats=cc.metadata['cats_vars_gan'], xgb_cats=cc.metadata['cats_vars_xgb'])
    specific_dataprepper = specific_dataprepper.fit(train)


    with open(cc.params['output_scaler'], 'wb') as f:
        pickle.dump(specific_dataprepper, f)

    # Train for beginning only
    train_beginning = train.copy(deep=True).loc[train['ClaimNb'] > 0]
    train_beginning2 = train.copy(deep=True).loc[train['ClaimNb'] == 0].head(len(train_beginning))

    # Transform all necessary data
    train_beginning = specific_dataprepper.transform(pd.concat([train_beginning, train_beginning2]))
    train = specific_dataprepper.transform(train)
    test = specific_dataprepper.transform(test)
    val = specific_dataprepper.transform(val)

    # Saving datasets again
    train.to_pickle(cc.train_specific)
    val.to_pickle(cc.val_specific)
    test.to_pickle(cc.test_specific)

    # Starting training run
    run_training(train, val, specific_dataprepper, train_beginning)

if __name__ == '__main__':
    main()