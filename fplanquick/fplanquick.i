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

void geomag_free();
double geomag_calc(double latitude,double longitude,double decimal_year,double alt_in_km);

std::string colorize_combine_heightmap(std::vector<std::string>& arr);
PyObject* decode_flightpath(const std::string& buf,int version);
%}

namespace std {
   %template(svector) vector<std::string>;
}

void geomag_free();
double geomag_calc(double latitude,double longitude,double decimal_year,double alt_in_km);
std::string colorize_combine_heightmap(std::vector<std::string>& arr);
PyObject* decode_flightpath(const std::string& buf,int version);


%exception {
  try {
    $action
  } catch (const std::exception& e) {
    SWIG_exception(SWIG_RuntimeError, e.what());
  }
}

