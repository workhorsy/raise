

import std.string;

private char* to_sz(string value) {
	return cast(char*)std.string.toStringz(value);
}

class Regex {
	private RegexAddress _address;
	private string _pattern;

	public this(string pattern) {
		_pattern = pattern;

		char* error = null;
		int erroffset = 0;
		_address = c_setup_regex(to_sz(_pattern), error, erroffset);

		if(!_address) {
			throw new Exception("Failed to compile regex: '" ~ _pattern ~ "'\n");
		}
	}

	public string pattern() {
		return _pattern;
	}

	public bool is_match(string value) {
		return c_is_match_regex(_address, to_sz(value));
	}
}

private:

extern (C):

alias size_t RegexAddress;
RegexAddress c_setup_regex(char* pattern, char* error, int erroffset);
bool c_is_match_regex(RegexAddress address, char* value);

