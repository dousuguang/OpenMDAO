"""Test the parallel groups."""

from __future__ import division, print_function

import unittest
import numpy

from openmdao.api import Problem, Group, ParallelGroup, ExecComp, IndepVarComp, \
                         ExplicitComponent

try:
    from openmdao.vectors.petsc_vector import PETScVector
except ImportError:
    PETScVector = None

from openmdao.test_suite.groups.parallel_groups import \
    FanOutGrouped, FanInGrouped2, Diamond, ConvergeDiverge, \
    FanOutGroupedVarSets

from openmdao.devtools.testutil import assert_rel_error



@unittest.skipUnless(PETScVector, "PETSc is required.")
class TestParallelGroups(unittest.TestCase):

    N_PROCS = 2

    def test_fan_out_grouped(self):
        prob = Problem(FanOutGrouped())

        of=['c2.y', "c3.y"]
        wrt=['iv.x']

        prob.setup(vector_class=PETScVector, check=False, mode='fwd')
        prob.set_solver_print(level=0)
        prob.run_model()

        J = prob.compute_total_derivs(of=['c2.y', "c3.y"], wrt=['iv.x'])

        assert_rel_error(self, J['c2.y', 'iv.x'][0][0], -6.0, 1e-6)
        assert_rel_error(self, J['c3.y', 'iv.x'][0][0], 15.0, 1e-6)

        assert_rel_error(self, prob['c2.y'], -6.0, 1e-6)
        assert_rel_error(self, prob['c3.y'], 15.0, 1e-6)

        prob.setup(vector_class=PETScVector, check=False, mode='rev')
        prob.run_model()

        J = prob.compute_total_derivs(of=['c2.y', "c3.y"], wrt=['iv.x'])

        assert_rel_error(self, J['c2.y', 'iv.x'][0][0], -6.0, 1e-6)
        assert_rel_error(self, J['c3.y', 'iv.x'][0][0], 15.0, 1e-6)

        assert_rel_error(self, prob['c2.y'], -6.0, 1e-6)
        assert_rel_error(self, prob['c3.y'], 15.0, 1e-6)

    #def test_fan_out_grouped_varsets(self):
        #prob = Problem(FanOutGroupedVarSets())

        #prob.setup(vector_class=PETScVector, check=False, mode='fwd')
        #prob.set_solver_print(level=0)
        #prob.run_model()

        #J = prob.compute_total_derivs(of=['c2.y', "c3.y"], wrt=['iv.x'])

        #assert_rel_error(self, J['c2.y', 'iv.x'][0][0], -6.0, 1e-6)
        #assert_rel_error(self, J['c3.y', 'iv.x'][0][0], 15.0, 1e-6)

        #assert_rel_error(self, prob['c2.y'], -6.0, 1e-6)
        #assert_rel_error(self, prob['c3.y'], 15.0, 1e-6)

        #prob.setup(vector_class=PETScVector, check=False, mode='rev')
        #prob.run_model()

        #J = prob.compute_total_derivs(of=['c2.y', "c3.y"], wrt=['iv.x'])

        #assert_rel_error(self, J['c2.y', 'iv.x'][0][0], -6.0, 1e-6)
        #assert_rel_error(self, J['c3.y', 'iv.x'][0][0], 15.0, 1e-6)

        #assert_rel_error(self, prob['c2.y'], -6.0, 1e-6)
        #assert_rel_error(self, prob['c3.y'], 15.0, 1e-6)

    def test_fan_in_grouped(self):

        prob = Problem()
        prob.model = FanInGrouped2()
        prob.setup(vector_class=PETScVector, check=False, mode='fwd')
        prob.set_solver_print(level=0)
        prob.run_model()


        indep_list = ['p1.x', 'p2.x']
        unknown_list = ['c3.y']

        assert_rel_error(self, prob['c3.y'], 29.0, 1e-6)

        J = prob.compute_total_derivs(of=unknown_list, wrt=indep_list)
        assert_rel_error(self, J['c3.y', 'p1.x'][0][0], -6.0, 1e-6)
        assert_rel_error(self, J['c3.y', 'p2.x'][0][0], 35.0, 1e-6)

        assert_rel_error(self, prob['c3.y'], 29.0, 1e-6)

        prob.setup(vector_class=PETScVector, check=False, mode='rev')
        prob.run_model()

        assert_rel_error(self, prob['c3.y'], 29.0, 1e-6)

        J = prob.compute_total_derivs(of=unknown_list, wrt=indep_list)
        assert_rel_error(self, J['c3.y', 'p1.x'][0][0], -6.0, 1e-6)
        assert_rel_error(self, J['c3.y', 'p2.x'][0][0], 35.0, 1e-6)

        assert_rel_error(self, prob['c3.y'], 29.0, 1e-6)

    def test_fan_in_grouped_feature(self):

        from openmdao.api import Problem, IndepVarComp, ParallelGroup, ExecComp, PETScVector

        prob = Problem()
        model = prob.model

        model.add_subsystem('p1', IndepVarComp('x', 1.0))
        model.add_subsystem('p2', IndepVarComp('x', 1.0))

        parallel = model.add_subsystem('parallel', ParallelGroup())
        parallel.add_subsystem('c1', ExecComp(['y=-2.0*x']))
        parallel.add_subsystem('c2', ExecComp(['y=5.0*x']))

        model.add_subsystem('c3', ExecComp(['y=3.0*x1+7.0*x2']))

        model.connect("parallel.c1.y", "c3.x1")
        model.connect("parallel.c2.y", "c3.x2")

        model.connect("p1.x", "parallel.c1.x")
        model.connect("p2.x", "parallel.c2.x")

        prob.setup(vector_class=PETScVector, check=False, mode='fwd')
        prob.set_solver_print(level=0)
        prob.run_model()

        assert_rel_error(self, prob['c3.y'], 29.0, 1e-6)

    def test_diamond(self):

        prob = Problem()
        prob.model = Diamond()
        prob.setup(vector_class=PETScVector, check=False, mode='fwd')
        prob.set_solver_print(level=0)
        prob.run_model()

        assert_rel_error(self, prob['c4.y1'], 46.0, 1e-6)
        assert_rel_error(self, prob['c4.y2'], -93.0, 1e-6)

        indep_list = ['iv.x']
        unknown_list = ['c4.y1', 'c4.y2']

        J = prob.compute_total_derivs(of=unknown_list, wrt=indep_list)
        assert_rel_error(self, J['c4.y1', 'iv.x'][0][0], 25, 1e-6)
        assert_rel_error(self, J['c4.y2', 'iv.x'][0][0], -40.5, 1e-6)

        prob.setup(vector_class=PETScVector, check=False, mode='rev')
        prob.run_model()

        assert_rel_error(self, prob['c4.y1'], 46.0, 1e-6)
        assert_rel_error(self, prob['c4.y2'], -93.0, 1e-6)

        J = prob.compute_total_derivs(of=unknown_list, wrt=indep_list)
        assert_rel_error(self, J['c4.y1', 'iv.x'][0][0], 25, 1e-6)
        assert_rel_error(self, J['c4.y2', 'iv.x'][0][0], -40.5, 1e-6)

    def test_converge_diverge(self):

        prob = Problem()
        prob.model = ConvergeDiverge()
        prob.setup(vector_class=PETScVector, check=False, mode='fwd')
        prob.set_solver_print(level=0)
        prob.run_model()

        assert_rel_error(self, prob['c7.y1'], -102.7, 1e-6)

        indep_list = ['iv.x']
        unknown_list = ['c7.y1']

        J = prob.compute_total_derivs(of=unknown_list, wrt=indep_list)
        assert_rel_error(self, J['c7.y1', 'iv.x'][0][0], -40.75, 1e-6)

        prob.setup(vector_class=PETScVector, check=False, mode='rev')
        prob.run_model()

        assert_rel_error(self, prob['c7.y1'], -102.7, 1e-6)

        J = prob.compute_total_derivs(of=unknown_list, wrt=indep_list)
        assert_rel_error(self, J['c7.y1', 'iv.x'][0][0], -40.75, 1e-6)

        assert_rel_error(self, prob['c7.y1'], -102.7, 1e-6)

    def test_zero_shape(self):
        raise unittest.SkipTest("zero shapes not fully supported yet")
        class MultComp(ExplicitComponent):
            def __init__(self, mult):
                self.mult = mult
                super(MultComp, self).__init__()

            def initialize_variables(self):
                if self.comm.rank == 0:
                    self.add_input('x', shape=1)
                    self.add_output('y', shape=1)
                else:
                    self.add_input('x', shape=0)
                    self.add_output('y', shape=0)

            def compute(self, inputs, outputs):
                outputs['y'] = inputs['x'] * self.mult

            def compute_partials(self, inputs, outputs, partials):
                """Intentionally incorrect derivative."""
                J = partials
                J['y', 'x'] = numpy.array([self.mult])

        prob = Problem()
        
        #import wingdbstub

        model = prob.model
        model.add_subsystem('iv', IndepVarComp('x', 1.0))
        model.add_subsystem('c1', MultComp(3.0))

        model.sub = model.add_subsystem('sub', ParallelGroup())
        model.sub.add_subsystem('c2', MultComp(-2.0))
        model.sub.add_subsystem('c3', MultComp(5.0))

        model.add_subsystem('c2', MultComp(1.0))
        model.add_subsystem('c3', MultComp(1.0))

        model.connect('iv.x', 'c1.x')

        model.connect('c1.y', 'sub.c2.x')
        model.connect('c1.y', 'sub.c3.x')

        model.connect('sub.c2.y', 'c2.x')
        model.connect('sub.c3.y', 'c3.x')

        of=['c2.y', "c3.y"]
        wrt=['iv.x']

        prob.setup(vector_class=PETScVector, check=False, mode='fwd')
        prob.set_solver_print(level=0)
        prob.run_model()

        J = prob.compute_total_derivs(of=['c2.y', "c3.y"], wrt=['iv.x'])

        assert_rel_error(self, J['c2.y', 'iv.x'][0][0], -6.0, 1e-6)
        assert_rel_error(self, J['c3.y', 'iv.x'][0][0], 15.0, 1e-6)

        assert_rel_error(self, prob['c2.y'], -6.0, 1e-6)
        assert_rel_error(self, prob['c3.y'], 15.0, 1e-6)

        prob.setup(vector_class=PETScVector, check=False, mode='rev')
        prob.run_model()

        J = prob.compute_total_derivs(of=['c2.y', "c3.y"], wrt=['iv.x'])

        assert_rel_error(self, J['c2.y', 'iv.x'][0][0], -6.0, 1e-6)
        assert_rel_error(self, J['c3.y', 'iv.x'][0][0], 15.0, 1e-6)

        assert_rel_error(self, prob['c2.y'], -6.0, 1e-6)
        assert_rel_error(self, prob['c3.y'], 15.0, 1e-6)

if __name__ == "__main__":
    from openmdao.utils.mpi import mpirun_tests
    mpirun_tests()
