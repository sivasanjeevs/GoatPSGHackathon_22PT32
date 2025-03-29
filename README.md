# Fleet Management System

A Python-based Fleet Management System for coordinating multiple robots in a shared environment. The system features real-time visualization, traffic negotiation, and collision avoidance.

## Features

- Interactive GUI with modern dark theme
- Real-time robot movement visualization
- Traffic negotiation and collision avoidance
- Dynamic robot spawning and task assignment
- Status monitoring and notifications
- Support for charging stations

## Requirements

- Python 3.8+
- Dependencies listed in requirements.txt

## Running the System

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the GUI system:
```bash
python src/main.py
```

## Using the System

1. Interacting with robots:
   - Click on any vertex to spawn a new robot
   - Click on a robot to select it
   - Click on a destination vertex to assign a task to the selected robot
   - Robots will automatically navigate while avoiding collisions
   - The status panel on the right shows robot information
   - Notifications appear at the top of the screen

2. Understanding the interface:
   - Blue vertices: Regular locations
   - Yellow vertices: Charging stations
   - Green edges: Available paths
   - Purple highlight: Selected robot/vertex
   - Unique colors for each robot
   - Status indicators below each robot
   - Battery indicators for charging robots
   - Red X markers for blocked paths

## Navigation Graph

The system uses a JSON-based navigation graph (`data/nav_graph.json`) that defines:
- Vertices: Locations with coordinates and attributes
- Lanes: Connections between vertices
- Charging stations: Special vertices marked with `is_charger: true`

## Traffic Management

The system implements the following traffic rules:
- Only one robot can occupy a vertex at a time
- Only one robot can traverse an edge at a time
- Robots automatically wait when their path is blocked
- Real-time path updates and collision avoidance

## Project Structure
```
fleet_management_system/
├── data/
│   └── nav_graph.json
├── src/
│   ├── models/
│   │   ├── nav_graph.py
│   │   └── robot.py
│   ├── controllers/
│   │   ├── fleet_manager.py
│   │   └── traffic_manager.py
│   ├── gui/
│   │   └── fleet_gui.py
│   └── main.py
├── requirements.txt
└── README.md
``` 