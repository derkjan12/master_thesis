import unittest
import numpy as np

import nudge

class TestNudge(unittest.TestCase):
    def setUp(self):
        pass

    def test1_nudge(self):
	distribution = np.array([0.001, 0.001, 0.003, 0.995])
	sum_nudged_distribution = np.zeros(distribution.shape)
	for i in range(10):
            nudged_distribution, nudged_states = nudge.nudge(distribution, 
                                                             0.01)
	    self.assertTrue(np.all(nudged_distribution >= 0))
	    self.assertTrue(np.all(nudged_distribution <= 1))
     
    def test2_nudge(self):
        distribution = np.array([0.3, 0.4, 0.3, 0.1])
        sum_nudged_distribution = np.zeros(distribution.shape)
        for i in range(1000):
            nudged_distribution, nudged_states = nudge.nudge(distribution, 
                                                             0.01)
            sum_nudged_distribution = (sum_nudged_distribution + 
                                       nudged_distribution)

        self.assertTrue(np.all((sum_nudged_distribution/1000)-distribution < 0.001))

    def test1_select_random_states(self):
        distribution = np.arange(40).reshape((4, 5, 2))
        states = nudge.select_random_states(distribution.shape, 1000)
        self.assertEqual(1000, len(states))
        #print(abs(np.mean([distribution[tuple(state)] for state in states])-19.5))
        self.assertTrue(abs(np.mean([distribution[tuple(state)] for state in states])-19.5) < 1)
