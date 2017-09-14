import random
import nudge_new as nudge
import numpy as np
from scipy.stats import entropy
import evolutionary_algorithms as ea
import nudge_new as nudge
import probability_distributions

class IndividualNudge(ea.Individual):
    """
    A class that represents one individual individual_nudge in a
    evolutionary algorithms. Note the difference between individuals
    in an evolutionary algorithm (part of a population etc), and 
    individual_nudges which are a certain type of nudges.

    Attributes:
    ----------
    genes: a 1d nd-array
        The length should be equal to the number of states of the nudged
        variable
    timestamp: integer
        At which generation the nudge was created.
    score: a number
        The impact of the nudge
    nudge_size: a number
        The l1-norm of the nudge

    """
    def __init__(self, genes, timestamp):
        """
        Create an individualNudge object representing an individual
        nudge.

        Parameters:
        ----------
        genes: a 1d nd-array
        timestamp: a number

        """
        self.genes = genes
        self.nudge_size = np.sum(np.absolute(genes))
        self.timestamp = timestamp
        self.score = None

    @classmethod
    def create_random_individual(cls, number_of_states, nudge_size,
                                 timestamp):
        """
        Create an IndividualNudge object randomly

        Parameters:
        ----------
        nudge_size: number
        number_of_states: integer
        timestamp: integer

        Returns: IndividualNudge object

        """
        genes = cls.create_genes(number_of_states, nudge_size)
        return cls(genes, timestamp)

    #method does not work just yet
    def mutate(self, mutation_size):
        """
        Mutate the genes of the individual.

        Parameters:
        ----------
        mutation_size: a number

        """
        print(self.genes)
        absolute_genes = np.absolute(self.genes)
        mutation = nudge.find_noise_vector(len(self.genes), mutation_size)
        print(mutation)
        absolute_genes = absolute_genes + mutation
        print("the sum of the absolute genes is {}".format(
            np.sum(absolute_genes)
        ))
        print(absolute_genes)
        absolute_genes[self.genes<0] = absolute_genes[self.genes<0] * -1
        print("the sum of the absolute genes is {}".format(
            np.sum(absolute_genes)
        ))
        print(absolute_genes)
        self.genes = absolute_genes
        if abs(np.sum(np.absolute(self.genes))-self.nudge_size) > 10**(-7):
            raise ValueError()
   
    def evaluate(self, start_distribution, cond_output):
        """
        Find the impact of the nudge on the output distribution and 
        set the score.

        Parameters:
        ----------
        start_distribution: an nd-array
            Representing a probability distribution
        cond_output: an nd-array
            The output conditioned on all input variables

        """
        new_input_dist = nudge.local_non_causal(
            start_distribution, self.nudge_size, self.genes
        )
        nudge_impact = nudge.find_nudge_impact(
            start_distribution, new_input_dist, cond_output,
            measure="absolute"
        )
        #to make it a minimization rather than a maximization problem
        self.score = -nudge_impact

    @staticmethod
    def create_genes(number_of_states, nudge_size):
        genes = nudge.find_noise_vector(number_of_states, nudge_size)
        if abs(np.sum(np.absolute(genes))-nudge_size) > 10**(-7):
            raise ValueError()
        return genes

def create_individual_nudges(number_of_individuals, number_of_states, 
                             nudge_size, timestamp=0):
    """
    Create a list of individual objects. The genes are either generated 
    according to the mode.

    Parameters:
    ----------
    number_of_individuals: an integer
    number_of_genes: an integer
    mode: a string
        Either "random" or "peaked"
    number_of_peaks: an integer
    timestamp: an integer

    Returns:
    -------
    a list of IndividualDistribution objects

    """
    individuals = []
    for i in range(number_of_individuals):
        individual = IndividualNudge.create_random_individual(
            number_of_states, nudge_size, timestamp
        )
        individuals.append(individual)

    return individuals

