

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

	int a = math.add(7, 9);
	std::cout << "16 == " << a << std::endl;

	return 0;
}


