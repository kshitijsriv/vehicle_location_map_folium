import folium as folium
from flask import Flask, render_template
import rethinkdb as rtdb
import os
from dotenv import load_dotenv
import requests
import json

app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello World!'


def get_route_polyline(route):
    # "http://routesapi.chartr.in/transit/dimts/get_transit_route_details?route=534UP"
    url = f"http://routesapi.chartr.in/transit/dimts/get_transit_route_details?route={route}UP"
    response = requests.get(url)
    response_dict = json.loads(response.text)
    polyline = list()
    stop_names = list()
    if response_dict['msg'] == 'Found':
        stop_list = response_dict['transit_route'][0]['stops']
        for stop in stop_list:
            polyline.append((float(stop['lat']), float(stop['lon'])))
            stop_names.append(stop['name'])
        return True, polyline, stop_names
    else:
        return False, polyline, stop_names


def plot_map(bus_number, coords, ac, route=None):
    m = folium.Map(location=[28.630691, 77.217648], zoom_start=11)
    if ac == "ac":
        folium.Marker(coords, popup=bus_number, icon=folium.Icon(color='red')).add_to(m)
    else:
        folium.Marker(coords, popup=bus_number, icon=folium.Icon(color='red')).add_to(m)
    if route is not None:
        got_polyline, route_polyline, stop_names = get_route_polyline(route)
        if got_polyline:
            folium.PolyLine(route_polyline, color='black', weight=1.5, opacity=1).add_to(m)
            for idx, stop_coord in enumerate(route_polyline):
                stop_name = stop_names[idx]
                folium.CircleMarker(location=stop_coord, radius=4, popup=stop_name,
                                    fill_color='blue', color='red', fill_opacity=1).add_to(m)
    return m._repr_html_()


# view/DL1PC0588/534DOWN
@app.route("/view/<bus_number>/<route>", methods=["GET"])
def view(bus_number, route):
    # rethinkdb connection
    env_path = '.env'
    load_dotenv(env_path)
    rDB_name = os.getenv("rDB_name")
    realtime_table = os.getenv("realtime_table")
    host = os.getenv("host")
    port = os.getenv("port")

    r = rtdb.RethinkDB()
    rconn = r.connect(host=host, port=port)

    bus_data = json.loads(r.db(rDB_name).table(realtime_table).get(bus_number).to_json().run(rconn))
    if bus_data is not None:
        ac = bus_data['ac']
        coordinates = bus_data['lat'], bus_data['lng']
        folium_map = plot_map(bus_number, coordinates, ac, route=route)
        return render_template('views/view.html', map=folium_map, bus=bus_number)
    else:
        return render_template('views/not_found.html')


if __name__ == '__main__':
    app.run()
