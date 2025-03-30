import random
import pygame
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from models.nav_graph import NavGraph
from models.robot import Robot, RobotStatus
from controllers.traffic_manager import TrafficManager
from gui.fleet_gui import FleetGUI
import os

class FleetManager:
    # Robot colors
    ROBOT_COLORS = [
        (239, 83, 80),   # Red
        (66, 165, 245),  # Blue
        (102, 187, 106), # Green
        (255, 167, 38),  # Orange
        (171, 71, 188),  # Purple
        (38, 166, 154),  # Teal
        (255, 138, 128), # Coral
        (92, 107, 192),  # Indigo
    ]
    
    def __init__(self, gui: FleetGUI, nav_graph_file: str):
        """Initialize fleet manager"""
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(console_handler)
        
        # File handler
        file_handler = logging.FileHandler('logs/fleet_logs.txt')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(file_handler)
        
        # Initialize components
        self.gui = gui
        self.nav_graph = NavGraph.from_json(nav_graph_file)
        self.gui.set_nav_graph(self.nav_graph)
        self.robots = {}
        self.selected_robot = None
        self.notifications = []
        self.next_robot_id = 0
        self.traffic_manager = TrafficManager()
        self.clock = pygame.time.Clock()
        self.running = True
        self.notification_duration = 3.0  # Duration in seconds to show notifications
        
        # Log initialization
        self.logger.info("Fleet Management System initialized")
        self.logger.info(f"Navigation graph loaded from {nav_graph_file}")
        
    def spawn_robot(self, vertex_id: int) -> Optional[Robot]:
        """Spawn a new robot at the given vertex"""
        if vertex_id not in self.nav_graph.vertices:
            return None
            
        # Check if vertex is already occupied
        for robot in self.robots.values():
            if robot.current_vertex == vertex_id and robot.status != RobotStatus.MOVING:
                self.gui.show_notification("Cannot spawn robot - vertex is occupied")
                return None
            
        # Create new robot
        robot = Robot(self.next_robot_id, vertex_id)
        robot.color = self.ROBOT_COLORS[self.next_robot_id % len(self.ROBOT_COLORS)]
        self.robots[robot.id] = robot
        self.next_robot_id += 1
        self.logger.info(f"Spawned Robot {robot.id} at vertex {vertex_id}")
        return robot
        
    def assign_task(self, robot_id: int, destination: int) -> bool:
        """Assign a new task to a robot"""
        if robot_id not in self.robots:
            self.logger.warning(f"Failed to assign task - Robot {robot_id} not found")
            return False
            
        if destination not in self.nav_graph.vertices:
            msg = f"Destination vertex {destination} does not exist in navigation graph"
            self.gui.show_notification(msg)
            self.logger.warning(f"Failed to assign task - {msg}")
            return False
            
        robot = self.robots[robot_id]
        if robot.status not in [RobotStatus.IDLE, RobotStatus.TASK_COMPLETE]:
            msg = f"Robot {robot_id} is {robot.status.value}"
            self.gui.show_notification(msg)
            self.logger.warning(f"Failed to assign task - {msg}")
            return False
            
        if robot.is_battery_dead:
            msg = f"Robot {robot_id} has no battery - needs charging"
            self.gui.show_notification(msg)
            self.logger.warning(f"Failed to assign task - {msg}")
            return False
            
        # Get currently blocked edges from moving robots and track robot positions
        blocked_edges = set()
        blocked_vertices = set()
        robot_positions = {}  # Track all robot positions and their status
        for other_robot in self.robots.values():
            if other_robot.id != robot_id:
                robot_positions[other_robot.id] = {
                    'vertex': other_robot.current_vertex,
                    'status': other_robot.status,
                    'next_vertex': other_robot.next_vertex
                }
                if (other_robot.status == RobotStatus.MOVING and 
                    other_robot.current_vertex is not None and 
                    other_robot.next_vertex is not None):
                    edge = (min(other_robot.current_vertex, other_robot.next_vertex),
                           max(other_robot.current_vertex, other_robot.next_vertex))
                    blocked_edges.add(edge)
                if other_robot.status not in [RobotStatus.MOVING, RobotStatus.WAITING]:
                    blocked_vertices.add(other_robot.current_vertex)
            
        # Get all possible paths
        alternative_paths = self.nav_graph.get_alternative_paths(robot.current_vertex, destination)
        if not alternative_paths:
            msg = f"No path found to vertex {destination}"
            self.gui.show_notification(msg)
            self.logger.warning(f"Failed to assign task - {msg}")
            return False
            
        # Find the shortest path first
        shortest_path = min(alternative_paths, key=len)
        shortest_length = len(shortest_path)
        
        # Check if shortest path is blocked but might become available soon
        shortest_path_blocked = False
        blocking_robots = set()
        
        # Check each vertex and edge in the shortest path
        for i in range(len(shortest_path) - 1):
            current = shortest_path[i]
            next_vertex = shortest_path[i + 1]
            
            # Check if any robot is blocking this part of the path
            for other_id, pos_info in robot_positions.items():
                # Check if robot is on current vertex or edge
                if pos_info['vertex'] == current or pos_info['vertex'] == next_vertex:
                    shortest_path_blocked = True
                    blocking_robots.add(other_id)
        
        # Score each path based on blockages and length
        best_path = None
        best_score = float('inf')
        for possible_path in alternative_paths:
            if len(possible_path) < 2:
                continue
                
            # Count number of blocked edges and vertices in this path
            blocked_count = 0
            for i in range(len(possible_path) - 1):
                v1, v2 = possible_path[i], possible_path[i + 1]
                edge = (min(v1, v2), max(v1, v2))
                if edge in blocked_edges:
                    blocked_count += 1
                if possible_path[i] in blocked_vertices:
                    blocked_count += 1
            
            # Score is based on path length and number of blockages
            # Heavily penalize paths with blockages
            score = len(possible_path) + (blocked_count * 100)
            
            # If this path is much longer than the shortest path, increase the penalty
            if len(possible_path) > shortest_length * 1.5:  # If path is 50% longer than shortest
                score += 200  # Add significant penalty
            
            if score < best_score and self.traffic_manager.reserve_path(robot_id, possible_path):
                best_score = score
                best_path = possible_path
        
        # If shortest path is blocked, assign it and make robot wait
        if shortest_path_blocked and len(shortest_path) < (len(best_path) if best_path else float('inf')):
            # Assign the shortest path even though it's blocked
            if self.traffic_manager.reserve_path(robot_id, shortest_path):
                robot.assign_task(shortest_path)
                robot.wait()  # Make robot wait immediately
                msg = f"Robot {robot_id} assigned path and waiting for robots {', '.join(map(str, blocking_robots))} to move"
                self.gui.show_notification(msg)
                self.logger.info(msg)
                return True
        
        # If we found an unblocked path, use it
        if best_path is not None:
            if robot.assign_task(best_path):
                msg = f"Robot {robot_id} assigned path to vertex {destination}"
                self.logger.info(msg)
                return True
        
        msg = "Could not find a valid path to destination"
        self.gui.show_notification(msg)
        self.logger.warning(f"Failed to assign task - {msg}")
        return False
        
    def update(self, delta_time: float):
        """Update all robots and manage traffic"""
        # Update robot positions and log status changes
        for robot in self.robots.values():
            old_status = robot.status
            old_vertex = robot.current_vertex
            
            # Check if robot is at a charging station
            if self.nav_graph.vertices[robot.current_vertex].get('is_charger', False):
                if robot.status == RobotStatus.TASK_COMPLETE:
                    robot.start_charging()
                    self.logger.info(f"Robot {robot.id} started charging at vertex {robot.current_vertex}")
            
            # Update robot and check if task failed due to battery
            if not robot.update(delta_time):
                msg = f"Robot {robot.id} task failed - battery depleted"
                self.gui.show_notification(msg)
                self.logger.warning(msg)
            
            # Log status changes
            if robot.status != old_status:
                self.logger.info(f"Robot {robot.id} status changed: {old_status.value} -> {robot.status.value}")
                if robot.status == RobotStatus.BATTERY_DEAD:
                    msg = f"Robot {robot.id} battery depleted at vertex {robot.current_vertex}"
                    self.gui.show_notification(msg)
                    self.logger.warning(msg)
            if robot.current_vertex != old_vertex:
                self.logger.info(f"Robot {robot.id} moved: vertex {old_vertex} -> {robot.current_vertex}")
            
        # Update traffic management
        self.traffic_manager.update(list(self.robots.values()))
        
        # Check for robots that need charging
        for robot in self.robots.values():
            if robot.needs_charging() and not robot.is_charging() and not robot.is_battery_dead:
                # If robot is already at a charging station, start charging
                if self.nav_graph.vertices[robot.current_vertex].get('is_charger', False):
                    robot.start_charging()
                    msg = f"Robot {robot.id} started charging at current location"
                    self.gui.show_notification(msg)
                    self.logger.info(msg)
                else:
                    # Find nearest charging station
                    charging_stations = [v for v, info in self.nav_graph.vertices.items() 
                                      if info.get('is_charger', False)]
                    if charging_stations:
                        nearest = min(charging_stations, 
                                    key=lambda v: len(self.nav_graph.get_shortest_path(robot.current_vertex, v)))
                        if self.assign_task(robot.id, nearest):
                            msg = f"Robot {robot.id} heading to charging station"
                            self.gui.show_notification(msg)
                            self.logger.info(msg)
                        else:
                            msg = f"Robot {robot.id} cannot reach charging station"
                            self.gui.show_notification(msg)
                            self.logger.warning(msg)
        
        # Update blocked robots
        blocked = []
        for robot_id in self.robots:
            robot = self.robots[robot_id]
            if robot.status == RobotStatus.WAITING:
                blocked.append(robot_id)
        
        # Only update GUI if there are blocked robots
        if blocked:
            # Don't show the waiting notification at the top anymore
            # self.gui.show_notification(f"Waiting: {', '.join(map(str, blocked))}")
            pass  # The waiting robots will be shown in the dedicated "Waiting Robots" section
        
        # Draw everything
        self.draw()
        
    def draw(self):
        """Draw the current state"""
        self.gui.clear()
        
        # Draw edges first (background layer)
        for v1 in self.nav_graph.vertices:
            pos1 = self.nav_graph.vertices[v1]['coordinates']
            for v2 in self.nav_graph.get_neighbors(v1):
                if v2 > v1:  # Draw each edge only once
                    pos2 = self.nav_graph.vertices[v2]['coordinates']
                    # Check if edge is blocked
                    is_blocked = self.traffic_manager.is_edge_occupied(v1, v2)
                    self.gui.draw_edge(pos1, pos2, is_blocked)
                    
        # Draw vertices (middle layer)
        for vertex_id, info in self.nav_graph.vertices.items():
            self.gui.draw_vertex(
                info['coordinates'],
                info['name'],
                info.get('is_charger', False)
            )
            
        # Draw robots (top layer)
        for robot in self.robots.values():
            start_pos = self.nav_graph.vertices[robot.current_vertex]['coordinates']
            end_pos = None
            if robot.next_vertex is not None:
                end_pos = self.nav_graph.vertices[robot.next_vertex]['coordinates']
            # Update the selected_robot_id in GUI before drawing
            self.gui.selected_robot_id = self.selected_robot.id if self.selected_robot else None
            self.gui.draw_robot(robot, start_pos, end_pos)
            
        # Draw status panel with robot information and notifications
        self.gui.draw_status_panel(list(self.robots.values()))
        
        self.gui.update()
        
    def get_robot_at_vertex(self, vertex_id: int) -> Optional[Robot]:
        """Get robot if there's a robot at the given vertex"""
        for robot in self.robots.values():
            if robot.current_vertex == vertex_id and robot.status != RobotStatus.MOVING:
                return robot
        return None

    def handle_click(self, screen_pos: Tuple[int, int]):
        """Handle mouse click events"""
        # First check if clicked on a robot
        clicked_robot = None
        for robot in self.robots.values():
            robot_pos = self.nav_graph.vertices[robot.current_vertex]['coordinates']
            if robot.next_vertex is not None and robot.status == RobotStatus.MOVING:
                # Interpolate position for moving robots
                next_pos = self.nav_graph.vertices[robot.next_vertex]['coordinates']
                x = robot_pos[0] + (next_pos[0] - robot_pos[0]) * robot.progress
                y = robot_pos[1] + (next_pos[1] - robot_pos[1]) * robot.progress
                robot_pos = (x, y)
            
            # Convert to screen coordinates
            robot_screen_pos = self.gui._world_to_screen(robot_pos)
            
            # Check if click is within robot radius
            dx = screen_pos[0] - robot_screen_pos[0]
            dy = screen_pos[1] - robot_screen_pos[1]
            if (dx * dx + dy * dy) <= (self.gui.robot_radius * self.gui.robot_radius):
                clicked_robot = robot
                break
        
        # Then check for vertex click
        vertex_id = self.gui.get_clicked_vertex(screen_pos, self.nav_graph.vertices)
        
        if clicked_robot is not None:
            # Select the clicked robot if it's not busy
            if clicked_robot.status in [RobotStatus.IDLE, RobotStatus.TASK_COMPLETE]:
                if clicked_robot.is_battery_dead:
                    self.gui.show_notification(f"Robot {clicked_robot.id} has no battery - needs charging")
                else:
                    self.selected_robot = clicked_robot
                    self.gui.show_notification(f"Selected Robot {clicked_robot.id}")
            else:
                self.gui.show_notification(f"Robot {clicked_robot.id} is {clicked_robot.status.value}")
        elif vertex_id is not None:
            if self.selected_robot is None:
                # Check if vertex is occupied
                if not self.traffic_manager.is_vertex_occupied(vertex_id):
                    # Spawn new robot
                    new_robot = self.spawn_robot(vertex_id)
                    if new_robot:
                        self.gui.show_notification(f"Spawned Robot {new_robot.id}")
                else:
                    self.gui.show_notification("Vertex is occupied by another robot")
            else:
                # Assign task to selected robot
                if self.assign_task(self.selected_robot.id, vertex_id):
                    self.gui.show_notification(
                        f"Assigned Robot {self.selected_robot.id} to vertex {vertex_id}")
                self.selected_robot = None
            
    def handle_events(self):
        """Handle all events"""
        for action in self.gui.handle_events():
            if action["type"] == "quit":
                self.running = False
            elif action["type"] == "click":
                self.handle_click(action["pos"])

    def run(self):
        """Main game loop"""
        while self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # Convert screen coordinates to world coordinates
                    screen_pos = event.pos
                    self.handle_click(screen_pos)

            # Update
            delta_time = self.clock.tick(60) / 1000.0  # Convert to seconds
            
            # Update robot positions and traffic
            self.update(delta_time)
            
            # Draw everything
            self.gui.draw(self.nav_graph.vertices, list(self.robots.values()), 
                         self.selected_robot.id if self.selected_robot else None)
            
            # Update display
            pygame.display.flip()

        pygame.quit() 