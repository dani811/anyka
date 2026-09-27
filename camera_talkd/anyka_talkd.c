/*
 * anyka-talkd - minimal raw G.711 A-law talk daemon for Anyka AK3918 cameras.
 *
 * Input:  raw PCMA/G.711 A-law, 8000 Hz, mono over TCP.
 * Output: Anyka audio decoder -> AK3918 audio output/speaker.
 *
 * This intentionally contains no HTTP, RTSP, ONVIF, transcoding or UI code.
 * go2rtc is responsible for the WebRTC/backchannel side.
 */
#define _POSIX_C_SOURCE 200809L

#include <arpa/inet.h>
#include <errno.h>
#include <netinet/in.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <unistd.h>

#include "ak_global.h"
#include "ak_ao.h"
#include "ak_adec.h"

#define DEFAULT_PORT 10000
#define DEFAULT_DAC_VOLUME 6
#define DEFAULT_ASLC_VOLUME 2
#define SAMPLE_RATE 8000
#define CHANNELS 1
#define SAMPLE_BITS 16
#define READ_BUFFER 4096
#define DECODE_WAIT_MS 100

static volatile sig_atomic_t g_stop = 0;

struct audio_session {
    void *ao;
    void *adec;
    void *stream;
};

static void on_signal(int signo)
{
    (void)signo;
    g_stop = 1;
}

static void usage(const char *program)
{
    fprintf(stderr,
            "Usage: %s [--port N] [--allow IPv4] [--volume 0..6]\n"
            "\n"
            "Receives raw PCMA/G.711 A-law 8000 Hz mono over TCP and plays it\n"
            "through the Anyka AK3918 speaker. Only one talk session is active\n"
            "at a time. --allow restricts clients to one IPv4 address.\n",
            program);
}

static int audio_open(struct audio_session *session, int dac_volume)
{
    struct pcm_param pcm = {0};
    struct audio_param decoder = {0};

    memset(session, 0, sizeof(*session));

    pcm.sample_bits = SAMPLE_BITS;
    pcm.channel_num = CHANNELS;
    pcm.sample_rate = SAMPLE_RATE;

    session->ao = ak_ao_open(&pcm);
    if (session->ao == NULL) {
        fprintf(stderr, "anyka-talkd: ak_ao_open failed\n");
        return -1;
    }

    if (ak_ao_enable_speaker(session->ao, AUDIO_FUNC_ENABLE) != AK_SUCCESS) {
        fprintf(stderr, "anyka-talkd: warning: ak_ao_enable_speaker failed\n");
    }
    if (ak_ao_set_dac_volume(session->ao, dac_volume) != AK_SUCCESS) {
        fprintf(stderr, "anyka-talkd: warning: ak_ao_set_dac_volume failed\n");
    }
    if (ak_ao_set_aslc_volume(session->ao, DEFAULT_ASLC_VOLUME) != AK_SUCCESS) {
        fprintf(stderr, "anyka-talkd: warning: ak_ao_set_aslc_volume failed\n");
    }
    if (ak_ao_set_resample(session->ao, AUDIO_FUNC_DISABLE) != AK_SUCCESS) {
        fprintf(stderr, "anyka-talkd: warning: ak_ao_set_resample failed\n");
    }
    (void)ak_ao_clear_frame_buffer(session->ao);

    decoder.type = AK_AUDIO_TYPE_PCM_ALAW;
    decoder.sample_bits = SAMPLE_BITS;
    decoder.channel_num = CHANNELS;
    decoder.sample_rate = SAMPLE_RATE;

    session->adec = ak_adec_open(&decoder);
    if (session->adec == NULL) {
        fprintf(stderr, "anyka-talkd: ak_adec_open(PCMA) failed\n");
        ak_ao_enable_speaker(session->ao, AUDIO_FUNC_DISABLE);
        ak_ao_close(session->ao);
        session->ao = NULL;
        return -1;
    }

    session->stream = ak_adec_request_stream(session->ao, session->adec);
    if (session->stream == NULL) {
        fprintf(stderr, "anyka-talkd: ak_adec_request_stream failed\n");
        ak_adec_close(session->adec);
        ak_ao_enable_speaker(session->ao, AUDIO_FUNC_DISABLE);
        ak_ao_close(session->ao);
        memset(session, 0, sizeof(*session));
        return -1;
    }

    return 0;
}

static void audio_close(struct audio_session *session)
{
    if (session->adec != NULL) {
        (void)ak_adec_notice_stream_end(session->adec);
    }
    if (session->stream != NULL) {
        (void)ak_adec_cancel_stream_no_wait(session->stream);
        session->stream = NULL;
    }
    if (session->adec != NULL) {
        (void)ak_adec_close(session->adec);
        session->adec = NULL;
    }
    if (session->ao != NULL) {
        (void)ak_ao_enable_speaker(session->ao, AUDIO_FUNC_DISABLE);
        (void)ak_ao_close(session->ao);
        session->ao = NULL;
    }
}

static int audio_write(struct audio_session *session,
                       const unsigned char *data,
                       size_t length)
{
    size_t offset = 0;

    while (offset < length && !g_stop) {
        int written = ak_adec_send_stream(
            session->adec,
            data + offset,
            (unsigned int)(length - offset),
            DECODE_WAIT_MS);

        if (written < 0) {
            fprintf(stderr, "anyka-talkd: ak_adec_send_stream failed\n");
            return -1;
        }
        if (written == 0) {
            usleep(10000);
            continue;
        }
        offset += (size_t)written;
    }

    return offset == length ? 0 : -1;
}

