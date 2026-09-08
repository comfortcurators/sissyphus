/* YA|RA language runtime — C. Polarity: 0 = ok. */
#ifndef YA_RA_H
#define YA_RA_H

enum {
  YARA_OK = 0,
  YARA_FAIL = 1
};

enum {
  YARA_CHECK_WORDS = 1,
  YARA_CHECK_EXISTS = 2,
  YARA_CHECK_RUN = 3,
  YARA_CHECK_CONTAINS = 4,
  YARA_CHECK_EQ = 5
};

struct yara_check {
  int kind;
  const char *a;
  const char *b;
  double amp_re;
  double amp_im;
};

struct yara_door {
  const char *intent;
  const char *pattern;
  const char *signer;
  const char *timestamp;
  const char *rv;
  int measure_any;
  int zero;
  int glimpse;
  const struct yara_check *checks;
  int nchecks;
};

struct yara_shot {
  int passed;
  double re;
  double im;
};

#define YARA_MAX_SHOTS 64
extern struct yara_shot yara_shots[YARA_MAX_SHOTS];
extern int yara_nshots;

extern int yara_missing_provenance; /* 1 when signer is absent; not a fail */

int yara_words(const char *s);
int yara_measure(const struct yara_door *d);

#endif
