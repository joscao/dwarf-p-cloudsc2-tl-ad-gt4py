ecbuild_enable_fortran(REQUIRED MODULE_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/module)

list(APPEND CLOUDSC2_COMMON_SOURCES
  module/parkind1.F90
  module/yoecldp.F90
  module/yomcst.F90
  module/yoethf.F90
  module/yoephli.F90
  module/yoecld.F90
  module/yoecldp.F90
  module/yophnc.F90
  module/yomncl.F90
  module/yomphyder.F90
  module/fcttre_mod.F90
  module/fccld_mod.F90
  module/routines.F90
  module/abor1.F90
  module/timer_mod.F90
  module/mycpu.c
  module/ec_pmon_mod.F90
  module/expand_mod.F90
  module/file_io_mod.F90
  module/hdf5_file_mod.F90
  module/validate_mod.F90
  module/cloudsc2_array_state_mod.F90
  module/cloudsc_mpi_mod.F90
)


if( HAVE_ACC )
    # ========================================================================
    # For OpenACC runs we can ensure global module variables from our utility
    # modules are copied to devices via `!$acc declare copyin(<module_vars>)`
    # However, this requries static linking as per this thread:
    # https://www.pgroup.com/userforum/viewtopic.php?t=7296
    # ========================================================================
    set( LIBRARY_TYPE STATIC )
else()
    set( LIBRARY_TYPE SHARED )
endif()

ecbuild_add_library( TARGET cloudsc2-common-lib
    TYPE ${LIBRARY_TYPE}
    DEFINITIONS
        ${CLOUDSC_DEFINITIONS}
    SOURCES
        ${CLOUDSC2_COMMON_SOURCES}
        $<${HAVE_MPI}:module/cloudsc_mpif.F90>
        $<${HAVE_HDF5}:module/hdf5_file_mod.F90>
    PRIVATE_INCLUDES
        $<${HAVE_HDF5}:${HDF5_Fortran_INCLUDE_DIRS}>
    PUBLIC_INCLUDES
        $<INSTALL_INTERFACE:include>
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<BUILD_INTERFACE:${CMAKE_CURRENT_BINARY_DIR}/module>
    PUBLIC_LIBS
        $<${HAVE_ACC}:OpenACC::OpenACC_Fortran>
        $<${HAVE_OMP}:OpenMP::OpenMP_Fortran>
        $<${HAVE_MPI}:MPI::MPI_Fortran>
        $<${HAVE_HDF5}:hdf5::hdf5_fortran>
)
