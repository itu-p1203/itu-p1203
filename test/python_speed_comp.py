#!/usr/bin/env python3

import timeit


def insert_pos_list():
    a = list(range(1000))
    for i in range(100):
        a.insert(0, i)

def list_equal_element_plus_list():
    a = list(range(1000))
    for i in range(100):
        a = [i] + a

print(
    timeit.timeit(
        "insert_pos_list()",
        setup="from __main__ import insert_pos_list",
        number=1000
    )
) #--> 0.49346098299974983

print(
    timeit.timeit(
        "list_equal_element_plus_list()",
        setup="from __main__ import list_equal_element_plus_list",
        number=1000
    )
) #--> 2.2644150630003423

a = [1,2,3]
i = 0
while i +1 < len(a):
    print(i)
    i += 1
    #if i+1 == len(a):
    #    break