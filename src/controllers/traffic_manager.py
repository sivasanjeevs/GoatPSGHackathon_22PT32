from typing import Dict, List, Set, Tuple, Optional
from models.robot import Robot, RobotStatus

class TrafficManager:
    def __init__(self):
        self.edge_occupancy: Dict[Tuple[int, int], int] = {}  # (v1, v2) -> robot_id
        self.vertex_occupancy: Dict[int, int] = {}  # vertex_id -> robot_id
        self.reserved_paths: Dict[int, List[int]] = {}  # robot_id -> path
        self.waiting_robots: Set[int] = set()  # Set of robots waiting for clearance
        
    def _get_edge_key(self, v1: int, v2: int) -> Tuple[int, int]:
        """Get a consistent key for an edge regardless of vertex order"""
        return (min(v1, v2), max(v1, v2))
        
    def is_edge_occupied(self, v1: int, v2: int, ignore_robot_id: Optional[int] = None) -> bool:
        """Check if an edge is occupied by any robot except the ignored one"""
        edge = self._get_edge_key(v1, v2)
        if edge not in self.edge_occupancy:
            return False
        if ignore_robot_id is not None and self.edge_occupancy[edge] == ignore_robot_id:
            return False
        return True

    def is_vertex_occupied(self, vertex: int, ignore_robot_id: Optional[int] = None) -> bool:
        """Check if a vertex is occupied by any robot except the ignored one"""
        if vertex not in self.vertex_occupancy:
            return False
        if ignore_robot_id is not None and self.vertex_occupancy[vertex] == ignore_robot_id:
            return False
        return True

    def is_path_available(self, robot_id: int, path: List[int]) -> bool:
        """Check if a path is available for a robot"""
        if not path:
            return False
            
        # Only check immediate next vertex and edge
        current_vertex = path[0]
        next_vertex = path[1] if len(path) > 1 else None
        
        if next_vertex is None:
            return True
            
        # Check if next vertex is occupied by another robot
        if self.is_vertex_occupied(next_vertex, ignore_robot_id=robot_id):
            return False
            
        # Check if edge to next vertex is occupied
        if self.is_edge_occupied(current_vertex, next_vertex, ignore_robot_id=robot_id):
            return False
            
        # Check for potential head-on collisions with other robots' reserved paths
        edge = self._get_edge_key(current_vertex, next_vertex)
        for other_id, other_path in self.reserved_paths.items():
            if other_id != robot_id and len(other_path) > 1:
                other_edge = self._get_edge_key(other_path[0], other_path[1])
                if edge == other_edge:
                    # If robots would move in opposite directions on the same edge
                    if other_path[0] == next_vertex and other_path[1] == current_vertex:
                        return False
            
        return True

    def reserve_path(self, robot_id: int, path: List[int]) -> bool:
        """Try to reserve a path for a robot"""
        if not self.is_path_available(robot_id, path):
            return False
            
        # Clear any existing reservations for this robot
        self.clear_reservations(robot_id)
        
        # Reserve the path
        self.reserved_paths[robot_id] = path
        return True

    def clear_reservations(self, robot_id: int):
        """Clear all reservations for a robot"""
        # Clear vertex reservations
        vertices_to_clear = [v for v, r_id in self.vertex_occupancy.items() 
                         if r_id == robot_id]
        for v in vertices_to_clear:
            del self.vertex_occupancy[v]

        # Clear edge reservations
        edges_to_clear = [(v1, v2) for (v1, v2), r_id in self.edge_occupancy.items() 
                         if r_id == robot_id]
        for e in edges_to_clear:
            del self.edge_occupancy[e]
            
        # Clear path reservation
        if robot_id in self.reserved_paths:
            del self.reserved_paths[robot_id]
            
        # Clear from waiting robots
        if robot_id in self.waiting_robots:
            self.waiting_robots.remove(robot_id)

    def update(self, robots: List[Robot]):
        """Update traffic management state"""
        # Clear all occupancy data
        self.edge_occupancy.clear()
        self.vertex_occupancy.clear()
        
        # First pass: Update occupancy based on current robot positions
        for robot in robots:
            # Update vertex occupancy for current position
            self.vertex_occupancy[robot.current_vertex] = robot.id
            
            if robot.status == RobotStatus.MOVING and robot.next_vertex is not None:
                # Occupy edge while moving
                edge = self._get_edge_key(robot.current_vertex, robot.next_vertex)
                self.edge_occupancy[edge] = robot.id
        
        # Second pass: Check for conflicts and manage traffic
        for robot in robots:
            if robot.status in [RobotStatus.MOVING, RobotStatus.WAITING]:
                path = self.reserved_paths.get(robot.id, [])
                if path and robot.path_index < len(path) - 1:
                    current = path[robot.path_index]
                    next_vertex = path[robot.path_index + 1]
                    
                    # Check if next vertex or edge is blocked
                    is_blocked = False
                    
                    # Check if next vertex is occupied
                    if self.is_vertex_occupied(next_vertex, robot.id):
                        is_blocked = True
                    
                    # Check if edge is occupied
                    if self.is_edge_occupied(current, next_vertex, robot.id):
                        is_blocked = True
                    
                    # Check for potential head-on collisions or crossing paths
                    for other_robot in robots:
                        if other_robot.id != robot.id:
                            # If other robot is at our next vertex
                            if other_robot.current_vertex == next_vertex:
                                # If other robot is moving or waiting
                                if other_robot.status in [RobotStatus.MOVING, RobotStatus.WAITING]:
                                    # If other robot's next vertex is our current vertex
                                    if other_robot.next_vertex == current:
                                        # Higher ID robot should wait
                                        if robot.id > other_robot.id:
                                            is_blocked = True
                                            break
                                else:  # Other robot is stationary
                                    is_blocked = True
                                    break
                            # If other robot is moving to our next vertex
                            elif (other_robot.status == RobotStatus.MOVING and 
                                  other_robot.next_vertex == next_vertex):
                                # Higher ID robot should wait
                                if robot.id > other_robot.id:
                                    is_blocked = True
                                    break
                    
                    if is_blocked:
                        if robot.id not in self.waiting_robots:
                            robot.wait()
                            self.waiting_robots.add(robot.id)
                    elif robot.id in self.waiting_robots:
                        robot.resume()
                        self.waiting_robots.remove(robot.id)

    def get_blocked_robots(self) -> List[int]:
        """Get list of robots that are currently blocked"""
        return list(self.waiting_robots) 