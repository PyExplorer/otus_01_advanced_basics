#!/usr/bin/env python
# -*- coding: utf-8 -*-

# -----------------
# Реализуйте функцию best_hand, которая принимает на вход
# покерную "руку" (hand) из 7ми карт и возвращает лучшую
# (относительно значения, возвращаемого hand_rank)
# "руку" из 5ти карт. У каждой карты есть масть(suit) и
# ранг(rank)
# Масти: трефы(clubs, C), пики(spades, S), червы(hearts, H), бубны(diamonds, D)
# Ранги: 2, 3, 4, 5, 6, 7, 8, 9, 10 (ten, T), валет (jack, J), дама (queen, Q),
# король (king, K), туз (ace, A)
# Например: AS - туз пик (ace of spades), TH - дестяка черв (ten of hearts), 3C
# - тройка треф (three of clubs)

# Задание со *
# Реализуйте функцию best_wild_hand, которая принимает на вход
# покерную "руку" (hand) из 7ми карт и возвращает лучшую
# (относительно значения, возвращаемого hand_rank)
# "руку" из 5ти карт. Кроме прочего в данном варианте "рука"
# может включать джокера. Джокеры могут заменить карту любой
# масти и ранга того же цвета, в колоде два джокерва.
# Черный джокер '?B' может быть использован в качестве треф
# или пик любого ранга, красный джокер '?R' - в качестве черв и бубен
# любого ранга.

# Одна функция уже реализована, сигнатуры и описания других даны.
# Вам наверняка пригодится itertoolsю
# Можно свободно определять свои функции и т.п.
# -----------------

from itertools import combinations
from itertools import product

LIST_RANK = [
    '1', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A'
]
DICT_RANK = {x[1]: x[0] for x in enumerate(LIST_RANK, 1)}
LIST_SUIT_BLACK = ['S', 'C']
LIST_SUIT_RED = ['H', 'D']
LIST_BLACK_CARD = ["".join(x) for x in product(LIST_RANK, LIST_SUIT_BLACK)]
LIST_RED_CARD = ["".join(x) for x in product(LIST_RANK, LIST_SUIT_RED)]


def hand_rank(hand):
    """Возвращает значение определяющее ранг 'руки'"""
    ranks = card_ranks(hand)
    if straight(ranks) and flush(hand):
        return (8, max(ranks))
    elif kind(4, ranks):
        return (7, kind(4, ranks), kind(1, ranks))
    elif kind(3, ranks) and kind(2, ranks):
        return (6, kind(3, ranks), kind(2, ranks))
    elif flush(hand):
        return (5, ranks)
    elif straight(ranks):
        return (4, max(ranks))
    elif kind(3, ranks):
        return (3, kind(3, ranks), ranks)
    elif two_pair(ranks):
        return (2, two_pair(ranks), ranks)
    elif kind(2, ranks):
        return (1, kind(2, ranks), ranks)
    else:
        return (0, ranks)


def card_ranks(hand):
    """Возвращает список рангов (его числовой эквивалент),
    отсортированный от большего к меньшему"""
    ranks = [DICT_RANK[x[0]] for x in hand]
    return sorted(ranks, reverse=True)


def flush(hand):
    """Возвращает True, если все карты одной масти"""
    list_m = [x[1] for x in hand]
    return len(set(list_m)) == 1


def straight(ranks):
    """Возвращает True, если отсортированные ранги формируют последовательность
    5ти, где у 5ти карт ранги идут по порядку (стрит)
    :param ranks:- отсортированный от большего к меньшему список
    """
    return ranks[0] - ranks[-1] == 4


def kind(n, ranks):
    """Возвращает первый ранг, который n раз встречается в данной руке.
    Возвращает None, если ничего не найдено
    :param ranks:- отсортированный от большего к меньшему список
    """
    for rank in ranks:
        if ranks.count(rank) == n:
            return rank


def two_pair(ranks):
    """Если есть две пары, то возвращает два соответствующих ранга,
    иначе возвращает None
    :param ranks:- отсортированный от большего к меньшему список
    """
    first_pair = kind(2, ranks)
    second_pair = kind(2, sorted(ranks))
    if not (first_pair or second_pair) or first_pair == second_pair:
        return None
    return first_pair, second_pair


def best_hand(hand):
    """Из "руки" в 7 карт возвращает лучшую "руку" в 5 карт """
    list_hands = []
    for full_hand in combinations(hand, 5):
        list_hands.append((hand_rank(list(full_hand)), list(full_hand)))
    list_hands.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return list_hands[0][1]


