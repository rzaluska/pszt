#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import phenotype
import unittest
import math

class Generation:
    """Generic generation class. It contains common fields for all other
    algorithm variations.
    """
    def __init__(self, number_of_individuals, size_of_genotype):
        self.population = [phenotype.Phenotype(size=size_of_genotype)
                           for i in range(number_of_individuals)]
        self.num_iterations = 0
        self.number_of_individuals = number_of_individuals

    def __str__(self):
        s = "\n".join([str(x) for x in self.population])
        s = "Population: \n" + s
        return s

    def set_destination(self, destination_sum, destination_product):
        self.destination_sum = destination_sum
        self.destination_product = destination_product

    def calc_fitness(self):
        "Fitness calculation based on actual fitness function"""
        for individiual in self.population:
            individiual.calc_fitness_function(self.destination_sum,
                                              self.destination_product)
        s = 0
        m = 0

        # Sum all influences and get the biggest one - we will use it
        # in calc_influence
        for agent in self.population:
            s += agent.get_fitness()
            if m < agent.get_fitness():
                m = agent.get_fitness()

        for x in self.population:
            x.calc_influence(s, m, self.number_of_individuals)

        self.population.sort(key=lambda x: x.get_influence(), reverse=True)

    def mutation(self):
        i = 0
        while i < self.number_of_individuals*0.1:
            self.population[
                    random.randint(0, len(self.population) - 1)
                    ].mutation()
            i += 1

    def get_best(self):
        for individiual in self.population:
            individiual.calc_fitness_function(self.destination_sum,
                                              self.destination_product)
        self.population.sort(key=lambda x: x.get_fitness(), reverse=False)
        return self.population[0]
    def get_worst(self):
        self.get_best()  # sorts population
        return self.population[-1]

    def get_avg_fitness(self):
        fitness_sum = 0.0
        for individiual in self.population:
            individiual.calc_fitness_function(self.destination_sum,
                                              self.destination_product)
            fitness_sum += individiual.get_fitness()

        return float(fitness_sum)/float(self.number_of_individuals)

    def step(self):
        pass


class MicrobalGaGeneration(Generation):
    def step(self):
        """Do one step of generation including mutations, crossovers, and
        selection.
        TODO This will be overwriten by child class
        """

        a = random.choice(self.population)
        b = random.choice(self.population)

        a.calc_fitness_function(self.destination_sum, self.destination_product)
        b.calc_fitness_function(self.destination_sum, self.destination_product)

        if a.get_fitness() < b.get_fitness():
            w = a
            l = b
        elif b.get_fitness() < a.get_fitness():
            w = b
            l = a
        else:
            return

        for bit in enumerate(w.genotype):
            if random.random() < 0.5:
                l.genotype[bit[0]] = bit[1]
            if random.random() < 10*self.get_best().get_fitness():
                l.genotype[bit[0]] ^= 1


class RuletteGeneration(Generation):
    def calc_fitness(self):
        """Rank based fitness calculation"""
        for individiual in self.population:
            individiual.calc_fitness_function(self.destination_sum,
                                              self.destination_product)

        curr_f = self.population[0].get_fitness()
        curr_rank = len(self.population)
        for agent in self.population:
            if agent.get_fitness() == curr_f:
                agent.fitness = curr_rank
            else:
                curr_rank -= 1
                curr_f = agent.get_fitness()
                agent.fitness = curr_rank

        s = 0
        # Sum all influences and get the biggest one - we will use it
        # in calc_influence
        for agent in self.population:
            s += agent.get_fitness()

        f_ave = 0
        for x in self.population:
            f_ave += x.get_fitness()

        f_ave /= len(self.population)

        f_max = 0
        for x in self.population:
            if x.get_fitness() > f_max:
                f_max = x.get_fitness()

        c = 2
        a = (c*f_ave - f_ave)/(f_max - f_ave)
        b = c*f_ave - a*f_max

        for x in self.population:
            x.fitness = a*x.fitness + b

        for x in self.population:
            x.calc_influence(s)

    def mutation(self):
        i = 0
        p = 1
        while i < self.number_of_individuals*0.1:
            self.population[
                    random.randint(0, len(self.population) - 1)
                    ].mutation(p)
            i += 1

    def step(self):
        self.calc_fitness()

        # select parents
        parents = []

        for i in self.population:
            # roll dice
            dice = random.random()
            for agent in self.population:
                dice -= agent.get_influence()
                if dice <= 0:
                    parents.append(agent)
                    break

        assert(len(parents) == len(self.population))

        list_of_indices = list(range(self.number_of_individuals))

        assert(self.number_of_individuals % 2 == 0)

        fitness_sum = 0
        for parent in parents:
            fitness_sum += parent.get_fitness()

        probability_of_mutation = 1 - math.exp(-fitness_sum*0.001)

        childrens = []
        for pair in range(int(self.number_of_individuals/2)):
            first = random.randint(0, len(list_of_indices) - 1)
            del list_of_indices[first]
            second = random.randint(0, len(list_of_indices) - 1)
            del list_of_indices[second]

            first_parent = parents[first]
            second_parent = parents[second]

            children = first_parent.crossover(second_parent)
            children['a'].mutation(probability_of_mutation)
            children['b'].mutation(probability_of_mutation)
            first_parent.calc_fitness_function(self.destination_sum,
                    self.destination_product)
            second_parent.calc_fitness_function(self.destination_sum,
                    self.destination_product)
            children['a'].calc_fitness_function(self.destination_sum,
                    self.destination_product)
            children['b'].calc_fitness_function(self.destination_sum,
                    self.destination_product)

            selector = []
            selector.append(first_parent)
            selector.append(second_parent)
            selector.append(children['a'])
            selector.append(children['b'])
            selector.sort(key=lambda x: x.get_fitness(), reverse=True)

            childrens.append(selector[0])
            childrens.append(selector[1])

        assert(len(childrens) == len(self.population))
        self.population = childrens

class TestGenerationMethods(unittest.TestCase):
    def test_get_best(self):
        g = Generation(4, 2)
        g.set_destination(3, 0)  # 00 bits
        g.population[0].genotype = [0, 0]
        selected_best = g.population[0]
        g.population[1].genotype = [1, 1]
        g.population[2].genotype = [1, 0]
        g.population[3].genotype = [0, 1]
        best = g.get_best()
        self.assertEqual(best, selected_best)

    def test_get_avg_fitness(self):
        g = Generation(4, 2)
        g.set_destination(3, 0)  # 00 bits
        g.population[0].genotype = [0, 0]
        g.population[1].genotype = [0, 0]
        g.population[2].genotype = [0, 0]
        g.population[3].genotype = [0, 0]
        self.assertEqual(g.get_avg_fitness(), 0)

if __name__ == '__main__':
        unittest.main()
