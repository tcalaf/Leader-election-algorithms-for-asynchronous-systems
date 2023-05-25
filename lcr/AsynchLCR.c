#include "mpi.h"
#include <stdio.h>
#include <stdlib.h>

typedef enum { UNKNOWN, WORKER, LEADER } process_states;

int main (int argc, char *argv[]) {
    int size, uid, recvUID;
    MPI_Request send;
    MPI_Status status;
    process_states state = UNKNOWN;

    MPI_Init(&argc, &argv);
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    MPI_Comm_rank(MPI_COMM_WORLD, &uid);

    int send_neighbour = (uid + 1) % size;
    int recv_neighbour = uid == 0 ? size - 1 : uid - 1;
    int leaderUid = uid;

    MPI_Isend(&uid, 1, MPI_INT, send_neighbour, 0, MPI_COMM_WORLD, &send);
    
    while (state == UNKNOWN) {
        MPI_Recv(&recvUID, 1, MPI_INT, recv_neighbour, 0, MPI_COMM_WORLD, NULL);

        if (recvUID == uid) {
            state = LEADER;
        } else if (recvUID > leaderUid) {
            leaderUid = recvUID;
            state = WORKER;
            MPI_Isend(&recvUID, 1, MPI_INT, send_neighbour, 0, MPI_COMM_WORLD, &send);
        }
    }

    printf("UID=%d, LeaderUID=%d\n", uid, leaderUid);

    MPI_Finalize();
    return 0;
}