FROM alpine:3.20

ARG GO2RTC_VERSION=1.9.9

RUN apk add --no-cache curl jq ca-certificates \
    && arch="$(apk --print-arch)" \
    && case "$arch" in \
        x86_64) goarch="amd64" ;; \
        aarch64) goarch="arm64" ;; \
        *) echo "Unsupported architecture: $arch"; exit 1 ;; \
    esac \
    && curl -fsSL -o /usr/local/bin/go2rtc "https://github.com/AlexxIT/go2rtc/releases/download/v${GO2RTC_VERSION}/go2rtc_linux_${goarch}" \
    && chmod +x /usr/local/bin/go2rtc

COPY go2rtc.yaml.template /etc/go2rtc.yaml.template
COPY run.sh /run.sh

EXPOSE 1984 8554

CMD ["/run.sh"]
