#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# MIT License
# 
# Copyright (c) 2025 Your Name
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import json

class CGroupSetting(object):
    def __init__(self, name, path):
        self.name = name
        self.path = path

        if not os.path.exists(self.path):
            print("Warning: cgroup setting file not found: " + self.path)

    def get(self):
        if os.access(self.path, os.R_OK):
            try:
                with open(self.path, "r") as f:
                    value = f.read()
                return value
            except (PermissionError, OSError) as e:
                print(f"Failed to read cgroup setting: {e}")
                return None
        else:
            print("Warning: cgroup setting not readable: " + self.path)
        
    def set(self, value):
        if os.access(self.path, os.W_OK):
            with open(self.path, "w") as f:
                f.write(value)
        else:
            print("Warning: cgroup setting not writable: " + self.path)

class CGroupNode(object):
    def __init__(self, parent=None, absname="", path=""):
        self.absname = os.path.normpath(absname)
        self.name = os.path.basename(self.absname)
        self.path = os.path.normpath(path) if path else ""
        self.parent = parent
        self.children = {}
        self.settings = {}

        if self.path:
            for entry in os.listdir(self.path):
                sub_path = os.path.join(self.path, entry)
                sub_absname = os.path.join(self.absname, entry)
                
                if os.path.islink(sub_path):
                    continue
                if os.path.isdir(sub_path):
                    self.children[sub_absname] = CGroupNode(self, sub_absname, sub_path)
                if os.path.isfile(sub_path):
                    self.settings[entry] = CGroupSetting(entry, sub_path)

        a = 0 
    def _formmat_self_as_dict(self):
        return {
            "name": self.name,
            "path": self.path,
            "children": [child._formmat_self_as_dict() for child in self.children.values()],
            "settings": {name: setting.get() for name, setting in self.settings.items()}
        }
    
    def export_to_json(self, filename: str):
        """ Export cgroup settings to a JSON file """
        cgroup_data = self._formmat_self_as_dict()
        with open(filename, 'w') as json_file:
            json.dump(cgroup_data, json_file, indent=4)


    def get_tasks(self):
        """ Return a list of tasks in this cgroup

        Either the tasks or cgroup.procs setting must be present in the cgroup,
        otherwise a warning message is printed and the empty list is returned.
        """

        if self.settings.get("tasks", None):
            with open(self.settings["tasks"].path, "r") as f:
                return f.read().split()
        elif self.settings.get("cgroup.procs", None):
            with open(self.settings["cgroup.procs"].path, "r") as f:
                return f.read().split()
        else:
            print("Warning: tasks or cgroup.procs not found in cgroup")

    def append_task(self, pid: int) -> bool:
        """
        Append a task to the cgroup by writing the given process ID (pid) to the
        'tasks' or 'cgroup.procs' file of the cgroup settings.

        Args:
            pid (int): The process ID to be appended to the cgroup.

        Returns:
            bool: True if the task was successfully appended, False otherwise.

        If the 'tasks' file is available in the cgroup settings, the pid is written
        to it. If the 'tasks' file is not available, the 'cgroup.procs' file is
        used instead. If neither file is available, a warning is printed. If there
        is an error while writing, such as a PermissionError or OSError, an error
        message is printed and the function returns False.
        """

        if self.settings.get("tasks", None):
            try:
                with open(self.settings["tasks"].path, "w") as f:
                    f.write(str(pid))
                    return True
            except (PermissionError, OSError) as e:
                print(f"Failed to append task {pid} to {self.absname}: {e}")
                return False
        elif self.settings.get("cgroup.procs", None):
            try:
                with open(self.settings["cgroup.procs"].path, "w") as f:
                    f.write(str(pid))
                    return True
            except (PermissionError, OSError) as e:
                print(f"Failed to append task {pid} to {self.absname}: {e}")
                return False
        else:
            print("Warning: tasks or cgroup.procs not found in cgroup")

    def create_cgroup(self, name: str):
        """
        Create a cgroup and its hierarchy based on the given name.

        This function takes a cgroup name with a hierarchical path, creates
        the necessary directories along the path if they don't exist, and 
        updates the cgroup's children mapping. It returns the final cgroup 
        node created or found in the hierarchy. If the current node's path 
        is None, it prints a warning and returns None.

        Args:
            name (str): The hierarchical name of the cgroup to create, e.g., "a/b".

        Returns:
            CGroupNode: The final CGroupNode created or found in the hierarchy.
        """

        if not self.path:
            print("Warning: CGroupNode path is None")
            return None

        parts = name.strip("/").split("/")
        current = self

        for part in parts:
            sub_absname = os.path.join(current.absname, part)
            sub_path = os.path.join(current.path, part)

            if sub_absname not in current.children:
                os.makedirs(sub_path, exist_ok=True)
                current.children[sub_absname] = CGroupNode(current, sub_absname, sub_path)

            current = current.children[sub_absname]

        return current

    def delete_cgroup(self, name: str) -> bool:
        """
        Delete the cgroup with the given name from the hierarchy.

        This function takes a hierarchical cgroup name, finds the cgroup node
        in the hierarchy, removes it from its parent's children mapping, and
        then calls the node's delete_self to recursively delete the cgroup.

        Args:
            name (str): The hierarchical name of the cgroup to delete.

        Returns:
            bool: True if the cgroup is found and deleted, False otherwise.
        """
        target = self.get_cgroup_by_name(name)
        if target:
            parent = target.parent
            if target.absname in parent.children:
                del parent.children[target.absname]
            return target.delete_self()
        return False
    
    def delete_self(self) -> bool:
        """
        Recursively delete the cgroup and all its children from the hierarchy.

        This function iterates over the cgroup's children and calls their
        delete_self, then tries to remove the cgroup's directory. If removing
        the directory fails, it prints an error message and returns False.

        Returns:
            bool: True if the cgroup and its children are deleted, False otherwise.
        """

        for child in list(self.children.values()):
            child.delete_self()

        try:
            os.rmdir(self.path)
        except OSError as e:
            print(f"Failed to delete {self.path}: {e}")
            return False

        return True

    def get_cgroup_by_path(self, path: str):
        """
        Find the cgroup with the given path from the hierarchy.

        This function takes an absolute path of a cgroup, looks up the cgroup
        in the hierarchy, and returns the cgroup node if found, or None
        otherwise.

        Args:
            path (str): The absolute path of the cgroup to find.

        Returns:
            CGroupNode or None: The cgroup node with the given path if found,
            None otherwise.
        """
        return next((node for node in self.children.values() if node.path == path), None)

    def get_cgroup_by_name(self, name: str):
        """
        Find the cgroup with the given name from the hierarchy.

        This function takes the name of a cgroup, looks up the cgroup in the
        hierarchy, and returns the cgroup node if found, or None otherwise.

        Args:
            name (str): The name of the cgroup to find.

        Returns:
            CGroupNode or None: The cgroup node with the given name if found,
            None otherwise.
        """

        name = os.path.normpath(name).lstrip("/")

        if name == self.absname.lstrip("/"):
            return self
        
        parts = name.strip("/").split("/")
        current = self

        for part in parts:
            sub_absname = os.path.join(current.absname, part)
            if sub_absname in current.children:
                current = current.children[sub_absname]
            else:
                return None

        return current
    
    def get_setting(self, name: str):
        return self.settings.get(name, None)
    
    def set_setting(self, name: str, value: str):
        setting = self.settings.get(name, None)
        if setting:
            setting.set(value)
        else:
            print(f"Warning: setting {name} not found in cgroup {self.absname}")
    
    def __str__(self):
        return f"{self.name}, {self.path}, {self.children.keys()}, {self.settings.keys()}"
    
    def __repr__(self):
        return self.__str__()

