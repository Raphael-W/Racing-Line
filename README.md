# Racing Line Finder
When racing, it's important to know where to position yourself on the track, where to brake and accelerate. For new racers, or simply new tracks this can be challenging and figuring this out can be time-consuming. This project aims to find the most optimal racing line around a track. 

## Setup:
This project requires you to have python installed
1. Clone the repository to your local machine
```bash
git clone https://github.com/Raphael-W/Racing-Line.git
```

2. Install the required libraries:
```bash
pip install -r requirements.txt
```

3. Run `Racing Line.bat`

To be able to open a `.track` file, double click it, and find `Racing Line.bat`.

## Track Designer
- Left click to add points (both to the end of the track and on the track)
- Right click to remove the point
<!-- -->
- Hold down the scroll wheel to pan
- Scroll to zoom
<!-- -->
- Set scale of track by choosing "Set Scale", selecting 2 points you known the distance of, and typing in the actual distance
- Set where the finish line is by choosing "Set Finish" and picking any point on the curve
- Upload a reference image in order to recreate a preexisting track (e.g. screenshots from Google Earth)
<!-- -->
- You can toggle the 'Racing Line' switch at any time to view the racing line

## Track Testing
- In order to test your newly created track, you are able to drive around a car using a controller of the arrow keys/WASD keys on your keyboard
- The car will turn red to indicate you have left the track
- Hit 'R' on your keyboard or 'X' on your controller to reset the car to the track's start line
- Hit 'Tab' or use the dropdown menu at the top to switch between 'Track Testing' and 'Track Editor'


## Examples:
Example tracks can be located in `tracks/`

**Tracks:**
- Aurora
- Dirt Mania
- Mountain Roads
- Silverstone
- Solaris Speedway
- Whittle Circuit
