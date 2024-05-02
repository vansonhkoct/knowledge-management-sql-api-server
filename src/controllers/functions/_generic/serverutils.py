import psutil

def get_memory_usage():
    memory = psutil.virtual_memory()
    total_memory = round(memory.total / (1024 ** 3), 2)  # Convert to GB
    used_memory = round(memory.used / (1024 ** 3), 2)
    memory_percentage = memory.percent

    return {
        "total_memory": total_memory,
        "used_memory": used_memory,
        "memory_percentage": memory_percentage
    }

def get_cpu_usage():
    cpu_percentage = psutil.cpu_percent()

    return {
        "cpu_percentage": cpu_percentage
    }

def get_disk_usage():
    disk = psutil.disk_usage('/')
    total_disk = round(disk.total / (1024 ** 3), 2)  # Convert to GB
    used_disk = round(disk.used / (1024 ** 3), 2)
    disk_percentage = disk.percent

    return {
        "total_disk": total_disk,
        "used_disk": used_disk,
        "disk_percentage": disk_percentage
    }

# Usage example
if __name__ == '__main__':

  memory_usage = get_memory_usage()
  cpu_usage = get_cpu_usage()
  disk_usage = get_disk_usage()

  print("Memory Usage:", memory_usage)
  print("CPU Usage:", cpu_usage)
  print("Disk Usage:", disk_usage)
