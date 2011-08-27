import distutils.sysconfig
import os
coreenv = Environment(
	SWIGFLAGS=['-python','-c++'],
    CPPPATH=[distutils.sysconfig.get_python_inc(),
    	os.getcwd()],
    SHLIBPREFIX="",
    CCFLAGS=['-Wall','-ggdb','-std=c++0x']
    )

swig_env = coreenv.Clone()
swig_env.Append(CCFLAGS='-Wno-uninitialized')
swig_env.Append(CCFLAGS='-Wno-sign-compare')
swig_env.Append(CCFLAGS='-Wno-parentheses')
coreenv.Append(CCFLAGS='-O2')
coreenv.SharedLibrary('_fplanquick.so', [
	swig_env.SharedObject("fplanquick/fplanquick.i"),        
    "fplanquick/colorize_heightmap.cpp",
	"fplanquick/flightpath.cpp",
	"fplanquick/Magnetic2010/geomag.cpp",
    ])
    
