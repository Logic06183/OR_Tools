# Import necessary libraries
import gradio as gr
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

# List of city names
city_names = ['Durban', 'Johannesburg', 'Pretoria', 'Cape Town', 'Bloemfontein']

def print_solution(data, manager, routing, solution):
    """Formats the solution into a string."""
    output = ''
    total_distance = 0
    total_load = 0
    total_fuel = 0

    capacity_dimension = routing.GetDimensionOrDie('Capacity')

    for vehicle_id in range(data['num_vehicles']):
        index = routing.Start(vehicle_id)
        plan_output = f'Route for vehicle {vehicle_id}:\n'
        route_distance = 0
        route_load = data['vehicle_capacities'][vehicle_id]
        route_fuel = 0
        previous_index = index

        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            load = solution.Value(capacity_dimension.CumulVar(index))
            plan_output += f' {city_names[node_index]} (Load: {load}) ->'
            if previous_index != index:
                # Add distance
                distance = data['distance_matrix'][manager.IndexToNode(previous_index)][node_index]
                route_distance += distance
                # Calculate fuel consumption
                fuel = distance * (1 + data['load_factor'] * route_load)
                route_fuel += fuel
                route_load = load
            previous_index = index
            index = solution.Value(routing.NextVar(index))

        # Return to depot
        node_index = manager.IndexToNode(index)
        plan_output += f' {city_names[node_index]} (Load: {load})\n'
        if previous_index != index:
            distance = data['distance_matrix'][manager.IndexToNode(previous_index)][node_index]
            route_distance += distance
            # Calculate fuel consumption
            fuel = distance * (1 + data['load_factor'] * route_load)
            route_fuel += fuel
        plan_output += f'Distance of the route: {route_distance} km\n'
        plan_output += f'Final Load of the route: {load}\n'
        plan_output += f'Fuel consumption of the route: {route_fuel:.2f} units\n\n'

        output += plan_output
        total_distance += route_distance
        total_load += data['vehicle_capacities'][vehicle_id] - load  # Total delivered
        total_fuel += route_fuel

    output += f'Total distance of all routes: {total_distance} km\n'
    output += f'Total goods delivered: {total_load} units\n'
    output += f'Total fuel consumption: {total_fuel:.2f} units\n'
    return output

def solve_vrp(demands, vehicle_capacities, num_vehicles, load_factor):
    """Solves the VRP with multiple vehicles and fuel efficiency optimization."""
    try:
        # Convert inputs to appropriate types
        demands = [int(d) for d in demands]
        vehicle_capacities = [int(c) for c in vehicle_capacities]
        num_vehicles = int(num_vehicles)
        load_factor = float(load_factor.replace(',', '.'))  # Handle comma as decimal separator

        # Prepare data
        data = {}
        data['distance_matrix'] = [
            [0, 568, 634, 569, 392],  # Durban
            [568, 0, 121, 595, 100],  # Johannesburg
            [634, 121, 0, 712, 216],  # Pretoria
            [569, 595, 712, 0, 497],  # Cape Town
            [392, 100, 216, 497, 0],  # Bloemfontein
        ]
        # Convert demands to negative values for deliveries
        data['demands'] = [0] + [-d for d in demands[1:]]
        data['vehicle_capacities'] = vehicle_capacities
        data['num_vehicles'] = num_vehicles
        data['depot'] = 0  # Starting at Durban
        data['load_factor'] = load_factor  # For fuel efficiency calculation

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
            distance = data['distance_matrix'][from_node][to_node]
            return distance

        transit_callback_index = routing.RegisterTransitCallback(distance_callback)

        # Define cost of each arc (distance).
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        # Add Capacity constraint.
        def demand_callback(from_index):
            """Returns the demand at each node."""
            from_node = manager.IndexToNode(from_index)
            return data['demands'][from_node]

        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,  # No slack
            data['vehicle_capacities'],  # Vehicle capacities
            False,  # Start cumul to max capacity (for deliveries)
            'Capacity')

        capacity_dimension = routing.GetDimensionOrDie('Capacity')

        # Set the starting load of vehicles to their capacities
        for vehicle_id in range(data['num_vehicles']):
            index = routing.Start(vehicle_id)
            capacity_dimension.CumulVar(index).SetValue(data['vehicle_capacities'][vehicle_id])

        # Set up search parameters.
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
        search_parameters.time_limit.seconds = 10  # Adjust as needed

        # Solve the problem.
        solution = routing.SolveWithParameters(search_parameters)

        # Process and return solution.
        if solution:
            return print_solution(data, manager, routing, solution)
        else:
            return 'No solution found. Please check the inputs and constraints.'
    except Exception as e:
        return f'An error occurred: {e}'

# Gradio app
with gr.Blocks() as demo:
    gr.Markdown("# Fleet Routing Optimization with Fuel Efficiency")
    gr.Markdown("Enter the demands at each city, vehicle capacities, number of vehicles, and load factor for fuel efficiency calculation.")

    with gr.Row():
        with gr.Column():
            demand_durban = gr.Number(value=0, label='Demand at Durban (Depot)')
            demand_johannesburg = gr.Number(value=1, label='Demand at Johannesburg')
            demand_pretoria = gr.Number(value=3, label='Demand at Pretoria')
            demand_cape_town = gr.Number(value=2, label='Demand at Cape Town')
            demand_bloemfontein = gr.Number(value=4, label='Demand at Bloemfontein')
            demands = [demand_durban, demand_johannesburg, demand_pretoria, demand_cape_town, demand_bloemfontein]
        with gr.Column():
            vehicle_capacities_input = gr.Textbox(value='5,5', label='Vehicle Capacities (comma-separated)')
            num_vehicles = gr.Number(value=2, label='Number of Vehicles')
            load_factor = gr.Textbox(value='0.01', label='Load Factor for Fuel Efficiency')

    output = gr.Textbox(label='Solution')

    btn = gr.Button("Optimize Routing")

    def on_click(*args):
        demands = args[:5]
        vehicle_capacities_str = args[5]
        num_vehicles = args[6]
        load_factor = args[7]

        # Parse vehicle capacities
        vehicle_capacities = [int(c.strip()) for c in vehicle_capacities_str.split(',') if c.strip()]
        return solve_vrp(demands, vehicle_capacities, num_vehicles, load_factor)

    btn.click(on_click, inputs=[demand_durban, demand_johannesburg, demand_pretoria,
                                demand_cape_town, demand_bloemfontein,
                                vehicle_capacities_input, num_vehicles, load_factor],
              outputs=output)

demo.launch()
