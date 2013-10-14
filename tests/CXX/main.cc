

#include <iostream>
#include "lib_math.h"


int main(int argc, char* argv[]) {
	LibMath math;

	int a = math.add(7, 9);
	std::cout << "7 + 9 = " << a << std::endl;

	return 0;
}


