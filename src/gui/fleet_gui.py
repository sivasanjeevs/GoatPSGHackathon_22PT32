import pygame
import pygame.gfxdraw
from typing import Dict, List, Tuple, Optional
import math
from models.robot import Robot, RobotStatus
from models.nav_graph import NavGraph
import time

class FleetGUI:
    # Colors
    BACKGROUND = (40, 44, 52)  # Dark theme background
    VERTEX_COLOR = (97, 175, 239)  # Blue for vertices
    EDGE_COLOR = (152, 195, 121)  # Green for edges
    TEXT_COLOR = (229, 229, 229)  # Light gray for text
    HEADING_COLOR = (86, 182, 194)  # Cyan for headings
    SUBHEADING_COLOR = (171, 178, 191)  # Light blue for subheadings
    CONTENT_COLOR = (229, 229, 229)  # Light gray for content
    CHARGER_COLOR = (255, 215, 0)  # Gold for charging stations
    CHARGER_GLOW = (255, 215, 0, 100)  # Semi-transparent gold for glow effect
    HIGHLIGHT_COLOR = (255, 0, 0)  # Red for selected robot
    PATH_PREVIEW_COLOR = (86, 182, 194)  # Cyan for path preview
    BLOCKED_COLOR = (224, 108, 117)  # Red for blocked paths
    PANEL_BACKGROUND = (30, 33, 39)  # Darker background for panel
    PANEL_BORDER = (50, 54, 61)  # Panel border color
    
    def __init__(self, width: int, height: int):
        """Initialize the GUI"""
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Fleet Management System")
        
        # Navigation graph
        self.nav_graph = None
        
        # Status panel parameters
        self.panel_width = 300
        self.graph_width = width - self.panel_width
        
        # Visual parameters
        self.vertex_radius = 20
        self.robot_radius = 15
        self.edge_width = 3
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        
        # Fonts - using sans-serif
        try:
            self.font = pygame.font.SysFont('sans-serif', 24)
            self.small_font = pygame.font.SysFont('sans-serif', 20)
        except:
            # Fallback to default font if sans-serif is not available
            self.font = pygame.font.Font(None, 24)
            self.small_font = pygame.font.Font(None, 20)
        
        # Create buffer surface for double buffering
        self.buffer = pygame.Surface((width, height))
        
        # Initialize time for animations
        self.start_time = time.time()
        
        # Path preview and notifications
        self.preview_path = []
        self.blocked_paths = set()
        self.selected_robot_id = None
        self.notifications = []
        
        # Panel spacing constants
        self.PANEL_PADDING = 20
        self.SECTION_SPACING = 40  # Increased from 30
        self.ITEM_SPACING = 25    # Increased from 15
        self.CONTENT_INDENT = 40  # New constant for content indentation
        
    def set_nav_graph(self, nav_graph):
        """Set the navigation graph and update bounds"""
        self.nav_graph = nav_graph
        self.update_graph_bounds()
        
    def update_graph_bounds(self):
        """Update scale and offset to center the graph"""
        if not self.nav_graph or not self.nav_graph.vertices:
            return
            
        # Find bounds
        min_x = float('inf')
        max_x = float('-inf')
        min_y = float('inf')
        max_y = float('-inf')
        
        for vertex in self.nav_graph.vertices.values():
            x, y = vertex['coordinates']
            min_x = min(min_x, x)
            max_x = max(max_x, x)
            min_y = min(min_y, y)
            max_y = max(max_y, y)
            
        # Calculate graph dimensions
        graph_width = max_x - min_x
        graph_height = max_y - min_y
        
        # Add padding (10% on each side)
        padding = 0.2
        graph_width *= (1 + padding)
        graph_height *= (1 + padding)
        
        # Calculate scale to fit the graph in the window
        width_scale = self.graph_width / graph_width if graph_width > 0 else 1.0
        height_scale = self.height / graph_height if graph_height > 0 else 1.0
        self.scale = min(width_scale, height_scale)
        
        # Calculate center point of the graph
        graph_center_x = (min_x + max_x) / 2
        graph_center_y = (min_y + max_y) / 2
        
        # Update offsets to center the graph
        self.offset_x = self.graph_width / 2 - graph_center_x * self.scale
        self.offset_y = self.height / 2 + graph_center_y * self.scale
        
        # Colors
        self.BACKGROUND_COLOR = (40, 40, 40)
        self.VERTEX_COLOR = (100, 100, 100)
        self.EDGE_COLOR = (80, 80, 80)
        self.BLOCKED_COLOR = (255, 0, 0)
        self.ROBOT_COLOR = (0, 255, 0)
        self.HIGHLIGHT_COLOR = (255, 0, 0)
        self.CHARGER_COLOR = (255, 165, 0)
        self.TEXT_COLOR = (255, 255, 255)
        self.STATUS_PANEL_COLOR = (30, 30, 30)
        self.STATUS_PANEL_BORDER = (60, 60, 60)
        self.NOTIFICATION_COLOR = (255, 255, 0)
        self.ERROR_COLOR = (255, 0, 0)
        self.SUCCESS_COLOR = (0, 255, 0)
        
    def _world_to_screen(self, coords: Tuple[float, float]) -> Tuple[int, int]:
        """Convert world coordinates to screen coordinates"""
        # Scale coordinates and center in window
        x = int(coords[0] * self.scale + self.offset_x)
        y = int(coords[1] * -self.scale + self.offset_y)  # Flip y-axis and scale
        return (x, y)
        
    def draw_vertex(self, pos: Tuple[float, float], name: str, is_charger: bool):
        """Draw a vertex with name and charging station indicator"""
        screen_pos = self._world_to_screen(pos)
        
        # Draw vertex circle
        color = self.CHARGER_COLOR if is_charger else self.VERTEX_COLOR
        
        # For charging stations, draw a pulsing glow effect
        if is_charger:
            glow_radius = self.vertex_radius + 5
            glow_alpha = abs(math.sin(pygame.time.get_ticks() * 0.003)) * 100 + 50
            glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.gfxdraw.filled_circle(glow_surface, glow_radius, glow_radius, 
                                       glow_radius, (*self.CHARGER_COLOR[:3], glow_alpha))
            self.screen.blit(glow_surface, 
                           (screen_pos[0] - glow_radius, screen_pos[1] - glow_radius))
        
        # Draw vertex circle
        pygame.gfxdraw.aacircle(self.screen, screen_pos[0], screen_pos[1],
                               self.vertex_radius, color)
        pygame.gfxdraw.filled_circle(self.screen, screen_pos[0], screen_pos[1],
                                   self.vertex_radius, color)
                                   
        # Draw vertex name
        text = self.font.render(name, True, self.TEXT_COLOR)
        text_rect = text.get_rect(center=(screen_pos[0], screen_pos[1] - self.vertex_radius - 15))
        self.screen.blit(text, text_rect)
        
        # For charging stations, add a lightning bolt symbol
        if is_charger:
            bolt_text = self.font.render("⚡", True, self.TEXT_COLOR)
            bolt_rect = bolt_text.get_rect(center=(screen_pos[0], screen_pos[1]))
            self.screen.blit(bolt_text, bolt_rect)
            
    def draw_edge(self, start_pos: Tuple[float, float], end_pos: Tuple[float, float], 
                is_blocked: bool = False):
        """Draw an edge between two vertices"""
        start = self._world_to_screen(start_pos)
        end = self._world_to_screen(end_pos)
        color = self.BLOCKED_COLOR if is_blocked else self.EDGE_COLOR
        pygame.draw.line(self.screen, color, start, end, self.edge_width)
        
    def draw_robot(self, robot: Robot, start_pos: Tuple[float, float], 
                  end_pos: Optional[Tuple[float, float]] = None):
        """Draw a robot with status indication"""
        if end_pos and robot.status == RobotStatus.MOVING:
            # Interpolate position
            progress = robot.progress
            x = start_pos[0] + (end_pos[0] - start_pos[0]) * progress
            y = start_pos[1] + (end_pos[1] - start_pos[1]) * progress
            pos = (x, y)
        else:
            pos = start_pos

        screen_pos = self._world_to_screen(pos)
        
        # Draw selection highlight if this robot is selected
        if robot.id == self.selected_robot_id:
            # Draw larger highlight circle
            pygame.gfxdraw.aacircle(self.screen, screen_pos[0], screen_pos[1],
                                   self.robot_radius + 8, self.HIGHLIGHT_COLOR)
            pygame.gfxdraw.filled_circle(self.screen, screen_pos[0], screen_pos[1],
                                       self.robot_radius + 8, self.HIGHLIGHT_COLOR)
            # Draw pulsing inner highlight
            pulse = abs(math.sin(pygame.time.get_ticks() * 0.005)) * 0.7 + 0.3  # Pulsing effect
            highlight_color = tuple(int(c * pulse) for c in self.HIGHLIGHT_COLOR)
            pygame.gfxdraw.aacircle(self.screen, screen_pos[0], screen_pos[1],
                                   self.robot_radius + 4, highlight_color)
            pygame.gfxdraw.filled_circle(self.screen, screen_pos[0], screen_pos[1],
                                       self.robot_radius + 4, highlight_color)
        
        # Draw status indicator
        status_color = {
            RobotStatus.IDLE: (100, 100, 100),  # Gray
            RobotStatus.MOVING: (0, 255, 0),    # Green
            RobotStatus.WAITING: (255, 165, 0),  # Orange
            RobotStatus.CHARGING: (255, 255, 0), # Yellow
            RobotStatus.TASK_COMPLETE: (0, 255, 255), # Cyan
        }.get(robot.status, robot.color)
        
        # Draw robot outline for status
        pygame.gfxdraw.aacircle(self.screen, screen_pos[0], screen_pos[1],
                                self.robot_radius + 3, status_color)
        pygame.gfxdraw.filled_circle(self.screen, screen_pos[0], screen_pos[1],
                                    self.robot_radius + 3, status_color)
        
        # Draw robot body
        pygame.gfxdraw.aacircle(self.screen, screen_pos[0], screen_pos[1],
                                self.robot_radius, robot.color)
        pygame.gfxdraw.filled_circle(self.screen, screen_pos[0], screen_pos[1],
                                    self.robot_radius, robot.color)
        
        # Draw robot ID
        text = self.font.render(str(robot.id), True, self.TEXT_COLOR)
        text_rect = text.get_rect(center=screen_pos)
        self.screen.blit(text, text_rect)
        
        # Draw battery indicator if low
        if robot.battery_level < 30.0:
            battery_width = 20
            battery_height = 4
            battery_x = screen_pos[0] - battery_width // 2
            battery_y = screen_pos[1] + self.robot_radius + 5
            
            # Draw battery outline
            pygame.draw.rect(self.screen, self.TEXT_COLOR,
                           (battery_x, battery_y, battery_width, battery_height), 1)
            
            # Draw battery level
            level_width = int(battery_width * (robot.battery_level / 100.0))
            if level_width > 0:
                color = (0, 255, 0) if robot.battery_level > 20 else (255, 0, 0)
                pygame.draw.rect(self.screen, color,
                               (battery_x + 1, battery_y + 1, level_width - 2, battery_height - 2))
        
    def draw_status_panel(self, robots: List[Robot]):
        """Draw status panel showing robot information"""
        # Draw panel background with gradient effect
        panel_rect = pygame.Rect(self.graph_width, 0, self.panel_width, self.height)
        pygame.draw.rect(self.screen, self.PANEL_BACKGROUND, panel_rect)
        pygame.draw.line(self.screen, self.PANEL_BORDER, 
                        (self.graph_width, 0), (self.graph_width, self.height), 2)
        
        # Current Y position for drawing
        y = self.PANEL_PADDING + 10
        
        # Draw main title with modern style
        title = self.font.render("Robot Status", True, self.HEADING_COLOR)
        title_rect = title.get_rect(midtop=(self.graph_width + self.panel_width // 2, y))
        self.screen.blit(title, title_rect)
        
        y += self.SECTION_SPACING + 10
        
        # Draw charging stations section
        section_title = self.font.render("Charging Stations", True, self.HEADING_COLOR)
        self.screen.blit(section_title, (self.graph_width + self.PANEL_PADDING, y))
        
        y += self.ITEM_SPACING
        # Draw charging station example
        pygame.gfxdraw.filled_circle(self.screen, 
                                   self.graph_width + self.PANEL_PADDING + 10, 
                                   y + 8, 8, self.CHARGER_COLOR)
        pygame.gfxdraw.aacircle(self.screen, 
                               self.graph_width + self.PANEL_PADDING + 10, 
                               y + 8, 8, self.CHARGER_COLOR)
        legend_text = self.small_font.render("Vertex E, J", True, self.CONTENT_COLOR)
        self.screen.blit(legend_text, (self.graph_width + self.CONTENT_INDENT, y))
        
        y += self.SECTION_SPACING
        
        # Draw separator line
        pygame.draw.line(self.screen, self.PANEL_BORDER,
                        (self.graph_width + self.PANEL_PADDING, y),
                        (self.width - self.PANEL_PADDING, y), 1)
        
        y += self.SECTION_SPACING
        
        # Draw waiting section
        waiting_title = self.font.render("Waiting Robots", True, self.HEADING_COLOR)
        self.screen.blit(waiting_title, (self.graph_width + self.PANEL_PADDING, y))
        
        y += self.ITEM_SPACING
        
        # Find and display waiting robots
        waiting_robots = [robot for robot in robots if robot.status == RobotStatus.WAITING]
        if waiting_robots:
            for robot in waiting_robots:
                waiting_text = f"Robot {robot.id}: waiting"
                text = self.small_font.render(waiting_text, True, self.CONTENT_COLOR)
                self.screen.blit(text, (self.graph_width + self.CONTENT_INDENT, y))
                y += self.ITEM_SPACING
        else:
            text = self.small_font.render("No robots waiting", True, self.CONTENT_COLOR)
            self.screen.blit(text, (self.graph_width + self.CONTENT_INDENT, y))
            y += self.ITEM_SPACING
        
        y += self.SECTION_SPACING
        
        # Draw separator line
        pygame.draw.line(self.screen, self.PANEL_BORDER,
                        (self.graph_width + self.PANEL_PADDING, y),
                        (self.width - self.PANEL_PADDING, y), 1)
        
        y += self.SECTION_SPACING
        
        # Draw robots section
        robots_title = self.font.render("Robots", True, self.HEADING_COLOR)
        self.screen.blit(robots_title, (self.graph_width + self.PANEL_PADDING, y))
        
        y += self.ITEM_SPACING + 10
        
        # Draw robot status information with increased spacing
        for robot in robots:
            # Draw robot status with color-coded indicators
            status_color = {
                RobotStatus.IDLE: (100, 100, 100),
                RobotStatus.MOVING: (0, 255, 0),
                RobotStatus.WAITING: (255, 165, 0),
                RobotStatus.CHARGING: (255, 255, 0),
                RobotStatus.TASK_COMPLETE: (0, 255, 255),
                RobotStatus.BATTERY_DEAD: (255, 0, 0)
            }.get(robot.status, robot.color)
            
            # Draw status indicator
            pygame.gfxdraw.filled_circle(self.screen, 
                                       self.graph_width + self.PANEL_PADDING + 10, 
                                       y + 8, 6, status_color)
            pygame.gfxdraw.aacircle(self.screen, 
                                   self.graph_width + self.PANEL_PADDING + 10, 
                                   y + 8, 6, status_color)
            
            # Draw robot information
            info_text = f"Robot {robot.id}: {robot.status.value}"
            text = self.small_font.render(info_text, True, self.SUBHEADING_COLOR)
            self.screen.blit(text, (self.graph_width + self.CONTENT_INDENT, y))
            
            # Draw battery level with more spacing
            y += self.ITEM_SPACING - 5
            battery_text = f"Battery: {robot.battery_level:.1f}%"
            text = self.small_font.render(battery_text, True, self.CONTENT_COLOR)
            self.screen.blit(text, (self.graph_width + self.CONTENT_INDENT, y))
            
            y += self.ITEM_SPACING + 10  # Added extra spacing between robots
        
    def show_notification(self, message: str):
        """Show a notification message in the status panel"""
        # Don't show waiting notifications at the top
        if message.startswith("Waiting:"):
            return
        notification = self.font.render(message, True, self.TEXT_COLOR)
        rect = notification.get_rect(topleft=(self.graph_width + 20, 85))
        self.screen.blit(notification, rect)

    def clear(self):
        """Clear the screen"""
        self.screen.fill(self.BACKGROUND)
        
    def update(self):
        """Update the display"""
        pygame.display.flip()

    def handle_events(self) -> List[Dict]:
        """Handle PyGame events and return relevant actions"""
        actions = []
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                actions.append({"type": "quit"})
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    actions.append({
                        "type": "click",
                        "pos": event.pos
                    })
                    
        return actions
        
    def get_clicked_vertex(self, screen_pos: Tuple[int, int], 
                          vertices: Dict[int, Dict]) -> Optional[int]:
        """Get vertex ID if click is within vertex radius"""
        for vertex_id, info in vertices.items():
            world_pos = info['coordinates']
            pos = self._world_to_screen(world_pos)
            dx = screen_pos[0] - pos[0]
            dy = screen_pos[1] - pos[1]
            if (dx * dx + dy * dy) <= (self.vertex_radius * self.vertex_radius):
                return vertex_id
        return None

    def set_path_preview(self, path: List[Tuple[float, float]]):
        """Set path to preview when selecting destination"""
        self.preview_path = path
        
    def clear_path_preview(self):
        """Clear the path preview"""
        self.preview_path = []
        
    def set_blocked_path(self, start: Tuple[float, float], end: Tuple[float, float]):
        """Mark a path segment as blocked"""
        self.blocked_paths.add((start, end))
        
    def clear_blocked_paths(self):
        """Clear all blocked path markers"""
        self.blocked_paths.clear()
        
    def draw_path_preview(self):
        """Draw the preview path if one is set"""
        if not self.preview_path:
            return
            
        # Draw path segments
        for i in range(len(self.preview_path) - 1):
            start = self._world_to_screen(self.preview_path[i])
            end = self._world_to_screen(self.preview_path[i + 1])
            
            # Draw dashed line
            dash_length = 10
            dash_gap = 5
            dx = end[0] - start[0]
            dy = end[1] - start[1]
            length = math.sqrt(dx * dx + dy * dy)
            
            if length < 1:  # Avoid division by zero
                continue
                
            dx /= length
            dy /= length
            
            pos = list(start)
            dash_pos = 0
            drawing = True
            
            while dash_pos < length:
                next_pos = [
                    pos[0] + dx * (dash_length if drawing else dash_gap),
                    pos[1] + dy * (dash_length if drawing else dash_gap)
                ]
                
                if drawing:
                    pygame.draw.line(self.screen, self.PATH_PREVIEW_COLOR,
                                   pos, next_pos, 2)
                    
                pos = next_pos
                dash_pos += dash_length if drawing else dash_gap
                drawing = not drawing
                
    def draw_blocked_paths(self):
        """Draw indicators for blocked paths"""
        for start, end in self.blocked_paths:
            start_screen = self._world_to_screen(start)
            end_screen = self._world_to_screen(end)
            
            # Draw red X at midpoint
            mid_x = (start_screen[0] + end_screen[0]) // 2
            mid_y = (start_screen[1] + end_screen[1]) // 2
            size = 10
            
            pygame.draw.line(self.screen, self.BLOCKED_COLOR,
                           (mid_x - size, mid_y - size),
                           (mid_x + size, mid_y + size), 3)
            pygame.draw.line(self.screen, self.BLOCKED_COLOR,
                           (mid_x - size, mid_y + size),
                           (mid_x + size, mid_y - size), 3)
                           
    def draw(self, vertices: Dict[int, Dict], robots: List[Robot], selected_robot_id: Optional[int] = None):
        """Draw the complete scene"""
        self.selected_robot_id = selected_robot_id
        self.clear()
        
        # Draw edges
        for v1 in vertices:
            pos1 = vertices[v1]['coordinates']
            for v2 in vertices[v1].get('neighbors', []):
                if v2 > v1:  # Draw each edge only once
                    pos2 = vertices[v2]['coordinates']
                    self.draw_edge(pos1, pos2)
                    
        # Draw vertices
        for vertex_id, info in vertices.items():
            self.draw_vertex(
                info['coordinates'],
                info['name'],
                info.get('is_charger', False)
            )
            
        # Draw robots
        for robot in robots:
            start_pos = vertices[robot.current_vertex]['coordinates']
            end_pos = None
            if robot.next_vertex is not None:
                end_pos = vertices[robot.next_vertex]['coordinates']
            self.draw_robot(robot, start_pos, end_pos)
            
        # Draw status panel
        self.draw_status_panel(robots)
        
        # Draw path preview and blocked paths
        self.draw_path_preview()
        self.draw_blocked_paths()
        
        self.update() 