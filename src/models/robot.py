from enum import Enum
from typing import List, Tuple, Optional
import random

class RobotStatus(Enum):
    IDLE = "idle"
    MOVING = "moving"
    WAITING = "waiting"
    CHARGING = "charging"
    TASK_COMPLETE = "task_complete"
    LOW_BATTERY = "low_battery"
    BATTERY_DEAD = "battery_dead"  # New status for when battery is completely depleted

class Robot:
    def __init__(self, id: int, start_vertex: int):
        self.id = id
        self.current_vertex = start_vertex
        self.next_vertex = None
        self.path: List[int] = []
        self.path_index = 0
        self.progress = 0.0
        self.status = RobotStatus.IDLE
        self.battery_level = 100.0
        self.battery_drain_rate = 5.0  # percent per second
        self.charging_rate = 20.0  # percent per second
        self.move_speed = 1.0  # units per second
        self.color = (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
        self.is_battery_dead = False  # New flag to track if battery is completely depleted

    def update(self, delta_time: float):
        """Update robot state"""
        if self.status == RobotStatus.MOVING:
            # Update progress along current edge
            self.progress += self.move_speed * delta_time
            
            # Check if reached next vertex
            if self.progress >= 1.0:
                self.current_vertex = self.next_vertex
                self.progress = 0.0
                self.path_index += 1
                
                # Check if path is complete
                if self.path_index >= len(self.path) - 1:
                    self.next_vertex = None
                    self.status = RobotStatus.TASK_COMPLETE
                    self.path = []
                    self.path_index = 0
                else:
                    self.next_vertex = self.path[self.path_index + 1]
            
            # Update battery level while moving
            self.battery_level = max(0.0, self.battery_level - self.battery_drain_rate * delta_time)
            if self.battery_level <= 0.0:
                self.is_battery_dead = True
                self.status = RobotStatus.BATTERY_DEAD
                self.next_vertex = None
                self.path = []
                self.path_index = 0
                return False  # Return False to indicate task failed
        
        elif self.status == RobotStatus.CHARGING:
            # Charge battery
            self.battery_level = min(100.0, self.battery_level + self.charging_rate * delta_time)
            if self.battery_level >= 100.0:
                self.status = RobotStatus.TASK_COMPLETE
                self.is_battery_dead = False  # Reset battery dead flag when fully charged
                
        return True  # Return True to indicate task is still valid

    def assign_task(self, path: List[int]) -> bool:
        """Assign a new path to follow"""
        if not path or len(path) < 2:
            return False
            
        if self.status not in [RobotStatus.IDLE, RobotStatus.TASK_COMPLETE]:
            return False
            
        if self.is_battery_dead:
            return False
            
        self.path = path
        self.path_index = 0
        self.next_vertex = path[1]
        self.progress = 0.0
        self.status = RobotStatus.MOVING
        return True

    def wait(self):
        """Make robot wait due to blocked path"""
        if self.status == RobotStatus.MOVING:
            self.status = RobotStatus.WAITING

    def resume(self):
        """Resume movement after waiting"""
        if self.status == RobotStatus.WAITING:
            self.status = RobotStatus.MOVING

    def needs_charging(self) -> bool:
        """Check if robot needs to charge"""
        return self.battery_level <= 20.0

    def is_charging(self) -> bool:
        """Check if robot is currently charging"""
        return self.status == RobotStatus.CHARGING

    def start_charging(self) -> None:
        """Start charging at a charging station"""
        self.status = RobotStatus.CHARGING
        
    def stop_charging(self) -> None:
        """Stop charging and return to idle state"""
        if self.status == RobotStatus.CHARGING:
            self.status = RobotStatus.IDLE
        
    def get_position(self) -> Tuple[int, Optional[int], float]:
        """Get current position information"""
        return (self.current_vertex, self.next_vertex, self.progress)
        
    def is_at_vertex(self, vertex_id: int) -> bool:
        """Check if robot is at specific vertex"""
        return self.current_vertex == vertex_id and self.progress == 0.0
        
    def get_status(self) -> RobotStatus:
        """Get current robot status"""
        return self.status 