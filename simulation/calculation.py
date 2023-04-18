#!/usr/bin/env python
# -*- coding: utf-8 -*-

# NOTE: 被験者番号とパターンについては、1-indexedで記述している

# imports
# standard library
from collections import defaultdict

# third party
import numpy as np
import polars as pl


# column names 
cols = ['game_No', 'seq_No',
        'block', 'seq_pattern','loc_pattern',
        'loc_left', 'loc_right', 'sd', 'pt', 'conf', 'reward',
        't_choice', 't_conf', 'idx_left', 'idx_right',
        'img_choice', 'img_correct', 'loc_choice',
        't_choice_pres', 't_choice_resp',
        't_conf_pres',   't_conf_resp',
        't_reward_pres', 't_reward_resp']

# random seed
seed = 0
np.random.seed(seed)

# variables
block_size = 3
seq_size = 12
subj_size = 15
pat_size = 2
img_size = 3
seq_label   = ['slf', 'obs', 'test']
rept_num = 10**4


""" softmax """
def softmax(x):
    return np.exp(x) / np.sum(np.exp(x), axis=0)


def calc_q_slf(df_slf, q_trial_slf, q_block_slf, alpha, trial_size_slf):
    """selfにおける行動履歴からQ値を計算する

    Args:
        df_slf (df): Q値を求めるためのデータが格納されたdf
        q_trial_slf (list): トライアルごとのQ値
        q_block_slf (defaultdict): ブロックごとのQ値。各ブロック終了時点でのq_trialの値を格納する
        alpha (float): 学習率
        trial_size_slf (int): シーケンスのトライアル数

    Returns:
        None: なし
    """
    for trial in range(trial_size_slf):
        reward = df_slf[trial, 'reward']
        idx_choice = df_slf[trial, 'idx_choice']

        # Update Q values
        q_trial_slf[idx_choice] += alpha * (reward - q_trial_slf[idx_choice])

        if (trial+1)%12==0:
            q_block_slf[(trial+1)//12] = q_trial_slf.copy()


def calc_log_like_test_ss_softmax(df_test, q_slf, beta, trial_size):
    """selfで求めたQ値と、testにおける行動履歴から、ss条件におけるQ値を計算する
        このとき、エージェントの方策にはsoftmax関数を用いる

    Args:
        df_test (df): Q値を求めるためのデータが格納されたtestのdf
        q_slf (defaultdict): selfで計算したQ値
        beta (float): 逆温度
        trial_size (int): シーケンスのトライアル数

    Returns:
        log_like_softmax: ss条件におけるsoftmax関数を用いたQ値の対数尤度
    """
    log_like_softmax = 0
    cnt_smaller_than_rand = 0
    
    for trial in range(trial_size):
        # 1 <= trial <= 6: q_slf[1], 7 <= trial <= 12: q_slf[2], 13 <= trial <= 18: q_slf[3]
        # q_slf[i]は、i番目のブロック終了時点でのQ値
        q_test = q_slf[trial//6+1]

        idx_left = df_test[trial, 'idx_left']
        idx_right = df_test[trial, 'idx_right']
        img_choice = df_test[trial, 'img_choice']

        # HACK: 冗長になっているのでできればdfの方で修正したい
        # NOTE: img_choiceは、0が画像選択に間に合わなかった、1が左、2が右を選択したことになるが、
        #       以下の計算では、画像を選択した場合に限り、その尤度を計算するため、0の場合は計算に含めず、
        #       1か2の場合はインデックスとして使用するため、-1をしている。
        if img_choice == -1:
            continue

        log_like_softmax += np.log(softmax(beta * np.array(
                                [q_test[idx_left], q_test[idx_right]]))[img_choice])
    
    for _ in range(rept_num):
        log_like_softmax_rand = 0
        
        for trial in range(trial_size):
            q_test = q_slf[trial//6+1]

            idx_left = df_test[trial, 'idx_left']
            idx_right = df_test[trial, 'idx_right']
            img_choice_rand = np.random.choice([0, 1], p=[.5, .5])

            log_like_softmax_rand += np.log(softmax(beta * np.array(
                                    [q_test[idx_left], q_test[idx_right]]))[img_choice_rand])
        
        if log_like_softmax_rand > log_like_softmax:
            cnt_smaller_than_rand += 1
    
    p_softmax = max(1, cnt_smaller_than_rand) / rept_num
        
    return log_like_softmax, p_softmax


""" matching law """
def matching(x):
    return x / np.sum(x, axis=0)


def calc_freq_slf(df_slf, freq_block_slf, block_size_slf):
    """selfにおける行動履歴から、各画像の選択頻度を計算する

    Args:
        df_slf (df): Q値を求めるためのデータが格納されたdf
        freq_block_slf (defaultdict): 各画像の選択頻度
        trial_size_slf (int): シーケンスのトライアル数

    Returns:
        None: なし
    """
    freq = [0] * (img_size+1)
    for block in range(1, block_size_slf+1):
        df = df_slf.filter(pl.col('block')<=block)
        for img in range(1, img_size+1):
            freq[img] = df.filter(pl.col('idx_choice')==img).height
        freq_block_slf[block] = freq.copy()


def calc_log_like_test_ss_matching(df_test, freq_slf, trial_size):
    """selfで求めた選択頻度と、testにおける行動履歴から、ss条件における選択頻度を計算する

    Args:
        df_test (df): 選択頻度を求めるためのデータが格納されたdf
        freq_slf (defaultdict): selfで計算した選択頻度
        trial_size (int): シーケンスのトライアル数

    Returns:
        log_like_softmax: ss条件におけるmathing lawに基づいて画像を選択した場合の対数尤度
    """
    log_like_matching = 0
    cnt_smaller_than_rand = 0
    
    for trial in range(trial_size):
        # 1 <= trial <= 6: freq_slf[1]
        # 7 <= trial <= 12: freq_slf[2]
        # 13 <= trial <= 18: freq_slf[3]
        # q_slf[i]は、i番目のブロック終了時点でのQ値
        freq_test = freq_slf[trial//6+1]

        idx_left = df_test[trial, 'idx_left']
        idx_right = df_test[trial, 'idx_right']
        img_choice = df_test[trial, 'img_choice']

        # NOTE: img_choiceは、-1が画像選択に間に合わなかった、0が左、1が右を選択したことになるが、
        #       以下の計算では、画像を選択した場合に限り、その尤度を計算するため、-1の場合は計算に含めていない
        if img_choice == -1:
            continue

        log_like_matching += np.log(matching(np.array(
                                [freq_test[idx_left], freq_test[idx_right]]))[img_choice])

    for _ in range(rept_num):
        log_like_matching_rand = 0
        
        for trial in range(trial_size):
            freq_test = freq_slf[trial//6+1]

            idx_left = df_test[trial, 'idx_left']
            idx_right = df_test[trial, 'idx_right']
            img_choice_rand = np.random.choice([0, 1], p=[.5, .5])

            log_like_matching_rand += np.log(matching(np.array(
                                    [freq_test[idx_left], freq_test[idx_right]]))[img_choice_rand])

        if log_like_matching_rand > log_like_matching:
            cnt_smaller_than_rand += 1

    p_matching = max(1, cnt_smaller_than_rand) / rept_num

    return log_like_matching, p_matching


def main():
    pass

if __name__ == "__main__":
    main()