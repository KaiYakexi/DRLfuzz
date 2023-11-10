#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>

#include "afl/include/afl-fuzz.h"

#define CIRCULAR_BUFFER_SIZE 6

int circular_buffer[CIRCULAR_BUFFER_SIZE];
int buffer_index = 0;

void do_child(int fd_rd, int fd_wr) {
    dup2(fd_rd, STDIN_FILENO);
    dup2(fd_wr, STDOUT_FILENO);
    close(fd_rd);
    close(fd_wr);
    execlp("rlfuzz/drl/environment.py", "./environment.py", NULL);
}

void do_parent(int fd_rd, int fd_wr) {
    char buf[10000];
    FILE *fin, *fout;
    fin = fdopen(fd_rd, "rb");
    fout = fdopen(fd_wr, "wb");
    setbuf(fout, NULL);

    while (1) {
        int mutation_index;
        fread(&mutation_index, sizeof(int), 1, fin);
        printf("Received mutation method index: %d\n", mutation_index);

        circular_buffer[buffer_index] = mutation_index;
        buffer_index = (buffer_index + 1) % CIRCULAR_BUFFER_SIZE;

        afl_state_t afl_state;

        // Assuming afl_state is the global instance or accessible in this scope
        afl_state.total_bitmap_entries = total_bitmap_entries;
        afl_state.total_bitmap_size = total_bitmap_size;
        afl_state.total_crashes = total_crashes;
        afl_state.saved_crashes = saved_crashes;

        fwrite(&afl_state, sizeof(afl_state_t), 1, fout);
        fflush(fout);
    }
}

int main(int argc, char **argv) {
    int fd1[2];
    int fd2[2];
    pid_t id;

    pipe(fd1);
    pipe(fd2);

    id = fork();
    if (id == 0) {
        // child
        close(fd1[1]);
        close(fd2[0]);
        do_child(fd1[0], fd2[1]);
    } else if (id > 0) {
        // parent
        close(fd1[0]);
        close(fd2[1]);
        do_parent(fd2[0], fd1[1]);
    } else {
        perror("fork");
    }

    return 0;
}

