
#Raise
A small build automation tool that ships with your software.

&copy; 2013 - 2014 Matthew Brennan Jones

Last updated on January 10th 2014

For Raise Version 0.3

[https://launchpad.net/raise](https://launchpad.net/raise)


* * *


### Table of Contents

1. [Introduction](#Introduction)
    1. License and Copyright
    2. Contact and Bugs
    3. Authors
2. Installation
3. Command Line Arguments
4. Supported Languages
    1. C/C++
    2. D
    3. C&#35;
    4. Java
5. Operating System Support
    1. Linux
    2. FreeBSD
    3. Windows
    4. Cygwin
    5. OS X
    6. Open Indiana
    7. Haiku
6. Fundamentals
    1. Emoticons
    2. Running functions that must succeed
    3. Running functions that may fail
    4. Running commands that must succeed
    5. Running commands that may fail
    6. Running commands and printing the result
    7. Running commands and getting the result
7. File System
8. Terminal
9. Concurrency
10. Libraries and Programs
11. C
12. C++
13. D
14. C&#35;
15. Java


* * *


#Introduction

##1. License and Copyright

Raise is licensed under a MIT style license. This is done in the hopes that it will be compatible with most popular software licenses.

Raise is &copy; 2013 - 2014 Matthew Brennan Jones. Other authors please add your copyright here too.

##1.2. Contact and Bugs

If you find any errors, bugs, or misinformation, please report a bug at [https://launchpad.net/raise](https://launchpad.net/raise) or contact one of the authors.

##1.3. Authors

Matthew Brennan Jones <mattjones@workhorsy.org>


* * *


#2. Installation


* * *


#3. Command Line Arguments


* * *


#4. Supported Languages

##4.1. C/C++

C and C++ are fully supported with GCC, and CLang. MS cl.exe support is not yet complete.

##4.2. D

D is fully supported with DMD and LDC.

##4.3. C&#35;

C&#35; works with Mono and MS .NET. Some advanced features such as installing into the GAC have not been implemented.

##4.4. Java

Java works with OpenJDK 7.


* * *


#5. Operating System Support

##5.1. Linux

Fully supported and developed primarily on Linux. Tested primarily on Ubuntu, Debian, Linux Mint, Fedora, and Centos.

##5.2. FreeBSD

Fully supported.

##5.3. Windows

Partially supported. Tested on Windows XP, and 7. There are still issues with building and finding C/C++ libraries on Windows. It is recommended that Windows users use Cygwin.

##5.4. Cygwin

Fully Supported.

##5.5. OS X

Not supported or tested. 

As of November 2nd 2013 there is no way to purchase OS X 10.9 without using the Mac App Store (running on OS X only), or buying dedicated hardware. I will not be fixing this until Apple allows me to buy a full install disk of the current release, and install it in a virtual machine without hacks.

If other contributors want to donate a machine, or add this feature themselves, they are welcome to do it.

##5.6. Open Indiana

Not supported.

Was not able to get it to work. As of October 17th 2013 (oi_151a_prestable8) they are still [migrating from SunStudio to GCC/Clang](http://wiki.openindiana.org/oi/Compiler+Migration). A basic C/C++ "Hello World" program does not compile. 

##5.7. Haiku

Not supported.

Was not able to get it to work. As of October 17th 2013 (R1 Alpha 4.1) The Python version uses all memory, and crashes. 


* * *


#6. Fundamentals

Raise uses a specific format to show messages to the user. It prints what it is going to do. Then when it is done, it prints an emoticon for success, warning, or failure. By using this format, it should be easy for anyone to quickly tell if everything is okay or not.

For example this prints out "Building C++ program 'main.exe' ..." when it starts. Then prints a ":)" when it is successful.

    Building C++ program 'main.exe' ...   :)

##6.1. Emoticons

:) - A green smile represents success. This is used when a command has a return code of zero, and has nothing printed to stderr.

:\ - A yellow half smile represents success with a warning. This is used when a command has a return code of zero, but has something printed to stderr.

:( - A red frown represents failure. This is used when a command has a return code that is not zero.

##6.2. Running functions that must succeed

Using the Process.do_on_fail_exit function, it will print the message, run the function, and print the failure message if the function raises an error. When the function is_broken throws an exception, the script prints the failure message then exits.

	def is_broken():
		raise Exception('broken')

	def is_not_broken():
		pass

	Process.do_on_fail_exit(
		"Running is_not_broken", 
		"It failed", 
		is_not_broken)

	Process.do_on_fail_exit(
		"Running is_broken", 
		"It failed", 
		is_broken)

Running that code will produce this result:

    Running is_not_broken ...                                                   :)
    Running is_broken ..........................................................:(
    It failed Exiting ...


##6.3. Running functions that may fail

If you do not want the script to exit when the function is_broken throws an exception, you can use the Process.do_on_fail_pass function. It will ignore any exceptions raised by the functions.

	def is_broken():
		raise Exception('broken')

	def is_not_broken():
		pass


	Process.do_on_fail_pass("Running is_not_broken", is_not_broken)

	Process.do_on_fail_pass("Running is_broken", is_broken)

Running that code will produce this result:

    Running is_not_broken ...                                                   :)
    Running is_broken ...                                                       :)

##6.4. Running commands that must succeed
##6.5. Running commands that may fail
##6.6. Running commands and printing the result

If you want to run a command and have its result printed, you can use the Process.run_print convenience function.

	Process.run_print("uptime")

Produces the result:

    Running command ...                                                         :)
    uptime
    17:15:09 up  3:43,  4 users,  load average: 0.12, 0.13, 0.14

##6.7. Running commands and getting the result

