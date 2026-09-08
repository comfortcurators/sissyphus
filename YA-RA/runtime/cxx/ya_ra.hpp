// YA|RA language runtime — C++. Field is how (measure is the verb).
#pragma once
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <sstream>
#include <string>
#include <vector>

namespace yara {

enum class How { All, Any };

enum class Kind { Words, Exists, Run, Contains, Eq };

struct Amp {
  double re{1.0};
  double im{0.0};
};

struct Check {
  Kind kind{Kind::Words};
  std::string a;
  std::string b;
  Amp amp{};
};

struct Door {
  std::string intent;
  std::string pattern;
  std::string signer;
  std::string timestamp;
  std::string rv{"rv0.2.0"};
  How how{How::All};
  bool zero{false};
  bool glimpse{false};
  std::vector<Check> checks{};

  static int words(const std::string &s) {
    int n = 0;
    bool in = false;
    for (char c : s) {
      if (c != ' ' && c != '\t' && c != '\n' && c != '\r') {
        if (!in) { n++; in = true; }
      } else in = false;
    }
    return n;
  }

  bool run_check(const Check &c) const {
    namespace fs = std::filesystem;
    if (c.kind == Kind::Words) {
      const std::string &text = (c.a == "pattern") ? pattern : intent;
      int n = c.b.empty() ? 17 : std::atoi(c.b.c_str());
      return words(text) <= n;
    }
    if (c.kind == Kind::Exists) return fs::exists(c.a);
    if (c.kind == Kind::Run) return std::system(c.a.c_str()) == 0;
    if (c.kind == Kind::Contains) {
      std::ifstream in(c.a);
      if (!in) return false;
      std::string body((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());
      return body.find(c.b) != std::string::npos;
    }
    if (c.kind == Kind::Eq) {
      std::ifstream in(c.a);
      if (!in) return false;
      std::string body((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());
      return body == c.b;
    }
    return false;
  }

  bool measure() const {
    if (intent.empty() || pattern.empty()) return false;
    if (words(intent) > 17 || words(pattern) > 17) return false;
    if (checks.empty()) return true;
    int ok_n = 0;
    for (const auto &c : checks) if (run_check(c)) ok_n++;
    if (how == How::Any) return ok_n > 0;
    return ok_n == static_cast<int>(checks.size());
  }

  bool ok() const { return measure(); }
};

} // namespace yara
