# Satellite subsystem components for the NUCLEO-H723ZG sim demo (sim/)
register_fprime_module(
    AUTOCODER_INPUTS
        "${CMAKE_CURRENT_LIST_DIR}/EpsCan.fpp"
        "${CMAKE_CURRENT_LIST_DIR}/Adcs.fpp"
        "${CMAKE_CURRENT_LIST_DIR}/Magnetorquer.fpp"
        "${CMAKE_CURRENT_LIST_DIR}/FramParams.fpp"
        "${CMAKE_CURRENT_LIST_DIR}/Detumble.fpp"
    SOURCES
        "${CMAKE_CURRENT_LIST_DIR}/EpsCan.cpp"
        "${CMAKE_CURRENT_LIST_DIR}/Adcs.cpp"
        "${CMAKE_CURRENT_LIST_DIR}/Magnetorquer.cpp"
        "${CMAKE_CURRENT_LIST_DIR}/FramParams.cpp"
        "${CMAKE_CURRENT_LIST_DIR}/Detumble.cpp"
)
