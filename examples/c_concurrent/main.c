

#include <stdio.h>
#include <assert.h>

// These functions come from the other C files.
extern int multiply(int a, int b);
extern int add(int a, int b);
extern int subtract(int a, int b);


int main(int argc, char* argv[]) {
	int a;
	int b;
	int c;

	assert(argc);
	assert(argv);
	
	a = multiply(7, 12);
	assert(a == 84);
	printf("7 * 12 = %d\n", a);

	b = add(9, 2);
	assert(b == 11);
	printf("9 + 2 = %d\n", b);

	c = subtract(64, 3);
	assert(c == 61);
	printf("64 - 3 = %d\n", c);

	return 0;
}


