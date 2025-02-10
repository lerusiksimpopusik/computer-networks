import subprocess
import re

ips = ['google.com', 'chatgpt.com', 'nsu.ru', 'ya.ru', 'gismeteo.ru',
       'pypi.org', 'youtube.com', 'vk.com', 'ru.wikipedia.org', 'otvet.mail.ru']

with open('sem1_output.csv', 'w', newline='', encoding='utf-8') as f:
    f.write("ip, rtt (ms)\n")

    for ip in ips:
        try:
            result = subprocess.check_output(f"ping {ip}").decode('oem')
            match = re.search(r'Среднее\s*=\s*(\d+)\s*мсек', result)
            # print(result)
            avg_rtt = match.group(1) if match else "N/A"

            f.write(f"{ip}, {avg_rtt}\n")
        except subprocess.CalledProcessError:
            f.write(f"{ip}, Ping failed\n")