class CGroupRoot:
    root_path = "/sys/fs/cgroup"
    version = ""

    @staticmethod
    def root() -> CGroupNode:
        return CGroupNode(None, "/", CGroupRoot.root_path)
    
    @staticmethod
    def cgroup_enabled() -> bool:
        """
        Check if cgroups are enabled on the system.

        This method verifies the presence of cgroups by checking the existence
        of the '/sys/fs/cgroup' directory and its type. Additionally, it reads
        the '/proc/mounts' file to detect if cgroups are mounted.

        Returns:
            bool: True if cgroups are enabled, False otherwise.
        """

        if os.path.exists("/sys/fs/cgroup") and os.path.isdir("/sys/fs/cgroup"):
            return True
        with open("/proc/mounts", "r") as f:
            if "cgroup" in f.read():
                return True
        return False
    
if __name__ == "__main__":
    root = CGroupRoot.root()

    # Get tasks from root node
    root_tasks = root.get_tasks()

    # Find a cgroup from root node
    cpu_cgroup = root.get_cgroup_by_name('cpu,cpuacct') # '/cpu,cpuacct' also work

    # Create a cgroup hierarchy
    cg1 = cpu_cgroup.create_cgroup("group1/subgroup1")

    # Append a task to a cgroup
    cg1.append_task(1234)

    # Export cgroup settings to JSON
    cg1.export_to_json("cg1.json")

    # Delete cgroup
    cpu_cgroup.delete_cgroup("group1/subgroup1")

    cpu_cgroup.delete_cgroup("group1")
    #print(tree)
