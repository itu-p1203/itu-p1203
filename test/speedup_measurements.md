# some notes

commands used
```
echo 'stats' | python3 -m pstats output.cprof 
echo -e 'sort tottime\nreverse\nstats' | python3 -m pstats output.cprof 
```

## initial run
4353493 function calls (4345610 primitive calls) in 13.148 seconds

### results
``` (last values only)
    12527    0.019    0.000    0.019    0.000 {method 'rstrip' of 'str' objects}
     8164    0.021    0.000    0.021    0.000 {method 'splitlines' of 'str' objects}
      852    0.021    0.000    0.042    0.000 /usr/lib/python3.8/functools.py:34(update_wrapper)
        1    0.021    0.021    2.117    2.117 /home/stg7/itu-p1203/itu_p1203/p1203Pv.py:454(calculate)
    11668    0.022    0.000    0.024    0.000 {built-in method builtins.getattr}
      596    0.023    0.000    0.023    0.000 /home/stg7/itu-p1203/itu_p1203/utils.py:249(<listcomp>)
     4414    0.024    0.000    0.070    0.000 <frozen importlib._bootstrap_external>:62(_path_join)
     4414    0.024    0.000    0.039    0.000 <frozen importlib._bootstrap_external>:64(<listcomp>)
    15894    0.024    0.000    0.024    0.000 {built-in method builtins.min}
    13733    0.025    0.000    0.028    0.000 {method 'join' of 'str' objects}
      859    0.025    0.000    0.123    0.000 <frozen importlib._bootstrap_external>:1431(find_spec)
      116    0.026    0.000    0.445    0.004 /home/stg7/.local/lib/python3.8/site-packages/scipy/stats/_distn_infrastructure.py:711(_construct_doc)
   1013/1    0.030    0.000   13.165   13.165 {built-in method builtins.exec}
    20348    0.030    0.000    0.030    0.000 {method 'lstrip' of 'str' objects}
    23751    0.035    0.000    0.035    0.000 {built-in method builtins.isinstance}
       93    0.036    0.000    0.043    0.000 {built-in method _imp.create_dynamic}
      298    0.051    0.000    0.051    0.000 /home/stg7/itu-p1203/itu_p1203/p1203Pa.py:69(<listcomp>)
    36000    0.054    0.000    0.054    0.000 {method 'pop' of 'list' objects}
      438    0.059    0.000    0.059    0.000 {built-in method marshal.loads}
    37250    0.063    0.000   10.518    0.000 /home/stg7/itu-p1203/itu_p1203/measurementwindow.py:62(_should_calculate_score)
        1    0.091    0.091    9.221    9.221 /home/stg7/itu-p1203/itu_p1203/p1203Pa.py:78(calculate)
      358    0.095    0.000    0.189    0.001 /home/stg7/.local/lib/python3.8/site-packages/scipy/_lib/doccer.py:177(indentcount_lines)
      339    0.138    0.000    0.462    0.001 /home/stg7/.local/lib/python3.8/site-packages/scipy/_lib/doccer.py:10(docformat)
    37250    0.254    0.000   10.913    0.000 /home/stg7/itu-p1203/itu_p1203/measurementwindow.py:82(add_frame)
409571/409184    0.519    0.000    0.521    0.000 {built-in method builtins.len}
   512150    0.647    0.000    0.647    0.000 {method 'append' of 'list' objects}
  1500048    1.867    0.000    1.867    0.000 {method 'keys' of 'dict' objects}
      596    3.369    0.006   10.599    0.018 /home/stg7/itu-p1203/itu_p1203/utils.py:208(get_chunk)
  1462688    4.475    0.000    6.295    0.000 /home/stg7/itu-p1203/itu_p1203/utils.py:185(get_chunk_hash)
```



## calculate frame representations before (A)
 4428025 function calls (4420141 primitive calls) in 12.395 seconds


## get_chunk with only_first = True  (B)
observation: 
    * the audio model has a high number of samples per second of sample_rate = 100.
    * this causes a lot of audio model callbacks
    * each of this call uses the get_chunk that creates a suitable chunk
    * however for each of the window chunks only the first frame is required for audio quality calculation, so it is not needed to create the complete window
before:  4427993 function calls (4420110 primitive calls) in 12.344 seconds, see (A)
after: 1502213 function calls (1494329 primitive calls) in 4.978 seconds


## get_chunk improvements
here `window = [i] + window` is used, check if `window.insert(0, i)` would be better, see `python_speed_comp.py`, results indicate speedup, so lets test

before: 1502245 function calls (1494360 primitive calls) in 5.023 seconds, see (B)
after:  1575301 function calls (1567417 primitive calls) in 5.126 seconds --> no real improvement, thus skipped

## get_chunk while loops
first there is a if i condition, that can be just part of the loop, 
second, the hash calculation is not required to be performed always

before:  4427993 function calls (4420110 primitive calls) in 12.344 seconds, see (A)
after:   1210914 function calls (1203031 primitive calls) in 4.106 seconds

(pure while loops with some changes were faster, but for loops are simpler to read)


# lru_cache

before: 1226569 function calls (1218583 primitive calls) in 1.299 seconds
after:  1226541 function calls (1218557 primitive calls) in 1.339 seconds

==> no real improvement
