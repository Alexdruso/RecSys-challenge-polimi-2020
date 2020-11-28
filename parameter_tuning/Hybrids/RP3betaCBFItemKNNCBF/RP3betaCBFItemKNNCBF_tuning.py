from src.Base.Evaluation.K_Fold_Evaluator import K_Fold_Evaluator_MAP
from src.Utils.ICM_preprocessing import *
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

from src.Hybrid.SimilarityMergedHybridRecommender import SimilarityMergedHybridRecommender
from src.KNN.ItemKNNCBFRecommender import ItemKNNCBFRecommender
from src.GraphBased.RP3betaCBFRecommender import RP3betaCBFRecommender

from bayes_opt import BayesianOptimization

ItemCBF_recommenders = []
rp3betaCBF_recommenders = []

for index in range(len(URMs_train)):
    ItemCBF_recommenders.append(
        ItemKNNCBFRecommender(
            URM_train=URMs_train[index],
            ICM_train=ICM_all,
            verbose=False
        )
    )

    rp3betaCBF_recommenders.append(
        RP3betaCBFRecommender(
            URM_train=URMs_train[index],
            ICM_train=ICM_all,
            verbose=False
        )
    )

tuning_params = {
    "knnTopK": (100, 400),
    "knnShrink": (10, 100),
    "rp3betaTopK": (10, 100),
    "rp3betaAlpha": (0.2, 0.3),
    "rp3betaBeta": (0.3, 0.45),
    "hybridTopK": (10, 200),
    "hybridAlpha": (0.1, 0.9)
}

results = []


def BO_func(
        knnTopK,
        knnShrink,
        rp3betaTopK,
        rp3betaAlpha,
        rp3betaBeta,
        hybridTopK,
        hybridAlpha
):
    recommenders = []

    for index in range(len(URMs_train)):
        ItemCBF_recommenders[index].fit(
            topK=int(knnTopK),
            shrink=knnShrink,
            similarity='jaccard',
            feature_weighting='none'
        )

        rp3betaCBF_recommenders[index].fit(
            topK=int(rp3betaTopK),
            alpha=rp3betaAlpha,
            beta=rp3betaBeta,
            implicit=False
        )

        recommender = SimilarityMergedHybridRecommender(
            URM_train=URMs_train[index],
            CFRecommender=ItemCBF_recommenders[index],
            CBFRecommender=rp3betaCBF_recommenders[index],
            verbose=False
        )

        recommender.fit(
            topK=int(hybridTopK),
            alpha=hybridAlpha
        )

        recommenders.append(recommender)

    result = evaluator_validation.evaluateRecommender(recommenders)
    results.append(result)
    return sum(result) / len(result)


optimizer = BayesianOptimization(
    f=BO_func,
    pbounds=tuning_params,
    verbose=5,
    random_state=5,
)

optimizer.maximize(
    init_points=30,
    n_iter=20,
)

p3alpha_recommender = ItemKNNCBFRecommender(URM_train=URM_all, ICM_train=ICM_all)

p3alpha_recommender.fit()

rp3betaCBF_recommender = RP3betaCBFRecommender(URM_train=URM_all, ICM_train=ICM_all)

rp3betaCBF_recommender.fit()

recommender = SimilarityMergedHybridRecommender(
    URM_train=URM_all,
    CFRecommender=p3alpha_recommender,
    CBFRecommender=rp3betaCBF_recommender
)
recommender.fit()

import json

with open("logs/" + recommender.RECOMMENDER_NAME + "_logs.json", 'w') as json_file:
    json.dump(optimizer.max, json_file)
