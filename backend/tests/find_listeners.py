import os
import re
import subprocess

ports = [int(x) for x in os.environ.get('PORTS', '8000,8001').split(',')]
ns_out = subprocess.run(['netstat', '-ano'], capture_output=True, text=True).stdout
pid_to_port = {}
for line in ns_out.splitlines():
    m = re.search(r'(\d+)\.\d+\.\d+\.\d+:(\d+)\s+\S+\s+LISTENING\s+(\d+)', line)
    if m:
        pid_to_port[int(m.group(3))] = int(m.group(2))
for port in ports:
    for pid, p2 in pid_to_port.items():
        if p2 == port:
            wmi_cmd = subprocess.run(
                ['wmic', 'process', 'where', f'ProcessId={pid}', 'get', 'CommandLine', '/value'],
                capture_output=True, text=True)
            print(f"PORT {port} pid={pid} cmd={wmi_cmd.stdout.strip()}")
