from ursina import *
from math import *

app = Ursina()

KM = 1/12742

def latlon_to_coords(lat, lon, alt, rad):
    lat = radians(lat)
    lon = radians(lon)

    f  = 0
    ls = atan((1 - f)**2 * tan(lat))

    x = rad * cos(ls) * cos(lon) + alt * cos(lat) * cos(lon)
    y = rad * cos(ls) * sin(lon) + alt * cos(lat) * sin(lon)
    z = rad * sin(ls) + alt * sin(lat)

    return Vec3(x, y, z)

def display_point(lat, lon, alt):
    point = Entity(model="sphere", scale=0.02, position=latlon_to_coords(lat, lon, alt*KM, 0.5))

earth = Entity(model="sphere", texture="earth8k.jpg")
# ref_z = Entity(model="cube", position=Vec3(0, 0, 10), scale=0.2)

display_point(-2.3, 51.2, 100)
display_point(0, 0, 100)

EditorCamera()

app.run()
