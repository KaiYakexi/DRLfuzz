#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <sys/shm.h>
#include <math.h>
#include <assert.h>
#include <stdint.h>

#include <afl-fuzz.h>


/* Filename of the named pipe to the rl model */
#define NAMED_PIPE_OUT  "pipe_to_rl_model"

/* Filename of the named pipe from the rl model */
#define NAMED_PIPE_IN   "pipe_from_rl_model"

typedef struct {
    /**
     * Here goes all stuff that needs to be preserved (state of the plugin)
     * */
    afl_state_t* afl; /* The AFL State Object */
    char send_buf[4096]; /* package size. Reward + Testcase */
    
    FILE* out_pipe_fd; /* File descriptor of pipe to ml model */
    FILE* in_pipe_fd; /* File descriptor of pipe from ml model */
    
} rl_state_t;

rl_state_t rl_state;

int32_t recv_mutation() {
	rl_state_t *data = &rl_state;
	int32_t mutation;
	if (fread(&mutation, 1, sizeof(int32_t), data->in_pipe_fd) < sizeof(int32_t)) {
		return (int32_t)-1;
	}
	return mutation;
}

int send_reward_testcase(uint32_t coverage, uint8_t edge, uint32_t crash, const void* testcase, uint32_t len) {
	int ret;
	rl_state_t *data = &rl_state;
	char *buf = data->send_buf;
	uint32_t testcase_max_len;
	size_t send_len;
	memcpy(buf, &coverage, sizeof(coverage));
	buf += sizeof(coverage);
	memcpy(buf, &edge, sizeof(edge));
	buf += sizeof(edge);
	memcpy(buf, &crash, sizeof(crash));
	buf += sizeof(crash);
	testcase_max_len = sizeof(data->send_buf) - ((buf + sizeof(len)) - data->send_buf);
	if (len > testcase_max_len) {
		len = testcase_max_len;
	}
	memcpy(buf, &len, sizeof(len));
	buf += sizeof(len);
	memcpy(buf, testcase, (size_t)len);
	buf += len;
	send_len = buf - data->send_buf;
	ret = fwrite(data->send_buf, 1, send_len, data->out_pipe_fd);
	return ret;
}

void rl_init(afl_state_t* afl) {
    // Let the RL python script run in another process
	rl_state_t *data = &rl_state;
	data->afl = afl;
        data->in_pipe_fd = fopen(NAMED_PIPE_IN, "rb");
        data->out_pipe_fd = fopen(NAMED_PIPE_OUT, "wb");
        setbuf(data->out_pipe_fd, NULL);

        if (data->out_pipe_fd == NULL || data->in_pipe_fd == NULL) {
            perror("Opening FIFOs failed!");
            exit(EXIT_FAILURE);
        }
}


void afl_deinit() {
  rl_state_t *data = &rl_state;
  //Close named pipes
  fclose(data->out_pipe_fd);
  fclose(data->in_pipe_fd);
}
