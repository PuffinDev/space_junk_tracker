import requests
from sgp4.api import Satrec, jday
from sgp4.conveniences import jday_datetime
from ursina import Ursina, Entity, EditorCamera, Vec3, Vec2
from ursina.prefabs.trail_renderer import TrailRenderer
import datetime

KM = 100/12742
RAD = 50

app = Ursina()

earth = Entity(model="sphere", texture="earth8k.jpg", scale=100)

result = requests.get("http://celestrak.org/NORAD/elements/gp.php?GROUP=iridium-33-debris&FORMAT=tle")
if result.status_code != 200:
    raise Exception("Failed to retrive TLE data")

text = result.text
tle = text.split("\r\n")[1:3]

print(tle)

print("SAT: " + tle[0])

debris = Entity(model="sphere", scale=0.25)
trail = TrailRenderer(target=debris)

satellite = Satrec.twoline2rv(tle[0], tle[1])

def update():
    dt = datetime.datetime.now()
    jd, fr = jday_datetime(dt)

    e, r, v = satellite.sgp4(jd, fr)

    pos = Vec3(r[0]*KM, r[1]*KM, r[2]*KM)
    debris.position = pos
        

EditorCamera(position=Vec3(0, 0, -300), pan_speed = Vec2(20, 20))

app.run()
