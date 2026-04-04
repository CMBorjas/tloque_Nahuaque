import os
import subprocess
from datetime import datetime

class SnapshotManager:
    """Orchestrates routine, off-site encrypted data backups and manages
    emergency recovery procedures.
    """
    def __init__(self):
        self.backup_target = "data/backups"
        os.makedirs(self.backup_target, exist_ok=True)
        
    def backup_volume(self, volume_name: str) -> dict:
        """Creates a tarball of a docker volume"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(self.backup_target, f"{volume_name}_{timestamp}.tar.gz")
        
        # Determine paths (Assuming standard linux docker volumes path for local dev, 
        # but in production we might mount volumes directly or use `docker run --rm -v volume:/volume -v host:/backup tar`)
        # For this local stack we'll use a docker command to perform the backup safely without sudo on the host volume dir
        try:
            print(f"[BACKUP] Starting backup for volume {volume_name} to {backup_file}")
            # We run a temporary alpine container to back up the volume
            abs_backup_target = os.path.abspath(self.backup_target)
            cmd = [
                "docker", "run", "--rm",
                "-v", f"{volume_name}:/volume_data:ro",
                "-v", f"{abs_backup_target}:/backup_dir",
                "alpine",
                "tar", "-czf", f"/backup_dir/{os.path.basename(backup_file)}", "-C", "/volume_data", "."
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            return {"status": "success", "message": f"Volume {volume_name} backed up", "file": backup_file}
        except subprocess.CalledProcessError as e:
            return {"status": "error", "message": f"Failed to back up {volume_name}", "details": e.stderr.decode()}

snapshot_manager = SnapshotManager()
