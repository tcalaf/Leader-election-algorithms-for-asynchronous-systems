build_lcr:
	mpicc AsynchLCR.c -o AsynchLCR

run_lcr:
	mpirun --oversubscribe -np 50 AsynchLCR > out.txt

clean_lcr:
	rm AsynchLCR