static int parse_port(const char *value)
{
    char *end = NULL;
    long port = strtol(value, &end, 10);
    if (value == end || *end != '\0' || port < 1 || port > 65535) {
        return -1;
    }
    return (int)port;
}

static int parse_volume(const char *value)
{
    char *end = NULL;
    long volume = strtol(value, &end, 10);
    if (value == end || *end != '\0' || volume < 0 || volume > 6) {
        return -1;
    }
    return (int)volume;
}

static int peer_allowed(const struct sockaddr_in *peer, const char *allowed_ip)
{
    struct in_addr allowed;

    if (allowed_ip == NULL) {
        return 1;
    }
    if (inet_pton(AF_INET, allowed_ip, &allowed) != 1) {
        return 0;
    }
    return peer->sin_addr.s_addr == allowed.s_addr;
}

static int serve_client(int fd, const char *peer_ip, int dac_volume)
{
    struct audio_session audio;
    unsigned char buffer[READ_BUFFER];
    struct timeval timeout = {1, 0};

    (void)setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));

    if (audio_open(&audio, dac_volume) != 0) {
        return -1;
    }

    fprintf(stderr, "anyka-talkd: talk session started from %s\n", peer_ip);

    while (!g_stop) {
        ssize_t count = recv(fd, buffer, sizeof(buffer), 0);

        if (count > 0) {
            if (audio_write(&audio, buffer, (size_t)count) != 0) {
                audio_close(&audio);
                return -1;
            }
            continue;
        }
        if (count == 0) {
            break;
        }
        if (errno == EINTR || errno == EAGAIN || errno == EWOULDBLOCK) {
            continue;
        }

        fprintf(stderr, "anyka-talkd: recv failed: %s\n", strerror(errno));
        audio_close(&audio);
        return -1;
    }

    audio_close(&audio);
    fprintf(stderr, "anyka-talkd: talk session stopped\n");
    return 0;
}

int main(int argc, char **argv)
{
    int port = DEFAULT_PORT;
    int dac_volume = DEFAULT_DAC_VOLUME;
    const char *allowed_ip = NULL;
    int listener;
    int reuse = 1;
    struct sockaddr_in bind_addr = {0};

    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--port") == 0 && i + 1 < argc) {
            port = parse_port(argv[++i]);
            if (port < 0) {
                fprintf(stderr, "anyka-talkd: invalid port\n");
                return EXIT_FAILURE;
            }
        } else if (strcmp(argv[i], "--allow") == 0 && i + 1 < argc) {
            allowed_ip = argv[++i];
            struct in_addr parsed;
            if (inet_pton(AF_INET, allowed_ip, &parsed) != 1) {
                fprintf(stderr, "anyka-talkd: invalid --allow IPv4 address\n");
                return EXIT_FAILURE;
            }
        } else if (strcmp(argv[i], "--volume") == 0 && i + 1 < argc) {
            dac_volume = parse_volume(argv[++i]);
            if (dac_volume < 0) {
                fprintf(stderr, "anyka-talkd: invalid volume (expected 0..6)\n");
                return EXIT_FAILURE;
            }
        } else if (strcmp(argv[i], "--help") == 0 || strcmp(argv[i], "-h") == 0) {
            usage(argv[0]);
            return EXIT_SUCCESS;
        } else {
            usage(argv[0]);
            return EXIT_FAILURE;
        }
    }

    signal(SIGINT, on_signal);
    signal(SIGTERM, on_signal);
    signal(SIGPIPE, SIG_IGN);

    listener = socket(AF_INET, SOCK_STREAM, 0);
    if (listener < 0) {
        fprintf(stderr, "anyka-talkd: socket failed: %s\n", strerror(errno));
        return EXIT_FAILURE;
    }

    (void)setsockopt(listener, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse));

    bind_addr.sin_family = AF_INET;
    bind_addr.sin_addr.s_addr = htonl(INADDR_ANY);
    bind_addr.sin_port = htons((uint16_t)port);

    if (bind(listener, (struct sockaddr *)&bind_addr, sizeof(bind_addr)) != 0) {
        fprintf(stderr, "anyka-talkd: bind :%d failed: %s\n", port, strerror(errno));
        close(listener);
        return EXIT_FAILURE;
    }

    if (listen(listener, 2) != 0) {
        fprintf(stderr, "anyka-talkd: listen failed: %s\n", strerror(errno));
        close(listener);
        return EXIT_FAILURE;
    }

    fprintf(stderr,
            "anyka-talkd: listening on 0.0.0.0:%d for raw PCMA/8000%s%s\n",
            port,
            allowed_ip ? " (allow=" : "",
            allowed_ip ? allowed_ip : "");
    if (allowed_ip != NULL) {
        fprintf(stderr, "anyka-talkd: source allowlist enabled\n");
    }

    while (!g_stop) {
        struct sockaddr_in peer = {0};
        socklen_t peer_len = sizeof(peer);
        int client = accept(listener, (struct sockaddr *)&peer, &peer_len);

        if (client < 0) {
            if (errno == EINTR) {
                continue;
            }
            fprintf(stderr, "anyka-talkd: accept failed: %s\n", strerror(errno));
            break;
        }

        char peer_ip[INET_ADDRSTRLEN] = "?";
        (void)inet_ntop(AF_INET, &peer.sin_addr, peer_ip, sizeof(peer_ip));

        if (!peer_allowed(&peer, allowed_ip)) {
            fprintf(stderr, "anyka-talkd: rejected client %s\n", peer_ip);
            close(client);
            continue;
        }

        (void)serve_client(client, peer_ip, dac_volume);
        close(client);
    }

    close(listener);
    fprintf(stderr, "anyka-talkd: stopped\n");
    return EXIT_SUCCESS;
}
