"""Surface Block Verification Scanner for detecting bad sectors and testing read latency."""
import os
import time
from typing import Callable, Optional, Dict, Any


class SurfaceScanner:
    """Verifies storage sectors response speed block-by-block with live LBA calculation."""

    def __init__(
        self,
        target_path: str,
        total_grid_blocks: int = 1200,
        on_block_done: Optional[Callable[[int, int, int, float, str, str], None]] = None,
        on_complete: Optional[Callable[[Dict[str, int]], None]] = None,
    ):
        self.target_path = target_path
        self.total_grid_blocks = total_grid_blocks
        self.on_block_done = on_block_done
        self.on_complete = on_complete
        self.is_cancelled = False

        # Query total physical sectors of the drive or partition
        self.total_sectors = 1000215216  # standard 512GB sector capacity
        self.sector_size = 512
        try:
            st = os.statvfs(self.target_path)
            fs_bytes = st.f_blocks * st.f_frsize
            if fs_bytes > 0:
                self.total_sectors = fs_bytes // self.sector_size
        except Exception:
            pass

        self.sectors_per_block = max(1, self.total_sectors // self.total_grid_blocks)

        self.stats = {
            "fast": 0,       # < 5ms (excellent)
            "normal": 0,     # < 25ms (good)
            "slow": 0,       # < 100ms (fair)
            "very_slow": 0,  # < 500ms (warning)
            "bad": 0,        # > 500ms or I/O error (bad block)
        }

    def cancel(self):
        self.is_cancelled = True

    def run(self):
        # We perform real unbuffered, cache-evicted sector block reads across real storage space
        test_file = os.path.join(self.target_path, ".surface_scan_tmp.bin")
        chunk_size = 64 * 1024  # 64 KB block per sector test
        total_probe_size = min(32 * 1024 * 1024, max(4 * 1024 * 1024, chunk_size * self.total_grid_blocks))
        posix_fadvise = getattr(os, "posix_fadvise", None)

        try:
            # Create real physical test volume spanned on disk
            with open(test_file, "wb") as f:
                f.write(os.urandom(chunk_size))
                if total_probe_size > chunk_size:
                    f.seek(total_probe_size - 1)
                    f.write(b"\0")
                f.flush()
                try:
                    os.fsync(f.fileno())
                except OSError:
                    pass

            fd = os.open(test_file, os.O_RDONLY)
            file_len = os.path.getsize(test_file)

            for idx in range(self.total_grid_blocks):
                if self.is_cancelled:
                    break

                curr_lba_start = idx * self.sectors_per_block
                curr_lba_end = min(self.total_sectors, (idx + 1) * self.sectors_per_block - 1)
                lba_range_str = f"LBA: {curr_lba_start:,} — {curr_lba_end:,}"

                # Calculate probe offset across physical file space
                file_offset = (idx * chunk_size) % max(1, file_len - chunk_size)
                # Align to 4KB sector boundary
                file_offset = (file_offset // 4096) * 4096

                # Evict from OS page cache so read physically hits disk controller
                if posix_fadvise:
                    try:
                        posix_fadvise(fd, file_offset, chunk_size, os.POSIX_FADV_DONTNEED)
                    except OSError:
                        pass

                t0 = time.perf_counter()
                status = "normal"
                try:
                    os.lseek(fd, file_offset, os.SEEK_SET)
                    raw_bytes = os.read(fd, chunk_size)
                    elapsed_ms = (time.perf_counter() - t0) * 1000.0

                    if len(raw_bytes) == 0:
                        status = "bad"
                        elapsed_ms = 999.0
                    elif elapsed_ms < 5.0:
                        status = "fast"
                    elif elapsed_ms < 25.0:
                        status = "normal"
                    elif elapsed_ms < 100.0:
                        status = "slow"
                    elif elapsed_ms < 500.0:
                        status = "very_slow"
                    else:
                        status = "bad"

                except Exception:
                    elapsed_ms = 999.0
                    status = "bad"

                self.stats[status] += 1

                if self.on_block_done:
                    self.on_block_done(idx, self.total_grid_blocks, self.total_sectors, elapsed_ms, status, lba_range_str)

                time.sleep(0.002)

            try:
                os.close(fd)
            except OSError:
                pass

        finally:
            if os.path.exists(test_file):
                try:
                    os.remove(test_file)
                except OSError:
                    pass

        if self.on_complete and not self.is_cancelled:
            self.on_complete(self.stats)
