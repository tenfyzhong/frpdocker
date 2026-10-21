"""Exercise an FRP 0.20.0 client/server pair using loopback-only TCP forwarding."""
import contextlib
import pathlib
import socket
import subprocess
import sys
import tempfile
import threading
import time


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def main():
    binaries = pathlib.Path(sys.argv[1]).resolve()
    control_port, remote_port = free_port(), free_port()
    with tempfile.TemporaryDirectory() as tmp, socket.socket() as backend:
        backend.bind(("127.0.0.1", 0))
        backend.listen()
        backend.settimeout(1)
        stopped = threading.Event()

        def echo():
            while not stopped.is_set():
                try:
                    conn, _ = backend.accept()
                except socket.timeout:
                    continue
                with conn:
                    conn.settimeout(2)
                    conn.sendall(conn.recv(1024))

        thread = threading.Thread(target=echo, daemon=True)
        thread.start()
        root = pathlib.Path(tmp)
        (root / "frps.ini").write_text(
            "[common]\nbind_addr = 127.0.0.1\nproxy_bind_addr = 127.0.0.1\n"
            f"bind_port = {control_port}\nlog_file = console\n"
        )
        (root / "frpc.ini").write_text(
            f"[common]\nserver_addr = 127.0.0.1\nserver_port = {control_port}\n"
            "log_file = console\nlogin_fail_exit = false\nhttp_proxy =\n"
            "[smoke]\ntype = tcp\nlocal_ip = 127.0.0.1\n"
            f"local_port = {backend.getsockname()[1]}\nremote_port = {remote_port}\n"
        )
        processes = []
        with contextlib.ExitStack() as stack:
            try:
                for name in ("frps", "frpc"):
                    log = stack.enter_context(open(root / (name + ".log"), "w"))
                    processes.append(subprocess.Popen(
                        [str(binaries / name), "-c", str(root / (name + ".ini"))],
                        stdout=log, stderr=subprocess.STDOUT,
                    ))
                deadline = time.monotonic() + 20
                while time.monotonic() < deadline:
                    if any(p.poll() is not None for p in processes):
                        raise RuntimeError("FRP process exited before forwarding succeeded")
                    try:
                        with socket.create_connection(("127.0.0.1", remote_port), timeout=1) as client:
                            client.sendall(b"patched-go-frp-smoke")
                            assert client.recv(1024) == b"patched-go-frp-smoke"
                        print("FRP 0.20.0 client/server TCP forwarding passed")
                        return
                    except OSError:
                        time.sleep(0.2)
                raise RuntimeError("FRP forwarding did not become ready in 20 seconds")
            except Exception:
                for name in ("frps", "frpc"):
                    print((root / (name + ".log")).read_text())
                raise
            finally:
                for process in processes:
                    process.terminate()
                for process in processes:
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                stopped.set()
                thread.join(timeout=2)


if __name__ == "__main__":
    main()
