import os
import csv

ips = ['google.com' 'chatgpt.com', 'nsu.ru', 'ya.ru', 'gismeteo.ru',
       'pypi.org', 'youtube.com', 'vk.com', 'ru.wikipedia.org', 'otvet.mail.ru']
# ip = "8.8.8.8"
for ip in ips:
    # os.system("ping {}".format(ip))
    result = os.popen("ping {}".format(ip))
    # print(result, type(result))
    with open('output.csv', 'a') as csvfile:
        writer = csv.writer(csvfile, delimiter=' ',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(result)