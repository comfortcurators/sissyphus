# YA|RA grammar — rv0.2.0

Version token is always `rv` plus dotted integers. Never bare `YARA`. Never unprefixed semver.

```
file        = [ rv NL ] door { stmt } EOF ;

rv          = 'rv' integer { '.' integer } ;

door        = intent NL pattern NL signed [ NL ] ;

intent      = 'Intent' [ ' ' ] ':' SP text ;
pattern     = 'Pattern' [ ' ' ] ':' SP text ;
signed      = 'Signed' '.' SP name SP '/' SP timestamp ;

stmt        = zero | glimpse | measure | use | check | rv ;

zero        = '00' | '0' ;
glimpse     = 'glimpse' ;
measure     = 'measure' SP ('all' | 'any') ;
use         = 'use' SP path ;
check       = ( '⊦' | 'check' ) SP check_body [ SP amp ] NL ;
amp         = 'amp' SP complex ;
check_body  = exists | words | run | contains | eq | use_check ;

exists      = 'exists' SP path ;
words       = 'words' SP ('intent' | 'pattern') SP '<=' SP integer ;
run         = 'run' SP command ;
contains    = 'contains' SP path SP string ;
eq          = 'eq' SP path SP string ;
use_check   = 'use' SP path ;
```

Default measure is `all`. Unknown check kinds are a parse error. Amp is complex (`1`, `1+0j`, `0.5+0.5i`).

The five files at the repository root are also a door. `ya-ra measure --root .` reads Intent, Pattern, Glimpse, README.md, IMG_3790.jpeg and signs from `git log` of Intent.
