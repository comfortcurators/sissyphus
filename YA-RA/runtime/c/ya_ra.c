#include "ya_ra.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef _WIN32
#include <unistd.h>
#define YARA_EXISTS(p) (access((p), F_OK) == 0)
#else
#include <io.h>
#define YARA_EXISTS(p) (_access((p), 0) == 0)
#endif

struct yara_shot yara_shots[YARA_MAX_SHOTS];
int yara_nshots = 0;

int yara_words(const char *s) {
  int n = 0, in = 0;
  if (!s) return 0;
  for (; *s; s++) {
    if (*s != ' ' && *s != '\t' && *s != '\n' && *s != '\r') {
      if (!in) { n++; in = 1; }
    } else in = 0;
  }
  return n;
}

static int file_contains(const char *path, const char *needle) {
  FILE *f = fopen(path, "rb");
  if (!f) return 0;
  if (fseek(f, 0, SEEK_END) != 0) { fclose(f); return 0; }
  long n = ftell(f);
  if (n < 0) { fclose(f); return 0; }
  rewind(f);
  char *buf = (char *)malloc((size_t)n + 1);
  if (!buf) { fclose(f); return 0; }
  size_t got = fread(buf, 1, (size_t)n, f);
  buf[got] = 0;
  fclose(f);
  int ok = needle && strstr(buf, needle) != NULL;
  free(buf);
  return ok;
}

static int file_eq(const char *path, const char *want) {
  FILE *f = fopen(path, "rb");
  if (!f) return 0;
  if (fseek(f, 0, SEEK_END) != 0) { fclose(f); return 0; }
  long n = ftell(f);
  if (n < 0) { fclose(f); return 0; }
  rewind(f);
  char *buf = (char *)malloc((size_t)n + 1);
  if (!buf) { fclose(f); return 0; }
  size_t got = fread(buf, 1, (size_t)n, f);
  buf[got] = 0;
  fclose(f);
  int ok = want && strcmp(buf, want) == 0;
  free(buf);
  return ok;
}

static int run_check(const struct yara_door *d, const struct yara_check *c) {
  if (!c) return 0;
  if (c->kind == YARA_CHECK_WORDS) {
    const char *text = d->intent;
    if (c->a && strcmp(c->a, "pattern") == 0) text = d->pattern;
    int n = c->b ? atoi(c->b) : 17;
    return yara_words(text) <= n;
  }
  if (c->kind == YARA_CHECK_EXISTS) {
    return c->a && YARA_EXISTS(c->a);
  }
  if (c->kind == YARA_CHECK_RUN) {
    if (!c->a) return 0;
    return system(c->a) == 0;
  }
  if (c->kind == YARA_CHECK_CONTAINS) {
    return c->a && c->b && file_contains(c->a, c->b);
  }
  if (c->kind == YARA_CHECK_EQ) {
    return c->a && c->b && file_eq(c->a, c->b);
  }
  return 0;
}

int yara_measure(const struct yara_door *d) {
  yara_nshots = 0;
  if (!d || !d->intent || !d->pattern || !d->signer) return YARA_FAIL;
  if (!d->signer[0]) return YARA_FAIL;
  if (yara_words(d->intent) > 17) return YARA_FAIL;
  if (yara_words(d->pattern) > 17) return YARA_FAIL;

  int any_ok = 0;
  int all_ok = 1;
  int n = d->nchecks;
  if (n < 0) n = 0;
  if (n > YARA_MAX_SHOTS) n = YARA_MAX_SHOTS;
  for (int i = 0; i < n; i++) {
    const struct yara_check *c = &d->checks[i];
    int passed = run_check(d, c);
    yara_shots[i].passed = passed;
    yara_shots[i].re = c->amp_re;
    yara_shots[i].im = c->amp_im;
    yara_nshots = i + 1;
    if (passed) any_ok = 1;
    else all_ok = 0;
  }
  if (n == 0) return YARA_OK;
  if (d->measure_any) return any_ok ? YARA_OK : YARA_FAIL;
  (void)d->zero;
  (void)d->glimpse;
  return all_ok ? YARA_OK : YARA_FAIL;
}
