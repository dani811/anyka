#include "ak_global.h"
void *ak_adec_open(const struct audio_param *);
void *ak_adec_request_stream(void *, void *);
int ak_adec_send_stream(void *, const unsigned char *, unsigned int, long);
int ak_adec_notice_stream_end(void *);
int ak_adec_cancel_stream(void *);
int ak_adec_close(void *);
