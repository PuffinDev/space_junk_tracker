# Learning process

## Getting started

First we planned out some basic ideas and features for the satellite tracker. we did some research on tle data and orbit calculations by looking at the suggested libraries on the NASA space apps website such as sgp4 and worldwind. we also looked at different python 3d libraries that could be used, and outlined the pros and cons of each.

## TLE data source

We decided to source TLE (two line element) data from celestrak.org, as the api looked easy to use and there is no sign-up.

## Basic 3d tests

Around this time we were also experimenting with Ursina 3d engine for python. we also created a function that converted latitude and longitude to a point in 3d space, and made a simple ISS tracker with this. But most satellite tracking apis supply TLE data, not coordinates, so this method was scrapped.

## Calculating orbits

We used the sgp4 library to calculate satellite positions from tle data. we got a simple tracker working by loading every tle set in a celestrak dataset, running each through sgp4, and displaying a sphere at the correct position. It took a while to figure out which way the axis went because the positions given by sgp4 use the earth centred inertial coordinate system in which z is up. The positions were also scaled down because the earth's radius was 1 unit in Ursina.

## Limitations of Ursina

As we tested larger datsets with hundreds or thousands of points, Ursina struggled to keep up. With 4,000 points displaying, the FPS was reduced to around 15. It was clear that rendering a physical 3d sphere for every satellite was not performant enough.

## Choosing a 3d datascience library

We needed a 3d library that could render thousands of points in 3d space at a high framerate, so we started looking for one on datascience websites. we eventually found open3d, and it seemed perfect as it could display massive point clouds. we did a stress test and it easily handled 1,000,000 points with no issues. The only problem was that open3d seemed to have some compatibility issues with the latest python versions. So then we found pyvista which has better compatibility, and seemed even better suited for the job.

## Pyvista rewrite

Rewriting the program in pyvista was relatively easy as we could just copy and paste large parts of the program. Soon we had a working pyvista version that was much more preformant than the Ursina version. We tried displaying 30,000 satellites and it worked flawlessly.

## Density heat map

We decided to color each point depending on how many other satellites were within a 1000KM range in order to highlight the dense areas where lots of satellites were passing. We did this by using a nested loop to iterate over every satellite and check every other satellite's proximity. This is an extremely inefficient way of doing things, so we rewrote it later.

## Pyqt5 UI

The goal was to have methods of integrating with the plot and display different datasets, have a time slider, etc. so we decided to use PyQt5 as there is a library that integrates it with pyvista called pyvistaqt. We took some example code from the pyvistaqt docs and worked from there. Eventually we had the pyvista plot running in a pyqt5 window.

## Dataset switching

In order to allow the user to switch datasets, we added a menubar that had a button for each dataset. These datasets were loaded from the datasets.json file and contain urls leading to tle data to be displayed. We had to stop the position update and density update threads and then restart them again, and also redraw the point cloud every time the dataset was changed.


## Speeding up density calculations

After looking into ways of quickly finding neighbours of a point in 3d space, we found the scipy library which had a wide range of algorithms, including KDTree which can quickly find neighbours. Once we implemented it, the density calculations were a lot quicker.

## Finding more TLE sources

CelesTrak only has a limited amount of TLE data so we tried to find more sources. We found the site space-track.org which had around 15,000 satellites.

## Loading from space-track

To use space-track data we looked at the api documentation, and found that you needed to have an account and authenticate requests by posting login credentials. We used the provided example as reference and created a seperate function to retrieve stace-track data. This function is only called when the url contains "space-track.org", otherwise the normal request function is called as other tle sites (like celestrak) don't require authentication.

## Speeding up requests

Loading all the data from celestrak and space-track from multiple urls took quite a while, so we looked into ways to speed it up. We sound the grequests python module that made requests asyncronously at the same time. This significantly sped up the load time.

## Time slider

To implement a time slider, we decided on using an offset of the current time to display past or future positions. If the offset was +10, the visualisation would be 10 minutes ahead, if it was -10 it would be 10 minutes behind. This meant that when the offset was changed, the satellites would still move and update. We used a pyvista slider to select the offset, and passed it into the calculate_positions function which then added it or subtracted it from the current unix time.

## Displaying debris

We wanted some way of differentiating debris and non-debris, so we decided to add a button to switch between showing density and showing debris with point colors. If a satellite is debris then it will have "DEB" in it's name in the tle data, so it was very easy to mark those satellites as debris and display them as a different color.
