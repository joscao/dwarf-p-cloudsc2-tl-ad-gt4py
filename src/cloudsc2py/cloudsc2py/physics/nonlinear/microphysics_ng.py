# -*- coding: utf-8 -*-
from functools import partial
from typing import Dict, Optional, TYPE_CHECKING

from gt4py import gtscript

from cloudsc2py.framework.components import ImplicitTendencyComponent
from cloudsc2py.framework.stencil import (
    function_collection,
    stencil_collection,
)
from cloudsc2py.utils.f2py import ported_method
from cloudsc2py.utils.storage import get_array

if TYPE_CHECKING:
    from datetime import timedelta

    from sympl._core.typingx import PropertyDict

    from cloudsc2py.framework.grid import Grid
    from cloudsc2py.framework.options import BackendOptions, StorageOptions
    from cloudsc2py.utils.typingx import ArrayDict, ParameterDict


class Cloudsc2NL(ImplicitTendencyComponent):
    def __init__(
        self,
        grid: "Grid",
        ldphylin: bool,
        ldrain1d: bool,
        yoethf_parameters: Optional["ParameterDict"] = None,
        yomcst_parameters: Optional["ParameterDict"] = None,
        yrecld_parameters: Optional["ParameterDict"] = None,
        yrecldp_parameters: Optional["ParameterDict"] = None,
        yrephli_parameters: Optional["ParameterDict"] = None,
        yrphnc_parameters: Optional["ParameterDict"] = None,
        *,
        enable_checks: bool = True,
        backend: str = "numpy",
        backend_options: Optional["BackendOptions"] = None,
        storage_options: Optional["StorageOptions"] = None,
    ) -> None:
        super().__init__(
            grid,
            enable_checks=enable_checks,
            backend=backend,
            backend_options=backend_options,
            storage_options=storage_options,
        )

        externals = {
            "ICALL": 0,
            "LDPHYLIN": ldphylin,
            "LDRAIN1D": ldrain1d,
            "ZEPS1": 1e-12,
            "ZEPS2": 1e-10,
            "ZQMAX": 0.5,
            "ZSCAL": 0.9,
        }
        externals.update(yoethf_parameters or {})
        externals.update(yomcst_parameters or {})
        externals.update(yrecld_parameters or {})
        externals.update(yrecldp_parameters or {})
        externals.update(yrephli_parameters or {})
        externals.update(yrphnc_parameters or {})
        self.bo.externals.update(externals)

        self.cloudsc = self.compile_stencil("cloudsc2_nl")

        # allocate temporary 2d arrays
        allocate_f = partial(
            get_array,
            self.grid,
            (self.grid.dims_x, self.grid.dims_y),
            backend=backend,
            dtype=self.so.dtypes.float,
            storage_options=self.so,
        )
        self.temporary_fields = {"tmp_trpaus": allocate_f()}

    @property
    @ported_method(
        from_file="cloudsc2_nl/cloudsc_driver_mod.F90",
        from_line=94,
        to_line=107,
    )
    @ported_method(
        from_file="cloudsc2_nl/cloudsc2.F90", from_line=50, to_line=66
    )
    def input_properties(self) -> "PropertyDict":
        dims = (self.grid.dims_x, self.grid.dims_y, self.grid.dims_z)
        dims_zh = (self.grid.dims_x, self.grid.dims_y, self.grid.dims_zh)
        return {
            "f_eta": {"dims": dims[2:], "units": ""},
            "f_aph": {"dims": dims_zh, "units": "Pa"},
            "f_ap": {"dims": dims, "units": "Pa"},
            "f_q": {"dims": dims, "units": "g g^-1"},
            "f_qsat": {"dims": dims, "units": "g g^-1"},
            "f_t": {"dims": dims, "units": "K"},
            "f_ql": {"dims": dims, "units": "g g^-1"},
            "f_qi": {"dims": dims, "units": "g g^-1"},
            "f_lude": {"dims": dims, "units": "kg m^-3 s^-1"},
            "f_lu": {"dims": dims, "units": "g g^-1"},
            "f_mfu": {"dims": dims, "units": "kg m^-2 s^-1"},
            "f_mfd": {"dims": dims, "units": "kg m^-2 s^-1"},
            "f_cml_tnd_t": {"dims": dims, "units": "K s^-1"},
            "f_cml_tnd_q": {"dims": dims, "units": "K s^-1"},
            "f_cml_tnd_ql": {"dims": dims, "units": "K s^-1"},
            "f_cml_tnd_qi": {"dims": dims, "units": "K s^-1"},
            "f_supsat": {"dims": dims, "units": "g g^-1"},
        }

    @property
    @ported_method(
        from_file="cloudsc2_nl/cloudsc2.F90", from_line=70, to_line=73
    )
    def tendency_properties(self) -> "PropertyDict":
        dims = (self.grid.dims_x, self.grid.dims_y, self.grid.dims_z)
        return {
            "f_t": {"dims": dims, "units": "K s^-1"},
            "f_q": {"dims": dims, "units": "g g^-1 s^-1"},
            "f_ql": {"dims": dims, "units": "g g^-1 s^-1"},
            "f_qi": {"dims": dims, "units": "g g^-1 s^-1"},
        }

    @property
    @ported_method(
        from_file="cloudsc2_nl/cloudsc2.F90", from_line=74, to_line=80
    )
    def diagnostic_properties(self) -> "PropertyDict":
        dims = (self.grid.dims_x, self.grid.dims_y, self.grid.dims_z)
        dims_zh = (self.grid.dims_x, self.grid.dims_y, self.grid.dims_zh)
        return {
            "f_clc": {"dims": dims, "units": ""},
            "f_fhpsl": {"dims": dims_zh, "units": "J m^-2 s^-1"},
            "f_fhpsn": {"dims": dims_zh, "units": "J m^-2 s^-1"},
            "f_fplsl": {"dims": dims_zh, "units": "Kg m^-2 s^-1"},
            "f_fplsn": {"dims": dims_zh, "units": "Kg m^-2 s^-1"},
            "f_covptot": {"dims": dims, "units": ""},
        }

    def array_call(
        self,
        state: "ArrayDict",
        timestep: "timedelta",
        out_tendencies: "ArrayDict",
        out_diagnostics: "ArrayDict",
        overwrite_tendencies: Dict[str, bool],
    ) -> None:
        self.cloudsc(
            in_eta=state["f_eta"],
            in_ap=state["f_ap"],
            in_aph=state["f_aph"],
            in_t=state["f_t"],
            in_q=state["f_q"],
            in_qsat=state["f_qsat"],
            in_ql=state["f_ql"],
            in_qi=state["f_qi"],
            in_lu=state["f_lu"],
            in_lude=state["f_lude"],
            in_mfd=state["f_mfd"],
            in_mfu=state["f_mfu"],
            in_supsat=state["f_supsat"],
            in_tnd_t=state["f_cml_tnd_t"],
            in_tnd_q=state["f_cml_tnd_q"],
            in_tnd_ql=state["f_cml_tnd_ql"],
            in_tnd_qi=state["f_cml_tnd_qi"],
            **self.temporary_fields,
            out_tnd_t=out_tendencies["f_t"],
            out_tnd_q=out_tendencies["f_q"],
            out_tnd_ql=out_tendencies["f_ql"],
            out_tnd_qi=out_tendencies["f_qi"],
            out_clc=out_diagnostics["f_clc"],
            out_fhpsl=out_diagnostics["f_fhpsl"],
            out_fhpsn=out_diagnostics["f_fhpsn"],
            out_fplsl=out_diagnostics["f_fplsl"],
            out_fplsn=out_diagnostics["f_fplsn"],
            out_covptot=out_diagnostics["f_covptot"],
            dt=timestep.total_seconds(),
            origin=(0, 0, 0),
            domain=(self.grid.nx, self.grid.ny, self.grid.nz + 1),
            validate_args=self.bo.validate_args,
            exec_info=self.bo.exec_info,
        )

    @staticmethod
    @ported_method(
        from_file="cloudsc2_nl/cloudsc2.F90", from_line=235, to_line=735
    )
    @stencil_collection("cloudsc2_nl", external_names=["cloudsc2_nl_0"])
    def cloudsc_def(
        in_eta: gtscript.Field[gtscript.K, "ftype"],
        in_ap: gtscript.Field["ftype"],
        in_aph: gtscript.Field["ftype"],
        in_t: gtscript.Field["ftype"],
        in_q: gtscript.Field["ftype"],
        in_qsat: gtscript.Field["ftype"],
        in_ql: gtscript.Field["ftype"],
        in_qi: gtscript.Field["ftype"],
        in_lu: gtscript.Field["ftype"],
        in_lude: gtscript.Field["ftype"],
        in_mfd: gtscript.Field["ftype"],
        in_mfu: gtscript.Field["ftype"],
        in_supsat: gtscript.Field["ftype"],
        in_tnd_t: gtscript.Field["ftype"],
        in_tnd_q: gtscript.Field["ftype"],
        in_tnd_ql: gtscript.Field["ftype"],
        in_tnd_qi: gtscript.Field["ftype"],
        tmp_trpaus: gtscript.Field[gtscript.IJ, "ftype"],
        out_tnd_t: gtscript.Field["ftype"],
        out_tnd_q: gtscript.Field["ftype"],
        out_tnd_ql: gtscript.Field["ftype"],
        out_tnd_qi: gtscript.Field["ftype"],
        out_clc: gtscript.Field["ftype"],
        out_fhpsl: gtscript.Field["ftype"],
        out_fhpsn: gtscript.Field["ftype"],
        out_fplsl: gtscript.Field["ftype"],
        out_fplsn: gtscript.Field["ftype"],
        out_covptot: gtscript.Field["ftype"],
        *,
        dt: "ftype",
    ):
        from __externals__ import ext

        with computation(PARALLEL), interval(0, -1):
            # first guess values for T
            t = in_t + dt * in_tnd_t

        # eta value at tropopause
        with computation(FORWARD), interval(0, 1):
            tmp_trpaus = 0.1
        with computation(FORWARD), interval(0, -2):
            if in_eta[0] > 0.1 and in_eta[0] < 0.4 and t[0, 0, 0] > t[0, 0, 1]:
                tmp_trpaus = in_eta[0]

        with computation(FORWARD):
            with interval(0, 1):
                (
                    out_tnd_t,
                    out_tnd_q,
                    out_tnd_ql,
                    out_tnd_qi,
                    out_clc,
                    out_covptot,
                    covptot,
                    rfl,
                    sfl,
                ) = ext.cloudsc2_nl_0(
                    in_eta,
                    in_ap,
                    in_aph,
                    in_q,
                    in_qsat,
                    in_ql,
                    in_qi,
                    in_lu,
                    in_lude,
                    in_mfd,
                    in_mfu,
                    in_supsat,
                    in_tnd_q,
                    in_tnd_ql,
                    in_tnd_qi,
                    tmp_trpaus,
                    0.0,
                    0.0,
                    0.0,
                    t,
                    dt,
                )
                out_fhpsl = 0.0
                out_fhpsn = 0.0
            with interval(1, -1):
                (
                    out_tnd_t,
                    out_tnd_q,
                    out_tnd_ql,
                    out_tnd_qi,
                    out_clc,
                    out_covptot,
                    covptot,
                    rfl,
                    sfl,
                ) = ext.cloudsc2_nl_0(
                    in_eta,
                    in_ap,
                    in_aph,
                    in_q,
                    in_qsat,
                    in_ql,
                    in_qi,
                    in_lu,
                    in_lude,
                    in_mfd,
                    in_mfu,
                    in_supsat,
                    in_tnd_q,
                    in_tnd_ql,
                    in_tnd_qi,
                    tmp_trpaus,
                    covptot[0, 0, -1],
                    rfl[0, 0, -1],
                    sfl[0, 0, -1],
                    t,
                    dt,
                )
                out_fplsl = rfl[0, 0, -1]
                out_fplsn = sfl[0, 0, -1]
                out_fhpsl = -out_fplsl * ext.RLVTT
                out_fhpsn = -out_fplsn * ext.RLSTT
            with interval(-1, None):
                out_fplsl = rfl[0, 0, -1]
                out_fplsn = sfl[0, 0, -1]
                out_fhpsl = -out_fplsl * ext.RLVTT
                out_fhpsn = -out_fplsn * ext.RLSTT

    @staticmethod
    @function_collection(
        "cloudsc2_nl_0",
        external_names=[
            "ICALL",
            "LDRAIN1D",
            "LEVAPLS2",
            "LDPHYLIN",
            "R2ES",
            "R3IES",
            "R3LES",
            "R4IES",
            "R4LES",
            "R5ALSCP",
            "R5ALVCP",
            "R5IES",
            "R5LES",
            "RALSDCP",
            "RALVDCP",
            "RCLCRIT",
            "RCPD",
            "RD",
            "RETV",
            "RG",
            "RKCONV",
            "RLMIN",
            "RLMLT",
            "RLPTRC",
            "RLSTT",
            "RLVTT",
            "RPECONS",
            "RTICE",
            "RTICECU",
            "RTT",
            "RTWAT",
            "RTWAT_RTICE_R",
            "RTWAT_RTICECU_R",
            "RVTMP2",
            "ZEPS1",
            "ZEPS2",
            "ZQMAX",
            "ZSCAL",
            "cuadjtqs_nl",
        ],
    )
    @gtscript.function
    def cloudsc2_nl_0(
        in_eta,
        in_ap,
        in_aph,
        in_q,
        in_qsat,
        in_ql,
        in_qi,
        in_lu,
        in_lude,
        in_mfd,
        in_mfu,
        in_supsat,
        in_tnd_q,
        in_tnd_ql,
        in_tnd_qi,
        tmp_trpaus,
        covptot,
        rfl,
        sfl,
        t,
        dt,
    ):
        from __externals__ import ext

        # first guess values for q, ql and qi
        q = in_q + dt * in_tnd_q + in_supsat
        ql = in_ql + dt * in_tnd_ql
        qi = in_qi + dt * in_tnd_qi

        # set up constants required
        ckcodtl = 2 * ext.RKCONV * dt
        ckcodti = 5 * ext.RKCONV * dt
        cons2 = 1 / (ext.RG * dt)
        cons3 = ext.RLVTT / ext.RCPD
        meltp2 = ext.RTT + 2

        # parameter for cloud formation
        scalm = ext.ZSCAL * max(in_eta - 0.2, ext.ZEPS1) ** 0.2

        # thermodynamic constants
        dp = in_aph[0, 0, 1] - in_aph[0, 0, 0]
        zz = ext.RCPD + ext.RCPD * ext.RVTMP2 * q
        lfdcp = ext.RLMLT / zz
        lsdcp = ext.RLSTT / zz
        lvdcp = ext.RLVTT / zz

        # calculate dqs/dT correction factor
        if __INLINED(ext.LDPHYLIN or ext.LDRAIN1D):
            if t < ext.RTT:
                fwat = 0.545 * (tanh(0.17 * (t - ext.RLPTRC)) + 1)
                z3es = ext.R3IES
                z4es = ext.R4IES
            else:
                fwat = 1.0
                z3es = ext.R3LES
                z4es = ext.R4LES
            foeew = ext.R2ES * exp(z3es * (t - ext.RTT) / (t - z4es))
            esdp = min(foeew / in_ap, ext.ZQMAX)
        else:
            fwat = ext.foealfa(t)
            foeew = ext.foeewm(t)
            esdp = foeew / in_ap
        facw = ext.R5LES / ((t - ext.R4LES) ** 2)
        faci = ext.R5IES / ((t - ext.R4IES) ** 2)
        fac = fwat * facw + (1 - fwat) * faci
        dqsdtemp = fac * in_qsat / (1 - ext.RETV * esdp)
        corqs = 1 + cons3 * dqsdtemp

        # use clipped state
        qlim = min(q, in_qsat)

        # set up critical value of humidity
        rh1 = 1.0
        rh2 = (
            0.35
            + 0.14 * ((tmp_trpaus - 0.25) / 0.15) ** 2
            + 0.04 * min(tmp_trpaus - 0.25, 0.0) / 0.15
        )
        rh3 = 1.0
        if in_eta < tmp_trpaus:
            crh2 = rh3
        else:
            deta2 = 0.3
            bound1 = tmp_trpaus + deta2
            if in_eta < bound1:
                crh2 = rh3 + (rh2 - rh3) * (in_eta - tmp_trpaus) / deta2
            else:
                deta1 = 0.09 + 0.16 * (0.4 - tmp_trpaus) / 0.3
                bound2 = 1 - deta1
                if in_eta < bound2:
                    crh2 = rh2
                else:
                    crh2 = rh1 + (rh2 - rh1) * sqrt((1 - in_eta) / deta1)

        # allow ice supersaturation at cold temperatures
        if t < ext.RTICE:
            qsat = in_qsat * (1.8 - 0.003 * t)
        else:
            qsat = in_qsat
        qcrit = crh2 * qsat

        # simple uniform distribution of total water from Leutreut & Li (1990)
        qt = q + ql + qi
        if qt < qcrit:
            out_clc = 0.0
            qc = 0.0
        elif qt >= qsat:
            out_clc = 1.0
            qc = (1 - scalm) * (qsat - qcrit)
        else:
            qpd = qsat - qt
            qcd = qsat - qcrit
            out_clc = 1 - sqrt(qpd / (qcd - scalm * (qt - qcrit)))
            qc = (scalm * qpd + (1 - scalm) * qcd) * (out_clc ** 2)

        # add convective component
        gdp = ext.RG / (in_aph[0, 0, 1] - in_aph[0, 0, 0])
        lude = dt * in_lude * gdp
        lo1 = lude[0, 0, 0] >= ext.RLMIN and in_lu[0, 0, 1] >= ext.ZEPS2
        if lo1:
            out_clc += (1 - out_clc[0, 0, 0]) * (
                1 - exp(-lude[0, 0, 0] / in_lu[0, 0, 1])
            )
            qc += lude

        # add compensating subsidence component
        rho = in_ap / (ext.RD * t)
        rodqsdp = -rho * in_qsat / (in_ap - ext.RETV * foeew)
        ldcp = fwat * lvdcp + (1 - fwat) * lsdcp
        dtdzmo = (
            ext.RG * (1 / ext.RCPD - ldcp * rodqsdp) / (1 + ldcp * dqsdtemp)
        )
        dqsdz = dqsdtemp * dtdzmo - ext.RG * rodqsdp
        dqc = min(dt * dqsdz * (in_mfu + in_mfd) / rho, qc)
        qc -= dqc

        # new cloud liquid/ice contents and condensation rates (liquid/ice)
        qlwc = qc * fwat
        qiwc = qc * (1 - fwat)
        condl = (qlwc - ql) / dt
        condi = (qiwc - qi) / dt

        # calculate precipitation overlap
        # simple form based on Maximum Overlap
        covptotn = max(covptot, out_clc)
        covpclr = max(covptotn - out_clc, 0.0)

        # melting of incoming snow
        if sfl != 0:
            cons = cons2 * dp / lfdcp
            snmlt = min(sfl, cons * max(t - meltp2, 0.0))
            rfln = rfl + snmlt
            sfln = sfl - snmlt
            t -= snmlt / cons
        else:
            rfln = rfl
            sfln = sfl

        # diagnostic calculation of rain production from cloud liquid water
        if out_clc > ext.ZEPS2:
            if __INLINED(ext.LEVAPLS2 or ext.LDRAIN1D):
                lcrit = 1.9 * ext.RCLCRIT
            else:
                lcrit = 2.0 * ext.RCLCRIT
            cldl = qlwc / out_clc
            dl = ckcodtl * (1 - exp(-((cldl / lcrit) ** 2)))
            prr = qlwc - out_clc * cldl * exp(-dl)
            qlwc -= prr
        else:
            prr = 0.0

        # diagnostic calculation of snow production from cloud ice
        if out_clc > ext.ZEPS2:
            if __INLINED(ext.LEVAPLS2 or ext.LDRAIN1D):
                icrit = 0.0001
            else:
                icrit = 2 * ext.RCLCRIT
            cldi = qiwc / out_clc
            di = (
                ckcodti
                * exp(0.025 * (t - ext.RTT))
                * (1 - exp(-((cldi / icrit) ** 2)))
            )
            prs = qiwc - out_clc * cldi * exp(-di)
            qiwc -= prs
        else:
            prs = 0.0

        # new precipitation (rain + snow)
        dr = cons2 * dp * (prr + prs)

        # rain fraction (different from cloud liquid water fraction!)
        if t < ext.RTT:
            rfreeze = cons2 * dp * prr
            fwatr = 0.0
        else:
            rfreeze = 0.0
            fwatr = 1.0
        rfln += fwatr * dr
        sfln += (1 - fwatr) * dr

        # precipitation evaporation
        prtot = rfln + sfln
        if (
            prtot > ext.ZEPS2
            and covpclr > ext.ZEPS2
            and (ext.LEVAPLS2 or ext.LDRAIN1D)
        ):
            preclr = prtot * covpclr / covptotn

            # this is the humidity in the moisest zcovpclr region
            qe = in_qsat - (in_qsat - qlim) * covpclr / ((1 - out_clc) ** 2)
            beta = (
                ext.RG
                * ext.RPECONS
                * (
                    sqrt(in_ap[0, 0, 0] / in_aph[0, 0, 1])
                    / 0.00509
                    * preclr
                    / covpclr
                )
                ** 0.5777
            )

            # implicit solution
            b = dt * beta * (in_qsat - qe) / (1 + dt * beta * corqs)

            dtgdp = dt * ext.RG / (in_aph[0, 0, 1] - in_aph[0, 0, 0])
            dpr = min(covpclr * b / dtgdp, preclr)
            preclr -= dpr
            if preclr <= 0:
                covptotn = out_clc
            out_covptot = covptotn

            # warm proportion
            evapr = dpr * rfln / prtot
            rfln -= evapr

            # ice proportion
            evaps = dpr * sfln / prtot
            sfln -= evaps
        else:
            out_covptot = 0.0
            evapr = 0.0
            evaps = 0.0

        # update of T and Q tendencies due to:
        # - condensation/evaporation of cloud water/ice
        # - detrainment of convective cloud condensate
        # - evaporation of precipitation
        # - freezing of rain (impact on T only)
        dqdt = -(condl + condi) + (in_lude + evapr + evaps) * gdp
        dtdt = (
            lvdcp * condl
            + lsdcp * condi
            - (
                lvdcp * evapr
                + lsdcp * evaps
                + in_lude * (fwat * lvdcp + (1 - fwat) * lsdcp)
                - (lsdcp - lvdcp) * rfreeze
            )
            * gdp
        )

        # first guess T and Q
        t += dt * dtdt
        q += dt * dqdt
        qold = q

        # clipping of final qv
        t, q = ext.cuadjtqs_nl(in_ap, t, q)

        # update rain fraction and freezing
        dq = max(qold - q, 0.0)
        dr2 = cons2 * dp * dq
        if t < ext.RTT:
            rfreeze2 = fwat * dr2
            fwatr = 0.0
        else:
            rfreeze2 = 0.0
            fwatr = 1.0
        rn = fwatr * dr2
        sn = (1 - fwatr) * dr2
        condl += fwatr * dq / dt
        condi += (1 - fwatr) * dq / dt
        rfln += rn
        sfln += sn
        rfreeze += rfreeze2

        # calculate output tendencies
        out_tnd_q = -(condl + condi) + (in_lude + evapr + evaps) * gdp
        out_tnd_t = (
            lvdcp * condl
            + lsdcp * condi
            - (
                lvdcp * evapr
                + lsdcp * evaps
                + in_lude * (fwat * lvdcp + (1 - fwat) * lsdcp)
                - (lsdcp - lvdcp) * rfreeze
            )
            * gdp
        )
        out_tnd_ql = (qlwc - ql) / dt
        out_tnd_qi = (qiwc - qi) / dt

        return (
            out_tnd_t,
            out_tnd_q,
            out_tnd_ql,
            out_tnd_qi,
            out_clc,
            out_covptot,
            covptotn,
            rfln,
            sfln,
        )