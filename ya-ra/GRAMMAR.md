# ya-ra grammar — rv0.1.0

Version token is always `rv` plus dotted integers. Never bare `YARA`. Never unprefixed semver.

```
file        = [ rv NL ] door { stmt } EOF ;

rv          = 'rv' integer { '.' integer } ;

door        = intent NL pattern NL signed [ NL ] ;

intent      = 'Intent' [ ' ' ] ':' SP text ;
pattern     = 'Pattern' [ ' ' ] ':' SP text ;
signed      = 'Signed' '.' SP name SP '/' SP timestamp ;

stmt        = measure | check | rv ;

measure     = 'measure' SP ('all' | 'any') ;
check       = ( '⊦' | 'check' ) SP check_body [ SP amp ] NL ;
amp         = 'amp' SP number ;
check_body  = exists | words | run | contains | eq ;

exists      = 'exists' SP path ;
words       = 'words' SP ('intent' | 'pattern') SP '<=' SP integer ;
run         = 'run' SP command ;
contains    = 'contains' SP path SP string ;
eq          = 'eq' SP path SP string ;
```

Default measure is `all`.
