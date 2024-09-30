# Filename: route_optimization_app.py

import streamlit as st
import networkx as nx
import plotly.graph_objects as go

# Define the ports and routes
ports = [
    'Durban',
    'Cape Town',
    'Port Elizabeth',
    'East London',
    'Richards Bay',
    'Walvis Bay',
    'Maputo',
    'Singapore',
    'Rotterdam',
    'Shanghai',
    'New York'
]

# Create a graph
G = nx.Graph()

# Add nodes (ports)
G.add_nodes_from(ports)

# Simulated distances between ports (in nautical miles)
routes = [
    ('Durban', 'Cape Town', 1400),
    ('Durban', 'Port Elizabeth', 800),
    ('Durban', 'East London', 650),
    ('Cape Town', 'Port Elizabeth', 460),
    ('Port Elizabeth', 'East London', 135),
    ('Durban', 'Richards Bay', 90),
    ('Richards Bay', 'Maputo', 220),
    ('Cape Town', 'Walvis Bay', 790),
    ('Walvis Bay', 'Rotterdam', 6800),
    ('Durban', 'Singapore', 4800),
    ('Singapore', 'Shanghai', 2400),
    ('Durban', 'Maputo', 250),
    ('Cape Town', 'New York', 6900),
    ('Port Elizabeth', 'Singapore', 5000),
    ('East London', 'Singapore', 4900),
    ('Maputo', 'Singapore', 4700),
    ('Richards Bay', 'Singapore', 4800),
    ('Durban', 'Walvis Bay', 2100)
]

# Add edges with distances
G.add_weighted_edges_from(routes)

# Function to find the shortest route
def find_shortest_route(G, start_port, end_port):
    try:
        shortest_distance = nx.dijkstra_path_length(G, start_port, end_port, weight='weight')
        shortest_path = nx.dijkstra_path(G, start_port, end_port, weight='weight')
        return shortest_distance, shortest_path
    except nx.NetworkXNoPath:
        return None, None

# Streamlit App
def main():
    st.title("South African Ports Route Optimization")
    st.write("Find the most efficient shipping route from a South African port to an international destination.")

    # User Inputs
    start_port = st.selectbox('Select the starting port:', ports, index=ports.index('Durban'))
    end_port = st.selectbox('Select the destination port:', ports, index=ports.index('Shanghai'))

    if st.button('Calculate Shortest Route'):
        if start_port == end_port:
            st.warning("Start port and destination port cannot be the same.")
            return

        distance, path = find_shortest_route(G, start_port, end_port)
        if path:
            st.success(f"Shortest route from **{start_port}** to **{end_port}**:")
            st.write(" ➔ ".join(path))
            st.write(f"**Total distance:** {distance} nautical miles")

            # Visualize the route
            visualize_route(G, path)
        else:
            st.error(f"No available route from {start_port} to {end_port}.")

def visualize_route(G, path):
    # Generate positions for the nodes using a layout algorithm
    pos = nx.spring_layout(G, seed=42)  # Seed for reproducibility

    # Create edge traces
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1, color='#888'),
        hoverinfo='none',
        mode='lines')

    # Highlight the shortest path
    if path:
        path_edges = list(zip(path, path[1:]))
        path_edge_x = []
        path_edge_y = []
        for edge in path_edges:
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            path_edge_x.extend([x0, x1, None])
            path_edge_y.extend([y0, y1, None])

        path_edge_trace = go.Scatter(
            x=path_edge_x, y=path_edge_y,
            line=dict(width=4, color='red'),
            hoverinfo='none',
            mode='lines')
    else:
        path_edge_trace = go.Scatter()  # Empty trace

    # Create node traces
    node_x = []
    node_y = []
    node_text = []
    node_color = []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(node)
        if node in path:
            node_color.append('red')
        else:
            node_color.append('blue')

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=node_text,
        textposition='top center',
        hoverinfo='text',
        marker=dict(
            color=node_color,
            size=10,
            line_width=2))

    # Create the figure
    fig = go.Figure(data=[edge_trace, path_edge_trace, node_trace],
                    layout=go.Layout(
                        title='Shipping Routes',
                        title_x=0.5,
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20, l=5, r=5, t=40),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                    )

    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
