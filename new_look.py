import pulp
import gradio as gr

# Distance matrix from inland locations to Durban (in kilometers)
city_names = ['Johannesburg', 'Pretoria', 'Bloemfontein', 'Nelspruit', 'Polokwane']
distances_to_durban = [568, 635, 569, 330, 392]  # Distances from Durban to each inland city

def optimize_pulp(dataframe, vehicle_capacities):
    # Extract cargo and priorities from the dataframe
    cargo = dataframe['Cargo'].tolist()
    priorities = dataframe['Priority'].tolist()
    
    # Parse vehicle capacities
    vehicle_capacities = [int(c.strip()) for c in vehicle_capacities.split(',') if c.strip()]
    num_vehicles = len(vehicle_capacities)
    num_cities = len(city_names)

    # Initialize the linear programming problem
    prob = pulp.LpProblem("Inland_Cargo_Optimization", pulp.LpMinimize)

    # Decision variables
    x = pulp.LpVariable.dicts("x", [(i, j) for i in range(num_vehicles) for j in range(num_cities)],
                              lowBound=0, upBound=1, cat='Binary')

    # Objective function: minimize total distance traveled by all vehicles
    prob += pulp.lpSum(distances_to_durban[j] * x[i, j] for i in range(num_vehicles) for j in range(num_cities)), "Total_Distance"

    # Constraint: Each city's cargo must be picked up exactly once by any one vehicle
    for j in range(num_cities):
        prob += pulp.lpSum(x[i, j] for i in range(num_vehicles)) == 1, f"City_{j}_Coverage"

    # Constraint: Respect vehicle capacities
    for i in range(num_vehicles):
        prob += pulp.lpSum(cargo[j] * x[i, j] for j in range(num_cities)) <= vehicle_capacities[i], f"Capacity_Vehicle_{i}"

    # Ensure that the total picked up from each city does not exceed the available cargo
    for j in range(num_cities):
        prob += pulp.lpSum(x[i, j] * cargo[j] for i in range(num_vehicles)) == cargo[j], f"Cargo_Exact_Pickup_City_{j}"

    # Solve the problem
    prob.solve()

    # Retrieve the optimized routes
    result = ""
    total_distance = 0
    for i in range(num_vehicles):
        vehicle_route = [city_names[j] for j in range(num_cities) if pulp.value(x[i, j]) == 1]
        if vehicle_route:
            vehicle_cargo = sum(cargo[j] for j in range(num_cities) if pulp.value(x[i, j]) == 1)
            route_distance = sum(distances_to_durban[j] for j in range(num_cities) if pulp.value(x[i, j]) == 1)
            result += f"**Vehicle {i + 1}** picks up cargo from **{', '.join(vehicle_route)}** and collects **{vehicle_cargo} units**.\n\n"
            total_distance += route_distance

    result += f"**Total distance traveled:** {total_distance} km"
    return result

def gradio_pulp_interface(dataframe, vehicle_capacities):
    return optimize_pulp(dataframe, vehicle_capacities)

with gr.Blocks() as demo_pulp:
    gr.Markdown("# Inland Cargo Pickup Optimization for Durban Port using PuLP with Vehicle Constraints")

    with gr.Row():
        with gr.Column():
            gr.Markdown("## Input Cargo and Priority for Each City")
            city_data = gr.Dataframe(
                headers=["City", "Cargo", "Priority"],
                value=[
                    ["Johannesburg", 2, 2],
                    ["Pretoria", 1, 1],
                    ["Bloemfontein", 3, 3],
                    ["Nelspruit", 2, 2],
                    ["Polokwane", 6, 1]
                ],
                datatype=["str", "number", "number"],
                interactive=True
            )
        with gr.Column():
            gr.Markdown("## Input Vehicle Capacities")
            vehicle_capacities = gr.Textbox(
                label="Vehicle Capacities (comma-separated)",
                value="5, 5, 5, 3, 8"
            )
            gr.Markdown("## Optimized Routes")
            output_pulp = gr.Markdown()
            run_button_pulp = gr.Button("Optimize Route using PuLP")

    run_button_pulp.click(
        gradio_pulp_interface,
        inputs=[city_data, vehicle_capacities],
        outputs=output_pulp
    )

demo_pulp.launch()
