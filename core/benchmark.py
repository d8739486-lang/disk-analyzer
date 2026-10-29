"""CrystalDiskMark-style speed benchmark module with live speed tracking."""
import os
import time
import random
from typing import Callable, Optional, Dict


class DiskBenchmark:
    def __init__(self, target_dir: str, file_size_mb: int = 1024):
        self.target_dir = target_dir
        self.file_size_bytes = file_size_mb * 1024 * 1024
        self.test_file_path = os.path.join(target_dir, f".disc_analyzer_bench_{os.getpid()}.tmp")
        self.is_cancelled = False

    def cancel(self):
        self.is_cancelled = True

    def run_all(self, on_update: Optional[Callable[[str, float], None]] = None,
                on_progress: Optional[Callable[[str, float, float], None]] = None) -> Dict[str, float]:
        """Runs benchmark suite with live progress:
        - SEQ 1M Q8T1 Write
        - SEQ 1M Q8T1 Read
        - RND 4K Q32T1 Write
        - RND 4K Q32T1 Read
        """
        results = {}

        try:
            # 1. Sequential Write
            if self.is_cancelled:
                return results
            speed = self._bench_seq_write(1024 * 1024, on_progress)
            if self.is_cancelled:
                return results
            results["seq_write"] = speed
            if on_update:
                on_update("seq_write", speed)

            # 2. Sequential Read
            if self.is_cancelled:
                return results
            speed = self._bench_seq_read(1024 * 1024, on_progress)
            if self.is_cancelled:
                return results
            results["seq_read"] = speed
            if on_update:
                on_update("seq_read", speed)

            # 3. Random 4K Write
            if self.is_cancelled:
                return results
            rnd_count = min(8192, max(2048, self.file_size_bytes // (64 * 1024)))
            speed = self._bench_rnd_write(4096, count=rnd_count, on_progress=on_progress)
            if self.is_cancelled:
                return results
            results["rnd_write"] = speed
            if on_update:
                on_update("rnd_write", speed)

            # 4. Random 4K Read
            if self.is_cancelled:
                return results
            speed = self._bench_rnd_read(4096, count=rnd_count, on_progress=on_progress)
            if self.is_cancelled:
                return results
            results["rnd_read"] = speed
            if on_update:
                on_update("rnd_read", speed)

        finally:
            self._cleanup()

        return results

    def _bench_seq_write(self, block_size: int, on_progress=None) -> float:
        data = os.urandom(block_size)
        total_blocks = self.file_size_bytes // block_size
        start = time.perf_counter()
        written = 0

        with open(self.test_file_path, "wb") as f:
            for i in range(total_blocks):
                if self.is_cancelled:
                    return 0.0
                f.write(data)
                written += block_size

                # Periodic sync every 32MB to avoid end-of-test buffer cache flush stall
                if (i + 1) % 32 == 0:
                    f.flush()
                    try:
                        os.fdatasync(f.fileno())
                    except OSError:
                        pass

                if on_progress and (i % 8 == 0 or i == total_blocks - 1):
                    elapsed = max(0.001, time.perf_counter() - start)
                    live_speed = (written / (1024 * 1024)) / elapsed
                    pct = (i + 1) / total_blocks
                    on_progress("seq_write", pct, live_speed)

            f.flush()
            try:
                os.fsync(f.fileno())
            except OSError:
                pass

        elapsed = time.perf_counter() - start
        return (self.file_size_bytes / (1024 * 1024)) / elapsed if elapsed > 0 else 0.0

    def _bench_seq_read(self, block_size: int, on_progress=None) -> float:
        if not os.path.exists(self.test_file_path):
            return 0.0
        start = time.perf_counter()
        bytes_read = 0
        total_bytes = self.file_size_bytes

        with open(self.test_file_path, "rb") as f:
            idx = 0
            while True:
                if self.is_cancelled:
                    return 0.0
                buf = f.read(block_size)
                if not buf:
                    break
                bytes_read += len(buf)
                idx += 1
                if on_progress and (idx % 8 == 0):
                    elapsed = max(0.001, time.perf_counter() - start)
                    live_speed = (bytes_read / (1024 * 1024)) / elapsed
                    pct = min(1.0, bytes_read / total_bytes)
                    on_progress("seq_read", pct, live_speed)

        elapsed = time.perf_counter() - start
        return (bytes_read / (1024 * 1024)) / elapsed if elapsed > 0 else 0.0

    def _bench_rnd_write(self, block_size: int, count: int, on_progress=None) -> float:
        if not os.path.exists(self.test_file_path):
            return 0.0
        data = os.urandom(block_size)
        max_blocks = max(1, (self.file_size_bytes // block_size) - 1)
        offsets = [random.randint(0, max_blocks) * block_size for _ in range(count)]

        start = time.perf_counter()
        with open(self.test_file_path, "r+b") as f:
            for i, off in enumerate(offsets):
                if self.is_cancelled:
                    return 0.0
                f.seek(off)
                f.write(data)

                # Periodic sync every 256 writes to prevent huge flush at end
                if (i + 1) % 256 == 0:
                    f.flush()
                    try:
                        os.fdatasync(f.fileno())
                    except OSError:
                        pass

                if on_progress and (i % 64 == 0 or i == count - 1):
                    elapsed = max(0.001, time.perf_counter() - start)
                    live_mb = ((i + 1) * block_size) / (1024 * 1024)
                    live_speed = live_mb / elapsed
                    on_progress("rnd_write", (i + 1) / count, live_speed)

            f.flush()
            try:
                os.fsync(f.fileno())
            except OSError:
                pass

        elapsed = time.perf_counter() - start
        total_mb = (count * block_size) / (1024 * 1024)
        return total_mb / elapsed if elapsed > 0 else 0.0

    def _bench_rnd_read(self, block_size: int, count: int, on_progress=None) -> float:
        if not os.path.exists(self.test_file_path):
            return 0.0
        max_blocks = max(1, (self.file_size_bytes // block_size) - 1)
        offsets = [random.randint(0, max_blocks) * block_size for _ in range(count)]

        start = time.perf_counter()
        bytes_read = 0
        with open(self.test_file_path, "rb") as f:
            for i, off in enumerate(offsets):
                if self.is_cancelled:
                    return 0.0
                f.seek(off)
                buf = f.read(block_size)
                bytes_read += len(buf)
                if on_progress and (i % 64 == 0 or i == count - 1):
                    elapsed = max(0.001, time.perf_counter() - start)
                    live_speed = (bytes_read / (1024 * 1024)) / elapsed
                    on_progress("rnd_read", (i + 1) / count, live_speed)

        elapsed = time.perf_counter() - start
        total_mb = bytes_read / (1024 * 1024)
        return total_mb / elapsed if elapsed > 0 else 0.0

    def _cleanup(self):
        try:
            if os.path.exists(self.test_file_path):
                os.remove(self.test_file_path)
        except OSError:
            pass
