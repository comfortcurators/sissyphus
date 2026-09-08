/* YA|RA language runtime — C */
#ifndef YA_RA_H
#define YA_RA_H

struct yara_door {
  const char *intent;
  const char *pattern;
  const char *signer;
  const char *timestamp;
  const char *rv;
  int measure_any;
  int zero;
  int glimpse;
};

int yara_words(const char *s);
int yara_measure(const struct yara_door *d);

#endif
