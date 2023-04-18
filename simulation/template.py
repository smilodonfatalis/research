#!/usr/bin/env python
# -*- coding: utf-8 -*-

# NOTE: 被験者番号とパターンについては、1-indexedで記述している

# imports
# standard library
import os

def get_subj_file_path():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    subj_file_path = os.path.join(base_dir, 'data', 'subj*')
    
    return subj_file_path


def get_param_file_path():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    param_file_path = os.path.join(base_dir, 'params.xlsx')
    
    return param_file_path


def main():
    pass

if __name__ == '__main__':
    main()