class FindMaximumIndividualNudge():
    """ 
    A class to find the maximal individual nudge

    Attributes:
    ----------
    start_distribution: nd-array
        Representing a probability distribution
    cond_output: nd-array
        Representing the output conditioned on the input
    nudge_size: a number
        The nudge_size on the input distribution.
    generational: Boolean
        Whether to discard the old individuals at every new timestep
    number_of_children: an integer
    parent_selection_mode: Either "rank_exponential" or None

    """
    def __init__(self, start_distribution, cond_output, nudge_size, 
                 generational, number_of_children, parent_selection_mode):
        """Create a FindMaximumIndividualNudge object"""
        self.start_distribution = start_distribution
        self.cond_output = cond_output
        self.nudge_size = nudge_size
        self.generational = generational
        self.number_of_children = number_of_children
        self.parent_selection_mode = parent_selection_mode

    def get_max_nudge(self, individuals, number_of_generations,
                      mutation_size):
        """
        Find the maximum individual nudge.

        Parameters:
        ----------
        number_of_generations: an integer
        mutation_size: a number
        individuals: list of IndividualNudge objects
 
        Returns:
        -------
        A numpy array which represents the maximum individual nudge
        for the start distribution.

        """
        population = individuals
        for timestep in range(number_of_generations):
            population = self.evolve(population, mutation_size, timestep)

        return ea.sort_individuals(population)[0]

    def evolve(self, individuals, mutation_size, timestep):
        """
        Evolve the population
        
        Parameters:
        ----------
        mutation_size: a number

        Returns: a list of IndividualNudge Objects

        """
        parents = ea.select_parents(individuals, self.number_of_children*2,
                                 self.parent_selection_mode)
        children = self.create_children(parents, self.number_of_children,
                                        timestep, mutation_size)
        for child in children:
            child.evaluate(self.start_distribution, self.cond_output)

        return ea.select_new_population(individuals, children, len(individuals),
                                        self.generational)

    def create_children(self, parents, number_of_children, timestamp,
                        mutation_size):
        """
        Create new individuals.

        Parameters:
        ----------
        parents: a list of individual objects
        number_of_children: an integer
        timestamp: a number
        mutation_size: a number

        """
        children = []
        for i in range(number_of_children):
            children.append(self.recombine(
                parents[i], parents[number_of_children+i], timestamp
            ))

        children = [child.mutate(mutation_size) for child in children]
        return children

    def recombine(self, parent1, parent2, timestamp):
        """recombine two individuals to create a new individual
        
        Parameters:
        ----------
        parent1: Individual object
        parent2: Individual object
        timestamp: a number

        Returns: Individual object

        """
        if np.random.random() > 0.5:
            genes = np.copy(parent1.genes)
        else:
            genes =  np.copy(parent2.genes)
        
        return IndividualNudge(genes, timestamp)

if __name__ == "__main__":
    input_variables = 4
    number_of_states = 5
    nudge_size = 0.01
    distribution_shape = [number_of_states]*input_variables

    total_number_of_states = reduce(lambda x,y: x*y, distribution_shape)
    input_dist = np.random.dirichlet([1]*total_number_of_states)
    input_dist = np.reshape(input_dist, distribution_shape)

    cond_shape = [number_of_states]*(input_variables+1)
    cond_output = [
        probability_distributions.compute_joint_uniform_random((number_of_states,))
        for i in range(number_of_states**(input_variables))
    ]
    cond_output = np.array(cond_output)
    cond_output = np.reshape(cond_output, cond_shape)

    #evolutionary algorithm parameters
    number_of_generations = 2000
    population_size = 10
    number_of_children = 5
    generational = False
    mutation_size = 0.005
    parent_selection_mode = "rank_exponential"

    individuals = create_individual_nudges(
        population_size, number_of_states, nudge_size, "random"
    )
    for individual in individuals:
        individual.evaluate(input_dist, cond_output)

    print("initial impact {}".format(
        ea.sort_individuals(individuals)[0].score
    ))

    find_max_nudge = FindMaximumIndividualNudge(
        input_dist, cond_output, nudge_size, generational, number_of_children,
        parent_selection_mode
    )
    max_individual = find_max_nudge.get_max_nudge(
        individuals, number_of_generations, mutation_size
    )

    print("the final impact {}".format(max_individual.score))


