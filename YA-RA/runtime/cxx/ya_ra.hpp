// YA|RA language runtime — C++
#pragma once
#include <string>

namespace yara {

enum class Measure { All, Any };

struct Door {
  std::string intent;
  std::string pattern;
  std::string signer;
  std::string timestamp;
  std::string rv{"rv0.1.0"};
  Measure how{Measure::All};
  bool zero{false};
  bool glimpse{false};

  static int words(const std::string &s) {
    int n = 0;
    bool in = false;
    for (char c : s) {
      if (c != ' ' && c != '\t' && c != '\n') {
        if (!in) { n++; in = true; }
      } else in = false;
    }
    return n;
  }

  bool measure_now() const {
    if (intent.empty() || pattern.empty() || signer.empty()) return false;
    if (words(intent) > 17 || words(pattern) > 17) return false;
    return true;
  }

  bool measure() const { return measure_now(); }
};

} // namespace yara
