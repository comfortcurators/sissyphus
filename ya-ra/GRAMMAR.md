# ya-ra grammar (EBNF)

Version token is always `rv` + integer. This file is **rv1**.

```
file        = [ rv NL ] door { check | rv } EOF ;

rv          = 'rv' integer ;

door        = intent NL pattern NL signed [ NL ] ;

intent      = 'Intent' [ ' ' ] ':' SP text ;
pattern     = 'Pattern' [ ' ' ] ':' SP text ;
signed      = 'Signed' '.' SP name SP '/' SP timestamp ;

text        = { char - NL } ;
name        = { char - '/' - NL } ;
timestamp   = { char - NL } ;

check       = ( '⊦' | 'check' ) SP check_body NL ;
check_body  = exists | words | run | contains | eq ;

exists      = 'exists' SP path ;
words       = 'words' SP ('intent' | 'pattern') SP '<=' SP integer ;
run         = 'run' SP command ;
contains    = 'contains' SP path SP string ;
eq          = 'eq' SP path SP string ;

SP          = ' ' ;
NL          = '\n' ;
```

Semantics
- Intent: hypothesis written before the outcome is known.
- Pattern: human-readable falsification route.
- Signed: principal bound to that pair.
- rv: the only version token. Never semver. Never bare YARA.
- ⊦ / check: machine-executable falsifiers. Any failure contradicts the Intent.
