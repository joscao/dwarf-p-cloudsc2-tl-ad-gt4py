# -*- coding: utf-8 -*-
from __future__ import annotations
from itertools import repeat
from functools import cached_property
import numpy as np
from typing import TYPE_CHECKING

from ifs_physics_common.framework.components import ImplicitTendencyComponent
from ifs_physics_common.framework.grid import I, J, K
from ifs_physics_common.framework.storage import managed_temporary_storage, zeros
from ifs_physics_common.utils.f2py import ported_method
from ifs_physics_common.utils.numpyx import assign

if TYPE_CHECKING:
    from datetime import timedelta
    from typing import Optional

    from gt4py.cartesian import StencilObject

    from ifs_physics_common.framework.config import GT4PyConfig
    from ifs_physics_common.framework.grid import ComputationalGrid
    from ifs_physics_common.utils.typingx import ParameterDict, PropertyDict, Storage, StorageDict


class Cloudsc2TL(ImplicitTendencyComponent):
    cloudsc2: StencilObject
    klevel: Storage

    def __init__(
        self,
        computational_grid: ComputationalGrid,
        lphylin: bool,
        ldrain1d: bool,
        yoethf_parameters: Optional[ParameterDict] = None,
        yomcst_parameters: Optional[ParameterDict] = None,
        yrecld_parameters: Optional[ParameterDict] = None,
        yrecldp_parameters: Optional[ParameterDict] = None,
        yrephli_parameters: Optional[ParameterDict] = None,
        yrncl_parameters: Optional[ParameterDict] = None,
        yrphnc_parameters: Optional[ParameterDict] = None,
        *,
        enable_checks: bool = True,
        gt4py_config: GT4PyConfig,
    ) -> None:
        super().__init__(computational_grid, enable_checks=enable_checks, gt4py_config=gt4py_config)

        nk = self.computational_grid.grids[I, J, K].shape[2]
        self.klevel = zeros(
            self.computational_grid, (K,), gt4py_config=self.gt4py_config, dtype="int"
        )
        assign(self.klevel[:], np.arange(0, nk + 1))

        externals = {}
        externals.update(yoethf_parameters or {})
        externals.update(yomcst_parameters or {})
        externals.update(yrecld_parameters or {})
        externals.update(yrecldp_parameters or {})
        externals.update(yrephli_parameters or {})
        externals.update(yrncl_parameters or {})
        externals.update(yrphnc_parameters or {})
        externals.update(
            {
                "ICALL": 0,
                "LPHYLIN": lphylin,
                "LDRAIN1D": ldrain1d,
                "NLEV": nk,
                "ZEPS1": 1e-12,
                "ZEPS2": 1e-10,
                "ZQMAX": 0.5,
                "ZSCAL": 0.9,
            }
        )
        self.cloudsc2 = self.compile_stencil("cloudsc2_tl", externals)

    @cached_property
    @ported_method(from_file="cloudsc2_tl/cloudsc2tl.F90", from_line=53, to_line=78)
    def _input_properties(self) -> PropertyDict:
        return {
            "f_eta": {"grid": (K,), "units": ""},
            "f_aph": {"grid": (I, J, K - 1 / 2), "units": "Pa"},
            "f_aph_i": {"grid": (I, J, K - 1 / 2), "units": "Pa"},
            "f_ap": {"grid": (I, J, K), "units": "Pa"},
            "f_ap_i": {"grid": (I, J, K), "units": "Pa"},
            "f_q": {"grid": (I, J, K), "units": "g g^-1"},
            "f_q_i": {"grid": (I, J, K), "units": "g g^-1"},
            "f_qsat": {"grid": (I, J, K), "units": "g g^-1"},
            "f_qsat_i": {"grid": (I, J, K), "units": "g g^-1"},
            "f_t": {"grid": (I, J, K), "units": "K"},
            "f_t_i": {"grid": (I, J, K), "units": "K"},
            "f_ql": {"grid": (I, J, K), "units": "g g^-1"},
            "f_ql_i": {"grid": (I, J, K), "units": "g g^-1"},
            "f_qi": {"grid": (I, J, K), "units": "g g^-1"},
            "f_qi_i": {"grid": (I, J, K), "units": "g g^-1"},
            "f_lude": {"grid": (I, J, K), "units": "kg m^-3 s^-1"},
            "f_lude_i": {"grid": (I, J, K), "units": "kg m^-3 s^-1"},
            "f_lu": {"grid": (I, J, K), "units": "g g^-1"},
            "f_lu_i": {"grid": (I, J, K), "units": "g g^-1"},
            "f_mfu": {"grid": (I, J, K), "units": "kg m^-2 s^-1"},
            "f_mfu_i": {"grid": (I, J, K), "units": "kg m^-2 s^-1"},
            "f_mfd": {"grid": (I, J, K), "units": "kg m^-2 s^-1"},
            "f_mfd_i": {"grid": (I, J, K), "units": "kg m^-2 s^-1"},
            "f_tnd_cml_t": {"grid": (I, J, K), "units": "K s^-1"},
            "f_tnd_cml_t_i": {"grid": (I, J, K), "units": "K s^-1"},
            "f_tnd_cml_q": {"grid": (I, J, K), "units": "K s^-1"},
            "f_tnd_cml_q_i": {"grid": (I, J, K), "units": "K s^-1"},
            "f_tnd_cml_ql": {"grid": (I, J, K), "units": "K s^-1"},
            "f_tnd_cml_ql_i": {"grid": (I, J, K), "units": "K s^-1"},
            "f_tnd_cml_qi": {"grid": (I, J, K), "units": "K s^-1"},
            "f_tnd_cml_qi_i": {"grid": (I, J, K), "units": "K s^-1"},
            "f_supsat": {"grid": (I, J, K), "units": "g g^-1"},
            "f_supsat_i": {"grid": (I, J, K), "units": "g g^-1"},
        }

    @cached_property
    @ported_method(from_file="cloudsc2_tl/cloudsc2tl.F90", from_line=80, to_line=90)
    def _tendency_properties(self) -> PropertyDict:
        return {
            "f_t": {"grid": (I, J, K), "units": "K s^-1"},
            "f_t_i": {"grid": (I, J, K), "units": "K s^-1"},
            "f_q": {"grid": (I, J, K), "units": "g g^-1 s^-1"},
            "f_q_i": {"grid": (I, J, K), "units": "g g^-1 s^-1"},
            "f_ql": {"grid": (I, J, K), "units": "g g^-1 s^-1"},
            "f_ql_i": {"grid": (I, J, K), "units": "g g^-1 s^-1"},
            "f_qi": {"grid": (I, J, K), "units": "g g^-1 s^-1"},
            "f_qi_i": {"grid": (I, J, K), "units": "g g^-1 s^-1"},
        }

    @cached_property
    @ported_method(from_file="cloudsc2_tl/cloudsc2tl.F90", from_line=92, to_line=106)
    def _diagnostic_properties(self) -> PropertyDict:
        return {
            "f_clc": {"grid": (I, J, K), "units": ""},
            "f_clc_i": {"grid": (I, J, K), "units": ""},
            "f_fhpsl": {"grid": (I, J, K - 1 / 2), "units": "J m^-2 s^-1"},
            "f_fhpsl_i": {"grid": (I, J, K - 1 / 2), "units": "J m^-2 s^-1"},
            "f_fhpsn": {"grid": (I, J, K - 1 / 2), "units": "J m^-2 s^-1"},
            "f_fhpsn_i": {"grid": (I, J, K - 1 / 2), "units": "J m^-2 s^-1"},
            "f_fplsl": {"grid": (I, J, K - 1 / 2), "units": "Kg m^-2 s^-1"},
            "f_fplsl_i": {"grid": (I, J, K - 1 / 2), "units": "Kg m^-2 s^-1"},
            "f_fplsn": {"grid": (I, J, K - 1 / 2), "units": "Kg m^-2 s^-1"},
            "f_fplsn_i": {"grid": (I, J, K - 1 / 2), "units": "Kg m^-2 s^-1"},
            "f_covptot": {"grid": (I, J, K), "units": ""},
            "f_covptot_i": {"grid": (I, J, K), "units": ""},
        }

    def array_call(
        self,
        state: StorageDict,
        timestep: timedelta,
        out_tendencies: StorageDict,
        out_diagnostics: StorageDict,
        overwrite_tendencies: dict[str, bool],
    ) -> None:
        with managed_temporary_storage(
            self.computational_grid, *repeat(((I, J), "float"), 9), gt4py_config=self.gt4py_config
        ) as (aph_s, aph_s_i, rfl, rfl_i, sfl, sfl_i, covptot, covptot_i, trpaus):
            aph_s[...] = state["f_aph"][..., -1]
            aph_s_i[...] = state["f_aph_i"][..., -1]
            self.cloudsc2(
                in_ap=state["f_ap"],
                in_ap_i=state["f_ap_i"],
                in_aph=state["f_aph"],
                in_aph_i=state["f_aph_i"],
                in_eta=state["f_eta"],
                in_lu=state["f_lu"],
                in_lu_i=state["f_lu_i"],
                in_lude=state["f_lude"],
                in_lude_i=state["f_lude_i"],
                in_mfd=state["f_mfd"],
                in_mfd_i=state["f_mfd_i"],
                in_mfu=state["f_mfu"],
                in_mfu_i=state["f_mfu_i"],
                in_q=state["f_q"],
                in_q_i=state["f_q_i"],
                in_qi=state["f_qi"],
                in_qi_i=state["f_qi_i"],
                in_ql=state["f_ql"],
                in_ql_i=state["f_ql_i"],
                in_qsat=state["f_qsat"],
                in_qsat_i=state["f_qsat_i"],
                in_supsat=state["f_supsat"],
                in_supsat_i=state["f_supsat_i"],
                in_t=state["f_t"],
                in_t_i=state["f_t_i"],
                in_tnd_cml_q=state["f_tnd_cml_q"],
                in_tnd_cml_q_i=state["f_tnd_cml_q_i"],
                in_tnd_cml_qi=state["f_tnd_cml_qi"],
                in_tnd_cml_qi_i=state["f_tnd_cml_qi_i"],
                in_tnd_cml_ql=state["f_tnd_cml_ql"],
                in_tnd_cml_ql_i=state["f_tnd_cml_ql_i"],
                in_tnd_cml_t=state["f_tnd_cml_t"],
                in_tnd_cml_t_i=state["f_tnd_cml_t_i"],
                out_clc=out_diagnostics["f_clc"],
                out_clc_i=out_diagnostics["f_clc_i"],
                out_covptot=out_diagnostics["f_covptot"],
                out_covptot_i=out_diagnostics["f_covptot_i"],
                out_fhpsl=out_diagnostics["f_fhpsl"],
                out_fhpsl_i=out_diagnostics["f_fhpsl_i"],
                out_fhpsn=out_diagnostics["f_fhpsn"],
                out_fhpsn_i=out_diagnostics["f_fhpsn_i"],
                out_fplsl=out_diagnostics["f_fplsl"],
                out_fplsl_i=out_diagnostics["f_fplsl_i"],
                out_fplsn=out_diagnostics["f_fplsn"],
                out_fplsn_i=out_diagnostics["f_fplsn_i"],
                out_tnd_q=out_tendencies["f_q"],
                out_tnd_q_i=out_tendencies["f_q_i"],
                out_tnd_qi=out_tendencies["f_qi"],
                out_tnd_qi_i=out_tendencies["f_qi_i"],
                out_tnd_ql=out_tendencies["f_ql"],
                out_tnd_ql_i=out_tendencies["f_ql_i"],
                out_tnd_t=out_tendencies["f_t"],
                out_tnd_t_i=out_tendencies["f_t_i"],
                tmp_aph_s=aph_s,
                tmp_aph_s_i=aph_s_i,
                tmp_covptot=covptot,
                tmp_covptot_i=covptot_i,
                tmp_klevel=self.klevel,
                tmp_rfl=rfl,
                tmp_rfl_i=rfl_i,
                tmp_sfl=sfl,
                tmp_sfl_i=sfl_i,
                tmp_trpaus=trpaus,
                dt=timestep.total_seconds(),
                origin=(0, 0, 0),
                domain=self.computational_grid.grids[I, J, K - 1 / 2].shape,
                validate_args=self.gt4py_config.validate_args,
                exec_info=self.gt4py_config.exec_info,
            )
