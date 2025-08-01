# src/tree_path_analyzer.py

import networkx as nx
import matplotlib.pyplot as plt
from collections import Counter
import pandas as pd
import plotly.graph_objects as go
from multiprocessing import Pool, cpu_count
# from google.colab import files # This line is specific to Google Colab, remove for local execution

# Step 1: Read numbers from file
def read_numbers(file_path):
    """Reads decimal numbers from a text file, one number per line."""
    with open(file_path, 'r') as f:
        lines = f.readlines()
    numbers = [int(line.strip()) for line in lines if line.strip().isdigit()]
    return numbers

# Step 2: Convert number to path in binary tree
def number_to_path(n):
    """
    Converts a decimal number 'n' into a path in a binary tree.
    '0' bit corresponds to moving left, '1' bit to moving right.
    The path starts from node 1 (root).
    """
    bin_str = bin(n)[2:] # Convert to binary string, remove '0b' prefix
    path = [1] # Start at root node
    node = 1
    for bit in bin_str[1:]: # Iterate from the second bit (first bit determines depth 0 or 1)
        node = node * 2 if bit == '0' else node * 2 + 1
        path.append(node)
    return path

# Parallel helper for generate_paths
def number_to_path_wrapper(n):
    """Wrapper function for multiprocessing map."""
    return number_to_path(n)

# Step 3: Generate paths using multiprocessing
def generate_paths(numbers):
    """Generates binary tree paths for a list of numbers using multiprocessing."""
    with Pool(cpu_count()) as pool: # Use all available CPU cores
        paths = pool.map(number_to_path_wrapper, numbers)
    return paths

# Step 4: Visualize path with matplotlib
def visualize_path(path, title='Binary Tree Path'):
    """Visualizes a single binary tree path using Matplotlib."""
    G = nx.DiGraph() # Create a directed graph
    for i in range(len(path)-1):
        G.add_edge(path[i], path[i+1]) # Add edges between consecutive nodes in the path
    
    pos = nx.spring_layout(G, seed=42) # Layout for nodes
    plt.figure(figsize=(12,6))
    nx.draw(G, pos, with_labels=True, node_color='lightblue', arrowsize=20)
    plt.title(title)
    plt.show()

# Step 4b: Interactive Plotly visualization (optional)
def visualize_path_interactive(path, title='Binary Tree Path'):
    """Visualizes a single binary tree path interactively using Plotly."""
    G = nx.DiGraph()
    for i in range(len(path)-1):
        G.add_edge(path[i], path[i+1])
    pos = nx.spring_layout(G, seed=42)

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

    node_x = []
    node_y = []
    text = []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        text.append(str(node))
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=text,
        textposition='top center',
        hoverinfo='text',
        marker=dict(
            showscale=False,
            color='lightblue',
            size=20,
            line_width=2))

    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        title=title,
                        title_x=0.5,
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20,l=5,r=5,t=40)))
    fig.show()

# Step 5: Calculate depth
def get_depth(path):
    """Calculates the depth of a node's path (number of edges from root)."""
    return len(path) - 1 # Depth is number of edges, which is path length - 1

# Step 6: Analyze paths
def analyze_paths(paths):
    """
    Analyzes a collection of paths to find common edges, nodes, and prefixes.
    """
    edge_counter = Counter()
    node_counter = Counter()
    prefix_counter = Counter()

    for path in paths:
        node_counter.update(path) # Count occurrences of each node
        edges = [(path[i], path[i+1]) for i in range(len(path)-1)]
        edge_counter.update(edges) # Count occurrences of each edge
        for i in range(1, len(path)+1):
            prefix = tuple(path[:i]) # Generate all prefixes of the path
            prefix_counter[prefix] += 1 # Count occurrences of each prefix

    most_common_edges = edge_counter.most_common(10)
    most_common_nodes = node_counter.most_common(10)
    most_common_prefixes = prefix_counter.most_common(10)

    return {
        'most_common_edges': most_common_edges,
        'most_common_nodes': most_common_nodes,
        'most_common_prefixes': most_common_prefixes,
        'total_paths': len(paths)
    }

# Step 7: Save stats to CSV
def save_stats_to_csv(stats):
    """Saves analysis statistics to CSV files."""
    edges_df = pd.DataFrame(stats['most_common_edges'], columns=['Edge', 'Count'])
    edges_df['From'] = edges_df['Edge'].apply(lambda x: x[0])
    edges_df['To'] = edges_df['Edge'].apply(lambda x: x[1])
    edges_df = edges_df[['From', 'To', 'Count']]
    edges_df.to_csv('most_common_edges.csv', index=False)

    nodes_df = pd.DataFrame(stats['most_common_nodes'], columns=['Node', 'Count'])
    nodes_df.to_csv('most_common_nodes.csv', index=False)

    prefixes_df = pd.DataFrame(stats['most_common_prefixes'], columns=['Prefix', 'Count'])
    prefixes_df['Prefix'] = prefixes_df['Prefix'].apply(lambda x: ' -> '.join(map(str,x)))
    prefixes_df.to_csv('most_common_prefixes.csv', index=False)

    print("Saved CSV files: 'most_common_edges.csv', 'most_common_nodes.csv', 'most_common_prefixes.csv'")

# Step 8: Main function
def main_analyzer(file_path, visualize_interactive=False):
    """Main function to run the binary tree path analysis."""
    print(f"--- Binary Tree Path Analyzer ---")
    print(f"Reading numbers from: {file_path}")
    numbers = read_numbers(file_path)
    print(f"Total numbers read: {len(numbers)}")

    paths = generate_paths(numbers)
    
    print("\nAll paths from root for each number:")
    for num, path in zip(numbers, paths):
        print(f"Number: {num}")
        print(f"Path: {path}")
        print(f"Depth: {get_depth(path)}\n")

    if numbers: # Ensure there are numbers to visualize
        print(f"Sample number for visualization: {numbers[0]}")
        print(f"Sample path: {paths[0]}")
        print(f"Depth of sample node: {get_depth(paths[0])}")

        # Visualization: Choose matplotlib or plotly
        if visualize_interactive:
            visualize_path_interactive(paths[0], title=f"Binary Tree Path for {numbers[0]}")
        else:
            visualize_path(paths[0], title=f"Binary Tree Path for {numbers[0]}")
    else:
        print("No numbers read for visualization.")


    stats = analyze_paths(paths)

    print("\n=== Analysis Statistics ===")
    print("Most common edges:")
    for edge, count in stats['most_common_edges']:
        print(f"  Edge {edge} appears {count} times")

    print("\nMost common nodes:")
    for node, count in stats['most_common_nodes']:
        print(f"  Node {node} appears {count} times")

    print("\nMost common prefixes (partial paths):")
    for prefix, count in stats['most_common_prefixes']:
        print(f"  Prefix {prefix} appears {count} times")

    print(f"\nTotal paths analyzed: {stats['total_paths']}")

    save_stats_to_csv(stats)

if __name__ == '__main__':
    # Example usage:
    # Create a dummy numbers.txt file for demonstration
    example_numbers = [10, 25, 30, 100, 500]
    with open("data/numbers.txt", "w") as f:
        for num in example_numbers:
            f.write(str(num) + "\n")
    print("Created 'data/numbers.txt' with example numbers.")

    # You can set visualize_interactive to True to use Plotly (requires web browser/notebook environment)
    # Set to False to use Matplotlib (shows static image)
    main_analyzer(file_path='data/numbers.txt', visualize_interactive=False)

    # Clean up the dummy file
    os.remove("data/numbers.txt")
    print("Cleaned up 'data/numbers.txt'.")
