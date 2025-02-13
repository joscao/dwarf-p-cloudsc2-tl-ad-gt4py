# -*- coding: utf-8 -*-
from gt4py.cartesian import gtscript

from ifs_physics_common.framework.stencil import function_collection
from ifs_physics_common.utils.f2py import ported_function


@ported_function(from_file="cloudsc2_tl/cuadjtqstl.F90", from_line=337, to_line=369)
@function_collection("cuadjtqs_tl_0")
@gtscript.function
def cuadjtqs_tl_0(ap, ap_i, t, t_i, q, q_i, z3es, z4es, z5alcp, zaldcp):
    from __externals__ import R2ES, RETV, RTT, ZQMAX

    qp = 1 / ap
    qp_i = - ap_i / ap**2
    foeew = R2ES * exp(z3es * (t - RTT) / (t - z4es))
    foeew_i = foeew * z3es * t_i * (RTT - z4es) / (t - z4es) ** 2
    qsat = qp * foeew
    qsat_i = qp_i * foeew + qp * foeew_i
    if qsat > ZQMAX:
        qsat = ZQMAX
        qsat_i = 0.0
    cor = 1 / (1 - RETV * qsat)
    cor_i = RETV * qsat_i / (1 - RETV * qsat) ** 2
    qsat_i = qsat_i * cor + qsat * cor_i
    qsat *= cor
    z2s = z5alcp / (t - z4es) ** 2
    z2s_i = -2 * z5alcp * t_i / (t - z4es) ** 3
    cond = (q - qsat) / (1 + qsat * cor * z2s)
    cond_i = (q_i - qsat_i) / (1 + qsat * cor * z2s) - (q - qsat) * (
        qsat_i * cor * z2s + qsat * cor_i * z2s + qsat * cor * z2s_i
    ) / (1 + qsat * cor * z2s) ** 2
    t += zaldcp * cond
    t_i += zaldcp * cond_i
    q -= cond
    q_i -= cond_i

    return t, t_i, q, q_i


@ported_function(from_file="cloudsc2_tl/cuadjtqstl.F90", from_line=10, to_line=482)
@function_collection("cuadjtqs_tl")
@gtscript.function
def cuadjtqs_tl(ap, ap_i, t, t_i, q, q_i):
    from __externals__ import (
        ICALL,
        R3IES,
        R3LES,
        R4IES,
        R4LES,
        R5ALSCP,
        R5ALVCP,
        RALSDCP,
        RALVDCP,
        RTT,
    )

    if t > RTT:
        z3es = R3LES
        z4es = R4LES
        z5alcp = R5ALVCP
        zaldcp = RALVDCP
    else:
        z3es = R3IES
        z4es = R4IES
        z5alcp = R5ALSCP
        zaldcp = RALSDCP

    if ICALL == 0:
        t, t_i, q, q_i = cuadjtqs_tl_0(ap, ap_i, t, t_i, q, q_i, z3es, z4es, z5alcp, zaldcp)
        t, t_i, q, q_i = cuadjtqs_tl_0(ap, ap_i, t, t_i, q, q_i, z3es, z4es, z5alcp, zaldcp)
        return t, t_i, q, q_i
