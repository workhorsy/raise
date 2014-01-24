

#include <stdio.h>
#include <assert.h>

// These functions come from the other C files.
extern int multiply(int a, int b);


int main(int argc, char* argv[]) {
	int a = multiply(7, 12);
	assert(a == 84);
	printf("7 * 12 = %d\n", a);

	return 0;
}


