#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "ak_ao.h"
#include "ak_adec.h"
static int token;
static int mode(const char *s) { const char *m = getenv("FAKE_MODE"); return m && !strcmp(m,s); }
static void event(const char *s) { fprintf(stderr, "fake: %s\n", s); }
void *ak_ao_open(const struct pcm_param *p) {
    if(p->sample_rate != 8000 || p->channel_num != 1 || p->sample_bits != 16) abort();
    event("ao_open"); return mode("ao_fail") ? NULL : &token;
}
void *ak_adec_open(const struct audio_param *p) {
    if(p->type != AK_AUDIO_TYPE_PCM_ALAW || p->sample_rate != 8000) abort();
    event("adec_open"); return mode("adec_fail") ? NULL : &token;
}
void *ak_adec_request_stream(void *a, void *b) { (void)a; (void)b; event("stream_open"); return mode("stream_fail") ? NULL : &token; }
int ak_adec_send_stream(void *a, const unsigned char *data, unsigned int len, long ms) {
    (void)a; (void)ms;
    if(mode("stall")) return 0;
    if(mode("write_fail")) return -1;
    if(len > 37) len = 37; /* Force partial SDK writes. */
    const char *path = getenv("FAKE_OUTPUT");
    if(path) { FILE *f = fopen(path,"ab"); if(!f) abort(); fwrite(data,1,len,f); fclose(f); }
    return (int)len;
}
#define OP(name) int name(void *a) { (void)a; event(#name); return 0; }
#define SET(name) int name(void *a, int b) { (void)a; (void)b; return 0; }
SET(ak_ao_enable_speaker)
SET(ak_ao_set_dac_volume)
SET(ak_ao_set_aslc_volume)
SET(ak_ao_set_resample)
OP(ak_ao_clear_frame_buffer)
OP(ak_ao_close)
OP(ak_adec_notice_stream_end)
OP(ak_adec_cancel_stream)
OP(ak_adec_close)
