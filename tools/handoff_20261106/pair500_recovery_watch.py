"""Recover a failed search controller with unchanged worker settings and a bounded retry count."""
import datetime
import fcntl
import os
import subprocess
import time
from pathlib import Path

from pair500_generate import load, write

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/audit/pair500"


def utc():
    return datetime.datetime.now(datetime.timezone.utc)


def alive(pid):
    try:
        path = Path("/proc") / str(pid)
        return path.stat().st_uid == os.getuid() and b"pair500_full_queue.py" in (path / "cmdline").read_bytes()
    except FileNotFoundError:
        return False


def snapshot(attempt, side):
    code = """from pathlib import Path
import hashlib,json
p=Path('/home/dell/Def/results/audit/pair500/generations.private')
print(json.dumps({q.stem:hashlib.sha256(q.read_bytes()).hexdigest() for q in sorted(p.glob('*.json'))}))
"""
    rows = __import__("json").loads(subprocess.check_output(
        ["ssh", "-o", "ConnectTimeout=10", "node01", "python3", "-"],
        input=code, text=True, timeout=30))
    path = OUT / "recovery_audit" / f"attempt{attempt}_{side}.json"
    write(path, {"utc": utc().isoformat(), "n": len(rows), "files": rows})
    from pair500_generate import digest
    with (ROOT / "docs/PREREG_LOG.txt").open("a") as log:
        log.write(f"{utc().isoformat()} PAIR_RESTART_{side.upper()} attempt={attempt} n={len(rows)} manifest_sha256={digest(path)}\n")
    return rows


def main():
    deadline = datetime.datetime.fromisoformat(load(OUT / "eval254_config.json")["search_stop_utc"])
    previous = OUT / "recovery_live.json"
    attempts = load(previous).get("attempts", load(previous).get("attempt", 0)) if previous.exists() else 0
    pending = OUT / "recovery_audit" / f"attempt{attempts}_before.json"
    after_path = OUT / "recovery_audit" / f"attempt{attempts}_after.json"
    before = load(pending)["files"] if pending.exists() and not after_path.exists() else None
    with (OUT / "recovery_watch.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        while utc() < deadline:
            state = load(OUT / "full_queue_live.json")
            if (OUT / "frozen_prompt_snapshot.json").exists():
                break
            running = alive(state["pid"])
            if running and before is not None:
                after = snapshot(attempts, "after")
                assert all(after.get(key) == value for key, value in before.items()), "Completed search output changed on restart"
                before = None
            if not running and state["phase"] == "failed":
                log = (ROOT / "logs/pair500_full_node.log").read_text(errors="replace")[-16000:]
                terminal = any(key in log for key in ("signature mismatch", "AssertionError", "invalid PAIR conversation"))
                if terminal or attempts >= 3:
                    write(OUT / "recovery_live.json", {"utc": utc().isoformat(), "pid": os.getpid(),
                          "phase": "stopped_after_failure", "attempts": attempts, "terminal_config_error": terminal})
                    return
                attempts += 1
                before = snapshot(attempts, "before")
                stamp = utc().isoformat()
                with (ROOT / "docs/PREREG_LOG.txt").open("a") as record:
                    record.write(f"{stamp} PAIR_CONTROLLER_RECOVERY attempt={attempts} previous_pid={state['pid']} same frozen config, atomically completed rows retained.\n")
                write(OUT / "recovery_live.json", {"utc": stamp, "pid": os.getpid(), "phase": "restarting",
                                                 "attempt": attempts, "oom_in_log": "OutOfMemoryError" in log})
                with (ROOT / "logs/pair500_recovery_launch.log").open("ab") as output:
                    subprocess.Popen(
                        ["bash", "-c", "source night/launch.sh; export NOGPU=1; launch_job python3 -u tools/handoff_20261106/pair500_full_queue.py"],
                        cwd=ROOT, env={**os.environ, "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True"},
                        stdin=subprocess.DEVNULL, stdout=output, stderr=output, start_new_session=True)
                time.sleep(30)
            write(OUT / "recovery_live.json", {"utc": utc().isoformat(), "pid": os.getpid(),
                                              "phase": "monitoring", "attempts": attempts,
                                              "controller_pid": state["pid"], "controller_alive": running})
            time.sleep(30)


if __name__ == "__main__":
    main()
