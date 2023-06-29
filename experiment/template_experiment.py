#!/usr/bin/env python
# -*- coding: utf-8 -*-

# NOTE: 被験者番号とパターンについては、1-indexedで記述している

# imports
# standard library
import os


def get_condition_dir_path():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    condition_dir_path = os.path.join(base_dir, 'experiment', 'sequences/')
    
    return condition_dir_path


def main():
    pass

if __name__ == '__main__':
    main()