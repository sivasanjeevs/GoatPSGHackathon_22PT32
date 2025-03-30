# Fleet Management System

A Python-based Fleet Management System for coordinating multiple robots in a shared environment. The system features real-time visualization, traffic negotiation, and collision avoidance with an interactive GUI built using Python and Pygame.

---
## Demo Video
[Watch the Video](https://drive.google.com/file/d/141KqgvCAwYq4NQOv4zF0yPuhKTsT41gC/view?usp=sharing)

## Navigation Graphs

### First Navigation Graph
![First Navigation Graph](goat1.jpg)

### Second Navigation Graph
![Second Navigation Graph](goat2.jpg)

### Third Navigation Graph
![Third Navigation Graph](goat3.jpg)

---

## Features

### Robot Management
- **Robot Spawning**: Click on an unoccupied vertex to spawn a robot.
- **Robot Selection**: Click on an idle or task-complete robot to select it.
- **Task Assignment**: Click on a destination vertex after selecting a robot.
- **Multiple Robots**: Supports multiple robots with unique IDs and colors.
- **Robot States**:
  - `IDLE`: Waiting for task assignment.
  - `MOVING`: In transit between vertices.
  - `WAITING`: Temporarily stopped due to path blockage.
  - `CHARGING`: Recharging at a charging station.
  - `TASK_COMPLETE`: Task successfully completed.
  - `BATTERY_DEAD`: Battery depleted, needs charging.

### Battery System
- **Battery Monitoring**: Each robot's battery depletes while moving.
- **Low Battery Indicator**: Alerts when below 30%.
- **Automatic Charging**:
  - Robots automatically navigate to the nearest charging station when battery drops below 20%.
  - If battery reaches 0%, the robot stops and requires manual intervention.
  - Charging stations are marked with a ⚡ symbol.
- **Battery Dead State**:
  - Robot stops moving at 0% battery.
  - Cannot accept new tasks until charged.

### Traffic Management
- **Path Finding**: Automatic calculation of optimal paths between vertices.
- **Collision Avoidance**:
  - Prevents multiple robots from occupying the same vertex.
  - Robots wait when paths are blocked.
- **Edge Blocking**: Blocked paths indicated with red X markers.
- **Alternative Paths**: Finds alternate routes when needed.

### Visual Interface
- **Interactive GUI**: Real-time visualization with a modern dark theme.
- **Status Panel**:
  - Robot statuses and battery levels.
  - Charging station information.
  - Waiting robots overview.
- **Visual Indicators**:
  - Color-coded robot states.
  - Path previews and blocked path markers.
  - Battery level bars and charging station glow effects.
  - Selection highlights.
  - **Vertex Colors**:
    - Blue: Regular locations
    - Yellow: Charging stations
  - **Edge Colors**:
    - Green: Available paths

---

## Installation and Running

### Requirements
- Python 3.8+
- Pygame 2.x
- Dependencies listed in `requirements.txt`

### Installation
```bash
pip install -r requirements.txt
```

### Running the System
```bash
cd src
python main.py
```

### Selecting a Navigation Graph
```bash
cd src

# First navigation graph
python main.py --graph 1

# Second navigation graph
python main.py --graph 2

# Third navigation graph
python main.py --graph 3
```
*If no graph is specified, the system defaults to Graph 1.*

---

## System Usage

### Basic Controls
- **Left Click on Vertex**: Spawn a new robot (if none selected) or set a destination (if a robot is selected).
- **Left Click on Robot**: Select a robot for task assignment.
- **Close Window**: Exit the application.

### Interface Elements
- **Status Panel**: Displays robot information and notifications.
- **Robot Indicators**: Each robot has a unique color and battery level indicator.
- **Charging Stations**: Marked in yellow with a glow effect.

---

## Navigation Graph
The system uses a JSON-based navigation graph (`data/nav_graph.json`) that defines:
- **Vertices**: Locations with coordinates and attributes.
- **Lanes**: Connections between vertices.
- **Charging Stations**: Special vertices marked as `is_charger: true`.

---

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

---

## Technical Details
- **Built With**: Python & Pygame
- **Navigation**: Graph-based pathfinding
- **Collision Avoidance**: Real-time path reservation system
- **Architecture**: Modular with separate components for:
  - Fleet Management
  - Traffic Control
  - Robot Control
  - GUI Rendering
  - Navigation System
  - Battery Management
- **Performance Optimizations**:
  - 60 FPS update rate for smooth animations
  - Double buffering for efficient rendering
  - Optimized pathfinding and collision detection

---
## Video
[Watch the Video](https://drive.google.com/file/d/141KqgvCAwYq4NQOv4zF0yPuhKTsT41gC/view?usp=sharing)

This Fleet Management System provides an interactive and efficient solution for coordinating multiple robots in a dynamic environment. 🚀

