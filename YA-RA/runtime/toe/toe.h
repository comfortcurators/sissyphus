/* YA|RA cut against the single action
 * The slide writes Z = integral D(Fields) exp(iS).
 * That integral is unsigned. YA|RA will not treat it as a door.
 */
#ifndef YA_RA_TOE_H
#define YA_RA_TOE_H

struct yara_toe_cut {
  const char *intent;
  const char *pattern;
  const char *signer;
  int action_is_door;
};

static inline int yara_toe_reject_unsigned(const struct yara_toe_cut *c) {
  if (!c) return 1;
  if (c->action_is_door) return 1;
  if (!c->signer || !c->signer[0]) return 1;
  return 0;
}

#endif
