# Keep FRP 0.20.0 and its INI configuration compatible while rebuilding its Go runtime.
FROM golang:1.26.10-alpine AS build

ENV GO111MODULE=off GOTOOLCHAIN=local CGO_ENABLED=0
WORKDIR /go/src/github.com/fatedier/frp

RUN apk add --no-cache patch && \
    wget -O /tmp/frp.tar.gz https://github.com/fatedier/frp/archive/629f2856b1d65641d494e538f4197bb11020d6f0.tar.gz && \
    echo 'a11ee450500b29773d1b16a244eac77e8e2ead416a853932922acb4e5d1a0403  /tmp/frp.tar.gz' | sha256sum -c - && \
    tar -xzf /tmp/frp.tar.gz --strip-components=1 && \
    rm /tmp/frp.tar.gz
COPY patches/go-vet.patch /tmp/go-vet.patch
RUN patch -p1 < /tmp/go-vet.patch && \
    go test ./assets/... ./client/... ./cmd/... ./models/... ./server/... ./utils/... && \
    go build -o /out/frps ./cmd/frps && \
    go build -o /out/frpc ./cmd/frpc && \
    go version -m /out/frps | grep -F ': go1.26.10' && \
    go version -m /out/frpc | grep -F ': go1.26.10'

FROM alpine:3.7
MAINTAINER tenfyzhong "tenfy@tenfy.cn"

ENV FRP_VERSION 0.20.0
COPY --from=build /out/frps /frps
COPY --from=build /out/frpc /frpc
COPY --from=build /go/src/github.com/fatedier/frp/conf/frps.ini /frps.ini
COPY --from=build /go/src/github.com/fatedier/frp/conf/frpc.ini /frpc.ini

WORKDIR /
EXPOSE 80 443 6000 7000 7500

CMD ["/frps", "-c", "/frps.ini"]
