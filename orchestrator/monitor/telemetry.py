import psutil

class TelemetryCollector:
    """Gathers real-time resource usage statistics (CPU, RAM, Disks)
    for the dashboard.
    """
    def __init__(self):
        pass
        
    def get_system_metrics(self):
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent
        }

telemetry_collector = TelemetryCollector()
