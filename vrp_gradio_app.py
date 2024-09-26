# Import necessary libraries
import gradio as gr
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

# List of city names
city_names = ['Durban', 'Johannesburg', 'Pretoria', 'Cape Town', 'Bloemfontein']

def print_solution(manager, routing, solution):
    """Formats the solution into a string."""
    output = ''
    # Objective value.
    output += 'Objective: {} kilometers\n'.format(solution.ObjectiveValue())
    index = routing.Start(0)
    plan_output = 'Route for vehicle 0:\n'
    route_distance = 0
    while not routing.IsEnd(index):
        plan_output += ' {} ->'.format(city_names[manager.IndexToNode(index)])
        previous_index = index
        index = solution.Value(routing.NextVar(index))
        route_distance += routing.GetArcCostForVehicle(previous_index, index, 0)
    plan_output += ' {}\n'.format(city_names[manager.IndexToNode(index)])
    output += plan_output
    output += 'Route distance: {} kilometers\n'.format(route_distance)
    return output

def solve_vrp(demand_durban, demand_johannesburg, demand_pretoria, demand_cape_town, demand_bloemfontein, vehicle_capacity):
    """Solves the VRP and returns the solution as a string."""
    try:
        # Convert inputs to integers
        demand_durban = int(demand_durban)
        demand_johannesburg = int(demand_johannesburg)
        demand_pretoria = int(demand_pretoria)
        demand_cape_town = int(demand_cape_town)
        demand_bloemfontein = int(demand_bloemfontein)
        vehicle_capacity = int(vehicle_capacity)
        
        # Prepare data
        data = {}
        data['distance_matrix'] = [
            [0, 568, 634, 569, 392],  # Durban
            [568, 0, 121, 595, 100],  # Johannesburg
            [634, 121, 0, 712, 216],  # Pretoria
            [569, 595, 712, 0, 497],  # Cape Town
            [392, 100, 216, 497, 0],  # Bloemfontein
        ]
        data['demands'] = [demand_durban, demand_johannesburg, demand_pretoria, demand_cape_town, demand_bloemfontein]
        data['vehicle_capacities'] = [vehicle_capacity]
        data['num_vehicles'] = 1
        data['depot'] = 0  # Starting at Durban

        # Create the routing index manager.
        manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']),
                                               data['num_vehicles'], data['depot'])

        # Create Routing Model.
        routing = pywrapcp.RoutingModel(manager)

        # Create and register a transit callback.
        def distance_callback(from_index, to_index):
            """Returns the distance between the two nodes."""
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return data['distance_matrix'][from_node][to_node]

        transit_callback_index = routing.RegisterTransitCallback(distance_callback)

        # Define cost of each arc.
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        # Add Capacity constraint.
        def demand_callback(from_index):
            """Returns the demand of the node."""
            from_node = manager.IndexToNode(from_index)
            return data['demands'][from_node]

        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,  # null capacity slack
            data['vehicle_capacities'],  # vehicle maximum capacities
            True,  # start cumul to zero
            'Capacity')

        # Set up search parameters.
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

        # Solve the problem.
        solution = routing.SolveWithParameters(search_parameters)

        # Process and return solution.
        if solution:
            return print_solution(manager, routing, solution)
        else:
            return 'No solution found. Please ensure the total demands do not exceed the vehicle capacity.'
    except Exception as e:
        return f'An error occurred: {e}'

# Gradio app
with gr.Blocks() as demo:
    gr.Markdown("# Vehicle Routing Problem Demo")
    gr.Markdown("Enter the demands at each city and vehicle capacity:")
    demand_durban = gr.Number(value=0, label='Demand at Durban (Depot)')
    demand_johannesburg = gr.Number(value=1, label='Demand at Johannesburg')
    demand_pretoria = gr.Number(value=1, label='Demand at Pretoria')
    demand_cape_town = gr.Number(value=2, label='Demand at Cape Town')
    demand_bloemfontein = gr.Number(value=4, label='Demand at Bloemfontein')
    vehicle_capacity = gr.Number(value=5, label='Vehicle Capacity')
    output = gr.Textbox(label='Solution')

    btn = gr.Button("Solve VRP")

    btn.click(solve_vrp, inputs=[demand_durban, demand_johannesburg, demand_pretoria,
                                 demand_cape_town, demand_bloemfontein, vehicle_capacity],
              outputs=output)

demo.launch()
