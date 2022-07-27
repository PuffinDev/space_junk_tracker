import requests
from sgp4.api import Satrec, jday
from sgp4.conveniences import jday_datetime
from ursina import Ursina, Entity, EditorCamera, Vec3, color
import datetime

KM = 100/12742
RAD = 50

def split(list_a, chunk_size):
  for i in range(0, len(list_a), chunk_size):
    yield list_a[i:i + chunk_size]

app = Ursina()

earth = Entity(model="sphere", texture="earth2k.jpg", scale=100)

urls = [
    "http://celestrak.org/NORAD/elements/gp.php?GROUP=cosmos-2251-debris&FORMAT=tle",
    "http://celestrak.org/NORAD/elements/gp.php?GROUP=iridium-33-debris&FORMAT=tle",
    "http://celestrak.org/NORAD/elements/gp.php?GROUP=1999-025&FORMAT=tle",
    "http://celestrak.org/NORAD/elements/gp.php?GROUP=1982-092&FORMAT=tle"]

tle_text = ""
for url in urls:
    result = requests.get(url)
    if result.status_code != 200:
        raise Exception("Failed to retrive TLE data")
    tle_text += result.text

tle_list = tle_text.split("\r\n")

sat_data = list(split(tle_list, 3))
satellites = [Entity(model="sphere", scale=.25) for _ in sat_data]

for i, data in enumerate(sat_data):
    if len(data) < 3:
        sat_data.remove(data)
    if "DEB" not in data[0]:
        satellites[i].color = color.red
        satellites[i].scale = .5

sat_data_batches = list(split(sat_data, int(len(sat_data)/30)))

i = 0
def update():
    global i
    dt = datetime.datetime.now()
    jd, fr = jday_datetime(dt)

    for satellite in sat_data_batches[i]:
        j = sat_data.index(satellite)
        sat = Satrec.twoline2rv(satellite[1], satellite[2])
        _, r, _ = sat.sgp4(jd, fr)
        satellites[j].position = Vec3(r[1]*KM, r[2]*KM, r[0]*KM*-1)
    
    i += 1
    if i == 30:
        i = 0


cam = EditorCamera()
cam.target_z -= cam.zoom_speed * (abs(cam.target_z)*20)


app.run()
