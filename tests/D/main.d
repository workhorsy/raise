

import std.stdio;
import lib_math;

int main() {
	int a = multiply(9, 12);
	assert(a == 108);
	writefln("9 * 12 = %d", a);

	return 0;
}

