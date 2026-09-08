#include "ya_ra.h"

int yara_words(const char *s) {
  int n = 0, in = 0;
  if (!s) return 0;
  for (; *s; s++) {
    if (*s != ' ' && *s != '\t' && *s != '\n') {
      if (!in) { n++; in = 1; }
    } else in = 0;
  }
  return n;
}

int yara_measure(const struct yara_door *d) {
  if (!d || !d->intent || !d->pattern || !d->signer) return 0;
  if (yara_words(d->intent) > 17) return 0;
  if (yara_words(d->pattern) > 17) return 0;
  if (!d->signer[0]) return 0;
  return 1;
}
