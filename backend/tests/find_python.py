import os, subprocess, re

ports = [8000, 8001]
out = subprocess.run(['netstat', '-ano'], capture_output=True, text=True).stdout
pid_to_port = {}
for line in out.splitlines():
    m = re.search(r'(\d+)\.\d+\.\d+\.\d+:(\d+)\s+\S+\s+LISTENING\s+(\d+)', line)
    if m:
        pid_to_port[int(m.group(3))] = int(m.group(2))

for port in ports:
    for pid in pid_to_port:
        if pid_to_port[pid] == port:
            try:
                wmic = subprocess.run(
                    ['powershell', '-NoProfile', '-Command',
                     f"(Get-CimInstance Win32_Process -Filter 'ProcessId={pid}').CommandLine"],
                    capture_output=True, text=True)
                print(f"PORT {port} pid={pid} cmd={wmic.stdout.strip()!r}")
            except Exception as e:
                print(f"PORT {port} pid={pid} ERR={e}")
