import requests
from sgp4.api import Satrec
from ursina import Ursina, Entity, EditorCamera, Vec3
from skyfield.api import load
import datetime

ts = load.timescale() # sorting out julian date time
t = ts.tt()
print(t)

jd = float('{:.10f}'.format(t.tdb))

print(jd)

exit()

KM = 100/12742
RAD = 50

app = Ursina()

earth = Entity(model="sphere", texture="earth8k.jpg", scale=100)

result = requests.get("http://celestrak.org/NORAD/elements/gp.php?GROUP=iridium-33-debris&FORMAT=tle")
if result.status_code != 200:
    raise Exception("Failed to retrive TLE data")

text = result.text
tle = text.split("\r\n")[1:3]

print("SAT: " + text[0])

satellite = Satrec.twoline2rv(tle[0], tle[1])

fr = 0.0
e, r, v = satellite.sgp4(jd, fr)

pos = Vec3(r[0]*KM, r[1]*KM, r[2]*KM)

debris = Entity(model="sphere", scale=0.25, position=pos)

EditorCamera(position=Vec3(0, 0, -300))

app.run()
