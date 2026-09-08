/* YA|RA cut against the single action.
 *
 * The slide writes Z = ∫ D(Fields) exp(iS). That integral is unsigned.
 * YA|RA will not treat it as a door.
 *
 * Instead it computes a signed sum over attributed checks:
 *   Z = Σ_k amp_k · [check_k passed]
 * Refuse only action_is_door. An empty signer is missing provenance, not a
 * refusal — the Python toe.project() is canonical here and refuses solely on
 * action_is_door, and "unsigned is still language" is the whole stance. This
 * runtime used to additionally refuse on an empty signer, so the same unsigned
 * door was not-refused under `ya-ra measure` and refused under an emitted
 * `--to toe` program: a silent cross-backend split on the one construct the
 * language insists remains valid.
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
  int missing_provenance;
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
  z->missing_provenance = 0;
  if (!c) {
    z->refused = 1;
    return YARA_FAIL;
  }
  /* Envelope, not language. Record it; do not refuse on it. */
  if (!c->signer || !c->signer[0]) z->missing_provenance = 1;
  if (c->action_is_door) {
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
