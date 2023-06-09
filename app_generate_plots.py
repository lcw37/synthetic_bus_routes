import route_variables
import travel_times
import plot2
import MIP

import streamlit as st
import osmnx as ox
import numpy as np
import pandas as pd

import io
import zipfile



def get_random_n_students():
    """ Randomly draws a new value for n_students """
    st.session_state["n_students"] = route_variables.random_n_students()
    return

def get_random_n_schools():
    """ Randomly draws a new value for n_schools """
    st.session_state["n_schools"] = np.random.randint(1, 8)
    return

def generate_points(n_students, n_schools, mode, location_data, container):
    # generate graph and coordinates
    G = travel_times.generate_G(mode, location_data)
    coords = travel_times.generate_random_coords(G, n_students, n_schools, depot_coords=(40.7283, -73.94060)) # (y, x)
    color_mapping = plot2.create_color_mapping(coords, n_students, n_schools)
    # save graph and coordinates to st.session_state
    st.session_state['coords'] = coords
    st.session_state['G'] = G
    st.session_state['color_mapping'] = color_mapping
    # plot graph and coordinates
    plot_points(G, coords, color_mapping, container)
    return

def plot_points(G, coords, color_mapping, container):
    fig, ax = ox.plot_graph(G)
    for node in coords:
        y, x = coords[node]
        ax.scatter(x=x, y=y, s=75, c=color_mapping[(y, x)])
    # save the coordinate graph to session_state
    st.session_state['points_fig'] = fig
    container.pyplot(st.session_state.points_fig)


def generate_routes(G, n_students, n_schools, coords, max_routes, container):
    
    progress_value = 0
    progress_text = "Starting..."
    my_bar = container.progress(progress_value, text=progress_text)
    progress_value += 5
    
    progress_text = 'Calculating travel times... (this may take a while!)'
    my_bar.progress(progress_value, text=progress_text)
    travel_time_table = travel_times.calculate_travel_times(G, n_students, n_schools, coords)
    progress_value += 40

    progress_text = 'Getting start times...'
    my_bar.progress(progress_value, text=progress_text)
    starting_times = MIP.generate_start_times(n_schools)
    progress_value += 15
    
    progress_text = 'Getting feasible routes...'
    my_bar.progress(progress_value, text=progress_text)
    routes, start_time_solutions  = MIP.get_feasible_routes(n_students, n_schools, starting_times, travel_time_table, coords, max_routes)
    progress_value += 20

    # check for accidental infeasible routes (integers included in the route when they shouldn't be)
    _routes = []
    for route in routes:
        print(route)
        if all(isinstance(r, tuple) for r in route):
            _routes.append(route)
    routes = _routes
    
    progress_text = 'Plotting routes...'
    my_bar.progress(progress_value, text=progress_text)
    plots = plot2.plot_our_routes(G, routes, st.session_state.color_mapping)
    progress_value += 20
    
    progress_text = 'Done!'
    my_bar.progress(progress_value, text=progress_text)
    
    if len(plots) > 0:
        container.write('Number of routes generated:')
        container.write(len(plots))
        
        # download routes as zip
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "x") as csv_zip:
            # plot routes and write to zip
            for i in range(len(plots)):
                container.pyplot(plots[i]) # plot route
                create_route_df(routes[i], start_time_solutions[i], coords)
                csv_zip.writestr(f"route_{i+1}.csv", pd.DataFrame(st.session_state.route_data).to_csv())
        # create download button
        container.download_button(
            label="Download zip",
            data=buf.getvalue(),
            file_name="routes.zip",
            mime="application/zip",
        )
                
    else:
        container.write('No feasible routes found.')
        
    return routes, start_time_solutions


def create_coords_df(coords):
    # build a DataFrame of the coordinates and save to session_state
    data = []
    for nodeid in coords:
        (y, x) = coords[nodeid]
        data.append([nodeid, y, x])
    data = pd.DataFrame(data, columns=['Node ID', 'Latitude (y)', 'Longitude (x)'])
    # data.index.name = 'Node ID'
    st.session_state['coords_data'] = data
    
    # create an expandable tab with the coordinates of each point
    with st.expander('View coordinates'):
        st.dataframe(data, use_container_width=True)
        
        
def create_route_df(route, start_times, coords_mapping):
    # first flip the coords_mapping from id:coords -> coords:id
    coords_mapping = {v: k for k, v in coords_mapping.items()}
    # build data
    data = []
    print('==== ROUTE', route)
    print('---- TIMES', start_times)
    for pair, t in zip(route, start_times):
        print('==== pair, t', pair, t)
        nodeid = coords_mapping[pair]
        (y, x) = pair
        data.append([nodeid, y, x, t])
    data = pd.DataFrame(data, columns=['Node ID', 'Latitude (y)', 'Longitude (x)', 'Arrival Time'])
    st.session_state['route_data'] = data
    
    # create an expandable tab with the coordinates/times of each route
    with st.expander('View coordinates'):
        st.dataframe(data, use_container_width=True)
    