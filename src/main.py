import pygame
import argparse
from gui.fleet_gui import FleetGUI
from controllers.fleet_manager import FleetManager

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Robot Fleet Management System')
    parser.add_argument('--graph', type=str, choices=['1', '2', '3'], default='1',
                      help='Select navigation graph (1, 2, or 3)')
    args = parser.parse_args()
    
    pygame.init()
    
    # Initialize GUI and Fleet Manager with selected graph
    gui = FleetGUI(1200, 800)
    graph_file = f"../data/nav_graph{args.graph}.json"
    fleet_manager = FleetManager(gui, graph_file)
    
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