#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import modules
import random 

import numpy as np
import pandas as pd

BLOCK_NUM = 4
SLF_TRIAL_NUM = 9
MEAN = [30, 40, 50]
SD = 7

ALPHA = 0.3
BETA = 0.2

SIM_NUM = 2**10

# Fix seed
# random.seed(0)
# np.random.seed(seed=0)


class RLmodel:
    def __init__(self):        
        # self.q_values = np.zeros((3,), dtype=int)
        self.q_values = np.full(3, 20)
        self.chosen_pairs = np.array([['30/40', '40/50', '50/30', '30/40', '40/50', '50/30', '30/40', '40/50', '50/30'],
                                    ['40/50', '50/30', '30/40', '40/50', '50/30', '30/40', '40/50', '50/30', '30/40'],
                                    ['50/30', '30/40', '40/50', '50/30', '30/40', '40/50', '50/30', '30/40', '40/50'],
                                    ['30/40', '40/50', '50/30', '30/40', '40/50', '50/30', '30/40', '40/50', '50/30'],])

    def softmax(self, x, beta):
        return np.exp(beta * x) / np.sum(np.exp(beta * x), axis=0)

    def choose_action(self, q_values, chosen_pair):
        policy = np.zeros((3,))
        policy[chosen_pair] = self.softmax(q_values[chosen_pair], BETA)
        action = np.random.choice(np.arange(3), p=policy)
        return policy, action
    
    def reward_generator(self):
        rewards = np.array([round(np.random.normal(mean, SD)) for mean in MEAN])
        return rewards
    
    def update_q_value(self, q_value, action, reward, alpha):
        q_value[action] += alpha * (reward[action] - q_value[action])
        return q_value
    
    def simulate(self):
        self.acc_list = []
        
        for block in range(BLOCK_NUM):
            acc = 0
            for trial in range(SLF_TRIAL_NUM):
                chosen_pair = self.chosen_pairs[block, trial]
                if chosen_pair == '30/40':
                    chosen_pair_ = np.array([True, True, False])
                elif chosen_pair == '40/50':
                    chosen_pair_ = np.array([False, True, True])
                elif chosen_pair == '50/30':
                    chosen_pair_ = np.array([True, False, True])
                
                policy, action = self.choose_action(self.q_values, chosen_pair_)
                rewards = self.reward_generator()
                self.q_values = self.update_q_value(self.q_values, action, rewards, ALPHA)
                
                if (chosen_pair=='30/40' and action==1) or (chosen_pair=='40/50' and action==2) or (chosen_pair=='50/30' and action==2):
                    acc += 1
                
                # print(f'Policy: {policy}')
                # print(f'Action: {action}')
                # print(f'Q_value: {self.q_values}\n')
            
            self.acc_list.append(acc / SLF_TRIAL_NUM)


def check_acc(acc_list):
    for i in range(BLOCK_NUM):
        if i == 0:
            if acc_list[i] < 0.5:
                return False
        else:
            if acc_list[i] < acc_list[i-1]:
                return False
    
    return True


def main():
    acc_lists = []
    for _ in range(SIM_NUM):
        model = RLmodel()
        model.simulate()
        acc_lists.append(model.acc_list)
    
    acc_mean = np.mean(acc_lists, axis=0)
    print(acc_mean)

    chk = check_acc(acc_mean)
    if chk:
        print('Success!')

if __name__ == '__main__':
    main()
