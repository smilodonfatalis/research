﻿# -*- coding: utf-8 -*-

# NOTE: 被験者番号とパターンについては、1-indexedで記述している

# imports
# standard library
from collections import defaultdict

# third party
import numpy as np
import polars as pl

# local
import calculation as calc
import formatting as fmt
# import writeToExcel as wte


cols = ['game_No', 'seq_No',
        'block', 'seq_pattern','loc_pattern',
        'loc_left', 'loc_right', 'sd', 'pt', 'conf', 'reward',
        't_choice', 't_conf', 'idx_left', 'idx_right',
        'img_choice', 'img_correct', 'loc_choice',
        't_choice_pres', 't_choice_resp',
        't_conf_pres',   't_conf_resp',
        't_reward_pres', 't_reward_resp']

def main():
    # random seed
    seed = 0
    np.random.seed(seed) # 20, 5, 14

    # variables
    subj_size = 15
    pat_size = 2
    block_size = 3
    seq_size_obs = 12
    seq_size_test_oo = 6
    img_size = 3

    rept_num = 10**3

    """
    individual[被験者番号(1〜15)][パターン(1, 2)]とすることで、該当番号の被験者の当該パターンにおけるインスタンスを取得できる
    ex) individual[i][j].slf : 被験者iのパターンjにおけるselfシーケンスのdf
    """
    individual = fmt.generate_individual_data_instance()

    # コンソールにシード値と繰り返し回数を表示
    print(f'{seed=}  {rept_num=}\n')

    """ 被験者ごと、パターンごとにシミュレーションを行う """
    for subj in range(1, subj_size+1):
        for pat in range(1, pat_size+1):
            
            df_obs = individual[subj][pat].obs
            df_test_oo = individual[subj][pat].test.filter(pl.col('seq_pattern') == 'oo')
            alpha = individual[subj][pat].alpha
            beta = individual[subj][pat].beta

            # softmaxモデルの計算
            q_trial_obs = [0] * (img_size+1)
            q_block_obs = defaultdict(int)
            calc.calc_q_obs(df_obs, q_trial_obs, q_block_obs, alpha, seq_size_obs*block_size)
            log_like_softmax, p_softmax = calc.calc_log_like_test_ss_softmax(
                                                df_test_oo, q_block_obs, beta, seq_size_test_oo*block_size
                                            )

            # # matchingモデルの計算
            # freq_block_slf = defaultdict(int)
            # calc.calc_freq_slf(df_slf, freq_block_slf, seq_size_slf*block_size)
            # log_like_matching, p_matching = calc.calc_log_like_test_ss_matching(
            #                                     df_test_ss, freq_block_slf, seq_size_test_ss*block_size
            #                                 )

            # コンソールに結果を表示
            # print(f'{subj=}, {pat=}, {p_softmax=}, {log_like_softmax=:.2f}, {p_matching=}, {log_like_matching=:.2f}\n')
            print(f'{subj=}, {pat=}, {p_softmax=}, {log_like_softmax=:.2f}\n')

    # TODO: Excelファイルに書き込むプログラムを作成する
    # wte.write_to_excel(p_softmax, log_like_softmax, p_matching, log_like_matching)


if __name__ == '__main__':
    main()
