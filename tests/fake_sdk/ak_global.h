/* Test double only. Never link this API stand-in into a camera binary. */
#ifndef TEST_AK_GLOBAL_H
#define TEST_AK_GLOBAL_H
#define AUDIO_FUNC_ENABLE 1
#define AUDIO_FUNC_DISABLE 0
#define AK_AUDIO_TYPE_PCM_ALAW 1
struct pcm_param { int sample_bits, channel_num, sample_rate; };
struct audio_param { int type, sample_bits, channel_num, sample_rate; };
#endif
