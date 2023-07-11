# Abstract
Addressing data privacy concerns within the insurance sector is essential to harness the full potential of predictive modeling. This research endeavors to explore the generation of synthetic insurance datasets via the implementation of Generative Adversarial Networks (GANs), specifically using the Multi-Categorical Wasserstein GAN with Gradient Penalty (MC-WGAN-GP) variant. A key aspect of this study is to examine how the integration of expert knowledge during the GAN training process influences the quality of the data subsequently generated. To assess the outcomes, we train Extreme Gradient Boosting (XGBoost) models on both real and GAN-generated data, with and without the integration of expert knowledge. The predictive results of these models are then compared for analysis. The findings of this study indicate that the MC-WGAN-GP exhibits a substantial capacity to identify patterns between dependent and independent variables in the datasets. However, it does not achieve perfect replication of the training data yet. Furthermore, the assimilation of expert knowledge during the GAN training phase markedly improves the predictive performance of models trained on larger datasets, although this advantage does not extend to smaller dataset subsets. These results underscore the potential of GANs to address data privacy issues within the insurance industry, while demonstrating the substantial value of incorporating domain-specific expertise into synthetic data generation processes. Simultaneously, the findings suggest an imperative for further research efforts aimed at refining these methodologies and exploring their broad applicability across varied datasets and predictive modeling paradigms.

# Important info
Running main.py with the model version as optional argument should run the entire pipeline and save the respective model. the model then can be compared and analyzed using the evaluation.ipynb .

The config Folder contains all configurations.

## Example (when running from Pycharm)
runfile('~/Documents/Afairo Single Projects/thesis/main.py', args=['--modelversion', '110'], wdir='/Users/janjaniszewski/Documents/Afairo Single Projects/thesis')

## Example (when running from terminal)
python3 --modelversion 110 ~/Documents/Afairo Single Projects/thesis/main.py

# In case of questions, contact jan.j.janiszewski@gmail.com