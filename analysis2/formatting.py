#!/usr/bin/env python
# -*- coding: utf-8 -*-

# NOTE: 被験者番号とパターンについては、1-indexedで記述している

# Imports
# standard library
import glob
import random
from collections import defaultdict

# third party
import numpy as np
import polars as pl

# local
import template_analysis as tp


def fix_seed(seed=0):
    random.seed(seed)
    np.random.seed(seed)

# variables
LOW = 'low'
HIGH = 'high'
SUBJ = 1
GAME = 4
pat_size = 2
block_size = 3
seq_slf_size = 12
seq_test_ss_size = 6
img_size = 3
seq_types = ['slf', 'obs', 'test']

# 
subj_cols = ['block_num', 'trial_num', 'seq_type', 'seq_trial_num', 
            'condition', 'pair_pat', 'order_pat', 
            'mean_left', 'mean_right', 'sd', 
            'idx_left', 'idx_right',
            'pos_correct', 'mean_correct', 'idx_correct', 
            'pos_chosen', 'mean_chosen', 'idx_chosen',  
            'conf_pat', 'conf', 'acc', 'reward',
            'img_time', 'conf_time', 
            'img_pres_time', 'img_resp_time',
            'conf_pres_time', 'conf_resp_time',
            'reward_pres_time', 'reward_resp_time']
param_cols = ['subj', 'pat', 'alpha', 'beta', 'log_likelihood']


class Individual:
    def __init__(self, subj_file, params, seq_types, subj_num, game_pat):
        self.seq_types = seq_types
        self.subj_num = subj_num
        self.game_pat = game_pat
        self.group_num = 1 if subj_num%2==1 else 2
        
        self.slf = convert_excel_result_into_df(
                        subj_file, 
                        seq_types[0], 
                        subj_num, 
                        game_pat, 
                        group_num=self.group_num
                    )
        self.slf = self.slf.with_columns(pl.when(pl.col('conf')==LOW).then(0)
                                            .otherwise(1).alias('conf_num'))

        self.obs = convert_excel_result_into_df(
                        subj_file, 
                        seq_types[1], 
                        subj_num, 
                        game_pat, 
                        group_num=self.group_num
                    )
        self.obs = self.obs.with_columns(pl.when(pl.col('conf')==LOW).then(0)
                                            .otherwise(1).alias('conf_num'))


        self.test = convert_excel_result_into_df(
                        subj_file, 
                        seq_types[2], 
                        subj_num, 
                        game_pat, 
                        group_num=self.group_num
                    )
        self.test = self.test.with_columns(pl.when(pl.col('conf')==LOW).then(0)
                                            .otherwise(1).alias('conf_num'))


        self.alpha = params[2*(subj_num-1) + (game_pat-1), 'alpha']
        self.beta = params[2*(subj_num-1) + (game_pat-1), 'beta']
        self.ll = params[2*(subj_num-1) + (game_pat-1), 'log_likelihood']


class Integrated:
    """全被験者の結果を結合したdfを取得するためのクラス
    """
    def __init__(self, individual, game_pat):
        self.slf = individual[1][game_pat].slf.clone()
        self.obs = individual[1][game_pat].obs.clone()
        self.test = individual[1][game_pat].test.clone()
        
        if SUBJ > 1:
            for subj in range(2, SUBJ+1):
                self.slf = pl.concat([self.slf, individual[subj][game_pat].slf.clone()])
                self.obs = pl.concat([self.obs, individual[subj][game_pat].obs.clone()])
                self.test = pl.concat([self.test, individual[subj][game_pat].test.clone()])



def convert_excel_result_into_df(file_name, seq_type, subj_num, game_pat, group_num):
    """被験者の結果が格納された.xlsxファイルを読み込んでdfを取得する

    Args:
        file_name (str): ファイルのパス
        seq_types (str): 読み込むデータのシーケンス (slf、obs、test)
        subj (int): 被験者番号 (1 - 15)
        game_pat (int): 読み込むデータのパターン (1 or 2)
        group_num (int): 被験者のグループ (1 or 2)

    Returns:
        df: .xlsxファイルを読み込んで得られたdf
    """
    df = pl.read_excel(
            file_name,
            sheet_name=seq_type+str(game_pat),
            read_csv_options={'has_header': True, 'new_columns': subj_cols}
            )
    df = df.with_columns(
            pl.lit(subj_num).alias('subj'), 
            pl.lit(seq_type).alias('seq_type'), 
            pl.lit(group_num).alias('group')
        )

    return df


def generate_individual_data_instance():
    """被験者のデータを取得する"""
    subj_file_path = tp.get_subj_file_path()
    subj_files = glob.glob(subj_file_path)
    subj_files.sort()


    param_file = tp.get_param_file_path()
    param = pl.read_excel(
                param_file, 
                sheet_name='params', 
                read_csv_options={'new_columns': param_cols}
            )
    param = param.select(
                param.columns[param.find_idx_by_name('subj'):param.find_idx_by_name('log_likelihood')+1]
            )

    individual = [[None] for _ in range(SUBJ+1)]

    for subj in range(1, SUBJ+1):
        for game in range(1, GAME+1):
            # print(f'{subj=}, {pat=}')
            individual[subj].append(Individual(subj_files[GAME*(subj-1) + (game-1)], param, seq_types, subj, game))

    return individual

def generate_integrated_data_instance():
    integrated = [0]
    for game_pat in range(1, GAME+1):
        integrated.append(Integrated(generate_individual_data_instance(), game_pat))
    
    return integrated


def main():
    pass

if __name__ == "__main__":
    main()