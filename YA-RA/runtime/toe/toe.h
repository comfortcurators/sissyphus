/* YA|RA cut against the single action.
 *
 * The slide writes Z = ∫ D(Fields) exp(iS). That integral is unsigned.
 * YA|RA will not treat it as a door.
 *
 * Instead it computes a signed sum over attributed checks:
 *   Z = Σ_k amp_k · [check_k passed]
 * Refuse if there is no signer, or if action_is_door.
 * Polarity: 0 = ok.
 */
#ifndef YA_RA_TOE_H
#define YA_RA_TOE_H

#ifndef YARA_OK
#define YARA_OK 0
#define YARA_FAIL 1
#endif

struct yara_toe_cut {
  const char *intent;
  const char *pattern;
  const char *signer;
  int action_is_door;
};

struct yara_toe_term {
  double re;
  double im;
  int passed;
};

struct yara_toe_z {
  double re;
  double im;
  int nterms;
  int refused;
};

static inline int yara_toe_project(
    const struct yara_toe_cut *c,
    const struct yara_toe_term *terms,
    int n,
    struct yara_toe_z *z) {
  if (!z) return YARA_FAIL;
  z->re = 0;
  z->im = 0;
  z->nterms = n;
  z->refused = 0;
  if (!c || c->action_is_door || !c->signer || !c->signer[0]) {
    z->refused = 1;
    return YARA_FAIL;
  }
  (void)c->intent;
  (void)c->pattern;
  if (n < 0) n = 0;
  for (int i = 0; i < n; i++) {
    if (terms[i].passed) {
      z->re += terms[i].re;
      z->im += terms[i].im;
    }
  }
  return YARA_OK;
}

#endif
