добавить в настройках docker engine
```
"fixed-cidr-v6": "2001:db8:1::/64",
"ipv6": true
```
перезапустить

создать и настроить контейнеры
```
docker run -d --name nginx-server nginx
docker run -d --name alpine-client alpine tail -f /dev/null
docker exec -it alpine-client apk add tcpdump curl
```
протестировать
```
docker exec -d alpine-client tcpdump -i eth0 -w /ipv4-ipv6.pcap
docker exec -it alpine-client ping -4 172.17.0.2
docker exec -it alpine-client ping -6 2001:db8:1::242:ac11:2
docker exec -it alpine-client curl -4 http://172.17.0.2
docker exec -it alpine-client curl -6 "http://[2001:db8:1::242:ac11:2]"
docker exec alpine-client pkill tcpdump
docker cp alpine-client:/ipv4-ipv6.pcap .
```
посмотреть ipv4-ipv6.pcap через wireshark