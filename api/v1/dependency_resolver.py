#!/usr/bin/env python3
"""
Configuration Dependency Resolver
A reference implementation for resolving configuration dependencies in the 3D printer repository.
"""

import json
import os
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path


class CircularDependencyError(Exception):
    """Raised when a circular dependency is detected."""
    pass


class ConfigurationNotFoundError(Exception):
    """Raised when a configuration file cannot be found."""
    pass


class DependencyResolver:
    """Resolves configuration dependencies and merges inherited configurations."""
    
    def __init__(self, repository_root: str):
        self.repository_root = Path(repository_root)
        self.cache = {}
        
    def get_dependencies(self, slicer: str, config_type: str, config_path: str) -> Dict:
        """
        Get the complete dependency tree for a configuration file.
        
        Args:
            slicer: Slicer type (e.g., 'orcaslicer')
            config_type: Configuration type ('printers', 'filaments', 'processes')
            config_path: Path to the configuration file (e.g., 'pla/generic-pla.json')
            
        Returns:
            Dictionary containing dependency information
        """
        full_path = self.repository_root / "slicers" / slicer / config_type / config_path
        
        if not full_path.exists():
            raise ConfigurationNotFoundError(f"Configuration not found: {full_path}")
            
        target_config = self._load_config(full_path)
        dependencies = []
        dependency_tree = {"name": target_config["config"]["name"], "children": []}
        visited = set()
        resolution_order = []
        
        # Build dependency tree
        self._build_dependency_tree(
            target_config, slicer, config_type, dependencies, 
            dependency_tree, visited, resolution_order
        )
        
        return {
            "target": {
                "name": target_config["config"]["name"],
                "path": f"/slicers/{slicer}/{config_type}/{config_path}",
                "inherits": target_config["config"].get("inherits"),
                "from": target_config["config"].get("from")
            },
            "dependencies": dependencies,
            "dependency_tree": dependency_tree,
            "resolution_order": resolution_order,
            "circular_dependencies": []  # Would be populated if circular deps detected
        }
    
    def resolve_config(self, slicer: str, config_type: str, config_path: str, 
                      include_source_map: bool = False) -> Dict:
        """
        Get a fully resolved configuration with all inheritance applied.
        
        Args:
            slicer: Slicer type
            config_type: Configuration type
            config_path: Path to the configuration file
            include_source_map: Whether to include source information
            
        Returns:
            Dictionary containing resolved configuration
        """
        deps = self.get_dependencies(slicer, config_type, config_path)
        
        # Start with empty config and merge in resolution order
        resolved_config = {}
        source_map = {} if include_source_map else None
        
        # Load and merge all configurations in resolution order
        for config_name in deps["resolution_order"]:
            config_data = self._find_and_load_config(config_name, slicer, config_type)
            if config_data:
                self._merge_config(resolved_config, config_data["config"], 
                                 config_name, source_map)
        
        # Finally merge the target configuration
        target_path = self.repository_root / "slicers" / slicer / config_type / config_path
        target_config = self._load_config(target_path)
        self._merge_config(resolved_config, target_config["config"], 
                          target_config["config"]["name"], source_map)
        
        result = {
            "resolved_config": resolved_config,
            "inheritance_chain": deps["resolution_order"] + [deps["target"]["name"]],
            "validation_errors": []  # Would contain validation results
        }
        
        if include_source_map:
            result["source_map"] = source_map
            
        return result
    
    def _load_config(self, config_path: Path) -> Dict:
        """Load a configuration file."""
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config
        except (FileNotFoundError) as e:
            raise ConfigurationNotFoundError(f"Failed to load config {str(config_path)}") from e
    
    def _build_dependency_tree(self, config: Dict, slicer: str, config_type: str,
                              dependencies: List, tree_node: Dict, visited: Set,
                              resolution_order: List):
        """Recursively build the dependency tree."""
        config_name = config["config"]["name"]
        
        if config_name in visited:
            return  # Already processed
            
        inherits = config["config"].get("inherits")
        if not inherits:
            # Base case: no inheritance
            if config_name not in resolution_order:
                resolution_order.append(config_name)
            return
            
        # Find and load parent configuration
        parent_config = self._find_and_load_config(inherits, slicer, config_type)
        if not parent_config:
            raise ConfigurationNotFoundError(f"Parent configuration not found: {inherits}")
            
        # Add to visited set to detect circular dependencies
        visited.add(config_name)
        
        # Recursively process parent
        parent_tree = {"name": inherits, "children": []}
        tree_node["children"].append(parent_tree)
        
        self._build_dependency_tree(
            parent_config, slicer, config_type, dependencies,
            parent_tree, visited, resolution_order
        )
        
        # Add parent to dependencies list
        dependencies.append({
            "name": inherits,
            "path": self._get_config_path(inherits, slicer, config_type),
            "inherits": parent_config["config"].get("inherits"),
            "from": parent_config["config"].get("from")
        })
        
        # Add current config to resolution order
        if config_name not in resolution_order:
            resolution_order.append(config_name)
    
    def _find_and_load_config(self, config_name: str, slicer: str, 
                             config_type: str) -> Optional[Dict]:
        """Find and load a configuration by name."""
        # Search paths for different inheritance types
        search_paths = [
            f"slicers/{slicer}/base/{config_name}.json",
            f"slicers/{slicer}/{config_type}/base/{config_name}.json",
            f"slicers/{slicer}/system/{config_name}.json",
        ]
        
        for search_path in search_paths:
            full_path = self.repository_root / search_path
            if full_path.exists():
                return self._load_config(full_path)
                
        return None
    
    def _get_config_path(self, config_name: str, slicer: str, config_type: str) -> str:
        """Get the path for a configuration by name."""
        search_paths = [
            f"/slicers/{slicer}/base/{config_name}.json",
            f"/slicers/{slicer}/{config_type}/base/{config_name}.json",
            f"/slicers/{slicer}/system/{config_name}.json",
        ]
        
        for search_path in search_paths:
            full_path = self.repository_root / search_path.lstrip('/')
            if full_path.exists():
                return search_path
                
        return f"/slicers/{slicer}/{config_type}/{config_name}.json"
    
    def _merge_config(self, target: Dict, source: Dict, source_name: str, 
                     source_map: Optional[Dict]):
        """Merge source configuration into target, with child overriding parent."""
        for key, value in source.items():
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                # Recursively merge dictionaries
                self._merge_config(target[key], value, source_name, 
                                 source_map.get(key, {}) if source_map else None)
            else:
                # Override with child value
                target[key] = value
                if source_map is not None:
                    source_map[key] = source_name


def main():
    """Example usage of the dependency resolver."""
    resolver = DependencyResolver(".")
    
    try:
        # Get dependencies for Generic PLA
        deps = resolver.get_dependencies("orcaslicer", "filaments", "pla/generic-pla.json")
        print("Dependencies for Generic PLA:")
        print(json.dumps(deps, indent=2))
        
        print("\n" + "="*50 + "\n")
        
        # Get resolved configuration
        resolved = resolver.resolve_config("orcaslicer", "filaments", "pla/generic-pla.json", 
                                         include_source_map=True)
        print("Resolved Generic PLA configuration:")
        print(json.dumps(resolved, indent=2))
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
