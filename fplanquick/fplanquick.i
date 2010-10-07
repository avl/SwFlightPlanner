%module fplanquick

#ifndef SwigPyIterator
/*Work around SWIG-bug 1863647*/
#define SwigPyIterator fplanquick_SwigPyIterator
#endif

%include "exception.i"
%include "std_string.i"
%include "std_vector.i"

%{
#include <exception>
#include <string>
std::string colorize_combine_heightmap(std::vector<std::string>& arr);
%}

namespace std {
   %template(svector) vector<std::string>;
}

std::string colorize_combine_heightmap(std::vector<std::string>& arr);


%exception {
  try {
    $action
  } catch (const std::exception& e) {
    SWIG_exception(SWIG_RuntimeError, e.what());
  }
}

