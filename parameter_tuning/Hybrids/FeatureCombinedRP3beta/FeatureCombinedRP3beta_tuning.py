from src.Base.Evaluation.K_Fold_Evaluator import K_Fold_Evaluator_MAP
from src.Utils.load_ICM import load_ICM
from src.Utils.load_URM import load_URM

URM_all = load_URM("../../../in/data_train.csv")
ICM_all = load_ICM("../../../in/data_ICM_title_abstract.csv")
from src.Data_manager.split_functions.split_train_validation_random_holdout import \
    split_train_in_two_percentage_global_sample

URMs_train = []
URMs_validation = []

for k in range(5):
    URM_train, URM_validation = split_train_in_two_percentage_global_sample(URM_all, train_percentage=0.80)
    URMs_train.append(URM_train)
    URMs_validation.append(URM_validation)

evaluator_validation = K_Fold_Evaluator_MAP(URMs_validation, cutoff_list=[10], verbose=False)

from src.GraphBased.FeatureCombinedRP3betaRecommender import FeatureCombinedRP3betaRecommender

from bayes_opt import BayesianOptimization

featureCombinedRp3beta_recommenders = []

for index in range(len(URMs_train)):
    featureCombinedRp3beta_recommenders.append(
        FeatureCombinedRP3betaRecommender(
            URM_train=URMs_train[index],
            ICM_train=ICM_all,
            verbose=False
        )
    )

tuning_params = {
    "alpha": (0.1, 0.9),
    "beta": (0.1, 0.9),
    "gamma": (0.1,100),
    "topK": (10, 600)
}

results = []


def BO_func(
        alpha,
        beta,
        gamma,
        topK
):
    for recommender in featureCombinedRp3beta_recommenders:
        recommender.fit(alpha=alpha, beta=beta, gamma=gamma, topK=int(topK), implicit=False)

    result = evaluator_validation.evaluateRecommender(featureCombinedRp3beta_recommenders)
    results.append(result)
    return sum(result) / len(result)


optimizer = BayesianOptimization(
    f=BO_func,
    pbounds=tuning_params,
    verbose=5,
    random_state=5,
)

optimizer.maximize(
    init_points=50,
    n_iter=50,
)


import json

with open("logs/" + featureCombinedRp3beta_recommenders[0].RECOMMENDER_NAME + "_logs.json", 'w') as json_file:
    json.dump(optimizer.max, json_file)
