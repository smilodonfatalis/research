#!/usr/bin/env python
# -*- coding: utf-8 -*-

# NOTE: 被験者番号とパターンについては、1-indexedで記述している

# Imports
# standard library
import glob
from collections import defaultdict

# third party
import numpy as np
import polars as pl

# local
import template_experiment as tp


seed = 0
np.random.seed(seed) # 20, 5, 14

# variables
subj_size = 15
pat_size = 2
block_size = 3
seq_slf_size = 12
seq_test_ss_size = 6
img_size = 3
seq_label   = ['slf', 'obs', 'test']

subj_cols = ['game_No', 'seq_No',
            'block', 'seq_pattern','loc_pattern',
            'loc_left', 'loc_right', 'sd', 'pt', 'conf', 'reward',
            't_choice', 't_conf', 'idx_left', 'idx_right',
            'img_choice', 'img_correct', 'loc_choice',
            't_choice_pres', 't_choice_resp',
            't_conf_pres',   't_conf_resp',
            't_reward_pres', 't_reward_resp']
param_cols = ['subj', 'pat', 'alpha', 'beta', 'log_likelihood']


class Individual:
    def __init__(self, subj_file, params, seq_label, subj, pat):
        self.seq_label = seq_label
        self.subj  = subj
        self.pat = pat
        self.group_num = 1 if subj%2==1 else 2
        
        self.slf = convert_excel_result_into_df(
                        subj_file, 
                        seq_label[0], 
                        subj, 
                        pat, 
                        group_num=self.group_num
                    )
        self.slf = self.slf.with_columns(pl.col('conf')-6)
        self.slf = self.slf.with_columns(pl.when(pl.col('loc_choice')==30).then(1)
                                            .when(pl.col('loc_choice')==40).then(2)
                                            .otherwise(3).alias('idx_choice')
                                            )
        self.slf = self.slf.with_columns(pl.when(pl.col('loc_choice')==30).then(1)
                                            .when(pl.col('loc_choice')==40).then(2)
                                            .otherwise(3).alias('idx_choice')
                                            )
        

        self.obs = convert_excel_result_into_df(
                        subj_file, 
                        seq_label[1], 
                        subj, 
                        pat, 
                        group_num=self.group_num
                    )
        self.obs = self.obs.with_columns(pl.col('conf')-6)
        self.obs = self.obs.with_columns(pl.when(pl.col('loc_choice')==30).then(1)
                                            .when(pl.col('loc_choice')==40).then(2)
                                            .otherwise(3).alias('idx_choice')
                                            )
        self.obs = self.obs.with_columns(pl.when(pl.col('img_choice')==1).then(0)
                                            .when(pl.col('img_choice')==2).then(1)
                                            .otherwise(-1).alias('img_choice')
                                            )

        self.test = convert_excel_result_into_df(
                        subj_file, 
                        seq_label[2], 
                        subj, 
                        pat, 
                        group_num=self.group_num
                    )
        self.test = self.test.with_columns(pl.col('conf')-6)
        self.test = self.test.with_columns(pl.when(pl.col('seq_pattern')==1).then('ss')
                                            .when(pl.col('seq_pattern')==2).then('oo')
                                            .otherwise('so').cast(pl.Utf8).alias('seq_pattern')
                                            )
        self.test = self.test.with_columns(pl.when(pl.col('loc_choice')==30).then(1)
                                            .when(pl.col('loc_choice')==40).then(2)
                                            .otherwise(3).alias('idx_choice')
                                            )
        self.test = self.test.with_columns(pl.when(pl.col('img_choice')==1).then(0)
                                            .when(pl.col('img_choice')==2).then(1)
                                            .otherwise(-1).alias('img_choice')
                                            )

        self.alpha = params[2*(subj-1) + (pat-1), 'alpha']
        self.beta = params[2*(subj-1) + (pat-1), 'beta']
        self.log_like = params[2*(subj-1) + (pat-1), 'log_likelihood']



class Integrated(Individual):
    def __init__(self, subj_file, params, seq_label, subj, pat):
        super().__init__(subj_file, params, seq_label, subj, pat)



def convert_excel_result_into_df(file_name, seq_label, subj, pat, group_num):
    """被験者の結果が格納された.xlsxファイルを読み込んでdfを取得する

    Args:
        file_name (str): ファイルのパス
        seq_label (str): 読み込むデータのシーケンス (slf、obs、test)
        subj (int): 被験者番号 (1 - 15)
        pat_size (int): 読み込むデータのパターン (1 or 2)
        group_num (int): 被験者のグループ (1 or 2)

    Returns:
        df: .xlsxファイルを読み込んで得られたdf
    """
    df = pl.read_excel(
            file_name,
            sheet_name=seq_label+str(pat),
            read_csv_options={'has_header': False, 'new_columns': subj_cols}
            )
    df = df.with_columns(
            pl.lit(subj).alias('subj_No'), 
            pl.lit(seq_label).alias('type'), 
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

    individual = [[None] for _ in range(subj_size+1)]

    for subj in range(1, subj_size+1):
        for pat in range(1, pat_size+1):
            # print(f'{subj=}, {pat=}')
            individual[subj].append(Individual(subj_files[2*(subj-1) + (pat-1)], param, seq_label, subj, pat))

    return individual


def main():
    pass

if __name__ == "__main__":
    main()