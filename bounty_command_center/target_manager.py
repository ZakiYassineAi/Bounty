import json
import os

class TargetManager:
    """Manages the lifecycle of bug bounty targets."""
    def __init__(self, db_file='targets.json'):
        self.db_file = db_file
        self.targets = self._load_targets()

    def _load_targets(self):
        """Loads targets from the JSON database, creating it if it doesn't exist."""
        if not os.path.exists(self.db_file):
            return []
        # Check for empty file
        if os.path.getsize(self.db_file) == 0:
            return []
        with open(self.db_file, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return [] # Return empty list if file is corrupted

    def _save_targets(self):
        """Saves the current list of targets to the JSON database."""
        with open(self.db_file, 'w') as f:
            json.dump(self.targets, f, indent=4)

    def add_target(self, name, url, scope):
        """
        Adds a new target to the database.
        Returns True on success, False on failure (e.g., duplicate).
        """
        if any(t['name'].lower() == name.lower() for t in self.targets):
            print(f"Error: A target with the name '{name}' already exists.")
            return False

        new_target = {
            'name': name,
            'url': url,
            'scope': scope
        }
        self.targets.append(new_target)
        self._save_targets()
        print(f"Successfully added target: {name}")
        return True

    def remove_target(self, name):
        """
        Removes a target by name from the database.
        Returns True on success, False if not found.
        """
        original_count = len(self.targets)
        self.targets = [t for t in self.targets if t['name'].lower() != name.lower()]

        if len(self.targets) < original_count:
            self._save_targets()
            print(f"Successfully removed target: {name}")
            return True
        else:
            print(f"Error: No target found with the name '{name}'.")
            return False

    def list_targets(self):
        """Displays all current targets in a formatted way."""
        print("\n--- Current Targets ---")
        if not self.targets:
            print("No targets in the database.")
            return

        for i, target in enumerate(self.targets):
            print(f"{i+1}. Name: {target['name']}")
            print(f"   URL: {target['url']}")
            print(f"   Scope: {', '.join(target['scope'])}")
            print("-" * 20)

    def get_target_by_name(self, name):
        """Finds and returns a target by name."""
        for target in self.targets:
            if target['name'].lower() == name.lower():
                return target
        return None
