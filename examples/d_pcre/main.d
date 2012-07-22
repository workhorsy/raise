

import std.stdio;
import lib_regex;

int main() {
	auto r = new Regex(r"^/users/\d+$");
	writefln("is_match: %b", r.is_match("/users/6"));

	return 0;
}

