from turtle import position
from ursina import Ursina, Entity, EditorCamera, Vec3
from utils import latlon_to_coords
from threading import Thread
from time import sleep
import requests
import json

app = Ursina()

def display_point(lat, lon, alt):
    return Entity(model="ISS_stationary.glb", scale=.025, position=latlon_to_coords(lat, lon, alt))

earth = Entity(model="sphere", texture="earth8k.jpg", scale=100)

iss = display_point(0, 0, 100)
pos = {"latitude": 0, "longitude": 0, "altitude": 0}

def get_pos():
    global pos

    while True:
        result = requests.get("https://api.wheretheiss.at/v1/satellites/25544")
        if result.status_code != 200:
            return
        
        pos = result.json()
        sleep(1)

def update():
    global pos
    iss.position = latlon_to_coords(pos["latitude"], pos["longitude"], pos["altitude"])

EditorCamera(position=Vec3(0, 0, -300))

get_pos_thread = Thread(target=get_pos)
get_pos_thread.start()

app.run()
