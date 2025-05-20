FROM nginx:1.27.4

RUN apt update && apt install -y \
    build-essential curl wget unzip libpcre3 libpcre3-dev zlib1g zlib1g-dev libssl-dev \
    libmaxminddb-dev git ca-certificates

RUN git clone --depth=1 https://github.com/leev/ngx_http_geoip2_module.git /usr/src/ngx_http_geoip2_module

WORKDIR /usr/src
RUN wget http://nginx.org/download/nginx-1.27.4.tar.gz && \
    tar -xvzf nginx-1.27.4.tar.gz && \
    cd nginx-1.27.4 && \
    ./configure --with-compat --add-dynamic-module=../ngx_http_geoip2_module && \
    make modules && \
    cp objs/ngx_http_geoip2_module.so /etc/nginx/modules/

COPY nginx.conf /etc/nginx/nginx.conf
COPY GeoLite2-Country.mmdb /etc/nginx/GeoLite2-Country.mmdb

COPY ru/nono.html /usr/share/nginx/ru/nono.html
COPY ru/nono.png /usr/share/nginx/ru/nono.png

COPY other/welcome.html /usr/share/nginx/other/welcome.html
COPY other/welcome.png /usr/share/nginx/other/welcome.png


# Старт nginx
CMD ["nginx", "-g", "daemon off;"]
