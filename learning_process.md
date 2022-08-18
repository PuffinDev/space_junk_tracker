# Learning process

## Getting started

First we planned out some basic ideas and features for the satellite tracker. we did some reasearch on tle data and orbit calculations by looking at the suggested libraries on the NASA space apps website such as sgp4 and worldwind. we also looked at different python 3d libraries that could be used, and outlined the pros and cons of each.

## TLE data source

We decided to source TLE (two line element) data from celestrak.org, as the api looked easy to use and there is no sign-up.

## Basic 3d tests

Around this time we were also experimenting with ursina 3d engine for python. we also created a function that converted latitude and longitude to a point in 3d space, and made a simple ISS tracker with this. But most satellite tracking apis supply TLE data, not coordinates, so this method was scrapped.

## Calculating orbits

We used the sgp4 library to calculate satellite positions from tle data. we got a simple tracker working by loading every tle set in a celestrak datset, running each through sgp4, and displaying a sphere at the correct position. It took a while to figure out which way the axis went because the positions given by sgp4 use the earth centered inertial coordinate system in which z is up. The positions were also scaled down because the earth's radius was 1 unit in ursina.

## Limitations of ursina

As we tested larger datsets with hundereds or thousands of points, ursina struggled to keep up. With 4,000 points displaying, the FPS was reduced to around 15. It was clear that rendering a physical 3d sphere for every satellite was not preformant enough.

## Choosing a 3d datascience library

We needed a 3d library that could render thousants of points in 3d space at a high framerate, so we started looking for one on datascience websites. we eventually found open3d, and it seemed perfect as it could display massive point clouds. we did a stress test and it easily handled 1,000,000 points with no issues. The only problem was that open3d seemed to have some compatability issues with the latest python versions. So then we found pyvista which has better compatability, and seemed even better suited for the job.

## Pyvista rewrite

Reweiting the program in pyvista was relatively easy as we could just copy and paste large parts of the program. Soon we had a working pyvista version that was much more preformant than the ursina version. We tried displaying 30,000 satellites and it worked flawlessly.
