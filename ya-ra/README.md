# ya-ra

Executable form of **YA|RA**. Version is always `rv`. This tree is **rv1**.

```
rv1
Intent : what may become true
Pattern: how reality can contradict it
Signed. who stood behind the attempt

⊦ exists PATH
⊦ words intent|pattern <= N
⊦ run COMMAND
⊦ contains PATH STRING
⊦ eq PATH STRING
```

```bash
python3 -m ya_ra --rv
python3 -m ya_ra check examples/door.ya-ra --root .
python3 -m ya_ra emit examples/door.ya-ra --lang python -o emit/door_test.py
python3 -m ya_ra emit examples/door.ya-ra --lang rust   -o emit/door.rs
python3 -m ya_ra emit examples/door.ya-ra --lang c      -o emit/door.c
```

Never write the name as bare `YARA`.
