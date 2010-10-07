
%module pyshapemerge2d
#ifndef SwigPyIterator
/*Work around SWIG-bug 1863647*/
#define SwigPyIterator shapemerge2d_SwigPyIterator
#endif

%{
#include <exception>
#include <string>
%}
%include "exception.i"
%include "std_string.i"

std::string colorize_heightmap(const std::string& s);


%exception {
  try {
    $action
  } catch (const std::exception& e) {
    SWIG_exception(SWIG_RuntimeError, e.what());
  }
}

