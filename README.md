# Leader-election-algorithms-for-asynchronous-systems
Leader election algorithms for asynchronous systems

10 vertices, 17 edges

0 1 3 
0 5 2 
1 2 17 
1 3 16 
2 3 8 
2 8 18 
3 4 11 
3 8 4 
4 5 1 
4 6 6 
4 7 5 
4 8 10 
5 6 7 
6 7 15 
7 8 12 
7 9 13 
8 9 9 



10
0 3 0 0 0 2 0 0 0 0
3 0 17 16 0 0 0 0 0 0
0 17 0 8 0 0 0 0 18 0
0 16 8 0 11 0 0 0 4 0
0 0 0 11 0 1 6 5 10 0
2 0 0 0 1 0 7 0 0 0
0 0 0 0 6 7 0 15 0 0
0 0 0 0 5 0 15 0 12 13
0 0 18 4 10 0 0 12 0 9
0 0 0 0 0 0 0 13 9 0

https://visualgo.net/


================= PHASE 1 ====================
0 -> 5
1 -> 0
2 -> 3
3 -> 8
4 -> 5
5 -> 4
6 -> 4
7 -> 4
8 -> 3
9 -> 8

0 primeste connect de la 1
3 primeste connect de la 2, 8
4 primeste connect de la 5, 6, 7
5 primeste connect de la 0, 4
8 primeste connect de la 3, 9

E mai probabil ca nodurile 0, 3, 4, 5, 8 sa fie printre primele trezite