if __name__ == '__main__':

    from src.Utils.ICM_preprocessing import *
    from src.Utils.load_ICM import load_ICM
    from src.Utils.load_URM import load_URM

    URM_all = load_URM("in/data_train.csv")
    ICM_all = load_ICM("in/data_ICM_title_abstract.csv")

    profile_length = np.ediff1d(URM_all.indptr)
    block_size = int(len(profile_length)*0.25)

    start_worst = 0
    end_worst = block_size
    end_normal = 3*block_size
    end_best = min(4 * block_size, len(profile_length))
    sorted_users = np.argsort(profile_length)

    users_in_worst = set(sorted_users[start_worst:end_worst])


    users_in_normal = set(sorted_users[end_worst+1:end_normal])

    users_in_best = set(sorted_users[end_normal+1:end_best])


    # from src.Hybrid.SimilarityMergedHybridRecommender import SimilarityMergedHybridRecommender
    # from src.Hybrid.GeneralizedSimilarityMergedHybridRecommender import GeneralizedSimilarityMergedHybridRecommender
    # from src.GraphBased.P3alphaRecommender import P3alphaRecommender
    # from src.GraphBased.RP3betaCBFRecommender import RP3betaCBFRecommender
    # from src.KNN.ItemKNNCBFRecommender import ItemKNNCBFRecommender
    #
    # ICM_combined = combine(ICM=ICM_all, URM=URM_all)
    #
    # p3alpha_recommender = P3alphaRecommender(URM_train=URM_all, verbose=False)
    # p3alpha_recommender.fit(topK=210,alpha=0.45,implicit=True)
    #
    # rp3betaCBF_recommender = RP3betaCBFRecommender(URM_train=URM_all, ICM_train=ICM_combined, verbose=False)
    # rp3betaCBF_recommender.fit(topK=536,alpha=0.41753274557496695,beta=0.2344960487580402,implicit=False)
    #
    # recommender_worst = SimilarityMergedHybridRecommender(URM_train=URM_all,CFRecommender=p3alpha_recommender,CBFRecommender=rp3betaCBF_recommender,verbose=False)
    # recommender_worst.fit(topK=481, alpha=0.1)
    #
    # p3alpha_recommender = P3alphaRecommender(URM_train=URM_all, verbose=False)
    # p3alpha_recommender.fit(topK=213,alpha=0.4729294763382114,implicit=True)
    #
    # rp3betaCombined_recommender = RP3betaCBFRecommender(URM_train=URM_all, ICM_train=ICM_combined, verbose=False)
    # rp3betaCombined_recommender.fit(topK=int(525.3588205773788),alpha=0.42658191175355076,beta=0.2284685880641364,implicit=False)
    #
    # rp3betaCBF_recommender = RP3betaCBFRecommender(URM_train=URM_all, ICM_train=ICM_all, verbose=False)
    # rp3betaCBF_recommender.fit(topK=int(188.6),alpha=0.1324,beta=0.981,implicit=False)
    #
    # recommender_normal = GeneralizedSimilarityMergedHybridRecommender(
    #             URM_train=URM_all,
    #             similarityRecommenders=[
    #                 p3alpha_recommender,
    #                 rp3betaCombined_recommender,
    #                 rp3betaCBF_recommender
    #             ],
    #             verbose=False
    #         )
    # recommender_normal.fit(
    #         topKs=[
    #             int(482.3259592432915),
    #             int(872.7)
    #         ],
    #         alphas=[
    #             0.2324902889610141,
    #             0.7876
    #         ]
    #     )
    #
    # p3alpha_recommender = ItemKNNCBFRecommender(URM_train=URM_all, ICM_train=ICM_combined)
    # p3alpha_recommender.fit(shrink=135, topK=983,similarity='cosine', feature_weighting='BM25')
    #
    # rp3betaCBF_recommender = RP3betaCBFRecommender(URM_train=URM_all, ICM_train=ICM_combined, verbose=False)
    # rp3betaCBF_recommender.fit(topK=577,alpha=0.448,beta=0.2612,implicit=False)
    #
    # recommender_best = SimilarityMergedHybridRecommender(URM_train=URM_all,CFRecommender=p3alpha_recommender,CBFRecommender=rp3betaCBF_recommender,verbose=False)
    # recommender_best.fit(topK=872, alpha=0.2776,)

    from src.GraphBased.RP3betaCBFRecommender import RP3betaCBFRecommender
    from src.Hybrid.MergedHybridRecommender import MergedHybridRecommender
    from src.Hybrid.GeneralizedMergedHybridRecommender import GeneralizedMergedHybridRecommender
    from src.Implicit.FeatureCombinedImplicitALSRecommender import FeatureCombinedImplicitALSRecommender
    from src.SLIM_ElasticNet.SLIMElasticNetRecommender import MultiThreadSLIM_ElasticNet
    from src.Utils.ICM_preprocessing import *
    from src.Utils.load_URM import load_URM
    from src.Utils.load_ICM import load_ICM
    from src.Utils.confidence_scaling import *

    ICM_combined = combine(ICM=ICM_all, URM = URM_all)

    # p3alpha_recommender = P3alphaRecommender(
    #     URM_train=URM_all,
    #     verbose=False
    # )
    #
    # p3alpha_recommender.fit(
    #     topK=int(212.8832860130684),
    #     alpha=0.4729294763382114,
    #     implicit=True
    # )

    rp3betaCombined_recommender= RP3betaCBFRecommender(
        URM_train=URM_all,
        ICM_train=ICM_combined,
        verbose=False
    )

    rp3betaCombined_recommender.fit(
        topK=int(529.1628484087545),
        alpha=0.45304737831676245,
        beta=0.226647894170121,
        implicit=False
    )

    IALS_recommender= FeatureCombinedImplicitALSRecommender(
        URM_train=URM_all,
        ICM_train=ICM_all,
        verbose=True
    )

    IALS_recommender.fit(
        factors=int(398.601583855084),
        regularization=0.01,
        use_gpu=False,
        iterations=int(94.22855449116447),
        num_threads=6,
        confidence_scaling=linear_scaling_confidence,
        **{
            'URM': {"alpha": 42.07374324671451},
            'ICM': {"alpha": 41.72067133975204}
        }
    )

    SLIM_recommender=MultiThreadSLIM_ElasticNet(
                    URM_train= ICM_combined.T,
                    verbose=False
    )

    SLIM_recommender.fit(
        alpha=0.00026894910579512645,
        l1_ratio=0.08074126876487486,
        topK=int(395.376118479588),
        workers=6
    )

    # rp3betaCBF_recommender= RP3betaCBFRecommender(
    #     URM_train=URM_all,
    #     ICM_train=ICM_all,
    #     verbose=False
    # )
    #
    # rp3betaCBF_recommender.fit(
    #     topK=int(117.1),
    #     alpha=0.9882,
    #     beta=0.7703,
    #     implicit=False
    # )

    # itemKNN_recommender= ItemKNNCFRecommender(
    #     URM_train=URM_all,
    #     verbose=False
    # )
    #
    # itemKNN_recommender.fit(
    #     topK=100,
    #     shrink=50
    # )
    #
    # pureSVD_recommender= PureSVDItemRecommender(
    #     URM_train=URM_all,
    #     verbose=False
    # )
    #
    #
    # pureSVD_recommender.fit(
    #     num_factors=772,
    #     topK= 599
    # )

    lower_recommender = GeneralizedMergedHybridRecommender(
        URM_train=URM_all,
        recommenders=[
            IALS_recommender,
            rp3betaCombined_recommender,
            SLIM_recommender
        ],
        verbose=False
    )

    lower_recommender.fit(
        alphas=[
            0.635089550770892*0.6686,
            0.635089550770892*(1-0.6686),
            1-0.635089550770892
        ]
    )

    rp3betaCombined_recommender= RP3betaCBFRecommender(
        URM_train=URM_all,
        ICM_train=ICM_combined,
        verbose=False
    )

    rp3betaCombined_recommender.fit(
        topK=int(741.3),
        alpha=0.4812,
        beta=0.2927,
        implicit=False
    )

    IALS_recommender= FeatureCombinedImplicitALSRecommender(
        URM_train=URM_all,
        ICM_train=ICM_all,
        verbose=True
    )

    IALS_recommender.fit(
        factors=500,
        regularization=0.01,
        use_gpu=False,
        iterations=94,
        num_threads=4,
        confidence_scaling=linear_scaling_confidence,
        **{
            'URM': {"alpha": 50},
            'ICM': {"alpha": 50}
        }
    )

    higher_recommender = MergedHybridRecommender(
        URM_train=URM_all,
        recommender1=IALS_recommender,
        recommender2=rp3betaCombined_recommender,
        verbose=False
    )

    higher_recommender.fit(
        alpha= 0.6354
    )

    import pandas as pd
    import csv
    import numpy as np

    targetUsers = pd.read_csv("in/data_target_users_test.csv")['user_id']

    targetUsers = targetUsers.tolist()

    with open('out/SwitchedHybrid_submission.csv','w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['user_id', 'item_list'])

        for userID in targetUsers:
            if userID in users_in_normal:
                writer.writerow([userID, str(np.array(lower_recommender.recommend(userID, 10)))[1:-1]])
            elif userID in users_in_best:
                writer.writerow([userID, str(np.array(higher_recommender.recommend(userID, 10)))[1:-1]])
            else:
                writer.writerow([userID, str(np.array(lower_recommender.recommend(userID, 10)))[1:-1]])

