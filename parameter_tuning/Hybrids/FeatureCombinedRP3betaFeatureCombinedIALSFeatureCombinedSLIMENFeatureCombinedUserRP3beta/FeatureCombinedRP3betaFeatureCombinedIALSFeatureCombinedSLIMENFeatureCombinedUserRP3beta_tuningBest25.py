if __name__ == '__main__':

    from src.Base.Evaluation.K_Fold_Evaluator import K_Fold_Evaluator_MAP
    from src.Utils.ICM_preprocessing import *
    from src.Utils.confidence_scaling import *
    from src.Utils.load_ICM import load_ICM
    from src.Utils.load_URM import load_URM

    URM_all = load_URM("../../../in/data_train.csv")
    ICM_all = load_ICM("../../../in/data_ICM_title_abstract.csv")
    from src.Data_manager.split_functions.split_train_validation_random_holdout import \
        split_train_in_two_percentage_global_sample

    URMs_train = []
    URMs_validation = []
    ignore_users_list = []

    import numpy as np

    for k in range(5):
        URM_train, URM_validation = split_train_in_two_percentage_global_sample(URM_all, train_percentage=0.80)
        URMs_train.append(URM_train)
        URMs_validation.append(URM_validation)

        profile_length = np.ediff1d(URM_train.indptr)
        block_size = int(len(profile_length) * 0.25)

        start_pos = 3 * block_size
        end_pos = len(profile_length)
        sorted_users = np.argsort(profile_length)

        users_in_group = sorted_users[start_pos:end_pos]

        users_in_group_p_len = profile_length[users_in_group]
        sorted_users = np.argsort(profile_length)

        users_not_in_group_flag = np.isin(sorted_users, users_in_group, invert=True)
        ignore_users_list.append(sorted_users[users_not_in_group_flag])

    evaluator_validation = K_Fold_Evaluator_MAP(URMs_validation, cutoff_list=[10], verbose=False,
                                                ignore_users_list=ignore_users_list)

    ICMs_combined = []
    for URM in URMs_train:
        ICMs_combined.append(combine(ICM=ICM_all, URM=URM))

    from src.Hybrid.GeneralizedMergedHybridRecommender import GeneralizedMergedHybridRecommender
    from src.Implicit.FeatureCombinedImplicitALSRecommender import FeatureCombinedImplicitALSRecommender
    from src.SLIM_ElasticNet.SLIMElasticNetRecommender import MultiThreadSLIM_ElasticNet
    from src.GraphBased.RP3betaCBFRecommender import RP3betaCBFRecommender
    from src.GraphBased.UserRP3betaRecommender import UserRP3betaRecommender

    from bayes_opt import BayesianOptimization

    IALS_recommenders = []
    rp3betaCBF_recommenders = []
    SLIM_recommenders = []
    userRp3beta_recommenders = []
    recommenders = []

    for index in range(len(URMs_train)):
        IALS_recommenders.append(
            FeatureCombinedImplicitALSRecommender(
                URM_train=URMs_train[index],
                ICM_train=ICM_all,
                verbose=True
            )
        )
        IALS_recommenders[index].fit(
            factors=500,
            regularization=0.01,
            use_gpu=False,
            iterations=94,
            num_threads=6,
            confidence_scaling=linear_scaling_confidence,
            **{
                'URM': {"alpha": 50},
                'ICM': {"alpha": 50}
            }
        )

        rp3betaCBF_recommenders.append(
            RP3betaCBFRecommender(
                URM_train=URMs_train[index],
                ICM_train=ICMs_combined[index],
                verbose=False
            )
        )

        rp3betaCBF_recommenders[index].fit(
            topK=int(741.3),
            alpha=0.4812,
            beta=0.2927,
            implicit=False
        )

        SLIM_recommenders.append(
            MultiThreadSLIM_ElasticNet(
                URM_train=ICMs_combined[index].T,
                verbose=False
            )
        )

        SLIM_recommenders[index].fit(
            alpha=0.00026894910579512645,
            l1_ratio=0.08074126876487486,
            topK=int(400),
            workers=6
        )

        SLIM_recommenders[index].URM_train = URMs_train[index]

        userRp3beta_recommenders.append(
            UserRP3betaRecommender(
                URM_train=ICMs_combined[index].T,
                verbose=False
            )
        )

        userRp3beta_recommenders[index].fit(
            topK=201,
            alpha=0.6436402193909941,
            beta=0.5094750943074225,
            implicit=False
        )

        recommender = GeneralizedMergedHybridRecommender(
            URM_train=URMs_train[index],
            recommenders=[
                IALS_recommenders[index],
                rp3betaCBF_recommenders[index],
                SLIM_recommenders[index],
                userRp3beta_recommenders[index]
            ],
            verbose=False
        )

        recommenders.append(recommender)

        recommenders[index].fit(
            alphas=[
                0.6879337082904029 * 0.590640363416649,
                0.6879337082904029 * (1 - 0.590640363416649),
                (1 - 0.6879337082904029)
            ]
        )

    result = evaluator_validation.evaluateRecommender(recommenders)
    print(sum(result) / len(result))


    tuning_params = {
        "gamma": (0, 1)
    }

    results = []


    def BO_func(
            gamma
    ):

        for index in range(len(URMs_train)):
            recommenders[index].fit(
                alphas=[
                    gamma * 0.6879337082904029 * 0.590640363416649,
                    gamma * 0.6879337082904029 * (1 - 0.590640363416649),
                    gamma * (1 - 0.6879337082904029),
                    1 - gamma
                ]
            )

        result = evaluator_validation.evaluateRecommender(recommenders)
        return sum(result) / len(result)


    optimizer = BayesianOptimization(
        f=BO_func,
        pbounds=tuning_params,
        verbose=5,
        random_state=5,
    )

    optimizer.maximize(
        init_points=100,
        n_iter=50,
    )

    import json

    with open("logs/FeatureCombined" + recommenders[0].RECOMMENDER_NAME + "_best25_logs.json", 'w') as json_file:
        json.dump(optimizer.max, json_file)
