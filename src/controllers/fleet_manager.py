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
            
        # Get all possible paths first
        alternative_paths = self.nav_graph.get_alternative_paths(robot.current_vertex, destination)
        if not alternative_paths:
            msg = f"No path found to vertex {destination}"
            self.gui.show_notification(msg)
            self.logger.warning(f"Failed to assign task - {msg}")
            return False
            
        # Get currently blocked edges and vertices
        blocked_edges = set()
        blocked_vertices = set()
        moving_robots = {}  # Track moving robots and their paths
        
        for other_robot in self.robots.values():
            if other_robot.id != robot_id:
                # Track moving robots and their paths
                if other_robot.status == RobotStatus.MOVING and other_robot.next_vertex is not None:
                    moving_robots[other_robot.id] = {
                        'current': other_robot.current_vertex,
                        'next': other_robot.next_vertex,
                        'path': self.traffic_manager.reserved_paths.get(other_robot.id, [])
                    }
                    edge = (min(other_robot.current_vertex, other_robot.next_vertex),
                           max(other_robot.current_vertex, other_robot.next_vertex))
                    blocked_edges.add(edge)
                # Track stationary robots
                elif other_robot.status not in [RobotStatus.MOVING, RobotStatus.WAITING]:
                    blocked_vertices.add(other_robot.current_vertex)
        
        # Find shortest path first
        shortest_path = min(alternative_paths, key=len)
        shortest_length = len(shortest_path)
        
        # Score and evaluate each path
        best_path = None
        best_score = float('inf')
        
        for path in alternative_paths:
            if len(path) < 2:
                continue
                
            # Initialize path metrics
            path_score = len(path)  # Base score is path length
            is_blocked = False
            has_collision = False
            
            # Check each segment of the path
            for i in range(len(path) - 1):
                current = path[i]
                next_vertex = path[i + 1]
                edge = (min(current, next_vertex), max(current, next_vertex))
                
                # Check for immediate blockages
                if next_vertex in blocked_vertices:
                    path_score += 100  # Heavy penalty for blocked vertices
                    is_blocked = True
                if edge in blocked_edges:
                    path_score += 50   # Medium penalty for blocked edges
                    is_blocked = True
                
                # Check for potential collisions with moving robots
                for robot_info in moving_robots.values():
                    robot_path = robot_info['path']
                    if len(robot_path) > i:
                        # Check if robots would meet at a vertex
                        if robot_path[i] == next_vertex:
                            has_collision = True
                            path_score += 75  # Penalty for potential collision
                
            # Add length penalty if path is much longer than shortest
            if len(path) > shortest_length * 1.5:
                path_score += 150  # Heavy penalty for very long paths
            
            # Try to reserve this path if it's better than current best
            if path_score < best_score and not has_collision:
                if self.traffic_manager.reserve_path(robot_id, path):
                    best_path = path
                    best_score = path_score
                    # If this is a good path with no collisions, use it immediately
                    if not is_blocked and len(path) <= shortest_length * 1.2:
                        break
        
        # If we found a valid path, use it
        if best_path is not None:
            if robot.assign_task(best_path):
                msg = f"Robot {robot_id} assigned path to vertex {destination}"
                self.logger.info(msg)
                return True
            
        # If no good path found, try shortest path and wait if needed
        if self.traffic_manager.reserve_path(robot_id, shortest_path):
            robot.assign_task(shortest_path)
            if any(v in blocked_vertices or (min(path[i], path[i+1]), max(path[i], path[i+1])) in blocked_edges 
                  for i, v in enumerate(shortest_path[:-1])):
                robot.wait()
                msg = f"Robot {robot_id} taking shortest path and waiting when blocked"
            else:
                msg = f"Robot {robot_id} taking shortest path"
            self.gui.show_notification(msg)
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