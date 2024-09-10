find_package(PkgConfig)

PKG_CHECK_MODULES(PC_GR_PYAIS_TOOLKIT gnuradio-pyais_toolkit)

FIND_PATH(
    GR_PYAIS_TOOLKIT_INCLUDE_DIRS
    NAMES gnuradio/pyais_toolkit/api.h
    HINTS $ENV{PYAIS_TOOLKIT_DIR}/include
        ${PC_PYAIS_TOOLKIT_INCLUDEDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/include
          /usr/local/include
          /usr/include
)

FIND_LIBRARY(
    GR_PYAIS_TOOLKIT_LIBRARIES
    NAMES gnuradio-pyais_toolkit
    HINTS $ENV{PYAIS_TOOLKIT_DIR}/lib
        ${PC_PYAIS_TOOLKIT_LIBDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/lib
          ${CMAKE_INSTALL_PREFIX}/lib64
          /usr/local/lib
          /usr/local/lib64
          /usr/lib
          /usr/lib64
          )

include("${CMAKE_CURRENT_LIST_DIR}/gnuradio-pyais_toolkitTarget.cmake")

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(GR_PYAIS_TOOLKIT DEFAULT_MSG GR_PYAIS_TOOLKIT_LIBRARIES GR_PYAIS_TOOLKIT_INCLUDE_DIRS)
MARK_AS_ADVANCED(GR_PYAIS_TOOLKIT_LIBRARIES GR_PYAIS_TOOLKIT_INCLUDE_DIRS)
