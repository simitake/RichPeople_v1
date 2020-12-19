# -*- coding: utf-8 -*-
"""
Created on Sun Aug 16 11:02:48 2020

@author: 81802
"""

import random
import copy
from tqdm import tqdm
from statistics import stdev, mean
import matplotlib.pyplot as plt

class Set:
    """
    ----------
    Perameters
    ----------
    player_counts             : プレイヤー人数_int_2~52_ini 4
    rules                     : 階段・縛り・都落ちの有無_list_[0or1, 0or1, 0or1]_ini [0,0,0]
    effects      : カードの効果の有無_list_[4,5,7,8,10,11,12]_ini [8,11]
                4 : 出した枚数のカードを捨て札から自分の手札に回収する
                5 : 出した枚数順番を一人飛ばす
                7 : 出した枚数のカードを自分の手札から次番に渡す
                8 : 出した場合流れを強制終了し、自分からターンを始める、このカードで上がれない
                10: 出した枚数のカードを自分の手札から捨てる
                11: 出した場合流れが切れるまでその時点での強弱を逆転する
                12: 出した枚数のカードの種類を指定、全プレイヤーの手札から該当するカードを捨てる
    joker_counts　              :　ジョーカーの枚数_int_0~2_ini 2
    exchange_cards             : 一巡終わるごとの手札交換最大枚数_int_0~26_ini 2
    games:[0~∞]}]        : 巡回する回数_int_1~10_ini 10
    strategies                 : 各プレイヤーの戦略_list_[0,0~] or [1,[0~,0~],[0~,0~]]_ini[0,0]
                strategies[0](全プレイヤー指定か各プレイヤー指定か)
                0 : 全プレイヤーが同戦略
                1 : 人数分の戦略を指定する
                strategies[1][0](全プレイヤー指定の場合一つの戦略を指定、各プレイヤー指定の場合プレイヤー分の捨て札戦略を指定)
                0 : ランダム
                1 : 枚数重視の捨て札
                2 : 縛り重視の捨て札
                3 : 階段重視の捨て札
                4 : 階段重視
                5 : 階段軽視
                ...10(これから考える)
                strategies[1][1](全プレイヤー指定の場合一つの戦略を指定、各プレイヤー指定の場合プレイヤー分の譲渡札戦略を指定)
                0 : ランダム
                1 : 弱いカードの譲渡
                2 : 効果なしカードの譲渡
                3 : 
                ...10(これから考える)
    vs                          : コンソールによる対戦を可能とする
    -----------
    Methods
    -----------
    recorder:戦績を返す
        
    """
    
    #初期化/初期設定
    def __init__(self, player_counts=4, rules=[0,0,0], effects=[8,11], \
                 joker_counts=2, exchange_cards=2, games=10, \
                     strategies=[0,0], vs=0):
        self.player_counts = player_counts
        self.rules = rules
        self.effects = effects
        self.joker_counts = joker_counts
        self.exchange_cards = exchange_cards
        self.games = games
        self.strategies = strategies
        self.vs = vs
        self.history = []
        self.battle_record = {}
        self.battle_record2 = {}
        self.priority_dicts = [{1:12, 2:13, 3:1, 4:2, 5:3, 6:4, 7:5,\
                                8:6, 9:7, 10:8, 11:9, 12:10, 13:11,\
                                    'J1':20, 'J2':20},\
                          {1:2, 2:1, 3:13, 4:12, 5:11, 6:10, 7:9, 8:8,\
                          9:7, 10:6, 11:5, 12:4, 13:3, 'J1':20, 'J2':20}]
        #使用カード設定
        self.card_set()
        
        #初期設定の表示
        print('player_count:'+str(self.player_counts), 
              'rules:'+str(self.rules),
              'effect:'+str(self.effects),
              'joker_count:'+str(self.joker_counts), 
              'exchange_cards:'+str(self.exchange_cards),
              'game_count:'+str(self.games),
              'cards:'+str(self.cards),
              'cards_count:'+str(self.cards_counts))
        
    #ゲームスタート    
    def start(self):
        #クラス開始時のオブジェクトの初期化
        priority = 0
        games = 0
        break_game_loop = False
        #ゲームのループ/プロクレスバーの設置
        for i in tqdm(range(self.games)):
            #ゲーム開始時のオブジェクトの初期化および更新
            games += 1
            self.battle_record[games] = []
            self.battle_record2[games] = []
            dust_box = []
            priority = 0
            sets = 0 
            select_counts = 0
            break_turn_loop = False
            presence_11 = 0
            pass_dict = {}
            playing_counts = self.player_counts
            #状態(0:未パス未上がり,1:パス済,2:上がり済み)の初期化
            for i in range(self.player_counts):
                pass_dict[i] = 0
            #カードの分配
            hands = self.card_shuffle()
            #1ゲーム前の順位からのカードの交換処理(vs)
            if games > 1:
                if self.vs == 0:
                    hands = self.exchange(hands, games)
                else:
                    hands = self.exchange_vs(hands, games)
            #初期カードの記録
            for  i in range(self.player_counts):
                self.battle_record2[games].append(hands[i])
            #最初にカードを出す人の決定
            if games == 1:
                for i in range(self.player_counts):
                    if ('♦', 3) in hands[i]:
                        start_player = i
            else:
                #print(games-1, self.battle_record)
                start_player = self.battle_record[games-1][-1]
            count = start_player
            #セットのループ
            while True:
                #パス/捨て札のリセット/セットの更新
                sets += 1
                pass_counts = 0
                last_cards = ()
                winning_set = 0
                turn = 0
                tie = {'sym':set(), 'num':0}
                select_symnum_box = {'sym':[], 'num':[]}
                #順番処理
                if not count < self.player_counts:
                    count = select_counts + self.player_counts
                #ターン中のパスの有無の確認
                for i in range(self.player_counts):
                    if pass_dict[i] == 1:
                        pass_dict[i] = 0
                #環境処理
                if presence_11:
                    priority = (priority + presence_11) % 2
                    presence_11 = 0
                #手札の記録
                hands_copy = copy.deepcopy(hands)
                self.history.append({sets:hands_copy})
                #安全装置
                if sets > 100:
                    break_game_loop = True
                    break
                if break_turn_loop == True:
                    print(self.battle_record[games])
                    break
                #ターンのループ                
                while True:
                    select_player = count % self.player_counts
                    print('------\nplayer:{}, hands_num:{}, priority:{}, {}, \ncount:{}, pass_counts:{}, turn:{}, sets:{}, games:{}'\
                          .format(select_player, len(hands[select_player]), priority, tie, \
                                  count, pass_counts, turn, sets, games))
                    print(pass_dict)
                    print('last_cards:{}'.format(last_cards))
                    #ターン処理
                    if pass_counts >= playing_counts - 1 and not last_cards == ():    
                        print('go to next sets')
                        break
                    #ゲーム終了判断(勝利者が規定を満たした場合)
                    if self.player_counts - list(pass_dict.values()).count(2) == 1:
                        for i in range(self.player_counts):
                            if hands[i] and pass_dict[i] != 3:
                                self.battle_record[games].append(i)
                        for i in range(self.player_counts):
                            if pass_dict[i] == 3:
                                self.battle_record[games].append(i)
                        break_turn_loop = True
                        break
                    #ゲーム終了判断(カード選択不可によるループ状態)
                    if turn > 54:
                        for i in range(self.player_counts):
                            if hands[i] and pass_dict[i] != 3:
                                self.battle_record[games].append(i)
                                #print('--------------\nfinish winners:{}'.\
                                #format(self.battle_record[games]))
                        for i in range(self.player_counts):
                            if pass_dict[i] == 3:
                                self.battle_record[games].append(i)
                        break_turn_loop = True
                        break
                    #行動処理
                    if pass_dict[select_player] == 0:
                        #print('strategy:pattern' + str(strategy))
                        #戦略決定
                        strategy = self.decide_strategies(select_player)
                        #手札からカード組み合わせを返す
                        preselectable_cards_list = \
                        self.preselectable(hands[select_player], self.rules)
                        #捨て札から選択可能カードを返す
                        selectable_cards_list = self.selectable(\
                        preselectable_cards_list, last_cards, priority, self.rules, \
                            self.effects, select_player, hands, count, pass_dict, \
                            pass_counts, presence_11, strategy, dust_box, tie)
                        #選択可能組み合わせがなかったらパス：パスで一周したら最後に出した人から
                        #print('PRE:{} \nSE:{}'.format(preselectable_cards_list, selectable_cards_list))
                        if not selectable_cards_list:
                            count += 1
                            pass_counts += 1
                            pass_dict[select_player] = 1
                            print('pass')
                            continue
                        #カード選択(出せるカードを最大or最小、階段優先、革命優先)
                        if self.vs == 0:
                            select_cards = self.selection(selectable_cards_list, strategy)
                        else:
                            if select_player == 0:
                                print('hands:{}'.format(sorted(hands[select_player], key=lambda x:self.priority_dicts[0][x[1]])))
                                while True:
                                    select_cards_pre = input('player0! Select cards or pass![ex)♥,7/♠,7/0]:')
                                    select_cards = []
                                    if select_cards_pre != 'pass':
                                        for i in select_cards_pre[:-2].split('/'):
                                            select_symbol = i.split(',')[0]
                                            try:
                                                select_number = int(i.split(',')[1])
                                            except IndexError:
                                                print('ERROR:Your choice is inaccurate!')
                                                continue
                                            except ValueError:
                                                select_number = i.split(',')[1]
                                            select_cards.append((select_symbol, select_number))
                                        try:
                                            select_cards.append(int(select_cards_pre[-1]))
                                        except ValueError:
                                            continue
                                    print(select_cards)
                                    print(selectable_cards_list)
                                    if select_cards in selectable_cards_list \
                                        or select_cards_pre == 'pass':
                                        break
                                    else:
                                        print('ERROR:Your select cards is not in selectable cards!')
                                        continue
                                if select_cards_pre == 'pass':
                                    count += 1
                                    pass_counts += 1
                                    pass_dict[select_player] = 1
                                    print('pass')
                                    continue
                            else:
                                select_cards = self.selection(selectable_cards_list, strategy)
                        select_counts = copy.copy(count)    
                        #print('select player:' + str(select_player))
                        print('last_cards:{}, select cards:{}'.format(last_cards, select_cards))
                        #if select_cards[-1] == 1:
                            #print('STAIRS!!!')
                        
                        #縛り処理
                        converted_cards = self.convert(select_cards, priority)
                        select_cards_symbol = set(i[0] for i in converted_cards[:-1])
                        if not select_symnum_box['sym']:
                            select_symnum_box['sym'].append(select_cards_symbol)
                        else:
                            union = select_cards_symbol & select_symnum_box['sym'][-1]
                            if union:
                                if tie['sym']:
                                    if '?' in union:
                                        union.remove('?')
                                    tie['sym'] = tie['sym'].union(union)
                                    select_symnum_box['sym'].append(tie['sym'])
                                else:
                                    if '?' in union:
                                        union.remove('?')
                                    tie['sym'] = tie['sym'].union(union)
                            else:
                                select_symnum_box['sym'].append(select_cards_symbol)
                        select_cards_number = []
                        if select_cards[-1] == 0:
                            if select_cards[0][1] == 'J1' or select_cards[0][1] == 'J2':
                                se_num = 'J'
                            else:
                                se_num = select_cards[0][1]
                            for i in range(len(select_cards[:-1])):
                                select_cards_number.append(se_num)
                        elif select_cards[-1] == 1:
                            for i in converted_cards[:-1]:
                                select_cards_number.append(i[-1])
                        next_num = []
                        if select_symnum_box['num']:
                            if not 'J' in select_symnum_box['num'][-1]:
                                for i in select_symnum_box['num'][-1]:
                                    if priority == 0:
                                        next_num.append(i + len(select_symnum_box['num'][-1]))
                                    elif priority == 1:
                                        next_num.append(i - len(select_symnum_box['num'][-1]))
                            #print(select_cards_number,next_num)
                            if tie['sym']:
                                if tie['num']:
                                    tie['num'] = next_num
                                    select_symnum_box['num'].append(next_num)
                                elif not tie['num']:
                                    if next_num == select_cards_number:
                                        tie['num'] = select_cards_number
                                        select_symnum_box['num'].append(next_num)
                                    else:
                                        select_symnum_box['num'].append(select_cards_number)
                            else:
                                select_symnum_box['num'].append(select_cards_number)
                        else:
                            select_symnum_box['num'].append(select_cards_number)
                        #カード効果処理
                        if len(select_cards) >= 5:
                            priority = (priority + 1) % 2
                        if select_player == 0 and self.vs == 1:
                            (hands, count, priority, pass_dict, pass_counts, \
                             presence_11, dust_box) = self.effection_vs\
                            (select_player, hands, select_cards, count, priority, \
                             pass_dict, pass_counts, presence_11, strategy, \
                                 last_cards, dust_box)
                        else:
                            (hands, count, priority, pass_dict, pass_counts, \
                             presence_11, dust_box) = self.effection\
                            (select_player, hands, select_cards, count, priority, \
                             pass_dict, pass_counts, presence_11, strategy, \
                                 last_cards, dust_box)
                        #捨て札処理
                        dust_box = dust_box + select_cards[:-1] 
                        last_cards = select_cards
                        #勝ち抜け処理
                        print('hands:' + str(hands[select_player]))
                        if not hands[select_player]:
                            self.battle_record[games].append(select_player)
                            pass_dict[select_player] = 2
                            playing_counts -= 1
                            pass_counts = -1 + [pass_dict[i] for i in range(self.player_counts)].count(1)
                            winning_set += 1
                            print('winners:' + str(self.battle_record[games]))                        
                            if self.rules[2] == 1 and  games >= 2:
                                if pass_dict[self.battle_record[games-1][0]] <= 1:
                                    pass_dict[self.battle_record[games-1][0]] = 3
                                    playing_counts -= 1
                                    winning_set += 1
                                    print('city_fall:'*100 + str(self.battle_record[games-1][0]))      
                            #カード効果処理で勝利者が出た時の処理
                            for i in range(self.player_counts):
                                if not hands[i] and pass_dict[i] <= 1:
                                    self.battle_record[games].append(i)
                                    pass_dict[i] = 2
                                    playing_counts -= 1
                                    winning_set += 1
                            count += 1
                            continue
                        
                        #カード効果処理で勝利者が出た時の処理
                        for i in range(self.player_counts):
                            if not hands[i] and pass_dict[i] <= 1:
                                self.battle_record[games].append(i)
                                pass_dict[i] = 2
                                playing_counts -= 1
                                winning_set += 1
                                if self.rules[2] == 1 and  games >= 2:
                                    if pass_dict[self.battle_record[games-1][0]] <= 1:
                                        pass_dict[self.battle_record[games-1][0]] = 3
                                        playing_counts -= 1
                                        winning_set += 1
                                        print('city_fall:'*100 + str(self.battle_record[games-1][0]))  
                        #勝利者が出た時のパスターン処理
                        if winning_set:
                            pass_counts += 1
                            winning_set -= 1
                        count += 1
                    elif pass_dict[select_player] == 1:
                        print('passed')
                        count += 1
                    elif pass_dict[select_player] == 2:
                        print('winned')
                        count += 1
                    elif pass_dict[select_player] == 3:
                        print('falled')
                        count += 1
                    turn += 1
            if break_game_loop == True:
                print('SETS ERROR!!')
                break
        #戦績を返す
        record = self.recorder()
        record_list = []
        #図示
        self.show_record()
        #データ解析
        for i in range(self.player_counts):
            record[i] = sum(record[i])/len(record[i])
        for i in range(self.player_counts):
            record_list.append(record[i])
        player0_rank_AVE = record[0]
        rank_SD = stdev(record_list)
        AVE = mean(range(self.player_counts)) + 1
        
        return print('\n[RESULT]player0(AVE)/AVE:{:.3f}/{:.3f}, SD:{:.3f}'.\
                     format(player0_rank_AVE, AVE, rank_SD))
    
    #手札からカード組み合わせのリストを返す   
    def preselectable(self, hands_cards, rules):
        if rules[0] == 0:
            #手札から出せる組み合わせ
            one_cards = []
            two_cards = []
            three_cards = []
            four_cards = []
            five_cards = []
            six_cards = []
            
            #手札にジョーカーが一枚もない場合
            if not ('J1', 'J1') in hands_cards and not ('J2', 'J2') in hands_cards: 
                #一枚組
                for i in hands_cards:
                    one_cards.append([i])
                #二枚組
                for i in hands_cards:
                    for i2 in hands_cards:
                        if i[1] == i2[1] and not i == i2:
                            two_cards.append([i, i2])
                #三枚組
                for i in two_cards:
                    for i2 in hands_cards:
                        if i[0][1] == i2[1] and not i2 in i:
                            i = i.copy()
                            i.append(i2)
                            three_cards.append(i)
                #四枚組
                for i in range(1,14):
                    number_cards = []
                    for i2 in hands_cards:
                        if i2[1] == i:
                            number_cards.append(i2)
                            if len(number_cards) == 4:
                                four_cards.append(number_cards)
            #手札にジョーカーが一枚ある場合('J1', 'J1')
            elif ('J1', 'J1') in hands_cards and not ('J2', 'J2') in hands_cards:
                #一枚組
                for i in hands_cards:
                    one_cards.append([i])
                one_cards.append([('J1', 'J1')])
                #二枚組
                for i in hands_cards:
                    if not ('J1', 'J1') == i:
                        two_cards.append([i, ('J1', 'J1')])
                for i in hands_cards:
                    for i2 in hands_cards:
                        if i[1] == i2[1] and not i == i2:
                            two_cards.append([i, i2])
                #三枚組
                for i in two_cards:
                    for i2 in hands_cards:
                        if i[0][1] == i2[1] and not i2 in i:
                            i = i.copy()
                            i.append(i2)
                            three_cards.append(i)
                for i in hands_cards:
                    for i2 in hands_cards:
                        if i[1] == i2[1] and not i == i2:
                            if not ('J1', 'J1') in [i, i2]:
                                three_cards.append([i, i2, ('J1', 'J1')])
                #四枚組
                for i in range(1,14):
                    number_cards = []
                    for i2 in hands_cards:
                        if i2[1] == i:
                            number_cards.append(i2)
                            if len(number_cards) == 4:
                                four_cards.append(number_cards)
                for i in two_cards:
                    for i2 in hands_cards:
                        if i[0][1] == i2[1] and not i2 in i:
                            i.append(i2)
                            i.append(('J1', 'J1'))
                            four_cards.append(i)
                #五枚組
                for i in four_cards:
                    if not ('J1', 'J1') in i:
                        i.append(('J1', 'J1'))
                        five_cards.append(i)
            #手札にジョーカーが一枚ある場合('J2', 'J2')
            elif ('J2', 'J2') in hands_cards and not ('J1', 'J1') in hands_cards:
                #一枚組
                for i in hands_cards:
                    one_cards.append([i])
                one_cards.append([('J2', 'J2')])
                #二枚組
                for i in hands_cards:
                    if not ('J2', 'J2') == i:
                        two_cards.append([i, ('J2', 'J2')])
                for i in hands_cards:
                    for i2 in hands_cards:
                        if i[1] == i2[1] and not i == i2:
                            two_cards.append([i, i2])
                #三枚組
                for i in two_cards:
                    for i2 in hands_cards:
                        if i[0][1] == i2[1] and not i2 in i:
                            i = i.copy()
                            i.append(i2)
                            three_cards.append(i)
                for i in hands_cards:
                    for i2 in hands_cards:
                        if i[1] == i2[1] and not i2 in i:
                            if not ('J2', 'J2') in [i,i2]:
                                three_cards.append([i, i2, ('J2', 'J2')])
                #四枚組
                for i in range(1,14):
                    number_cards = []
                    for i2 in hands_cards:
                        if i2[1] == i:
                            number_cards.append(i2)
                            if len(number_cards) == 4:
                                four_cards.append(number_cards)
                for i in two_cards:
                    for i2 in hands_cards:
                        if i[0][1] == i2[1] and not i2 in i:
                            i = i.copy()
                            i.append(i2)
                            i.append(('J2', 'J2'))
                            four_cards.append(i)
                #五枚組
                for i in four_cards:
                    if not ('J2', 'J2') in i:
                        i.append(('J2', 'J2'))
                        five_cards.append(i)
            #手札にジョーカーが二枚ある場合
            elif ('J1', 'J1') in hands_cards and ('J2', 'J2') in hands_cards: 
                #一枚組
                for i in hands_cards:
                    one_cards.append([i])
                one_cards.append([('J1', 'J1')])
                one_cards.append([('J2', 'J2')])
                #二枚組
                for i in hands_cards:
                    if not ('J1', 'J1') == i:
                        two_cards.append([i, ('J1', 'J1')])
                for i in hands_cards:
                    if not ('J2', 'J2') == i:
                        two_cards.append([i, ('J2', 'J2')])
                for i in hands_cards:
                    for i2 in hands_cards:
                        if i[1] == i2[1] and not i == i2:
                            two_cards.append([i, i2])
                #三枚組#
                for i in two_cards:
                    for i2 in hands_cards:
                        if i[0][1] == i2[1] and not i2 in i:
                            i = i.copy()
                            i.append(i2)
                            three_cards.append(i)
                for i in hands_cards:
                    for i2 in hands_cards:
                        if i[1] == i2[1] and not i == i2:
                            if not ('J1', 'J1') in [i,i2]:
                                three_cards.append([i, i2, ('J1', 'J1')])
                for i in hands_cards:
                    for i2 in hands_cards:
                        if i[1] == i2[1] and not i == i2:
                            if not ('J2', 'J2') in [i,i2]:
                                three_cards.append([i, i2, ('J2', 'J2')])
                #四枚組
                for i in range(1,14):
                    number_cards = []
                    for i2 in hands_cards:
                        if i2[1] == i:
                            number_cards.append(i2)
                            if len(number_cards) == 4:
                                four_cards.append(number_cards)
                for i in two_cards:
                    for i2 in hands_cards:
                        if i[0][1] == i2[1] and not i2 in i:
                            i = i.copy()
                            i.append(i2)
                            i.append(('J1', 'J1'))
                            four_cards.append(i)
                for i in two_cards:
                    for i2 in hands_cards:
                        if i[0][1] == i2[1] and not i2 in i:
                            i = i.copy()
                            i.append(i2)
                            i.append(('J2', 'J2'))
                            four_cards.append(i)
                #五枚組
                for i in four_cards:
                    if not ('J1', 'J1') in i:
                        i = i.copy()
                        i.append(('J1', 'J1'))
                        five_cards.append(i)
                for i in four_cards:
                    if not ('J2', 'J2') in i:
                        i = i.copy()
                        i.append(('J2', 'J2'))
                        five_cards.append(i)
                #六枚組
                for i in five_cards:
                    if not ('J1', 'J1') in i:
                        i = i.copy()
                        i.append(('J1', 'J1'))
                        six_cards.append(i)
                for i in five_cards:
                    if not ('J2', 'J2') in i:
                        i = i.copy()
                        i.append(('J2', 'J2'))
                        six_cards.append(i)
            #枚数以上の除外(例：one_cardsは一枚組以外除外)
            one_cards_copy = one_cards.copy()
            for i in one_cards_copy:
                if not len(i) == 1:
                    one_cards.remove(i)
            two_cards_copy = two_cards.copy()
            for i in two_cards_copy:
                if not len(i) == 2:
                    two_cards.remove(i)
            three_cards_copy = three_cards.copy()
            for i in three_cards_copy:
                if not len(i) == 3:
                    three_cards.remove(i)
            four_cards_copy = four_cards.copy()
            for i in four_cards_copy:
                if not len(i) == 4:
                    four_cards.remove(i)
            five_cards_copy = five_cards.copy()
            for i in five_cards_copy:
                if not len(i) == 5:
                    five_cards.remove(i)
            six_cards_copy = six_cards.copy()
            for i in six_cards_copy:
                if not len(i) == 6:
                    six_cards.remove(i)
            #選択可能組み合わせの重複除外
            preselectable_cards_list = []
            preselect_cards_list = one_cards + two_cards + three_cards + \
                                  four_cards + five_cards + six_cards
            for i in preselect_cards_list:
                prelist = list(set(i))
                prelist = sorted(prelist, key=lambda x:self.priority_dicts[0][x[1]]) 
                if not prelist + [0] in preselectable_cards_list:
                    preselectable_cards_list.append(prelist + [0])
            return preselectable_cards_list
              
        elif rules[0] == 1:
            #手札から出せる組み合わせ
            one_cards = []
            two_cards = []
            three_cards = []
            three_cards_stairs = []
            four_cards = []
            four_cards_stairs = []
            five_cards = []
            five_cards_stairs = []
            six_cards = []
            six_cards_stairs = []
            seven_over_cards = []
            seven_over_cards_stairs = []
            new_hands_cards = []
            for i in hands_cards:
                new_hands_cards.append((i[0], self.priority_dicts[0][i[1]]))
            #手札にジョーカーが一枚もない場合
            if not ('J1', 'J1') in hands_cards and not ('J2', 'J2') in hands_cards: 
                #一枚組
                for i in hands_cards:
                    one_cards.append([i])
                #二枚組
                for i in hands_cards:
                    for i2 in hands_cards:
                        if i[1] == i2[1] and not i == i2:
                            two_cards.append([i, i2])
                #三枚組
                for i in two_cards:
                    for i2 in hands_cards:
                        if i[0][1] == i2[1] and not i2 in i:
                            i = i.copy()
                            i.append(i2)
                            three_cards.append(i)
                #四枚組
                for i in range(1,14):
                    number_cards = []
                    for i2 in hands_cards:
                        if i2[1] == i:
                            number_cards.append(i2)
                            if len(number_cards) == 4:
                                four_cards.append(number_cards)
                #階段
                for i in hands_cards:
                    i_list = [i]
                    i_next = (i[0], self.priority_dicts[0][i[1]]+1)
                    while i_next in new_hands_cards:
                        i_next_index = new_hands_cards.index(i_next)
                        i_list.append(hands_cards[i_next_index])
                        i_next = (i_list[-1][0], self.priority_dicts[0][i_list[-1][1]]+1)
                        if len(i_list) == 3:
                            three_cards_stairs.append(i_list)
                        elif len(i_list) == 4:
                            four_cards_stairs.append(i_list)
                        elif len(i_list) == 5:
                            five_cards_stairs.append(i_list)
                        elif len(i_list) == 6:
                            six_cards_stairs.append(i_list)
                        elif len(i_list) > 6:
                            seven_over_cards_stairs.append(i_list)
            #手札にジョーカーが一枚ある場合('J1', 'J1')
            elif ('J1', 'J1') in hands_cards and not ('J2', 'J2') in hands_cards:
                #一枚組
                for i in hands_cards:
                    one_cards.append([i])
                one_cards.append([('J1', 'J1')])
                #二枚組
                for i in hands_cards:
                    if not ('J1', 'J1') == i:
                        two_cards.append([i, ('J1', 'J1')])
                for i in hands_cards:
                    for i2 in hands_cards:
                        if i[1] == i2[1] and not i == i2:
                            two_cards.append([i, i2])
                #三枚組
                for i in two_cards:
                    for i2 in hands_cards:
                        if i[0][1] == i2[1] and not i2 in i:
                            i = i.copy()
                            i.append(i2)
                            three_cards.append(i)
                for i in hands_cards:
                    for i2 in hands_cards:
                        if i[1] == i2[1] and not i == i2:
                            if not ('J1', 'J1') in [i, i2]:
                                three_cards.append([i, i2, ('J1', 'J1')])
                
                #四枚組
                for i in range(1,14):
                    number_cards = []
                    for i2 in hands_cards:
                        if i2[1] == i:
                            number_cards.append(i2)
                            if len(number_cards) == 4:
                                four_cards.append(number_cards)
                for i in two_cards:
                    for i2 in hands_cards:
                        if i[0][1] == i2[1] and not i2 in i:
                            i.append(i2)
                            i.append(('J1', 'J1'))
                            four_cards.append(i)
                #五枚組
                for i in four_cards:
                    if not ('J1', 'J1') in i:
                        i.append(('J1', 'J1'))
                        five_cards.append(i)
                #階段
                for i in hands_cards:
                    i_list = [i]
                    i_next = (i[0], self.priority_dicts[0][i[1]]+1)
                    while i_next in new_hands_cards:
                        i_next_index = new_hands_cards.index(i_next)
                        i_list.append(hands_cards[i_next_index])
                        i_next = (i_list[-1][0], self.priority_dicts[0][i_list[-1][1]]+1)
                        if len(i_list) == 3:
                            three_cards_stairs.append(i_list)
                        elif len(i_list) == 4:
                            four_cards_stairs.append(i_list)
                        elif len(i_list) == 5:
                            five_cards_stairs.append(i_list)
                        elif len(i_list) == 6:
                            six_cards_stairs.append(i_list)
                        elif len(i_list) > 6:
                            seven_over_cards_stairs.append(i_list)
                for i in hands_cards:
                    i_list = [i]
                    i_next = (i[0], self.priority_dicts[0][i[1]]+1)
                    while i_next in new_hands_cards:
                        i_next_index = new_hands_cards.index(i_next)
                        i_list.append(hands_cards[i_next_index])
                        i_next = (i_list[-1][0], self.priority_dicts[0][i_list[-1][1]]+1)
                        if len(i_list) == 2:
                            three_cards_stairs.append(i_list + [('J1', 'J1')])
                            three_cards_stairs.append([('J1', 'J1')] + i_list)
                        elif len(i_list) == 3:
                            four_cards_stairs.append(i_list + [('J1', 'J1')])
                            four_cards_stairs.append([('J1', 'J1')] + i_list)
                        elif len(i_list) == 4:
                            five_cards_stairs.append(i_list + [('J1', 'J1')])
                            five_cards_stairs.append([('J1', 'J1')] + i_list)
                        elif len(i_list) == 5:
                            six_cards_stairs.append(i_list + [('J1', 'J1')])
                            six_cards_stairs.append([('J1', 'J1')] + i_list)
                        elif len(i_list) > 5:
                            seven_over_cards_stairs.append(i_list + [('J1', 'J1')])
                            seven_over_cards_stairs.append([('J1', 'J1')] + i_list)
                for i in hands_cards:
                    i_list = [i]
                    i_next_2 = (i[0], self.priority_dicts[0][i[1]]+2)
                    hands_cards_removed = hands_cards.copy()
                    hands_cards_removed.remove(i)
                    if i_next_2 in new_hands_cards:
                        i_next_2_index = new_hands_cards.index(i_next_2)
                        i_list.append(('J1', 'J1'))
                        i_list.append(hands_cards[i_next_2_index])
                        i_next = (i_list[-1][0], self.priority_dicts[0][i_list[-1][1]]+1)
                        i_previous = (i_list[0][0], self.priority_dicts[0][i_list[0][1]]-1)
                        while i_next in new_hands_cards:
                            i_next_index = new_hands_cards.index(i_next)
                            i_list.append(hands_cards[i_next_index])
                            i_next = (i_list[-1][0], self.priority_dicts[0][i_list[-1][1]]+1)
                        while i_previous in new_hands_cards:
                            i_previous_index = new_hands_cards.index(i_previous)
                            i_list = [hands_cards[i_previous_index]] + i_list
                            i_previous = (i_list[0][0], self.priority_dicts[0][i_list[0][1]]-1)
                        if len(i_list) >= 3:
                            for i2 in range(len(i_list)-2):
                                three_cards_stairs.append(i_list[i2:i2+3])
                        elif len(i_list) >= 4:
                            for i2 in range(len(i_list)-3):
                                four_cards_stairs.append(i_list[i2:i2+4])
                        elif len(i_list) >= 5:
                            for i2 in range(len(i_list)-4):
                                five_cards_stairs.append(i_list[i2:i2+5])
                        elif len(i_list) >= 6:
                            for i2 in range(len(i_list)-5):
                                six_cards_stairs.append(i_list[i2:i2+6])
                        elif len(i_list) > 6:
                            for i2 in range(7, len(i_list)):
                                for i3 in range(len(i_list)-i2):
                                    seven_over_cards_stairs.append(i_list[i3:i3+i2])
            #手札にジョーカーが一枚ある場合('J2', 'J2')
            elif ('J2', 'J2') in hands_cards and not ('J1', 'J1') in hands_cards:
                #一枚組
                for i in hands_cards:
                    one_cards.append([i])
                one_cards.append([('J2', 'J2')])
                #二枚組
                for i in hands_cards:
                    if not ('J2', 'J2') == i:
                        two_cards.append([i, ('J2', 'J2')])
                for i in hands_cards:
                    for i2 in hands_cards:
                        if i[1] == i2[1] and not i == i2:
                            two_cards.append([i, i2])
                #三枚組
                for i in two_cards:
                    for i2 in hands_cards:
                        if i[0][1] == i2[1] and not i2 in i:
                            i = i.copy()
                            i.append(i2)
                            three_cards.append(i)
                for i in hands_cards:
                    for i2 in hands_cards:
                        if i[1] == i2[1] and not i2 in i:
                            if not ('J2', 'J2') in [i,i2]:
                                three_cards.append([i, i2, ('J2', 'J2')])
                #四枚組
                for i in range(1,14):
                    number_cards = []
                    for i2 in hands_cards:
                        if i2[1] == i:
                            number_cards.append(i2)
                            if len(number_cards) == 4:
                                four_cards.append(number_cards)
                for i in two_cards:
                    for i2 in hands_cards:
                        if i[0][1] == i2[1] and not i2 in i:
                            i = i.copy()
                            i.append(i2)
                            i.append(('J2', 'J2'))
                            four_cards.append(i)
                #五枚組
                for i in four_cards:
                    if not ('J2', 'J2') in i:
                        i.append(('J2', 'J2'))
                        five_cards.append(i)
                #階段
                for i in hands_cards:
                    i_list = [i]
                    i_next = (i[0], self.priority_dicts[0][i[1]]+1)
                    while i_next in new_hands_cards:
                        i_next_index = new_hands_cards.index(i_next)
                        i_list.append(hands_cards[i_next_index])
                        i_next = (i_list[-1][0], self.priority_dicts[0][i_list[-1][1]]+1)
                        if len(i_list) == 3:
                            three_cards_stairs.append(i_list)
                        elif len(i_list) == 4:
                            four_cards_stairs.append(i_list)
                        elif len(i_list) == 5:
                            five_cards_stairs.append(i_list)
                        elif len(i_list) == 6:
                            six_cards_stairs.append(i_list)
                        elif len(i_list) > 6:
                            seven_over_cards_stairs.append(i_list)
                for i in hands_cards:
                    i_list = [i]
                    i_next = (i[0], self.priority_dicts[0][i[1]]+1)
                    while i_next in new_hands_cards:
                        i_next_index = new_hands_cards.index(i_next)
                        i_list.append(hands_cards[i_next_index])
                        i_next = (i_list[-1][0], self.priority_dicts[0][i_list[-1][1]]+1)
                        if len(i_list) == 2:
                            three_cards_stairs.append(i_list + [('J2', 'J2')])
                            three_cards_stairs.append([('J2', 'J2')] + i_list)
                        elif len(i_list) == 3:
                            four_cards_stairs.append(i_list + [('J2', 'J2')])
                            four_cards_stairs.append([('J2', 'J2')] + i_list)
                        elif len(i_list) == 4:
                            five_cards_stairs.append(i_list + [('J2', 'J2')])
                            five_cards_stairs.append([('J2', 'J2')] + i_list)
                        elif len(i_list) == 5:
                            six_cards_stairs.append(i_list + [('J2', 'J2')])
                            six_cards_stairs.append([('J2', 'J2')] + i_list)
                        elif len(i_list) > 5:
                            seven_over_cards_stairs.append(i_list + [('J2', 'J2')])
                            seven_over_cards_stairs.append([('J2', 'J2')] + i_list)
                for i in hands_cards:
                    i_list = [i]
                    i_next_2 = (i[0], self.priority_dicts[0][i[1]]+2)
                    hands_cards_removed = hands_cards.copy()
                    hands_cards_removed.remove(i)
                    if i_next_2 in new_hands_cards:
                        i_next_2_index = new_hands_cards.index(i_next_2)
                        i_list.append(('J2', 'J2'))
                        i_list.append(hands_cards[i_next_2_index])
                        i_next = (i_list[-1][0], self.priority_dicts[0][i_list[-1][1]]+1)
                        i_previous = (i_list[0][0], self.priority_dicts[0][i_list[0][1]]-1)
                        while i_next in new_hands_cards:
                            i_next_index = new_hands_cards.index(i_next)
                            i_list.append(hands_cards[i_next_index])
                            i_next = (i_list[-1][0], self.priority_dicts[0][i_list[-1][1]]+1)
                        while i_previous in new_hands_cards:
                            i_previous_index = new_hands_cards.index(i_previous)
                            i_list = [hands_cards[i_previous_index]] + i_list
                            i_previous = (i_list[0][0], self.priority_dicts[0][i_list[0][1]]-1)
                        if len(i_list) >= 3:
                            for i2 in range(len(i_list)-2):
                                three_cards_stairs.append(i_list[i2:i2+3])
                        elif len(i_list) >= 4:
                            for i2 in range(len(i_list)-3):
                                four_cards_stairs.append(i_list[i2:i2+4])
                        elif len(i_list) >= 5:
                            for i2 in range(len(i_list)-4):
                                five_cards_stairs.append(i_list[i2:i2+5])
                        elif len(i_list) >= 6:
                            for i2 in range(len(i_list)-5):
                                six_cards_stairs.append(i_list[i2:i2+6])
                        elif len(i_list) > 6:
                            for i2 in range(7, len(i_list)):
                                for i3 in range(len(i_list)-i2):
                                    seven_over_cards_stairs.append(i_list[i3:i3+i2])
            #手札にジョーカーが二枚ある場合
            elif ('J1', 'J1') in hands_cards and ('J2', 'J2') in hands_cards: 
                #一枚組
                for i in hands_cards:
                    one_cards.append([i])
                one_cards.append([('J1', 'J1')])
                one_cards.append([('J2', 'J2')])
                #二枚組
                for i in hands_cards:
                    if not ('J1', 'J1') == i:
                        two_cards.append([i, ('J1', 'J1')])
                for i in hands_cards:
                    for i2 in hands_cards:
                        if i[1] == i2[1] and not i == i2:
                            two_cards.append([i, i2])
                two_cards.append([('J1', 'J1'), ('J2', 'J2')])
                #三枚組
                for i in two_cards:
                    for i2 in hands_cards:
                        if i[0][1] == i2[1] and not i2 in i:
                            i = i.copy()
                            i.append(i2)
                            three_cards.append(i)
                for i in hands_cards:
                    for i2 in hands_cards:
                        if i[1] == i2[1] and not i == i2:
                            if not ('J1', 'J1') in [i,i2]:
                                three_cards.append([i, i2, ('J1', 'J1')])
                    if ('J1', 'J1') != i and ('J2', 'J2') != i:
                        three_cards.append([i, ('J1', 'J1'), ('J2', 'J2')])
                #四枚組
                for i in range(1,14):
                    number_cards = []
                    for i2 in hands_cards:
                        if i2[1] == i:
                            number_cards.append(i2)
                            if len(number_cards) == 4:
                                four_cards.append(number_cards)
                for i in two_cards:
                    for i2 in hands_cards:
                        if i[0][1] == i2[1] and not i2 in i:
                            i = i.copy()
                            i.append(i2)
                            i.append(('J1', 'J1'))
                            four_cards.append(i)
                    if not ('J1', 'J1') in i and not ('J2', 'J2') in i:
                        four_cards.append(i + [('J1', 'J1'), ('J2', 'J2')])
                #五枚組
                for i in four_cards:
                    if not ('J1', 'J1') in i and not ('J2', 'J2') in i:
                        i = i.copy()
                        i.append(('J1', 'J1'))
                        five_cards.append(i)
                #六枚組
                for i in five_cards:
                    if not ('J1', 'J1') in i:
                        i = i.copy()
                        i.append(('J1', 'J1'))
                        six_cards.append(i)
                #階段
                #[1,2,3]
                for i in hands_cards:
                    i_list = [i]
                    i_next = (i[0], self.priority_dicts[0][i[1]]+1)
                    while i_next in new_hands_cards:
                        i_next_index = new_hands_cards.index(i_next)
                        i_list.append(hands_cards[i_next_index])
                        i_next = (i_list[-1][0], self.priority_dicts[0][i_list[-1][1]]+1)
                        if len(i_list) == 3:
                            three_cards_stairs.append(i_list)
                        elif len(i_list) == 4:
                            four_cards_stairs.append(i_list)
                        elif len(i_list) == 5:
                            five_cards_stairs.append(i_list)
                        elif len(i_list) == 6:
                            six_cards_stairs.append(i_list)
                        elif len(i_list) > 6:
                            seven_over_cards_stairs.append(i_list)
                #[1,2,j],[1,2,j,j]
                for i in hands_cards:
                    i_list = [i]
                    i_next = (i[0], self.priority_dicts[0][i[1]]+1)
                    while i_next in new_hands_cards:
                        i_next_index = new_hands_cards.index(i_next)
                        i_list.append(hands_cards[i_next_index])
                        i_next = (i_list[-1][0], self.priority_dicts[0][i_list[-1][1]]+1)
                        if len(i_list) == 2:
                            three_cards_stairs.append(i_list + [('J1', 'J1')])
                            three_cards_stairs.append([('J1', 'J1')] + i_list)
                            four_cards_stairs.append(i_list + [('J1', 'J1'),('J2', 'J2')])
                            four_cards_stairs.append([('J1', 'J1'),('J2', 'J2')] + i_list)
                            four_cards_stairs.append([('J1', 'J1')] + i_list + [('J2', 'J2')])
                        elif len(i_list) == 3:
                            four_cards_stairs.append(i_list + [('J1', 'J1')])
                            four_cards_stairs.append([('J1', 'J1')] + i_list)
                            five_cards_stairs.append(i_list + [('J1', 'J1'),('J2', 'J2')])
                            five_cards_stairs.append([('J1', 'J1'),('J2', 'J2')] + i_list)
                            five_cards_stairs.append([('J1', 'J1')] + i_list + [('J2', 'J2')])
                        elif len(i_list) == 4:
                            five_cards_stairs.append(i_list + [('J1', 'J1')])
                            five_cards_stairs.append([('J1', 'J1')] + i_list)
                            six_cards_stairs.append(i_list + [('J1', 'J1'),('J2', 'J2')])
                            six_cards_stairs.append([('J1', 'J1'),('J2', 'J2')] + i_list)
                            six_cards_stairs.append([('J1', 'J1')] + i_list + [('J2', 'J2')])
                        elif len(i_list) == 5:
                            six_cards_stairs.append(i_list + [('J1', 'J1')])
                            six_cards_stairs.append([('J1', 'J1')] + i_list)
                            seven_over_cards_stairs.append(i_list + [('J1', 'J1'),('J2', 'J2')])
                            seven_over_cards_stairs.append([('J1', 'J1'),('J2', 'J2')] + i_list)
                            seven_over_cards_stairs.append([('J1', 'J1')] + i_list + [('J2', 'J2')])
                        elif len(i_list) > 5:
                            seven_over_cards_stairs.append(i_list + [('J1', 'J1')])
                            seven_over_cards_stairs.append([('J1', 'J1')] + i_list)
                            seven_over_cards_stairs.append(i_list + [('J1', 'J1'),('J2', 'J2')])
                            seven_over_cards_stairs.append([('J1', 'J1'),('J2', 'J2')] + i_list)
                            seven_over_cards_stairs.append([('J1', 'J1')] + i_list + [('J2', 'J2')])
                #[1,j,3,4]
                for i in hands_cards:
                    i_list = [i]
                    i_next_2 = (i[0], self.priority_dicts[0][i[1]]+2)
                    hands_cards_removed = hands_cards.copy()
                    hands_cards_removed.remove(i)
                    if i_next_2 in new_hands_cards:
                        i_next_2_index = new_hands_cards.index(i_next_2)
                        i_list.append(('J1', 'J1'))
                        i_list.append(hands_cards[i_next_2_index])
                        i_next = (i_list[-1][0], self.priority_dicts[0][i_list[-1][1]]+1)
                        i_previous = (i_list[0][0], self.priority_dicts[0][i_list[0][1]]-1)
                        while i_next in new_hands_cards:
                            i_next_index = new_hands_cards.index(i_next)
                            i_list.append(hands_cards[i_next_index])
                            i_next = (i_list[-1][0], self.priority_dicts[0][i_list[-1][1]]+1)
                        while i_previous in new_hands_cards:
                            i_previous_index = new_hands_cards.index(i_previous)
                            i_list = [hands_cards[i_previous_index]] + i_list
                            i_previous = (i_list[0][0], self.priority_dicts[0][i_list[0][1]]-1)
                        if len(i_list) >= 3:
                            for i2 in range(len(i_list)-2):
                                three_cards_stairs.append(i_list[i2:i2+3])
                                four_cards_stairs.append(i_list[i2:i2+3] + [('J2', 'J2')])
                                four_cards_stairs.append([('J2', 'J2')] + i_list[i2:i2+3])
                        elif len(i_list) >= 4:
                            for i2 in range(len(i_list)-3):
                                four_cards_stairs.append(i_list[i2:i2+4])
                                five_cards_stairs.append(i_list[i2:i2+4] + [('J2', 'J2')])
                                five_cards_stairs.append([('J2', 'J2')] + i_list[i2:i2+4])
                        elif len(i_list) >= 5:
                            for i2 in range(len(i_list)-4):
                                five_cards_stairs.append(i_list[i2:i2+5])
                                six_cards_stairs.append(i_list[i2:i2+5] + [('J2', 'J2')])
                                six_cards_stairs.append([('J2', 'J2')] + i_list[i2:i2+5])
                        elif len(i_list) >= 6:
                            for i2 in range(len(i_list)-5):
                                six_cards.append(i_list[i2:i2+6])
                                seven_over_cards_stairs.append(i_list[i2:i2+6])
                                seven_over_cards_stairs.append(i_list[i2:i2+6] + [('J2', 'J2')])
                                seven_over_cards_stairs.append([('J2', 'J2')] + i_list[i2:i2+6])
                        elif len(i_list) > 6:
                            for i2 in range(7, len(i_list)):
                                for i3 in range(len(i_list)-i2):
                                    seven_over_cards_stairs.append(i_list[i3:i3+i2])
                                    seven_over_cards_stairs.append(i_list[i3:i3:i2] + [('J2', 'J2')])
                                    seven_over_cards_stairs.append([('J2', 'J2')] + i_list[i3:i3:i2])
                #[1,j,3,j,5]        
                for i in hands_cards:
                    i_list = [i]
                    i_next_2 = (i[0], self.priority_dicts[0][i[1]]+2)
                    hands_cards_removed = hands_cards.copy()
                    hands_cards_removed.remove(i)
                    if i_next_2 in new_hands_cards:
                        i_next_2_index = new_hands_cards.index(i_next_2)
                        i_list.append(('J1', 'J1'))
                        i_list.append(hands_cards[i_next_2_index])
                        i_next = (i_list[-1][0], self.priority_dicts[0][i_list[-1][1]]+1)        
                        for i2 in hands_cards_removed:
                            if i2[0] == i[0]:
                                i2_next_2 = (i2[0], self.priority_dicts[0][i2[1]]+2)
                                hands_cards_removed_2 = hands_cards.copy()
                                hands_cards_removed_2.remove(i2)
                                if i2_next_2 in new_hands_cards:
                                    if self.priority_dicts[0][i[1]]+2 == self.priority_dicts[0][i2[1]]:  
                                        i_list.append(('J2', 'J2'))
                                        i2_next_2_index = new_hands_cards.index(i2_next_2)
                                        i_list.append(hands_cards[i2_next_2_index])
                                    elif self.priority_dicts[0][i[1]]+3 == self.priority_dicts[0][i2[1]]:  
                                        i_list.append(i2)
                                        i_list.append(('J2', 'J2'))
                                        i2_next_2_index = new_hands_cards.index(i2_next_2)
                                        i_list.append(hands_cards[i2_next_2_index])
                                    elif self.priority_dicts[0][i[1]]+3 < self.priority_dicts[0][i2[1]]:    
                                        between_exist = []
                                        mini_count = 3
                                        for i3 in range(self.priority_dicts[0][i[1]]+3, self.priority_dicts[0][i2[1]]):
                                            between_card = (i[0], i3)
                                            between_exist.append(between_card in new_hands_cards)
                                            i_list.append((i[0], i[1] + mini_count))
                                            mini_count += 1
                                        if all(between_exist):
                                            i_list.append(i2)
                                            i_list.append(('J2', 'J2'))
                                            i2_next_2_index = new_hands_cards.index(i2_next_2)
                                            i_list.append(hands_cards[i2_next_2_index])
                                            i_next = (i_list[-1][0], self.priority_dicts[0][i_list[-1][1]]+1)
                                            i_previous = (i_list[0][0], self.priority_dicts[0][i_list[0][1]]-1)
                                            while i_next in new_hands_cards:
                                                i_next_index = new_hands_cards.index(i_next)
                                                i_list.append(hands_cards[i_next_index])
                                                i_next = (i_list[-1][0], self.priority_dicts[0][i_list[-1][1]]+1)
                                            while i_previous in new_hands_cards:
                                                i_previous_index = new_hands_cards.index(i_previous)
                                                i_list = [hands_cards[i_previous_index]] + i_list
                                                i_previous = (i_list[0][0], self.priority_dicts[0][i_list[0][1]]-1)
                                            if len(i_list) >= 5:
                                                for i4 in range(len(i_list)-4):
                                                    five_cards_stairs.append(i_list[i4:i4+5])
                                            elif len(i_list) >= 6:
                                                for i4 in range(len(i_list)-5):
                                                    six_cards_stairs.append(i_list[i4:i4+6])
                                                    seven_over_cards_stairs.append(i_list[i4:i4+6])
                                            elif len(i_list) > 6:
                                                for i4 in range(7, len(i_list)):
                                                    for i5 in range(len(i_list)-i4):
                                                        seven_over_cards_stairs.append(i_list[i5:i5+i4])
                    #[1,j,j,4,5]
                    for i in hands_cards:
                        i_list = [i]
                        i_next_3 = (i[0], self.priority_dicts[0][i[1]]+3)
                        hands_cards_removed = hands_cards.copy()
                        hands_cards_removed.remove(i)
                        if i_next_3 in new_hands_cards:
                            i_next_3_index = new_hands_cards.index(i_next_3)
                            i_list.append(('J1', 'J1'))
                            i_list.append(('J2', 'J2'))
                            i_list.append(hands_cards[i_next_3_index])
                            i_next = (i_list[-1][0], self.priority_dicts[0][i_list[-1][1]]+1)
                            i_previous = (i_list[0][0], self.priority_dicts[0][i_list[0][1]]-1)
                            while i_next in new_hands_cards:
                                i_next_index = new_hands_cards.index(i_next)
                                i_list.append(hands_cards[i_next_index])
                                i_next = (i_list[-1][0], self.priority_dicts[0][i_list[-1][1]]+1)
                            while i_previous in new_hands_cards:
                                i_previous_index = new_hands_cards.index(i_previous)
                                i_list = [hands_cards[i_previous_index]] + i_list
                                i_previous = (i_list[0][0], self.priority_dicts[0][i_list[0][1]]-1)
                            if len(i_list) >= 4:
                                for i2 in range(len(i_list)-3):
                                    four_cards_stairs.append(i_list[i2:i2+4])
                            elif len(i_list) >= 5:
                                for i2 in range(len(i_list)-4):
                                    five_cards_stairs.append(i_list[i2:i2+5])
                            elif len(i_list) >= 6:
                                for i2 in range(len(i_list)-5):
                                    six_cards_stairs.append(i_list[i2:i2+6])
                            elif len(i_list) > 6:
                                for i2 in range(7, len(i_list)):
                                    for i3 in range(len(i_list)-i2):
                                        seven_over_cards_stairs.append(i_list[i3:i3+i2])       
            #枚数異常の除外(例：one_cardsは一枚組以外除外)
            one_cards_copy = one_cards.copy()
            for i in one_cards_copy:
                if not len(i) == 1:
                    one_cards.remove(i)
            two_cards_copy = two_cards.copy()
            for i in two_cards_copy:
                if not len(i) == 2:
                    two_cards.remove(i)
            three_cards_copy = three_cards.copy()
            for i in three_cards_copy:
                if not len(i) == 3:
                    three_cards.remove(i)
            four_cards_copy = four_cards.copy()
            for i in four_cards_copy:
                if not len(i) == 4:
                    four_cards.remove(i)
            five_cards_copy = five_cards.copy()
            for i in five_cards_copy:
                if not len(i) == 5:
                    five_cards.remove(i)
            six_cards_copy = six_cards.copy()
            for i in six_cards_copy:
                if not len(i) == 6:
                    six_cards.remove(i)
            #選択可能組み合わせの重複除外
            preselectable_cards_list = []
            preselect_cards_list = one_cards + two_cards + three_cards + \
                                  four_cards + five_cards + six_cards + \
                                  seven_over_cards
            for i in preselect_cards_list:
                prelist = list(set(i))
                prelist = sorted(prelist, key=lambda x:self.priority_dicts[0][x[1]]) 
                if not prelist + [0] in preselectable_cards_list:
                    preselectable_cards_list.append(prelist + [0])
            preselectable_cards_list_stairs = three_cards_stairs + \
                                              four_cards_stairs + \
                                              five_cards_stairs + \
                                              six_cards_stairs + \
                                              seven_over_cards_stairs
            for i in preselectable_cards_list_stairs:
                if not i + [1] in preselectable_cards_list:
                    preselectable_cards_list.append(i + [1]) 
            return preselectable_cards_list
    
    #カード組み合わせおよび捨て札からカード選択可能組み合わせのリストを返す 
    def selectable(self, preselectable_cards_list, last_cards, priority, rules,\
                   effects, select_player, hands, count, pass_dict, \
                       pass_counts, presence_11, strategy, dust_box, tie):
        preselectable_cards_list = copy.deepcopy(preselectable_cards_list)
        #階段なし・縛りなし
        if rules[:2] == [0, 0]:
            selectable_cards_list = []
            if len(last_cards) == 0:
                selectable_cards_list = preselectable_cards_list
            else:
                if [('J1', 'J1'), 0] == last_cards or [('J2', 'J2'), 0] == last_cards:
                    if [('♠', 3), 0] in preselectable_cards_list:
                        selectable_cards_list.append([('♠', 3), 0])
                for i in preselectable_cards_list:
                    if len(i) == len(last_cards):
                        select_num = self.priority_dicts[priority][i[0][1]]
                        last_num = self.priority_dicts[priority][last_cards[-2][1]]
                        if select_num > last_num:
                            selectable_cards_list.append(i)
        #階段あり・縛りなし
        elif rules[:2] == [1, 0]:
            selectable_cards_list = []
            if len(last_cards) == 0:
                selectable_cards_list = preselectable_cards_list
            else:
                if [('J1', 'J1'), 0] == last_cards or [('J2', 'J2'), 0] == last_cards:
                    if [('♠', 3), 0] in preselectable_cards_list:
                        selectable_cards_list.append([('♠', 3), 0])
                for i in preselectable_cards_list:
                    i_converted = self.convert(i, priority)
                    if priority == 0:
                        select_num = self.priority_dicts[priority][i_converted[0][1]]
                        last_num = self.priority_dicts[priority][last_cards[-2][1]]
                    elif priority == 1:
                        select_num = self.priority_dicts[priority][i_converted[-2][1]]
                        last_num = self.priority_dicts[priority][last_cards[0][1]]
                    if len(i) == len(last_cards) and select_num > last_num and last_cards[-1] == i[-1]:
                            selectable_cards_list.append(i)
                    
        #階段なし・縛りあり
        elif rules[:2] == [0, 1]:
            selectable_cards_list = []
            if len(last_cards) == 0:
                selectable_cards_list = preselectable_cards_list
            else:
                if [('J1', 'J1'), 0] == last_cards or [('J2', 'J2'), 0] == last_cards:
                    if [('♠', 3), 0] in preselectable_cards_list:
                        selectable_cards_list.append([('♠', 3), 0])
                for i in preselectable_cards_list:
                    i_converted = self.convert(i, priority)
                    select_num = self.priority_dicts[priority][i_converted[0][1]]
                    last_num = self.priority_dicts[priority][last_cards[-2][1]]
                    select_cards_sym = set(i2[0] for i2 in i_converted[:-1])
                    cards_number = []
                    unions = select_cards_sym & tie['sym']
                    j_num = i.count(('J1', 'J1')) + i.count(('J2', 'J2'))
                    if i[0][1] == 'J1' or i[0][1] == 'J2':
                        sem_num = 'J'
                        for i2 in range(len(i[:-1])):
                            cards_number.append(sem_num)
                    else:
                        sem_num = i[0][1]
                        for i2 in range(len(i[:-1])):
                            if priority == 0:
                                cards_number.append(sem_num-1)
                            elif priority == 1:
                                cards_number.append(sem_num+1)
                    if len(i) == len(last_cards) and select_num > last_num:
                        if tie['sym']:        
                            if tie['sym'] <= select_cards_sym and not '?' in select_cards_sym:
                                if tie['num']:
                                    if tie['num'] == cards_number or 'J' in cards_number:
                                        selectable_cards_list.append(i)
                                else:
                                    selectable_cards_list.append(i)
                            elif len(select_cards_sym - unions) < j_num:
                                if tie['num']:
                                    if tie['num'] == cards_number or 'J' in cards_number:
                                        selectable_cards_list.append(i)
                                else:
                                    selectable_cards_list.append(i)
                        else:
                            selectable_cards_list.append(i)
        #階段あり・縛りあり
        elif rules[:2] == [1, 1]:
            selectable_cards_list = []
            if len(last_cards) == 0:
                selectable_cards_list = preselectable_cards_list
            else:
                if [('J1', 'J1'), 0] == last_cards or [('J2', 'J2'), 0] == last_cards:
                    if [('♠', 3), 0] in preselectable_cards_list:
                        selectable_cards_list.append([('♠', 3), 0])
                for i in preselectable_cards_list:
                    i_converted = self.convert(i, priority)
                    select_cards_sym = set(i2[0] for i2 in i_converted[:-1])
                    cards_number = []
                    unions = select_cards_sym & tie['sym']
                    j_num = i.count(('J1', 'J1')) + i.count(('J2', 'J2'))
                    if priority == 0:
                        select_num = self.priority_dicts[priority][i_converted[0][1]]
                        last_num = self.priority_dicts[priority][last_cards[-2][1]]
                    elif priority == 1:
                        select_num = self.priority_dicts[priority][i_converted[-2][1]]
                        last_num = self.priority_dicts[priority][last_cards[0][1]]
                    if i[-1] == 0:
                        if len(i) == len(last_cards) and select_num > last_num and last_cards[-1] == 0:
                            if i[0][1] == 'J1' or i[0][1] == 'J2':
                                sem_num = 'J'
                                for i2 in range(len(i[:-1])):
                                    cards_number.append(sem_num)
                            else:
                                sem_num = i[0][1]
                                for i2 in range(len(i[:-1])):
                                    if priority == 0:
                                        cards_number.append(sem_num-1)
                                    elif priority == 1:
                                        cards_number.append(sem_num+1)
                            if len(i) == len(last_cards) and select_num > last_num:
                                if tie['sym']:        
                                    if tie['sym'] <= select_cards_sym and not '?' in select_cards_sym:
                                        if tie['num']:
                                            if tie['num'] == cards_number or 'J' in cards_number:
                                                selectable_cards_list.append(i)
                                        else:
                                            selectable_cards_list.append(i)
                                    elif len(select_cards_sym - unions) < j_num:
                                        if tie['num']:
                                            if tie['num'] == cards_number or 'J' in cards_number:
                                                selectable_cards_list.append(i)
                                        else:
                                            selectable_cards_list.append(i)
                                else:
                                    selectable_cards_list.append(i)
                    elif i[-1] == 1:
                        i_num = [i2[-1] for i2 in i_converted[:-1]]
                        previous_num = []
                        for i2 in i_num: 
                            if priority == 0:
                                previous_num.append(i2 - len(last_cards[:-1]))
                            elif priority == 1:
                                previous_num.append(i2 + len(last_cards[:-1]))
                        if select_num > last_num and last_cards[-1] == 1:
                            if tie['sym']:        
                                if tie['sym'] == select_cards_sym:
                                    if tie['num']:
                                        if tie['num'] == previous_num:
                                            selectable_cards_list.append(i)
                                    else:
                                        selectable_cards_list.append(i)
                            else:
                                selectable_cards_list.append(i)
        selectable_cards_list_copy = copy.deepcopy(selectable_cards_list)
        #環境上位カード上がり除去
        for i in selectable_cards_list_copy:
            if len(hands[select_player]) == len(i) - 1:
                if (priority == 0 and 2 in [i2[-1] for i2 in i[:-1]]) or\
                    (priority == 1 and 3 in [i2[-1] for i2 in i[:-1]]) or\
                    ('J1', 'J1') in i or ('J2', 'J2') in i or\
                    8 in [i2[-1] for i2 in i[:-1]]:
                    selectable_cards_list.remove(i)
        #カード効果処理矛盾の除去
        selectable_cards_list_copy = copy.deepcopy(selectable_cards_list)
        for i in selectable_cards_list_copy:
            try:
                self.effection(select_player, hands, i, count, priority, \
                               pass_dict, pass_counts, presence_11, strategy, \
                                   last_cards, dust_box)
            except IndexError:
                #print('ERROR')
                print('remove:{}'.format(i))
                selectable_cards_list.remove(i)
        return selectable_cards_list
    
    #各プレイヤーの戦略を返す
    def decide_strategies(self, select_player):
        if self.strategies[0] == 0:
            strategy = self.strategies[1]    
        elif self.strategies[0] == 1:
            strategy = self.strategies[1][select_player]
        return strategy
    
    #選択可能カード組み合わせのうち戦術に沿った組み合わせを返す
    def selection(self, selectable_cards_list, strategy):
        #戦術パターン0：リストからランダムに選択
        if strategy == 0:
            select_cards = random.choice(selectable_cards_list)
            return select_cards
        #戦術パターン1：リストから最大組み合わせを返す
        elif strategy == 1:
            sort_list = sorted(selectable_cards_list, key=lambda x:len(x))
            select_cards = sort_list[-1]
            return select_cards
    
    #戦績まとめ
    def recorder(self):
        record = {}
        for i in range(self.player_counts):
            record[i] = []
        for i in range(self.games):
            for i2 in range(self.player_counts):
                record[i2].append(self.battle_record[i+1].index(i2)+1)
        return record
    
    #J含み組み合わせのJ除外変換
    def convert(self, cards, priority):
        cards = copy.copy(cards)
        if len(cards) == 2 and ('J1', 'J1') in cards:
            cards_converted = cards
        elif len(cards) == 2 and ('J2', 'J2') in cards:
            cards_converted = cards
        elif len(cards) == 3 and ('J1', 'J1') in cards and ('J2', 'J2') in cards:
            cards_converted = cards
        elif ('J1', 'J1') in cards or ('J2', 'J2') in cards:
            cards_converted = []
            if cards[-1] == 1:
                for i in cards:
                    if i != ('J1', 'J1') and i != ('J2', 'J2'):
                        num_card = i
                        break
                for i in range(len(cards) - 1):
                    num_card_indx = cards.index(num_card)
                    num_card_num = self.priority_dicts[priority][num_card[1]]
                    i_num = num_card_num - (num_card_indx - i)
                    for k, v in self.priority_dicts[priority].items():
                        if v == i_num:
                            cards_converted.append((num_card[0], k))
                cards_converted.append(1)
            elif cards[-1] == 0:
                for i in cards[:-1]:
                    if i[-1] != 'J1' and i[-1] != 'J2':
                        number = i[-1]
                for i in cards[:-1]:
                    if i[-1] != 'J1' and i[-1] != 'J2':
                        cards_converted.append(i)
                    else:
                        cards_converted.append(('?', number))
                cards_converted.append(0)
        else:
            cards_converted = cards
        return cards_converted
    
    #カード効果処理(player!=0 or vs==0)
    def effection(self, select_player, hands, select_cards, count, priority, \
                  pass_dict, pass_counts, presence_11, strategy, last_cards, dust_box):
        hands = copy.deepcopy(hands)
        pass_dict = copy.deepcopy(pass_dict)
        select_cards_num = [i[-1] for i in select_cards[:-1]]
        count = copy.copy(count)
        dust_box = copy.copy(dust_box)
        priority = copy.copy(priority)
        presence_11 = copy.copy(presence_11)
        for i in select_cards[:-1]:
            hands[select_player].remove(i)  
        if last_cards == [('J1', 'J1'), 0] or last_cards == [('J2', 'J2'), 0]:
            if select_cards == [('♠', 3), 0]:
                pass_counts = self.player_counts
        if 4 in self.effects and 4 in select_cards_num:
            count_4 = select_cards_num.count(4)
            for i in range(count_4):
                #戦術パターン0:リストからランダムに選択
                if strategy == 0:
                    select_revival_card = random.choice(dust_box)
                    dust_box.remove(select_revival_card)
                    hands[select_player].append(select_revival_card)
        if 5 in self.effects and 5 in select_cards_num:
            count_5 = select_cards_num.count(5)
            select_player_copy = copy.copy(select_player)
            skip_count = 0
            count_sub = 0
            while count_5 * 2 - 1 > skip_count:
                select_player_copy += 1
                select_player_sub = select_player_copy % self.player_counts
                if pass_dict[select_player_sub] == 0:
                    pass_dict[select_player_sub] = 1
                    pass_counts += 1
                    skip_count += 1
                count += 1
                count_sub += 1
                if count_sub == self.player_counts - 1:
                    break
        if 7 in self.effects and 7 in select_cards_num:
            #受け取る人の指定
            receive_player = None
            counter = 1
            while receive_player == None:
                if hands[(select_player + counter) % self.player_counts]:
                    receive_player = (select_player + counter) % self.player_counts
                counter += 1
            count_7 = select_cards_num.count(7)
            for i in range(count_7):
                #戦術パターン0：リストからランダムに選択
                if strategy == 0:
                    give_cards = random.choice(hands[select_player])
                hands[select_player].remove(give_cards)
                hands[receive_player].append(give_cards)
        if 8 in self.effects and 8 in select_cards_num:
            pass_counts = self.player_counts
        if 10 in self.effects and 10 in select_cards_num:
            #受け取る人の指定
            count_10 = select_cards_num.count(10)
            for i in range(count_10):
                #戦術パターン0：リストからランダムに選択
                if strategy == 0:
                    dump_card = random.choice(hands[select_player])
                hands[select_player].remove(dump_card)
                dust_box.append(dump_card)
        if 11 in self.effects and 11 in select_cards_num:
            if priority == 0:
                priority = 1
            elif priority == 1:
                priority = 0
            presence_11 += 1
        if 12 in self.effects and 12 in select_cards_num:
            count_12 = select_cards_num.count(12)
            for i in range(count_12):
                #戦術パターン0:リストからランダムに選択
                if strategy == 0:
                    dump_num = random.choice(list(self.priority_dicts[0].keys()))
                for i2 in range(self.player_counts):
                    if hands[i2]:
                        hands_prelist = [self.priority_dicts[0][i3[-1]] for i3 in hands[i2]]
                        while dump_num in hands_prelist:
                            dump_index = hands_prelist.index(dump_num)
                            dust_box.append(hands[i2][dump_index])
                            hands[i2].remove(hands[i2][dump_index])
                            hands_prelist = [self.priority_dicts[0][i3[-1]] for i3 in hands[i2]]
        return (hands, count, priority, pass_dict, pass_counts, presence_11, dust_box)
    
    #カード効果処理(player==0 and vs==1)
    def effection_vs(self, select_player, hands, select_cards, count, priority, \
                  pass_dict, pass_counts, presence_11, strategy, last_cards, dust_box):
        hands = copy.deepcopy(hands)
        pass_dict = copy.deepcopy(pass_dict)
        select_cards_num = [i[-1] for i in select_cards[:-1]]
        count = copy.copy(count)
        dust_box = copy.copy(dust_box)
        priority = copy.copy(priority)
        presence_11 = copy.copy(presence_11)
        for i in select_cards[:-1]:
            hands[select_player].remove(i)  
        if last_cards == [('J1', 'J1'), 0] or last_cards == [('J2', 'J2'), 0]:
            if select_cards == [('♠', 3), 0]:
                pass_counts = self.player_counts
        if 4 in self.effects and 4 in select_cards_num:
            count_4 = select_cards_num.count(4)
            for i in range(count_4):
                #コンソールによる蘇生カード選択
                while True:
                    print(dust_box)
                    select_revival_card_pre = input('Select revival card![ex)♥,7 (or J1,J1)]:')
                    select_symbol = select_revival_card_pre.split(',')[0]
                    try:
                        select_number = int(select_revival_card_pre.split(',')[1])
                    except ValueError:
                        select_number = select_revival_card_pre.split(',')[1]
                    select_revival_card = (select_symbol, select_number)
                    if not select_revival_card in dust_box:
                        print('Your select card is not dust box!')
                        continue
                    else:
                        dust_box.remove(select_revival_card)
                        hands[select_player].append(select_revival_card)
                        break
        if 5 in self.effects and 5 in select_cards_num:
            count_5 = select_cards_num.count(5)
            select_player_copy = copy.copy(select_player)
            skip_count = 0
            count_sub = 0
            while count_5 * 2 - 1 > skip_count:
                select_player_copy += 1
                select_player_sub = select_player_copy % self.player_counts
                if pass_dict[select_player_sub] == 0:
                    pass_dict[select_player_sub] = 1
                    pass_counts += 1
                    skip_count += 1
                count += 1
                count_sub += 1
                if count_sub == self.player_counts - 1:
                    break
        if 7 in self.effects and 7 in select_cards_num:
            #受け取る人の指定
            receive_player = None
            counter = 1
            while receive_player == None:
                if hands[(select_player + counter) % self.player_counts]:
                    receive_player = (select_player + counter) % self.player_counts
                counter += 1
            count_7 = select_cards_num.count(7)
            for i in range(count_7):
                #コンソールによる選択
                while True:
                    print(hands[0])
                    select_give_card_pre = input('Select give card![ex)♥,7 (or J1,J1)]:')
                    select_symbol = select_give_card_pre.split(',')[0]
                    try:
                        select_number = int(select_give_card_pre.split(',')[1])
                    except ValueError:
                        select_number = select_give_card_pre.split(',')[1]
                    select_give_card = (select_symbol, select_number)
                    if not select_give_card in hands[0]:
                        print('Your select card is not in hand!')
                        continue
                    else:
                        hands[0].remove(select_give_card)
                        hands[receive_player].append(select_give_card)
                        break
        if 8 in self.effects and 8 in select_cards_num:
            pass_counts = self.player_counts
        if 10 in self.effects and 10 in select_cards_num:
            count_10 = select_cards_num.count(10)
            for i in range(count_10):
                #コンソールによる選択
                while True:
                    print(hands[0])
                    select_dump_card_pre = input('Select dump card![ex)♥,7 (or J1,J1)]:')
                    select_symbol = select_dump_card_pre.split(',')[0]
                    try:
                        select_number = int(select_dump_card_pre.split(',')[1])
                    except ValueError:
                        select_number = select_dump_card_pre.split(',')[1]
                    select_dump_card = (select_symbol, select_number)
                    if not select_dump_card in hands[0]:
                        print('Your select card is not in hand!')
                        continue
                    else:
                        hands[0].remove(select_dump_card)
                        dust_box.append(select_dump_card)
                        break
        if 11 in self.effects and 11 in select_cards_num:
            if priority == 0:
                priority = 1
            elif priority == 1:
                priority = 0
            presence_11 += 1
        if 12 in self.effects and 12 in select_cards_num:
            count_12 = select_cards_num.count(12)
            for i in range(count_12):
                #コンソールによる選択
                while True:
                    print(hands[0])
                    select_dump_num_pre = input('Select dump number![ex)7 (or J)]:')
                    try:
                        select_dump_num = int(select_dump_num_pre)
                    except:
                        select_dump_num = select_dump_num_pre
                    try:
                        dump_num = self.priority_dicts[0][select_dump_num]
                        break
                    except:
                        print('Your choice in inaccurate!')
                        continue
                for i2 in range(self.player_counts):
                    if hands[i2]:
                        hands_prelist = [self.priority_dicts[0][i3[-1]] for i3 in hands[i2]]
                        while dump_num in hands_prelist:
                            dump_index = hands_prelist.index(dump_num)
                            dust_box.append(hands[i2][dump_index])
                            hands[i2].remove(hands[i2][dump_index])
                            hands_prelist = [self.priority_dicts[0][i3[-1]] for i3 in hands[i2]]
        return (hands, count, priority, pass_dict, pass_counts, presence_11, dust_box)
            
    #カード交換処理(vs=0)
    def exchange(self, hands, games):
        exchange_counts = self.exchange_cards 
        for i in range(self.exchange_cards):
            exchange_counts -= 1 
            sender_give_cards = []
            receiver_give_cards = []
            for i2 in range(i+1):
                receiver = self.battle_record[games-1][exchange_counts]
                sender = self.battle_record[games-1][::-1][exchange_counts]
                #[送り手]最上位カードの選択/[受け手]戦術による選択
                sender_prelist = sorted(hands[sender], key=lambda x:self.priority_dicts[0][x[1]]) 
                sender_give_cards.append(sender_prelist[-1])
                hands[sender].remove(sender_give_cards[-1])
                #[受け手]
                if self.decide_strategies(receiver) == 0:
                    receiver_give_cards.append(random.choice(hands[receiver]))
                hands[receiver].remove(receiver_give_cards[-1])
            for i2 in sender_give_cards:
                hands[receiver].append(i2)
            for i2 in receiver_give_cards:
                hands[sender].append(i2)
        return hands
    
    #カード交換処理(vs=1)
    def exchange_vs(self, hands, games):
        exchange_counts = self.exchange_cards 
        for i in range(self.exchange_cards):
            exchange_counts -= 1 
            sender_give_cards = []
            receiver_give_cards = []
            for i2 in range(i+1):
                receiver = self.battle_record[games-1][exchange_counts]
                sender = self.battle_record[games-1][::-1][exchange_counts]
                #[送り手]最上位カードの選択/[受け手]戦術による選択
                sender_prelist = sorted(hands[sender], key=lambda x:self.priority_dicts[0][x[1]]) 
                sender_give_cards.append(sender_prelist[-1])
                hands[sender].remove(sender_give_cards[-1])
                #[受け手]receiver=0の場合、コンソールからsender_give_cardsの選択
                if receiver == 0:
                    print('hands:{}'.format(sorted(hands[receiver], key=lambda x:self.priority_dicts[0][x[1]])))
                    while True:
                        try:
                            receiver_give_cards_pre = input('Player {}!'.format(receiver) +
                                    ' Select a send card![ex)♥,7(or J1,J1))]:')
                            receiver_symbol = receiver_give_cards_pre.split(',')[0]
                            receiver_number = int(receiver_give_cards_pre.split(',')[1])
                            receiver_give_cards.append((receiver_symbol, receiver_number))
                            hands[receiver].remove(receiver_give_cards[-1])
                            break
                        except ValueError:
                            receiver_number = receiver_give_cards_pre.split(',')[1]
                            receiver_give_cards.append((receiver_symbol, receiver_number))
                            hands[receiver].remove(receiver_give_cards[-1])
                            break
                        except:
                            print('Your choice is inaccurate!')
                            continue
                    print(receiver_give_cards)
                else:
                    #strategy=0の場合、ランダム選択
                    if self.decide_strategies(receiver) == 0:
                        receiver_give_cards.append(random.choice(hands[receiver]))
                        hands[receiver].remove(receiver_give_cards[-1])
            for i2 in sender_give_cards:
                hands[receiver].append(i2)
            for i2 in receiver_give_cards:
                hands[sender].append(i2)
        return hands
                
    #カード分配処理
    def card_shuffle(self):
        cards_shuffled = self.cards.copy()
        random.shuffle(cards_shuffled)
        hands = {}
        for i in range(self.player_counts):
            hands[i] = []
        for i in range(self.cards_counts//self.player_counts+1):
            for i2 in range(self.player_counts):
                if cards_shuffled:
                    hands[i2].append(cards_shuffled.pop())
        return hands
    
    #図示
    def show_record(self):
        record = self.recorder()
        #100ゲームまでの各プレイヤーの順位推移と平均
        fig1 = plt.figure()
        ax1 = fig1.add_subplot(111)
        cmap = plt.get_cmap('tab10')
        for i in range(self.player_counts):
            if self.games > 100:
                x = range(1, 101)
                y = record[i][:100]
            else:
                x = range(1, len(record[i])+1)
                y = record[i]
            y2 = sum(record[i])/len(record[i])
            ax1.set_title('player_ranking')
            ax1.set_xlabel('games')
            ax1.set_ylabel('ranking')
            ax1.plot(x, y, ls='solid', color = cmap(i), label = 'player{}:transition'.format(i))
            ax1.axhline(y2, ls = 'dashed', color = cmap(i), label = 'player{}:AVE'.format(i))
            plt.plot()
        ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0)
        plt.show()
        #各順位からの順位変化
        rank_dict = {}
        for rank in range(self.player_counts):
            rank_dict[rank] = []
            for game in range(1, len(list(self.battle_record.keys()))):
                n_player = self.battle_record[game][rank]
                n_player_next_rank = self.battle_record[game+1].index(n_player)
                rank_dict[rank].append(n_player_next_rank)
        rank_rate = {}
        for rank in range(self.player_counts):
            rank_rate[rank] = []
            for rank2 in range(self.player_counts):
                rank_rate[rank].append(rank_dict[rank].count(rank2))
        fig2 = plt.figure(figsize=(10.0,10.0))
        fig2.suptitle('ranking_rate_for_previous_one')
        for i in range(self.player_counts):
            labels_pie = [i+1 for i in rank_rate.keys()]
            ax2 = fig2.add_subplot(self.player_counts-1//4,4,i+1)
            ax2.set_title('pre_rank:{}'.format(i+1))
            ax2.pie(rank_rate[i], labels=labels_pie, shadow=True, \
                    counterclock=False, autopct='%1.0f%%', startangle=90)
        #配られたカード別の順位への寄与率(1位:3,2位:2,3位:1,4位:0としてジョーカーが1位と4位が持っていた場合((3-3/2)+(0-3/2))/2ポイントとする
        if self.joker_counts:
            contribution_point = {1:[],2:[],3:[],4:[],5:[],6:[],7:[],8:[],9:[],10:[],11:[],12:[],13:[],'J':[]}
        else:
            contribution_point = {1:[],2:[],3:[],4:[],5:[],6:[],7:[],8:[],9:[],10:[],11:[],12:[],13:[]}
        contribution_rate = {}
        for player in range(self.player_counts):
            for game in range(self.games):
                player_rank = record[player][game]
                player_cards = []
                for i in self.battle_record2[game+1][player]:
                    if i[-1] == 'J1' or  i[-1] == 'J2':
                        player_cards.append('J')
                    else:
                        player_cards.append(i[-1])
                for card_num in list(contribution_point.keys()):
                    if card_num in player_cards:
                        card_num_num = player_cards.count(card_num)
                        contribution_point[card_num].append(((self.player_counts-player_rank)-(self.player_counts-1)/2)*card_num_num)
        for card_num in list(contribution_point.keys()):
            sum_point = sum(contribution_point[card_num])
            if card_num == 'J':
                all_card_num = self.joker_counts * self.games
            else:
                all_card_num = 4 * self.games
            contribution_rate[card_num] = sum_point / all_card_num
        fig3 = plt.figure()
        fig3.suptitle('contribution_rate_for_card')
        ax3 = fig3.add_subplot()
        labels_bar = list(contribution_rate.keys())
        x = range(1,len(contribution_rate.keys())+1)
        y = list(contribution_rate.values())
        ax3.bar(x, y, 0.1)
        ax3.set_xticks(x)
        ax3.set_xticklabels(labels_bar)
        #figの保存
        #fig1.savefig('player_ranking.png')
        #fig2.savefig('ranking_rate.png')
        #fig3.savefig('contribution.png')
        plt.show()
    
    def card_set(self):
        symbols = ['♦','♥','♣','♠','J1','J2']
        numbers = [1,2,3,4,5,6,7,8,9,10,11,12,13]
        self.cards = []
        if self.joker_counts == 1:
            del symbols[-1]
        elif self.joker_counts == 0:
            del symbols[-2: ]       
        for i in symbols:
            if i == 'J1':
                self.cards.append(('J1', 'J1'))
            elif i == 'J2':
                self.cards.append(('J2', 'J2'))
            else:
                for i2 in numbers:
                    self.cards.append((i, i2))
        self.cards_counts = len(self.cards)
        

class Pipeline:
    """
    --------------
    Parameters
    --------------
    sets            :[(parameter, conditions)]_tuple_in_list
    parameters      :RichPeopleのパラメータ名_str
    conditions      :RichPeopleのパラメータ値_list
    
    ex.[x = Pipeline([('rules', [[0,0,0], [1,0.0], [0,1,1]]), ('games', [10, 100, 1000])])] 
    """
    def __init__(self, sets):
        self.sets = sets
        self.pipe_record = {}
    
    def start(self):
        #parameters初期値
        para_dict = {'player_counts':4, 'rules':[0,0,0], 'effects':[8,11], 
                     'joker_counts':2, 'exchange_cards':2, 
                         'games':10, 'strategies':[0,0]}
        count = 0
        para_con = [len(self.sets[i][-1]) for i in range(len(self.sets))]
        count_max = 1
        for para in self.sets:
            count_max *= len(para[-1])
        while count < count_max:
            para_cou = []
            stack = 1
            for i in range(len(self.sets)):
                if i > 0:
                    stack = stack * len(self.sets[i-1])
                add = count // stack
                para_cou.append(add)
            para_con_cou = []
            for i_con, i_cou in zip(para_con, para_cou):
                para_con_cou.append(i_cou % i_con)
            counts = 0
            for para_num in para_con_cou:
                para_dict[self.sets[counts][0]] = self.sets[counts][1][para_num]
                counts += 1
            X = Set(para_dict['player_counts'], para_dict['rules'], para_dict['effects'],
                           para_dict['joker_counts'], para_dict['exchange_cards'],para_dict['games'],
                           para_dict['strategies'])
            X.start()
            battle_record = X.battle_record
            self.pipe_record[count] = {'player_counts':para_dict['player_counts'], 'rules':para_dict['rules'],
                                'effects':para_dict['effects'], 'joker_counts':para_dict['joker_counts'],
                               'exchange_cards':para_dict['exchange_cards'], 'games':para_dict['games'],
                               'strangies':para_dict['strategies'], 'results':battle_record}
            count += 1
            
    
            
        
        
