# Copyright (C) 2010-2011 Power System Engineering Research Center
# Copyright (C) 2010-2011 Richard Lincoln
#
# PYPOWER is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# PYPOWER is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY], without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PYPOWER. If not, see <http://www.gnu.org/licenses/>.

from pymosek import mosekopt

def mosek_options(overrides=None, ppopt=None):
    """Sets options for MOSEK.

    Inputs are all optional, second argument must be either a string
    (FNAME) or a vector (ppopt):

        OVERRIDES - struct containing values to override the defaults
        FNAME - name of user-supplied function called after default
            options are set to modify them. Calling syntax is:
                MODIFIED_OPT = FNAME(DEFAULT_OPT)
        ppopt - MATPOWER options vector, uses the following entries:
            OPF_VIOLATION (16)  - used to set opt.MSK_DPAR_INTPNT_TOL_PFEAS
            VERBOSE (31)        - not currently used here
            MOSEK_MAX_IT (112)  - used to set opt.MSK_IPAR_INTPNT_MAX_ITERATIONS
            MOSEK_GAP_TOL (113) - used to set opt.MSK_DPAR_INTPNT_TOL_REL_GAP
            MOSEK_MAX_TIME (114) - used to set opt.MSK_DPAR_OPTIMIZER_MAX_TIME
            MOSEK_NUM_THREADS (115) - used to set opt.MSK_IPAR_INTPNT_NUM_THREADS
            MOSEK_OPT (116)     - user option file, if ppopt(116) is non-zero
                non-zero it is apped to 'mosek_user_options_' to form
                the name of a user-supplied function used as FNAME
                described above, except with calling syntax:
                    MODIFIED_OPT = FNAME(DEFAULT_OPT, ppopt)

    Output is a param dict to pass to MOSEKOPT.

    Example:

    If PPOPT(116) = 3, then after setting the default MOSEK options,
    MOSEK_OPTIONS will execute the following user-defined function
    to allow option overrides:

        opt = mosek_user_options_3(opt, ppopt)

    The contents of mosek_user_options_3.m, could be something like:

        def mosek_user_options_3(opt, ppopt):
            opt = {}
            opt.MSK_DPAR_INTPNT_TOL_DFEAS   = 1e-9
            opt.MSK_IPAR_SIM_MAX_ITERATIONS = 5000000
            return opt

    See the Parameters reference in Appix E of "The MOSEK
    optimization toolbox for MATLAB manaul" for
    details on the available options.

        U{http://www.mosek.com/documentation/}

    @see C{mosekopt}, C{ppoption}.

    @see: U{http://www.pserc.cornell.edu/matpower/}
    """
    ##-----  initialization and arg handling  -----
    ## defaults
    verbose = 2
    gaptol  = 0
    fname   = ''

    ## get symbolic constant names
    r, res = mosekopt('symbcon echo(0)')
    sc = res['symbcon']

    ## second argument
    if ppopt == None:
        if isinstance(ppopt, basestring):        ## 2nd arg is FNAME (string)
            fname = ppopt
            have_ppopt = False
        else:                    ## 2nd arg is ppopt (MATPOWER options vector)
            have_ppopt = True
            ## (make default OPF_VIOLATION correspond to default MOSEK intpnt_tol_pfeas)
            verbose = ppopt['VERBOSE']
            if ppopt['MOSEK_OPT']:
                fname = 'mosek_user_options_#d' # ppopt['MOSEK_OPT']
    else:
        have_ppopt = False

    opt = {}
    ##-----  set default options for MOSEK  -----
    ## solution algorithm
    if have_ppopt:
        alg = ppopt['MOSEK_LP_ALG']
        if alg == sc['MSK_OPTIMIZER_FREE'] or \
            alg == sc['MSK_OPTIMIZER_INTPNT'] or \
            alg == sc['MSK_OPTIMIZER_PRIMAL_SIMPLEX'] or \
            alg == sc['MSK_OPTIMIZER_DUAL_SIMPLEX'] or \
            alg == sc['MSK_OPTIMIZER_PRIMAL_DUAL_SIMPLEX'] or \
            alg == sc['MSK_OPTIMIZER_FREE_SIMPLEX'] or \
            alg == sc['MSK_OPTIMIZER_CONCURRENT']:
                opt['MSK_IPAR_OPTIMIZER'] = alg
        else:
            opt['MSK_IPAR_OPTIMIZER'] = sc['MSK_OPTIMIZER_FREE'];

        ## (make default OPF_VIOLATION correspond to default MSK_DPAR_INTPNT_TOL_PFEAS)
        opt['MSK_DPAR_INTPNT_TOL_PFEAS'] = ppopt['OPF_VIOLATION'] / 500
        if ppopt['MOSEK_MAX_IT']:
            opt['MSK_IPAR_INTPNT_MAX_ITERATIONS'] = ppopt['MOSEK_MAX_IT']

        if ppopt['MOSEK_GAP_TOL']:
            opt['MSK_DPAR_INTPNT_TOL_REL_GAP'] = ppopt['MOSEK_GAP_TOL']

        if ppopt['MOSEK_MAX_TIME']:
            opt['MSK_DPAR_OPTIMIZER_MAX_TIME'] = ppopt['MOSEK_MAX_TIME']

        if ppopt['MOSEK_NUM_THREADS']:
            opt['MSK_IPAR_INTPNT_NUM_THREADS'] = ppopt['MOSEK_NUM_THREADS']
    else:
        opt['MSK_IPAR_OPTIMIZER'] = sc['MSK_OPTIMIZER_FREE']

    # opt['MSK_DPAR_INTPNT_TOL_PFEAS'] = 1e-8       ## primal feasibility tol
    # opt['MSK_DPAR_INTPNT_TOL_DFEAS'] = 1e-8       ## dual feasibility tol
    # opt['MSK_DPAR_INTPNT_TOL_MU_RED'] = 1e-16     ## relative complementarity gap tol
    # opt['MSK_DPAR_INTPNT_TOL_REL_GAP'] = 1e-8     ## relative gap termination tol
    # opt['MSK_IPAR_INTPNT_MAX_ITERATIONS'] = 400   ## max iterations for int point
    # opt['MSK_IPAR_SIM_MAX_ITERATIONS'] = 10000000 ## max iterations for simplex
    # opt['MSK_DPAR_OPTIMIZER_MAX_TIME'] = -1       ## max time allowed (< 0 --> Inf)
    # opt['MSK_IPAR_INTPNT_NUM_THREADS'] = 1        ## number of threads
    # opt['MSK_IPAR_PRESOLVE_USE'] = sc['MSK_PRESOLVE_MODE_OFF']

    # if verbose == 0:
    #     opt['MSK_IPAR_LOG'] = 0
    #

    ##-----  call user function to modify defaults  -----
    if len(fname) > 0:
        if have_ppopt:
            opt = feval(fname, opt, ppopt)
        else:
            opt = feval(fname, opt)

    ##-----  apply overrides  -----
    if overrides is not None:
        names = overrides.keys()
        for k in range(len(names)):
            opt[names[k]] = overrides[names[k]]


def feval(funcName, *args, **kw_args):
    return eval(funcName)(*args, **kw_args)