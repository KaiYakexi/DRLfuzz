#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/wait.h>

#include "afl-fuzz.h"

#define MAX_QUEUE_ENTRIES 100
#define FIFO_SEND_PATH "send_fifo"
#define FIFO_RECEIVE_PATH "receive_fifo"
#define STATS_MESSAGE_SIZE 100

struct queue_entry {
    // ... (your existing definition)
};

struct afl_state {
    // ... (your existing definition)
    struct queue_entry queue_buf[MAX_QUEUE_ENTRIES];
};

struct afl_state afl;

// Function to send mutated test cases and receive data from Python
void sendMutatedTestCasesAndReceiveData() {
    int send_fifo_fd, receive_fifo_fd;

    // Create two named pipes (FIFOs)
    if (mkfifo(FIFO_SEND_PATH, 0666) == -1 || mkfifo(FIFO_RECEIVE_PATH, 0666) == -1) {
        perror("Error creating FIFOs");
        exit(EXIT_FAILURE);
    }

    // Open the send FIFO for writing
    send_fifo_fd = open(FIFO_SEND_PATH, O_WRONLY);
    if (send_fifo_fd == -1) {
        perror("Error opening send_fifo");
        exit(EXIT_FAILURE);
    }

    // Iterate through the queue
    for (int i = 0; i < MAX_QUEUE_ENTRIES; ++i) {
        struct queue_entry entry = afl.queue_buf[i];

        // Check if the test case was mutated
        if (entry.stats_mutated > 0) {
            // Write the mutated test case to the send FIFO
            if (write(send_fifo_fd, entry.testcase_buf, entry.len) == -1) {
                perror("Error writing to send_fifo");
                exit(EXIT_FAILURE);
            }

            // Send additional information
            char* stats_message = (char*)malloc(STATS_MESSAGE_SIZE);
            if (stats_message == NULL) {
                perror("Error allocating memory for stats_message");
                exit(EXIT_FAILURE);
            }

            snprintf(stats_message, STATS_MESSAGE_SIZE, "%lu %lu %u", afl.saved_crashes, afl.total_crashes, afl.queued_with_cov);

            // Write the stats message to the send FIFO
            if (write(send_fifo_fd, stats_message, strlen(stats_message)) == -1) {
                perror("Error writing stats message to send_fifo");
                exit(EXIT_FAILURE);
            }

            free(stats_message);
        }
    }

    // Close the send FIFO
    close(send_fifo_fd);

    // Call the Python script as a subprocess
    FILE *python_process = popen("python3 python_script.py", "r");
    if (python_process == NULL) {
        perror("Error opening python subprocess");
        exit(EXIT_FAILURE);
    }

    // Open the receive FIFO for reading
    receive_fifo_fd = open(FIFO_RECEIVE_PATH, O_RDONLY);
    if (receive_fifo_fd == -1) {
        perror("Error opening receive_fifo");
        exit(EXIT_FAILURE);
    }

    // Read data from the receive FIFO
    ssize_t bytes_read = read(receive_fifo_fd, NULL, 0);

    if (bytes_read == -1) {
        perror("Error getting size from receive_fifo");
        exit(EXIT_FAILURE);
    }

    char *received_data = (char *)malloc(bytes_read + 1);  // +1 for null terminator
    if (received_data == NULL) {
        perror("Error allocating memory for received_data");
        exit(EXIT_FAILURE);
    }

    ssize_t actual_bytes_read = read(receive_fifo_fd, received_data, bytes_read);
    if (actual_bytes_read == -1) {
        perror("Error reading from receive_fifo");
        free(received_data);
        exit(EXIT_FAILURE);
    }

    received_data[actual_bytes_read] = '\0';  // Null-terminate the received data
    printf("Received data from Python: %s\n", received_data);

    // Close the receive FIFO
    close(receive_fifo_fd);

    // Close the communication with the Python script
    if (pclose(python_process) == -1) {
        perror("Error closing python subprocess");
        exit(EXIT_FAILURE);
    }

    // Clean up FIFOs
    unlink(FIFO_SEND_PATH);
    unlink(FIFO_RECEIVE_PATH);

    free(received_data);
}





