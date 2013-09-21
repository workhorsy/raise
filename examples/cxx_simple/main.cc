

#include <iostream>


class MathHelper {
	public:

	int add(int a, int b) {
		return a + b;
	}

	int multiply(int a, int b) {
		return a * b;
	}
};

int main(int argc, char* argv[]) {
	MathHelper math;

	#ifdef ADD
	int a = math.add(7, 9);
	std::cout << "7 + 9 == " << a << std::endl;
	#endif

	#ifdef MULTIPLY
	int b = math.multiply(9, 12);
	std::cout << "9 * 12 == " << b << std::endl;
	#endif

	return 0;
}