def best_wild_hand(hand):
    """best_hand но с джокерами"""

    list_hands = []
    for full_hand in combinations(hand, 5):
        if is_jokers(full_hand, '?B', '?R'):
            replaced_joker_hands = []
            if is_joker(full_hand, '?B', '?R'):
                replaced_joker_hands = get_replaced_all_jokers_hands(full_hand)
            elif is_joker(full_hand, '?B'):
                replaced_joker_hands = get_replaced_joker_hands(
                    full_hand, LIST_BLACK_CARD, '?B'
                )
            elif is_joker(full_hand, '?R'):
                replaced_joker_hands = get_replaced_joker_hands(
                    full_hand, LIST_RED_CARD, '?R'
                )

            for replaced_hand in replaced_joker_hands:
                list_hands.append(
                    (hand_rank(list(replaced_hand)), list(replaced_hand))
                )

        else:
            list_hands.append((hand_rank(list(full_hand)), list(full_hand)))

    list_hands.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return list_hands[0][1]


def is_joker(hand, *args):
    return all(x if x in hand else False for x in args)


def is_jokers(hand, *args):
    return any(x if x in hand else False for x in args)


def change_full_hand(fh, suit, repl):
    return fh[0:fh.index(suit)] + (repl,) + fh[fh.index(suit) + 1:]


def get_replaced_joker_hands(hand, list_card, letter):
    """
    Получаем руку и возвращаем список рук с замененным джокером
    :param hand: исходная рука
    :param list_card: список карт для замены джокера
    :param letter: буква джокера
    :return:
    """
    list_replaced_joker_hands = []
    for joker_repl in list_card:
        # если карта есть в руке - не заменяем
        if joker_repl in hand:
            continue
        replaced_joker_hand = change_full_hand(hand, letter, joker_repl)
        list_replaced_joker_hands.append(replaced_joker_hand)
    return list_replaced_joker_hands


def get_replaced_all_jokers_hands(hand):
    """
    Заменяем обоих джокеров и возвращаем общий список замен
    :param hand: исходная рука
    :return:
    """
    replaced_joker_hands = []

    replaced_black_joker_hands = get_replaced_joker_hands(
        hand, LIST_BLACK_CARD, '?B'
    )
    for replaced_black_joker_hand in replaced_black_joker_hands:
        replaced_red_joker_hands = get_replaced_joker_hands(
            replaced_black_joker_hand, LIST_RED_CARD, '?R'
        )
        replaced_joker_hands.extend(replaced_red_joker_hands)

    return replaced_joker_hands


def test_best_hand():
    print "test_best_hand..."
    assert (sorted(best_hand("6C 7C 8C 9C TC 5C JS".split())) ==
            ['6C', '7C', '8C', '9C', 'TC'])
    assert (sorted(best_hand("TD TC TH 7C 7D 8C 8S".split())) ==
            ['8C', '8S', 'TC', 'TD', 'TH'])
    assert (sorted(best_hand("JD TC TH 7C 7D 7S 7H".split())) ==
            ['7C', '7D', '7H', '7S', 'JD'])
    print 'OK'


def test_best_wild_hand():
    print "test_best_wild_hand..."
    assert (sorted(best_wild_hand("6C 7C 8C 9C TC 5C ?B".split())) ==
            ['7C', '8C', '9C', 'JC', 'TC'])
    assert (sorted(best_wild_hand("TD TC 5H 5C 7C ?R ?B".split())) ==
            ['7C', 'TC', 'TD', 'TH', 'TS'])
    assert (sorted(best_wild_hand("JD TC TH 7C 7D 7S 7H".split())) ==
            ['7C', '7D', '7H', '7S', 'JD'])
    print 'OK'


def test_card_ranks():
    print "test_card_ranks..."
    assert (card_ranks(['7C', '8C', '9C', 'JC', 'TC']) == [11, 10, 9, 8, 7])
    assert (card_ranks(['3C', '2C', '5C', 'AC', 'TC']) == [14, 10, 5, 3, 2])
    print 'OK'


def test_flush():
    print "test_flush..."
    assert flush(['7C', '8C', '9C', 'JC', 'TC'])
    assert not flush(['3H', '2C', '5C', 'AC', 'TC'])
    print 'OK'


def test_straight():
    print "test_straight..."
    assert straight([11, 10, 9, 8, 7])
    assert not straight([11, 10, 9, 8, 6])
    print 'OK'


def test_kind():
    print "test_kind..."
    assert kind(2, [11, 10, 9, 8, 7]) is None
    assert kind(3, [11, 10, 9, 8, 7]) is None
    assert kind(2, [11, 11, 9, 8, 6]) == 11
    assert kind(2, [11, 10, 9, 6, 6]) == 6
    assert kind(2, [10, 10, 9, 6, 6]) == 10
    assert kind(3, [11, 10, 4, 4, 4]) == 4
    assert kind(3, [10, 10, 10, 4, 4]) == 10
    print 'OK'


def test_two_pair():
    print "test_two_pair..."
    assert two_pair([11, 10, 9, 8, 7]) is None
    assert two_pair([11, 11, 9, 8, 7]) is None
    assert two_pair([11, 11, 9, 6, 6]) == (11, 6)
    assert two_pair([11, 10, 10, 6, 6]) == (10, 6)
    print 'OK'


if __name__ == '__main__':
    test_best_hand()
    test_best_wild_hand()
    test_card_ranks()
    test_flush()
    test_straight()
    test_kind()
    test_two_pair()
