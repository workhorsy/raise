

#include <stdio.h>
#include <assert.h>
#include "libexample.h"

int main() {
	int result = multiply(7, 12);
	assert(result == 84);
	printf("7 * 12 = %d\n", result);
	return 0;
}

