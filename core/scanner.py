"""Directory disk usage scanner running recursively with virtual FS protection."""
import os
import threading
from typing import Dict, Any, Callable, Optional


class DirectoryScanner:
    def __init__(self, target_path: str, on_progress: Optional[Callable[[int, str], None]] = None):
        self.target_path = os.path.realpath(target_path)
        self.on_progress = on_progress
        self.is_cancelled = False
        self._scanned_files = 0
        try:
            self._target_dev = os.stat(self.target_path).st_dev
        except OSError:
            self._target_dev = None

        # Virtual pseudo-filesystems and endless caches/logs
        self.ignored_dirs = {
            "/proc",
            "/sys",
            "/dev",
            "/run",
            "/snap",
            "/var/lib/docker",
            "/var/run",
        }
        # Folder names to skip deep recursive scan to keep response snappy and prevent freeze
        self.skipped_dir_names = {
            ".git",
            "node_modules",
            "__pycache__",
        }

    def cancel(self):
        self.is_cancelled = True

    def scan(self) -> Dict[str, Any]:
        """Perform scan and return hierarchical tree dictionary."""
        self._scanned_files = 0
        return self._scan_node(self.target_path)

    def _scan_node(self, path: str) -> Dict[str, Any]:
        node = {
            "name": os.path.basename(path) or path,
            "path": path,
            "size": 0,
            "is_dir": os.path.isdir(path),
            "children": [],
            "items_count": 0,
        }

        if self.is_cancelled:
            return node

        # Safety: avoid virtual pseudo-filesystems when scanning root or parent
        norm_path = os.path.normpath(path)
        if norm_path in self.ignored_dirs and self.target_path not in self.ignored_dirs:
            node["name"] = f"{node['name']} [виртуальная ФС]"
            return node

        # Check st_dev boundary (do not traverse other mounted drives/virtual mounts if scanning a partition)
        try:
            st = os.stat(path, follow_symlinks=False)
            if self._target_dev is not None and st.st_dev != self._target_dev and norm_path != self.target_path:
                node["name"] = f"{node['name']} [другой раздел]"
                return node
        except (PermissionError, OSError):
            return node

        if not os.path.isdir(path):
            try:
                # Use st_blocks * 512 for actual disk allocated space if available, or st_size capped
                # Guard against /proc/kcore and sparse RAM mappings
                if st.st_blocks > 0:
                    node["size"] = st.st_blocks * 512
                else:
                    node["size"] = st.st_size
            except OSError:
                node["size"] = 0
            return node

        total_size = 0
        total_items = 0

        try:
            with os.scandir(path) as it:
                for entry in it:
                    if self.is_cancelled:
                        break
                    try:
                        # Skip symlinks entirely to prevent loops and duplicate counts
                        if entry.is_symlink():
                            continue

                        if entry.is_dir(follow_symlinks=False):
                            if entry.name in self.skipped_dir_names:
                                # Rapid quick size calculation without deep leaf recursion
                                dir_sz = 0
                                dir_cnt = 0
                                try:
                                    for root, _, files in os.walk(entry.path):
                                        if self.is_cancelled:
                                            break
                                        for f in files:
                                            dir_cnt += 1
                                            try:
                                                dir_sz += os.path.getsize(os.path.join(root, f))
                                            except OSError:
                                                pass
                                except OSError:
                                    pass
                                self._scanned_files += dir_cnt
                                total_size += dir_sz
                                total_items += dir_cnt + 1
                                node["children"].append({
                                    "name": entry.name,
                                    "path": entry.path,
                                    "size": dir_sz,
                                    "is_dir": True,
                                    "children": [],
                                    "items_count": dir_cnt,
                                })
                            else:
                                child_node = self._scan_node(entry.path)
                                total_size += child_node["size"]
                                total_items += child_node.get("items_count", 0) + 1
                                if child_node["size"] > 0 or child_node.get("children"):
                                    node["children"].append(child_node)
                        else:
                            st_child = entry.stat(follow_symlinks=False)
                            # Physical allocation check
                            if st_child.st_blocks > 0:
                                fsize = min(st_child.st_size, st_child.st_blocks * 512)
                            else:
                                fsize = st_child.st_size

                            total_size += fsize
                            total_items += 1
                            self._scanned_files += 1
                            node["children"].append({
                                "name": entry.name,
                                "path": entry.path,
                                "size": fsize,
                                "is_dir": False,
                                "children": [],
                                "items_count": 1,
                            })

                        if self.on_progress and self._scanned_files % 250 == 0:
                            self.on_progress(self._scanned_files, entry.path)

                    except (PermissionError, OSError):
                        continue
        except (PermissionError, OSError):
            pass

        # Sort children descending by size
        node["children"].sort(key=lambda x: x["size"], reverse=True)
        node["size"] = total_size
        node["items_count"] = total_items
        return node
