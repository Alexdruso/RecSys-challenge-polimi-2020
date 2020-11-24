from src.Base.Evaluation.K_Fold_Evaluator import K_Fold_Evaluator_MAP
from src.Utils.load_ICM import load_ICM
from src.Utils.load_URM import load_URM
from src.Utils.ICM_preprocessing import *

URM_all = load_URM("../../in/data_train.csv")
ICM_all = load_ICM("../../in/data_ICM_title_abstract.csv")
from src.Data_manager.split_functions.split_train_validation_random_holdout import \
    split_train_in_two_percentage_global_sample

URMs_train = []
URMs_validation = []

for k in range(5):
    URM_train, URM_validation = split_train_in_two_percentage_global_sample(URM_all, train_percentage=0.80)
    URMs_train.append(URM_train)
    URMs_validation.append(URM_validation)

evaluator_validation = K_Fold_Evaluator_MAP(URMs_validation, cutoff_list=[10], verbose=False)

ICMs_combined = []
for URM in URMs_train:
    ICMs_combined.append(combine(ICM=ICM_all, URM=URM))

from src.GraphBased.RP3betaCBFRecommender import RP3betaCBFRecommender

from bayes_opt import BayesianOptimization

rp3betaCBF_recommenders = []

for index in range(len(URMs_train)):
    rp3betaCBF_recommenders.append(
        RP3betaCBFRecommender(
            URM_train=URMs_train[index],
            ICM_train=ICMs_combined[index],
            verbose=False
        )
    )

tuning_params = {
    "alpha": (0.1, 0.9),
    "beta": (0.1, 0.9),
    "topK": (10, 600)
}

results = []


def BO_func(
        alpha,
        beta,
        topK
):
    for recommender in rp3betaCBF_recommenders:
        recommender.fit(alpha=alpha, beta=beta, topK=int(topK), implicit=False)

    result = evaluator_validation.evaluateRecommender(rp3betaCBF_recommenders)
    results.append(result)
    return sum(result) / len(result)


optimizer = BayesianOptimization(
    f=BO_func,
    pbounds=tuning_params,
    verbose=5,
    random_state=5,
)

optimizer.maximize(
    init_points=20,
    n_iter=8,
)


import json

with open("logs/FeatureCombined" + rp3betaCBF_recommenders[0].RECOMMENDER_NAME + "_logs.json", 'w') as json_file:
    json.dump(optimizer.max, json_file)

from src.Base.Evaluation.k_fold_significance_test import compute_k_fold_significance

for recommender in rp3betaCBF_recommenders:
    recommender.fit(alpha=optimizer.max['params']['alpha'], beta=optimizer.max['params']['beta'],
                    topK=int(optimizer.max['params']['topK']), implicit=False)

result = evaluator_validation.evaluateRecommender(rp3betaCBF_recommenders)

compute_k_fold_significance(result, *results)
