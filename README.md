# CGroup Management Tool

This project provides a simple Python-based utility for managing Linux cgroups using the `CGroupNode` and `CGroupSetting` classes. It allows users to create, delete, read, and write cgroup settings, as well as manage cgroup tasks.

## Features
- Create and delete cgroups hierarchically.
- Read and write cgroup settings.
- Manage tasks by appending PIDs to cgroups.
- Export cgroup information to JSON.
- Check if cgroups are enabled on the system.

## Install
```
pip3 install .
```

## Uninstall
```
pip3 uninstall pycgroup
```

## Prerequisites
- Python 3.6 or higher.
- Linux system with cgroups enabled.

## Usage
You can import the `CGroupNode` and `CGroupRoot` classes in your Python script to interact with the cgroups.

### Example 1: Initialize and Manage CGroups
```python
from your_module_name import CGroupRoot

# Initialize root cgroup node
root = CGroupRoot.root()

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
```

### Example 2: Check if Cgroups are Enabled
```python
from pycgroup import CGroupRoot

if CGroupRoot.cgroup_enabled():
    print("Cgroups are enabled on this system.")
else:
    print("Cgroups are not enabled.")
```

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing
Contributions are welcome! Please submit a pull request or open an issue on the repository.

## Contact
If you have any questions or issues, feel free to reach out at `shaobohuang.1998@gmail.com`.

