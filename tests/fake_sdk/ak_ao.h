#include "ak_global.h"
void *ak_ao_open(const struct pcm_param *);
int ak_ao_enable_speaker(void *, int);
int ak_ao_set_dac_volume(void *, int);
int ak_ao_set_aslc_volume(void *, int);
int ak_ao_set_resample(void *, int);
int ak_ao_clear_frame_buffer(void *);
int ak_ao_close(void *);
