/* YA|RA language kernel — syscall ABI. Freestanding C.
 * Observation is the only entry. Polarity: 0 = ok.
 *
 *   1 WORDS    arg: const char *           -> word count (not a status)
 *   2 MEASURE  arg: const struct yara_k_door * -> YARA_K_OK / YARA_K_FAIL
 *
 * Hosted code may overlay exists via yara_k_set_exists.
 * This is the language kernel, not a Linux driver.
 */
#ifndef YA_RA_K_H
#define YA_RA_K_H

#define YARA_K_OK   0
#define YARA_K_FAIL 1

#define YARA_SYS_WORDS   1
#define YARA_SYS_MEASURE 2
#define YARA_SYS_EXISTS  3

struct yara_k_door {
  const char *intent;
  const char *pattern;
  const char *signer;
  const char *timestamp;
  const char *rv;
  int measure_any;
};

typedef int (*yara_k_exists_fn)(const char *path);

static yara_k_exists_fn yara_k_exists_hook;

static inline void yara_k_set_exists(yara_k_exists_fn fn) {
  yara_k_exists_hook = fn;
}

static inline int yara_k_words(const char *s) {
  int n = 0, in = 0;
  if (!s) return 0;
  for (; *s; ++s) {
    if (*s != ' ' && *s != '\t' && *s != '\n' && *s != '\r') {
      if (!in) { ++n; in = 1; }
    } else in = 0;
  }
  return n;
}

static inline int yara_k_measure(const struct yara_k_door *d) {
  if (!d || !d->intent || !d->pattern || !d->signer) return YARA_K_FAIL;
  if (!d->signer[0]) return YARA_K_FAIL;
  if (yara_k_words(d->intent) > 17) return YARA_K_FAIL;
  if (yara_k_words(d->pattern) > 17) return YARA_K_FAIL;
  (void)d->measure_any;
  (void)d->timestamp;
  (void)d->rv;
  return YARA_K_OK;
}

static inline int yara_k_syscall(int nr, void *arg) {
  if (nr == YARA_SYS_WORDS) return yara_k_words((const char *)arg);
  if (nr == YARA_SYS_MEASURE) return yara_k_measure((const struct yara_k_door *)arg);
  if (nr == YARA_SYS_EXISTS) {
    if (!yara_k_exists_hook || !arg) return YARA_K_FAIL;
    return yara_k_exists_hook((const char *)arg) ? YARA_K_OK : YARA_K_FAIL;
  }
  return YARA_K_FAIL;
}

#endif
