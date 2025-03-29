import json
import networkx as nx
import numpy as np
import heapq
from typing import Dict, List, Tuple, Optional, Set

class NavGraph:
    def __init__(self, vertices=None, edges=None):
        """Initialize navigation graph"""
        self.graph = nx.Graph()
        self.vertices = {}
        
        if vertices and edges:
            for vertex in vertices:
                self.add_vertex(
                    vertex.id,
                    vertex.coordinates,
                    vertex.name,
                    vertex.is_charger
                )
            for edge in edges:
                self.add_edge(edge[0], edge[1])
    
    @classmethod
    def from_json(cls, graph_file: str) -> 'NavGraph':
        """Create a NavGraph instance from a JSON file"""
        with open(graph_file, 'r') as f:
            data = json.load(f)
            
        # Create vertices
        vertices = []
        for vertex_data in data['vertices']:
            vertex = type('Vertex', (), {
                'id': vertex_data['id'],
                'coordinates': tuple(vertex_data['coordinates']),
                'name': vertex_data['name'],
                'is_charger': vertex_data['is_charger']
            })
            vertices.append(vertex)
            
        # Extract lanes
        edges = data['lanes']
            
        return cls(vertices, edges)
        
    def add_vertex(self, vertex_id: int, coordinates: Tuple[float, float], 
                  name: str, is_charger: bool = False) -> None:
        """Add a vertex to the graph"""
        self.graph.add_node(
            vertex_id,
            pos=coordinates,
            name=name,
            is_charger=is_charger
        )
        self.vertices[vertex_id] = {
            'coordinates': coordinates,
            'name': name,
            'is_charger': is_charger
        }
        
    def add_edge(self, v1: int, v2: int) -> None:
        """Add an edge (lane) between two vertices"""
        # Calculate edge weight as Euclidean distance
        pos1 = self.vertices[v1]['coordinates']
        pos2 = self.vertices[v2]['coordinates']
        weight = np.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
        self.graph.add_edge(v1, v2, weight=weight)
        
    def get_shortest_path(self, start: int, end: int, blocked_edges: Optional[Set[Tuple[int, int]]] = None) -> Optional[List[int]]:
        """Find shortest path between two vertices using A* algorithm"""
        if start == end:
            return [start]
            
        # Initialize data structures for A*
        open_set = {start}  # Vertices to explore
        closed_set = set()  # Vertices already explored
        
        # For node n, g_score[n] is the cost of the cheapest path from start to n currently known
        g_score = {start: 0}
        
        # For node n, f_score[n] = g_score[n] + h(n), where h is the heuristic
        f_score = {start: self._euclidean_distance(start, end)}
        
        # For node n, came_from[n] is the node immediately preceding it on the cheapest path from start
        came_from = {}
        
        while open_set:
            # Get node in open_set having the lowest f_score
            current = min(open_set, key=lambda v: f_score.get(v, float('inf')))
            
            if current == end:
                # We found the goal, reconstruct the path
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                return path[::-1]
                
            open_set.remove(current)
            closed_set.add(current)
            
            # Check all neighbors
            for neighbor in self.get_neighbors(current):
                if neighbor in closed_set:
                    continue
                    
                # Check if this edge is blocked
                if blocked_edges and (min(current, neighbor), max(current, neighbor)) in blocked_edges:
                    continue
                    
                # Calculate tentative g_score
                tentative_g_score = g_score[current] + self.get_edge_weight(current, neighbor)
                
                if neighbor not in open_set:
                    open_set.add(neighbor)
                elif tentative_g_score >= g_score.get(neighbor, float('inf')):
                    continue
                    
                # This path is the best until now. Record it!
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = g_score[neighbor] + self._euclidean_distance(neighbor, end)
        
        return None
        
    def get_alternative_paths(self, start: int, end: int, max_paths: int = 3) -> List[List[int]]:
        """Get multiple alternative paths between two vertices using A*"""
        if start == end:
            return [[start]]
            
        paths = []
        blocked_edges = set()  # Set of edges to avoid
        
        # Get first path
        path = self.get_shortest_path(start, end)
        if not path:
            return []
            
        paths.append(path)
        
        # Try to find alternative paths by blocking edges from previous paths
        while len(paths) < max_paths:
            # Add edges from the last found path to blocked edges
            last_path = paths[-1]
            for i in range(len(last_path) - 1):
                v1, v2 = last_path[i], last_path[i + 1]
                blocked_edges.add((min(v1, v2), max(v1, v2)))
                
            # Try to find a new path avoiding blocked edges
            new_path = self.get_shortest_path(start, end, blocked_edges)
            if not new_path:
                break
                
            paths.append(new_path)
            
        return paths
        
    def _euclidean_distance(self, u: int, v: int) -> float:
        """Calculate Euclidean distance between two vertices (heuristic function)"""
        pos_u = self.vertices[u]['coordinates']
        pos_v = self.vertices[v]['coordinates']
        return np.sqrt((pos_u[0] - pos_v[0])**2 + (pos_u[1] - pos_v[1])**2)
        
    def get_neighbors(self, vertex_id: int) -> List[int]:
        """Get list of neighboring vertices"""
        return list(self.graph.neighbors(vertex_id))
        
    def get_charging_stations(self) -> List[int]:
        """Get list of charging station vertex IDs"""
        return [vid for vid, data in self.vertices.items() if data['is_charger']]
        
    def get_vertex_info(self, vertex_id: int) -> Optional[Dict]:
        """Get information about a specific vertex"""
        return self.vertices.get(vertex_id)
        
    def get_edge_weight(self, v1: int, v2: int) -> Optional[float]:
        """Get the weight (distance) of an edge between two vertices"""
        try:
            return self.graph[v1][v2]['weight']
        except KeyError:
            return None 