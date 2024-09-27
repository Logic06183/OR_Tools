import random
import numpy as np
from deap import base, creator, tools, algorithms
import gradio as gr

# Distance matrix between inland locations and Durban
city_names = ['Johannesburg', 'Pretoria', 'Bloemfontein', 'Nelspruit', 'Polokwane']
distances_to_durban = [
    [0, 121, 395, 317, 320],  # Johannesburg
    [121, 0, 512, 438, 340],  # Pretoria
    [395, 512, 0, 460, 300],  # Bloemfontein
    [317, 438, 460, 0, 350],  # Nelspruit
    [320, 340, 300, 350, 0],  # Polokwane
]

# Setting up the genetic algorithm problem
creator.create("FitnessMin", base.Fitness, weights=(-1.0,))  # We want to minimize the distance
creator.create("Individual", list, fitness=creator.FitnessMin)

toolbox = base.Toolbox()
toolbox.register("indices", random.sample, range(len(city_names)), len(city_names))
toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.indices)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)

# Evaluation function for the genetic algorithm considering vehicle capacity constraints
def evaluate(individual, cargo, vehicle_capacities):
    total_distance = 0
    vehicle_loads = [0] * len(vehicle_capacities)  # Keeps track of cargo loads per vehicle
    vehicle_distances = [0] * len(vehicle_capacities)  # Keeps track of distances traveled
    current_vehicle = 0  # Start with the first vehicle

    # Calculate the route and cargo distribution for each vehicle
    for idx in individual:
        cargo_at_location = cargo[idx]
        
        # Check if current vehicle can handle more cargo; if not, switch to next vehicle
        if vehicle_loads[current_vehicle] + cargo_at_location <= vehicle_capacities[current_vehicle]:
            vehicle_loads[current_vehicle] += cargo_at_location
            # Calculate distance for the current trip
            if vehicle_distances[current_vehicle] == 0:
                vehicle_distances[current_vehicle] += distances_to_durban[0][idx]  # Initial pickup from Durban
            else:
                vehicle_distances[current_vehicle] += distances_to_durban[0][idx]
        else:
            # Switch to the next vehicle if available
            current_vehicle += 1
            if current_vehicle >= len(vehicle_capacities):
                break  # No more vehicles available, stop the evaluation
            # Start the route for the next vehicle
            vehicle_loads[current_vehicle] += cargo_at_location
            vehicle_distances[current_vehicle] += distances_to_durban[0][idx]
    
    # Sum up the distances traveled by all vehicles
    total_distance = sum(vehicle_distances)
    
    # Apply a heavy penalty if any vehicle exceeded its capacity to prevent invalid solutions
    penalty = 10000 * sum(1 for load, capacity in zip(vehicle_loads, vehicle_capacities) if load > capacity)
    
    return total_distance + penalty,

toolbox.register("mate", tools.cxOrdered)
toolbox.register("mutate", tools.mutShuffleIndexes, indpb=0.05)
toolbox.register("select", tools.selTournament, tournsize=3)
toolbox.register("evaluate", evaluate)

# Genetic Algorithm parameters
population_size = 50
num_generations = 40
crossover_probability = 0.7
mutation_probability = 0.2

def optimize_routes(cargo, priorities, vehicle_capacities):
    # Parse vehicle capacities
    vehicle_capacities = [int(c.strip()) for c in vehicle_capacities.split(',') if c.strip()]
    
    # Create an initial population
    population = toolbox.population(n=population_size)

    # Run the genetic algorithm
    for generation in range(num_generations):
        offspring = algorithms.varAnd(population, toolbox, cxpb=crossover_probability, mutpb=mutation_probability)
        fits = list(map(lambda ind: toolbox.evaluate(ind, cargo, vehicle_capacities), offspring))
        for fit, ind in zip(fits, offspring):
            ind.fitness.values = fit

        population = toolbox.select(offspring, k=len(population))

    # Get the best solution found
    best_individual = tools.selBest(population, 1)[0]

    # Display the results
    result = ""
    current_vehicle = 0
    vehicle_load = 0
    total_distance = 0

    for idx in best_individual:
        cargo_picked = cargo[idx]
        if vehicle_load + cargo_picked <= vehicle_capacities[current_vehicle]:
            vehicle_load += cargo_picked
            result += f"Vehicle {current_vehicle + 1} picks up cargo from {city_names[idx]} with priority {priorities[idx]} and collects {cargo_picked} units.\n"
        else:
            current_vehicle += 1
            if current_vehicle >= len(vehicle_capacities):
                break
            vehicle_load = cargo_picked
            result += f"\nVehicle {current_vehicle + 1} picks up cargo from {city_names[idx]} with priority {priorities[idx]} and collects {cargo_picked} units.\n"
        total_distance += distances_to_durban[0][idx]

    result += f"\nTotal distance traveled: {total_distance} km"
    return result

def gradio_interface(cargo_jhb, cargo_pta, cargo_blm, cargo_nlp, cargo_plw,
                     priority_jhb, priority_pta, priority_blm, priority_nlp, priority_plw, vehicle_capacities):
    cargo = [cargo_jhb, cargo_pta, cargo_blm, cargo_nlp, cargo_plw]
    priorities = [priority_jhb, priority_pta, priority_blm, priority_nlp, priority_plw]
    return optimize_routes(cargo, priorities, vehicle_capacities)

with gr.Blocks() as demo:
    gr.Markdown("# Inland Cargo Pickup Optimization for Durban Port using Genetic Algorithm with Vehicle Constraints")
    
    with gr.Row():
        with gr.Column():
            cargo_jhb = gr.Number(label="Cargo at Johannesburg", value=2)
            cargo_pta = gr.Number(label="Cargo at Pretoria", value=1)
            cargo_blm = gr.Number(label="Cargo at Bloemfontein", value=3)
            cargo_nlp = gr.Number(label="Cargo at Nelspruit", value=2)
            cargo_plw = gr.Number(label="Cargo at Polokwane", value=2)
        
        with gr.Column():
            priority_jhb = gr.Number(label="Priority of Johannesburg", value=2)
            priority_pta = gr.Number(label="Priority of Pretoria", value=1)
            priority_blm = gr.Number(label="Priority of Bloemfontein", value=3)
            priority_nlp = gr.Number(label="Priority of Nelspruit", value=2)
            priority_plw = gr.Number(label="Priority of Polokwane", value=1)
            vehicle_capacities = gr.Textbox(label="Vehicle Capacities (comma-separated)", value="5,5,5")
    
    output = gr.Textbox(label="Optimized Route")
    run_button = gr.Button("Optimize Route")
    
    run_button.click(gradio_interface, inputs=[cargo_jhb, cargo_pta, cargo_blm, cargo_nlp, cargo_plw,
                                               priority_jhb, priority_pta, priority_blm, priority_nlp, priority_plw,
                                               vehicle_capacities], outputs=output)

demo.launch()
