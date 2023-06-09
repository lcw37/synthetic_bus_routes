import taxicab as tc
from taxicab.plot import plot_graph_route
from osmnx.plot import _save_and_show
import networkx as nx
import matplotlib.colors as mcolors

import matplotlib.cm as cm
import numpy as np

import matplotlib.pyplot as plt

def plot_graph_routes(G, routes, route_colors="r", route_linewidths=4, **pgr_kwargs):
    """
    Plot several routes along a graph.

    Parameters
    ----------
    G : networkx.MultiDiGraph
        input graph
    routes : list
        routes as a list of lists of node IDs
    route_colors : string or list
        if string, 1 color for all routes. if list, the colors for each route.
    route_linewidths : int or list
        if int, 1 linewidth for all routes. if list, the linewidth for each route.
    pgr_kwargs
        keyword arguments to pass to plot_graph_route

    Returns
    -------
    fig, ax : tuple
        matplotlib figure, axis
    """
    # check for valid arguments
    # if not all(isinstance(r, list) for r in routes):  # pragma: no cover
    #     raise ValueError("routes must be a list of route lists")
    if not all(isinstance(r, tuple) for r in routes):  # pragma: no cover
        raise ValueError("routes must be a list of route tuples")
    
    if len(routes) < 2:  # pragma: no cover
        raise ValueError("You must pass more than 1 route")
    if isinstance(route_colors, str):
        route_colors = [route_colors] * len(routes)
    if len(routes) != len(route_colors):  # pragma: no cover
        raise ValueError("route_colors list must have same length as routes")
    if isinstance(route_linewidths, int):
        route_linewidths = [route_linewidths] * len(routes)
    if len(routes) != len(route_linewidths):  # pragma: no cover
        raise ValueError("route_linewidths list must have same length as routes")

    # plot the graph and the first route
    override = {"route", "route_color", "route_linewidth", "show", "save", "close"}
    kwargs = {k: v for k, v in pgr_kwargs.items() if k not in override}
    fig, ax = plot_graph_route(
        G,
        route=routes[0],
        route_color=route_colors[0],
        route_linewidth=route_linewidths[0],
        show=False,
        save=False,
        close=False,
        **kwargs,
    )

    # plot the subsequent routes on top of existing ax
    override.update({"ax"})
    kwargs = {k: v for k, v in pgr_kwargs.items() if k not in override}
    r_rc_rlw = zip(routes[1:], route_colors[1:], route_linewidths[1:])
    for route, route_color, route_linewidth in r_rc_rlw:
        fig, ax = plot_graph_route(
            G,
            route=route,
            route_color=route_color,
            route_linewidth=route_linewidth,
            show=False,
            save=False,
            close=False,
            ax=ax,
            **kwargs,
        )

    # save and show the figure as specified, passing relevant kwargs
    sas_kwargs = {"save", "show", "close", "filepath", "file_format", "dpi"}
    kwargs = {k: v for k, v in pgr_kwargs.items() if k in sas_kwargs}
    fig, ax = _save_and_show(fig, ax, show=False, **kwargs)
    return fig, ax



def plot_our_route(G, route, color_mapping):
    
    route_pairs = list(zip(route[:-1], route[1:]))

    # get shortest path between route nodes
    route_legs = []
    for orig, dest in route_pairs:
        try:
            leg = tc.distance.shortest_path(G, orig, dest)
        # if no path exists between two points:
        except nx.NetworkXNoPath: 
            return None, None
        route_legs.append(leg)
        
    # assign colors to route legs
    n_colors = len(route_legs)
    
    ## alternate red -> orange -> yellow
    # colors = ['r', 'orange', 'yellow']
    # route_colors = []
    # for i in range(len(route_legs)):
    #     route_colors.append(colors[i % len(colors)])
        
    ## lime -> blue
    startcolor = mcolors.to_rgb('lime')
    endcolor = mcolors.to_rgb('cornflowerblue')
    route_colors = [mcolors.to_hex(color) for color in mcolors.LinearSegmentedColormap.from_list("", [startcolor, endcolor], n_colors)(range(n_colors))]
    
    ## rainbow
    # cmap = cm.get_cmap('gist_rainbow')
    # indices = np.linspace(0, 1, n_colors)
    # color_list = [cmap(index) for index in indices]
    # route_colors = [mcolors.to_hex(color) for color in color_list]
    
    
    
    
    
    # plot route
    fig, ax = plot_graph_routes(G, route_legs, route_colors)
    for (y, x) in route:
        ax.scatter(x=x, y=y, s=75, c=color_mapping[(y, x)])
    return fig, ax



def plot_our_routes(G, routes, color_mapping):
    print('Plotting routes...')
    figs = []
    for route in routes:
        
        # initial check
        if not all(isinstance(r, tuple) for r in route):
            continue
 
        fig, ax = plot_our_route(G, route, color_mapping) # returns None, None if no path exists

        if fig is not None:
            figs.append(fig)
    return figs


def create_color_mapping(coord_mapping, n_students, n_schools):
    # point color mapping
    school_color = 'yellow'
    student_color = 'r'
    depot_color = 'green'
    color_mapping = {}
    color_mapping[coord_mapping[0]] = depot_color
    for i in range(n_students):
        color_mapping[coord_mapping[i+1]] = student_color
    for i in range(n_schools):
        color_mapping[coord_mapping[i+n_students+1]] = school_color
    return color_mapping