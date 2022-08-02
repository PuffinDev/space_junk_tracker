from math import radians, tan, atan, cos, sin
from ursina import Vec3

KM = 100/12742
RAD = 50

def latlon_to_coords(lat, lon, alt):
    lat = radians(lat)
    lon = radians(lon)
    alt = alt*KM

    f  = 0
    ls = atan((1 - f)**2 * tan(lat))

    x = RAD * cos(ls) * cos(lon) + alt * cos(lat) * cos(lon)
    y = RAD * cos(ls) * sin(lon) + alt * cos(lat) * sin(lon)
    z = RAD * sin(ls) + alt * sin(lat)

    return Vec3(x, y, z)
