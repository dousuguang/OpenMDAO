"""Define the LinearBlockJac class."""
from openmdao.solvers.solver import BlockLinearSolver


class LinearBlockJac(BlockLinearSolver):
    """
    Linear block Jacobi solver.
    """

    SOLVER = 'LN: LNBJ'

    def _iter_execute(self):
        """
        Perform the operations in the iteration loop.
        """
        system = self._system
        mode = self._mode
        vec_names = self._vec_names

        if mode == 'fwd':

            for vec_name in vec_names:
                system._transfer(vec_name, mode)
            for subsys in system._subsystems_myproc:
                scope_out, scope_in = system._get_scope(subsys)
                subsys._apply_linear(vec_names, mode, scope_out, scope_in)
            for vec_name in vec_names:
                b_vec = system._vectors['residual'][vec_name]
                b_vec *= -1.0
                b_vec += self._rhs_vecs[vec_name]

            for subsys in system._subsystems_myproc:

                subsys._solve_linear(vec_names, mode)

            # The changeover to DenseJacobian as the default component jacobian short-circuits
            # the scoping of the vectors under apply_linear, so we have to be careful in
            # cleaing up.
            # Here, clear out all inputs before we move onto the apply_linear for norm calculation.
            #for vec_name in vec_names:
                #for subsys in system._subsystems_myproc:
                    #subsys._vectors['input'][vec_name].set_const(0.0)
                    #print(subsys.name)
                    ##if subsys.name == 'sub':
                        ##system._vectors['output'][vec_name]['sub.d2.y2'][0] = 0.0
                        ##subsys._vectors['output'][vec_name].set_const(0.0)

            print('END Block Jac', system._vectors['input']['linear'].get_data(), system._vectors['output']['linear'].get_data(), system._vectors['residual']['linear'].get_data())

        elif mode == 'rev':
            for subsys in system._subsystems_myproc:
                scope_out, scope_in = system._get_scope(subsys)
                subsys._apply_linear(vec_names, mode, scope_out, scope_in)
            for vec_name in vec_names:
                system._transfer(vec_name, mode)

                b_vec = system._vectors['output'][vec_name]
                b_vec *= -1.0
                b_vec += self._rhs_vecs[vec_name]
            for subsys in system._subsystems_myproc:
                subsys._solve_linear(vec_names, mode)
