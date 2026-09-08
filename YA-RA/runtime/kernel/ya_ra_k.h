/* YA|RA language kernel — freestanding
 * Cura: to see. Observation is the only entry.
 * Not a Linux driver. Link with or without libc.
 */
#ifndef YA_RA_K_H
#define YA_RA_K_H

struct yara_k_door {
  const char *intent;
  const char *pattern;
  const char *signer;
  const char *rv;
};

static inline int yara_k_words(const char *s) {
  int n = 0, in = 0;
  if (!s) return 0;
  for (; *s; ++s) {
    if (*s != ' ' && *s != '\t' && *s != '\n') {
      if (!in) { ++n; in = 1; }
    } else in = 0;
  }
  return n;
}

static inline int yara_k_measure(const struct yara_k_door *d) {
  if (!d || !d->intent || !d->pattern || !d->signer) return 1;
  if (yara_k_words(d->intent) > 17) return 1;
  if (yara_k_words(d->pattern) > 17) return 1;
  return 0;
}

#endif
