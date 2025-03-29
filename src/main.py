import pygame
from gui.fleet_gui import FleetGUI
from controllers.fleet_manager import FleetManager

def main():
    pygame.init()
    
    # Initialize GUI and Fleet Manager
    gui = FleetGUI(1200, 800)
    fleet_manager = FleetManager(gui, "nav_graph.json")
    
    # Initialize time tracking
    last_time = pygame.time.get_ticks()
    
    # Main game loop
    while fleet_manager.running:
        # Calculate delta time in seconds
        current_time = pygame.time.get_ticks()
        delta_time = (current_time - last_time) / 1000.0  # Convert to seconds
        last_time = current_time
        
        fleet_manager.handle_events()
        fleet_manager.update(delta_time)
        fleet_manager.draw()
        pygame.display.flip()
        fleet_manager.clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main() 