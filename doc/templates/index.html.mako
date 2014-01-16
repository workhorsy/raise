<!DOCTYPE html>

<html xmlns="http://www.w3.org/1999/xhtml" >
	<head>
		<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
		<title>Raise Documentation 0.3</title>
		<link type="text/css" rel="Stylesheet" href="styles.css" />
		<link href="themes/obsidian.css" rel="stylesheet" type="text/css" media="screen" />
	</head>

	<body>

<h1 class="header">Raise Documentation 0.3</h1>

<p>
A small build automation tool that ships with your software.
<p>

<p>
Copyright &copy; 2014 <a href="#authors_and_copyright">Raise Authors</a>
</p>

<p>
Last updated on January 14th 2014
</p>

<p>
<a href="https://launchpad.net/raise" target="_blank" rel="external">https://launchpad.net/raise</a>
</p>


<hr />


<h3>Table of Contents</h3>

<ol>
	<li><a href="#introduction">Introduction</a></li>
	<ol>
		<li><a href="#license">License
		<li><a href="#authors_and_copyright">Authors and Copyright</a></li>
		<li><a href="#contact_and_bugs">Contact and Bugs</a></li>
		<li><a href="#documentation">Documentation</a></li>
		<li><a href="#philosophy">Philosophy</a></li>
		<li><a href="#goals">Goals</a></li>
	</ol>
	<li><a href="#installation">Installation</a></li>
	<ol>
		<li><span class="fixme">FIXME</span></li>
	</ol>
	<li><a href="#command_line_arguments">Command Line Arguments</a></li>
	<ol>
		<li><span class="fixme">FIXME</span></li>
	</ol>
	<li><a href="#supported_languages">Supported Languages</a></li>
	<ol>
		<li><a href="#c_and_c++_support">C/C++</a></li>
		<li><a href="#d_support">D</a></li>
		<li><a href="#c_sharp_support">C#</a></li>
		<li><a href="#java_support">Java</a></li>
	</ol>
	<li><a href="#operating_system_support">Operating System Support</a></li>
	<ol>
		<li><a href="#linux_support">Linux</a></li>
		<li><a href="#freebsd_support">FreeBSD</a></li>
		<li><a href="#windows_support">Windows</a></li>
		<li><a href="#cygwin_support">Cygwin</a></li>
		<li><a href="#os_x_support">OS X</a></li>
		<li><a href="#open_indiana_support">Open Indiana</a></li>
		<li><a href="#haiku_support">Haiku</a></li>
		<li><a href="#mobile_support">Android, iOS, Chrome OS</a></li>
	</ol>
	<li><a href="#fundamentals">Fundamentals</a></li>
	<ol>
		<li><a href="#emoticons">Emoticons</a></li>
		<li><a href="#file_extensions">File Extensions</a></li>
	</ol>
	<li><a href="#basics">Basics</a></li>
	<span class="fixme">FIXME</span>: Change these to be generated by scripts.
	<ol>
		<li><a href="#functions_that_must_succeed">Functions that must succeed</a></li>
		<li><a href="#functions_that_may_fail">Functions that may fail</a></li>
		<li><a href="#commands_that_must_succeed">Commands that must succeed</a></li>
		<li><a href="#commands_that_may_fail">Commands that may fail</a></li>
		<li><a href="#commands_and_printing_the_result">Commands and printing the result</a></li>
		<li><a href="#commands_and_getting_the_result">Commands and getting the result</a></li>
	</ol>
	<li><a href="#users">Users</a></li>
	<ol>
		<li><a href="#users_running_as_root">Running as Root</a></li>
		<li><a href="#users_running_as_a_normal_user">Running as a Normal User</a></li>
		<li><a href="#users_privilege_escalation">Privilege Escalation</a></li>
		<li><a href="#users_user_name">User Name</a></li>
		<li><a href="#users_user_id">User ID</a></li>
	</ol>
	<li><a href="#file_system">File System</a></li>
	<ol>
		<li><a href="#fs_change_dir">change_dir</a></li>
		<li><a href="#fs_move_file">move_file</a></li>
		<li><a href="#fs_copy_file">copy_file</a></li>
		<li><a href="#fs_copy_new_file">copy_new_file</a></li>
		<li><a href="#fs_copy_dir">copy_dir</a></li>
		<li><a href="#fs_make_dir">make_dir</a></li>
		<li><a href="#fs_remove_dir">remove_dir</a></li>
		<li><a href="#fs_remove_file">remove_file</a></li>
		<li><a href="#fs_remove_binaries">remove_binaries</a></li>
		<li><a href="#fs_symlink">symlink</a></li>
	</ol>
	<li><a href="#terminal">Terminal</a></li>
	<ol>
		<li><span class="fixme">FIXME</span></li>
	</ol>
	<li><a href="#libraries_and_programs">Libraries and Programs</a></li>
	<ol>
		<li><span class="fixme">FIXME</span></li>
	</ol>
	<li><a href="#c">C</a></li>
	<ol>
		<li><a href="#c_file_extensions">File Extensions</a></li>
		<li><a href="#c_compilers">Compilers</a></li>
		<li><a href="#c_compiler_setup">Compiler Setup</a></li>
		<li><a href="#c_building_object">Building Object</a></li>
		<li><a href="#c_building_program">Building Program</a></li>
		<li><a href="#c_building_shared_library">Building Shared Library</a></li>
		<li><a href="#c_program_installation">Program Installation</a></li>
		<li><a href="#c_uninstall_program">Program Uninstallation</a></li>
		<li><a href="#c_library_installation">Library Installation</a></li>
		<li><a href="#c_library_uinstallation">Library Uninstallation</a></li>
		<li><a href="#c_header_installation">Header Installation</a></li>
		<li><a href="#c_header_uinstallation">Header Uninstall</a></li>
		<li><a href="#c_running_and_printing">Running and Printing</a></li>
	</ol>
	<li><a href="#c++">C++</a></li>
	<ol>
		<li><span class="fixme">FIXME</span></li>
	</ol>
	<li><a href="#d">D</a></li>
	<ol>
		<li><a href="#d_file_extensions">File Extensions</a></li>
		<li><span class="fixme">FIXME</span></li>
	</ol>
	<li><a href="#c_sharp">C#</a></li>
	<ol>
		<li><span class="fixme">FIXME</span></li>
	</ol>
	<li><a href="#java">Java</a></li>
	<ol>
		<li><span class="fixme">FIXME</span></li>
	</ol>
	<li><a href="#concurrency">Concurrency</a></li>
	<ol>
		<li><span class="fixme">FIXME</span></li>
	</ol>
</ol>


<hr />


<a id="introduction"></a>
<h1>1. Introduction</h1>

<a id="license"></a>
<h2>1.1. License</h2>

<p>
Raise is licensed as freely as posible, in the hopes that it will be 
compatible with most other software licenses.
</p>

<p>
The Raise software is licensed under 
<a href="http://bazaar.launchpad.net/~workhorsy/raise/main/view/head:/LICENSE" target="_blank" rel="external">The MIT License</a>
.
</p>

<p>
The Raise documentation is license under
<a href="http://creativecommons.org/licenses/by/3.0" target="_blank" rel="external">The Creative Commons Attribution License v3.0</a>
.
</p>

<a id="authors_and_copyright"></a>
<h2>1.2. Authors and Copyright</h2>

<p>
&copy; 2013 - 2014 Matthew Brennan Jones <a href="mailto:mattjones@workhorsy.org">&lt;mattjones@workhorsy.org&gt;</a>
</p>

<p>
Other authors please add your copyright and contact info here.
</p>

<a id="contact_and_bugs"></a>
<h2>1.3. Contact and Bugs</h2>

<p>
If you find any errors, bugs, or misinformation, please report a bug at 
<a href="https://launchpad.net/raise">https://launchpad.net/raise</a> or 
contact one of the authors.
</p>


<a id="documentation"></a>
<h2>1.4. Documentation</h2>

<p>
	Documentation is provided in the doc/index.html file. It is generated 
	from the <a href="http://makotemplates.org" target="_blank"rel="external">Python Mako Template</a> 
	file doc/templates/index.html.mako.
</p>

<p>
	Warning! Because Raise uses scripts to generate the documentation, you 
	won't be able to generate the documentation unless you have all the compilers and
	tools installed.
</p>

<p>
To generate the index.html file you can run:
</p>

<pre><code data-language="shell">
python generate_documentation.py
</code></pre>

<p>
	Any changes should be added to the index.html.mako file, as it will 
	whipe out any changes in index.html when generate_documentation.py 
	is run.
</p>


<a id="philosophy"></a>
<h2>1.5. Philosophy</h2>

<p>
The philosophy of Raise is that it says what it is doing. Not how
 it is doing it. It only shows the details when something goes wrong. 
That way the build output does not fill with information you 
don't need. It shows the output for each step of the build 
process, as its own line.
</p>

<a id="goals"></a>
<h2>1.6. Goals</h2>

<p>
	<ol>
		<li>Should be fast for incremental and clean builds, even with 10,000 of files.</li>
		<li>Should be able to automatically find libraries and programs.</li>
		<li>Should work with Python instead of creating its own language or using a graph.</li>
		<li>Should run without needing to be installed.</li>
		<li>Should be small enough to include in your VCS and ship with your software.</li>
		<li>Should not require any external dependencies, libraries, or tools.</li>
		<li>Should do everything implicitly instead of explicitly.</li>
		<li>Should work consistently across platforms.</li>
		<li>Should be easy to do things sequentially or concurrently.</li>
		<li>Should present output in a uniform and intuitive way.</li>
	</ol>
</p>


<hr />


<a id="installation"></a>
<h1>2. Installation</h1>


<hr />

<a id="command_line_arguments"></a>
<h1>3. Command Line Arguments</h1>


<hr />


<a id="supported_languages"></a>
<h1>4. Supported Languages</h1>

<a id="c_and_c++_support"></a>
<h2>4.1. C/C++</h2>

<p>
C and C++ are fully supported with GCC, and CLang. MS cl.exe support is not yet complete.
</p>

<a id="d_support"></a>
<h2>4.2. D</h2>

<p>
D is fully supported with DMD and LDC.
</p>

<a id="c_sharp_support"></a>
<h2>4.3. C#</h2>

<p>
C# works with Mono and MS .NET. Some advanced features such as installing into the GAC have not been implemented.
</p>

<a id="java_support"></a>
<h2>4.4. Java</h2>

<p>
Java works with OpenJDK 7.
</p>


<hr />


<a id="operating_system_support"></a>
<h1>5. Operating System Support</h1>

<a id="linux_support"></a>
<h2>5.1. Linux</h2>

<p>
Fully supported.
</p>

<p>
Primarily developed on Linux with kernel 2.6 and greater. 
Tested primarily on 
<a href="http://ubuntu.com" target="_blank" rel="external">Ubuntu</a>, 
<a href="http://debian.org" target="_blank" rel="external">Debian</a>, 
<a href="http://linuxmint.com" target="_blank" rel="external">Linux Mint</a>, 
<a href="http://fedoraproject.org" target="_blank" rel="external">Fedora</a>, and 
<a href="http://centos.org" target="_blank" rel="external">Centos</a>. It should 
"just work" on other Linux distros.
</p>

<a id="freebsd_support"></a>
<h2>5.2. FreeBSD</h2>

<p>
Fully supported.
</p>

<p>
Has not yet been tested on other BSDs such as OpenBSD, NetBSD, or DragonflyBSD.
</p>

<p>
<a href="http://freebsd.org" target="_blank" rel="external">FreeBSD</a>
</p>

<a id="windows_support"></a>
<h2>5.3. Windows</h2>

<p>
Partially supported.
</p>

<p>Tested on 
<a href="http://en.wikipedia.org/wiki/Windows_XP" target="_blank" rel="external">Windows XP</a>, and 
<a href="http://en.wikipedia.org/wiki/Windows_7" target="_blank" rel="external">Windows 7</a>. 
There are still issues with 
building and finding C/C++ libraries on Windows. It is recommended 
that Windows users use Cygwin.
</p>

<p>
Has not been tested on Windows 8 or Windows RT.
</p>

<a id="cygwin_support"></a>
<h2>5.4. Cygwin</h2>

<p>
Fully Supported.
</p>

<p>
<a href="http://cygwin.com" target="_blank" rel="external">Cygwin</a>
</p>

<a id="os_x_support"></a>
<h2>5.5. OS X</h2>

<p>
Not supported or tested. 
</p>

<p>
As of November 2nd 2013 there is no way to purchase OS X 10.9 without using 
the Mac App Store (running on OS X only), or buying dedicated hardware. 
I will not be fixing this until Apple allows me to buy a full install disk 
of the current release, and install it in a virtual machine without hacks.
</p>

<p>
If other contributors want to donate a machine, or add this feature 
themselves, they are welcome to do it.
</p>

<p>
<a href="http://en.wikipedia.org/wiki/OS_X" target="_blank" rel="external">OS X</a>
</p>

<a id="open_indiana_support"></a>
<h2>5.6. Open Indiana</h2>

<p>
Not supported.
</p>

<p>
Was not able to get it to work. As of October 17th 2013 (oi_151a_prestable8) 
they are still 
<a href="http://wiki.openindiana.org/oi/Compiler+Migration" target="_blank" rel="external">migrating from SunStudio</a> 
to GCC/Clang. A basic C/C++ "Hello World" program does not compile. 
</p>

<p>
<a href="http://openindiana.org" target="_blank" rel="external">Open Indiana</a>
<p>

<a id="haiku_support"></a>
<h2>5.7. Haiku</h2>

<p>
Not supported.
</p>

<p>
Was not able to get it to work. As of October 17th 2013 (R1 Alpha 4.1) The 
Python version uses all memory, and crashes. 
</p>

<p>
<a href="https://haiku-os.org" target="_blank" rel="external">Haiku</a>
<p>


<a id="mobile_support"></a>
<h2>5.8. Android, iOS, Chrome OS</h2>

<p>
Not supported.
</p>

<p>
None of the mobile OSes are supported. They either do not support the required 
compilers, or are locked down too tightly to use. Hopefully this will change in 
the future.
</p>


<hr />


<a id="fundamentals"></a>
<h1>6. Fundamentals</h1>

<p>
Raise uses a specific format to show messages to the user. It prints what it 
is going to do. Then when it is done, it prints an emoticon for success, 
warning, or failure. By using this format, it should be easy for anyone to 
quickly tell if everything is okay or not.
</p>

<p>
For example this prints out "Building C++ program 'main.exe' ..." when it 
starts. Then prints a "<span class="smile">:)</span>" when it is successful.
</p>

<pre class="raise_output">
Building C++ program 'main.exe' ...   <span class="smile">:)</span>
</pre>

<a id="emoticons"></a>
<h2>6.1. Emoticons</h2>

<code>
<p>
<span class="smile">:)</span> - A green smile represents success. This is used when a command has a return code of zero, and has nothing printed to stderr.
</p>

<p>
<span class="normal">:\</span> - A yellow half smile represents success with a warning. This is used when a command has a return code of zero, but has something printed to stderr.
</p>

<p>
<span class="frown">:(</span> - A red frown represents failure. This is used when a command has a return code that is not zero.
</p>

</code>


<a id="file_extensions"></a>
<h2>6.2. File Extensions</h2>

<p>
One of the huge issue in dealing with differnt platforms, is how they handle file 
extensions. Many have different extensions for the same type of file. For example
Windows typically uses .exe for executable, and .obj for object. While Linux 
typically uses no extension for executable, and .o for object.
</p>

<p>
Raise gets around this by having its own list of file extensions and mapping 
them to the native type for that Operating System.
</p>

<p>
For example when building a C program you would say:
</p>

<pre><code data-language="python">
C.build_program('main.exe', ['main.c'])
</code></pre>

<p>
On Windows it will create "main.exe", but on Linux it will create "main".
</p>

<p>
To see the mappings, look at the section for each language.
</p>


<hr />


<a id="basics"></a>
<h1>7. Basics</h1>

<a id="functions_that_must_succeed"></a>
<h2>7.1. Functions that must succeed</h2>

<p>
Using the Process.do_on_fail_exit function, it will print the message, run the 
function, and print the failure message if the function raises an error. When 
the function is_broken throws an exception, the script prints the failure 
message then exits.
</p>

<pre><code data-language="python">
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
</code></pre>

<p>
Running that code will produce this result:
</p>

<pre class="raise_output">
    Running is_not_broken ...                                                   <span class="smile">:)</span>
    Running is_broken ..........................................................<span class="frown">:(</span>
    It failed Exiting ...
</pre>

<a id="functions_that_may_fail"></a>
<h2>7.2. Functions that may fail</h2>

<p>
If you do not want the script to exit when the function is_broken throws an 
exception, you can use the Process.do_on_fail_pass function. It will ignore 
any exceptions raised by the functions.
</p>

<pre><code data-language="python">
	def is_broken():
		raise Exception('broken')

	def is_not_broken():
		pass


	Process.do_on_fail_pass("Running is_not_broken", is_not_broken)

	Process.do_on_fail_pass("Running is_broken", is_broken)
</code></pre>

<p>
Running that code will produce this result:
</p>

<pre class="raise_output">
    Running is_not_broken ...                                                   <span class="smile">:)</span>
    Running is_broken ...                                                       <span class="smile">:)</span>
</pre>

<a id="commands_that_must_succeed"></a>
<h2>7.3. Commands that must succeed</h2>

<a id="commands_that_may_fail"></a>
<h2>7.4. Commands that may fail</h2>

<a id="commands_and_printing_the_result"></a>
<h2>7.5. Commands and printing the result</h2>

<p>
If you want to run a command and have its result printed, you can use the 
Process.run_print convenience function.
</p>

<pre><code data-language="python">
	Process.run_print("uptime")
</code></pre>

<p>
Produces the result:
</p>

<pre class="raise_output">
    Running command ...                                                         <span class="smile">:)</span>
    uptime
    17:15:09 up  3:43,  4 users,  load average: 0.12, 0.13, 0.14
</pre>

<a id="commands_and_getting_the_result"></a>
<h2>7.6. Commands and getting the result</h2>


<hr />



<a id="users"></a>
<h1>8. Users</h1>

<a id="users_running_as_root"></a>
<h2>8.1. Running as Root</h2>

	<p>
	If you want to ensure that a script is run as root. You can use the
	<span class="fun">OS.require_root</span> function. If the script is not
	run as root, it will print an error and exit.
	</p>

	<p>
	Example:
	</p>

	<pre><code data-language="python">
${template_info['users_running_as_root']['example']}
	</code></pre>

	<p>
	Example output when run as root:
	</p>

	<pre class="raise_output">
Effective user id: 0
	</pre>

	<p>
	Example output when NOT run as root:
	</p>

	<pre class="raise_output">
Effective user id: 1000
<span class="failure">Must be run as root. Exiting ...</span>
	</pre>


<a id="users_running_as_a_normal_user"></a>
<h2>8.2. Running as a Normal User</h2>

	<p>
	If you want to ensure that a script is run as a normal user, you can 
	use the <span class="fun">OS.require_not_root</span> function. If the
	script is run as root, it will print an error and exit.
	</p>

	<p>
	Example output when run as root:
	</p>

	<pre class="raise_output">
Effective user id: 0
<span class="failure">Must not be run as root. Exiting ...</span>
	</pre>

	<p>
	Example output when NOT run as root:
	</p>

	<pre class="raise_output">
Effective user id: 1000
	</pre>


<a id="users_privilege_escalation"></a>
<h2>8.3. Privilege Escalation</h2>

	<p>
	Often you will need do some actions as root, and others as a normal user, 
	all in the same script. A common example is to compile a program as a 
	normal user, then install it as root. You can do this by running the 
	script as root, then using the function 
	<span class="fun">OS.do_as_normal_user</span>
	to temporarily step down as a normal user.
	</p>

	<p>
	Example:
	</p>

	<pre><code data-language="python">
${template_info['users_privilege_escalation']['example']}
	</code></pre>

	<p>
	Example output:
	</p>

	<pre class="raise_output">
Effective user id: 0
Effective user id: 1000
Effective user id: 0
	</pre>


<a id="users_user_name"></a>
<h2>8.4. User Name</h2>

	<p>
	When running a script with a privilege escalation tool such as 
	<span class="fun">sudo</span>, you often need to get the actual user
	name. Most python functions such as 
	<span class="fun">getpass.getuser</span> 
	will return 'root', because it is actually being run as root. To get
	the actual user name, you can use the 
	<span class="fun">OS.get_normal_user_name</span> function.
	</p>

	<p>
	Example:
	</p>

	<pre><code data-language="python">
${template_info['users_user_name']['example']}
	</code></pre>

	<p>
	Example output when NOT run as root:
	</p>

	<pre class="raise_output">
Current user name: matt
Normal user name: matt
	</pre>

	<p>
	Example output when run as root:
	</p>

	<pre class="raise_output">
Current user name: root
Normal user name: matt
	</pre>

<a id="users_user_id"></a>
<h2>8.5. User ID</h2>

	<p>
	When running a script with a privilege escalation tool such as 
	<span class="fun">sudo</span>, you often need to get the actual user
	name. Most python functions such as 
	<span class="fun">os.getuid</span> and 
	<span class="fun">os.geteuid</span> will return 0, because it is
	actually being run as root.
	</p>

	<p>
	Example output when NOT run as root:
	</p>

	<pre class="raise_output">
Current user id: 1000
Normal user id: 1000
	</pre>

	<p>
	Example output when run as root:
	</p>

	<pre class="raise_output">
Current user id: 0
Normal user id: 1000
	</pre>


<hr />


<a id="file_system"></a>
<h1>9. File System</h1>

<a id="fs_change_dir"></a>
<h2>9.1. Change Dir</h2>

	<p>
	<span class="fun">change_dir(<span class="arg">name</span>)</span><br />
		Uses the standard Python <span class="fun">os.chdir</span> 
	function to change to the <span class="arg">name</span> directory.
	</p>

	<p>
	Example:
	</p>

	<pre><code data-language="python">
${template_info['fs_change_dir']['example']}
	</code></pre>

	<p>
	Example output:
	</p>

	<pre class="raise_output">
${template_info['fs_change_dir']['output']}
	</pre>

<a id="fs_move_file"></a>
<h2>9.2. Move File</h2>

	<p>
	<span class="fun">move_file(<span class="arg">source</span>, <span class="arg">dest</span>)</span><br />
	Uses the standard Python <span class="fun">shutil.move</span> function to move the file
	<span class="arg">source</span> to <span class="arg">dest</span>.
	</p>

	<p>
	Example:
	</p>

	<pre><code data-language="python">
${template_info['fs_move_file']['example']}
	</code></pre>

	<p>
	Example output:
	</p>

	<pre class="raise_output">
${template_info['fs_move_file']['output']}
	</pre>

<a id="fs_copy_file"></a>
<h2>9.3. Copy File</h2>
	<p>
	<span class="fun">copy_file(<span class="arg">source</span>, <span class="arg">dest</span>)</span><br />
	Uses the standard Python <span class="fun">shutil.copy2</span> function to copy the file
	<span class="arg">source</span> to <span class="arg">dest</span>.
	</p>

	<p>
	Example:
	</p>

	<pre><code data-language="python">
${template_info['fs_copy_file']['example']}
	</code></pre>

	<p>
	Example output:
	</p>

	<pre class="raise_output">
${template_info['fs_copy_file']['output']}
	</pre>

<a id="fs_copy_new_file"></a>
<h2>9.4. Copy New File</h2>
	<p>
	<span class="fun">copy_new_file(<span class="arg">source</span>, <span class="arg">dest</span>)</span><br />
	Copies the file only if <span class="arg">dest</span> does not exist, or <span class="arg">source</span> is
	different from <span class="arg">dest</span>.
	</p>

	<p>
	Example:
	</p>

	<pre><code data-language="python">
${template_info['fs_copy_new_file']['example']}
	</code></pre>

	<p>
	Example output:
	</p>

	<pre class="raise_output">
${template_info['fs_copy_new_file']['output']}
	</pre>

<a id="fs_copy_dir"></a>
<h2>9.5. Copy Dir</h2>
	<p>
	<span class="fun">copy_dir(<span class="arg">source</span>, <span class="arg">dest</span>, <span class="arg">symlinks</span> = False)</span><br />
	Uses the standard Python <span class="fun">shutil.copytree</span> function to recursively copy 
	the directory from <span class="arg">source</span> to <span class="arg">dest</span>. If
	<span class="arg">symlinks</span> is True, symlinks remail links. If symlinks is False the links 
	are replaced with copies of the actual data.
	</p>

	<p>
	Example:
	</p>

	<pre><code data-language="python">
${template_info['fs_copy_dir']['example']}
	</code></pre>

	<p>
	Example output:
	</p>

	<pre class="raise_output">
${template_info['fs_copy_dir']['output']}
	</pre>

<a id="fs_make_dir"></a>
<h2>9.6. Make Dir</h2>
	<p>
	<span class="fun">make_dir(<span class="arg">source</span>, <span class="arg">ignore_failure</span> = False)</span><br />
	Uses the standard Python <span class="fun">os.mkdir</span> function to make the 
	directory <span class="arg">source</span>. If <span class="arg">ignore_failure</span> 
	is False, any errors will be ignored.
	</p>

	<p>
	Example:
	</p>

	<pre><code data-language="python">
${template_info['fs_make_dir']['example']}
	</code></pre>

	<p>
	Example output:
	</p>

	<pre class="raise_output">
${template_info['fs_make_dir']['output']}
	</pre>

<a id="fs_remove_dir"></a>
<h2>9.7. Remove Dir</h2>
	<p>
	<span class="fun">remove_dir(<span class="arg">name</span>, <span class="arg">and_children</span> = False)</span><br />
	Uses the standard Python <span class="fun">shutil.rmtree</span> function to remove the 
	directory <span class="arg">name</span>. If <span class="arg">name</span> is the current 
	directory, it will display an error. If <span class="arg">and_children</span> 
	is True it will remove any child directories.
	</p>

	<p>
	Example:
	</p>

	<pre><code data-language="python">
${template_info['fs_remove_dir']['example']}
	</code></pre>

	<p>
	Example output:
	</p>

	<pre class="raise_output">
${template_info['fs_remove_dir']['output']}
	</pre>

<a id="fs_remove_file"></a>
<h2>9.8. Remove File</h2>
	<p>
	<span class="fun">remove_file(<span class="arg">name</span>, <span class="arg">ignore_failure</span> = False)</span><br />
	Uses the standard Python <span class="fun">os.rmdir</span> function to remove the 
	file <span class="arg">name</span>. If <span class="arg">ignore_failure</span> 
	is True it will ignore any errors.
	</p>

	<p>
	Example:
	</p>

	<pre><code data-language="python">
${template_info['fs_remove_file']['example']}
	</code></pre>

	<p>
	Example output:
	</p>

	<pre class="raise_output">
${template_info['fs_remove_file']['output']}
	</pre>

<a id="fs_remove_binaries"></a>
<h2>9.9. Remove Binaries</h2>
	<p>
	<span class="fun">remove_binaries(<span class="arg">name</span>)</span><br />
	Will remove any files that start with <span class="arg">name</span>, and have the 
	extensions .exe, .o, .obj, .so, .a, .dll, .lib, .pyc, .exe.mdb, .dll.mdb, 
	.jar, .class.
	</p>

	<p>
	Example:
	</p>

	<pre><code data-language="python">
${template_info['fs_remove_binaries']['example']}
	</code></pre>

	<p>
	Example output:
	</p>

	<pre class="raise_output">
${template_info['fs_remove_binaries']['output']}
	</pre>

<a id="fs_symlink"></a>
<h2>9.10. Symlink</h2>
	<p>
	<span class="fun">symlink(<span class="arg">source</span>, <span class="arg">link_name</span>)</span><br />
	Uses the standard Python <span class="fun">os.symlink</span> function to create a 
	symlink from <span class="arg">source</span> to <span class="arg">link_name</span>.
	</p>

	<p>
	Example:
	</p>

	<pre><code data-language="python">
${template_info['fs_symlink']['example']}
	</code></pre>

	<p>
	Example output:
	</p>

	<pre class="raise_output">
${template_info['fs_symlink']['output']}
	</pre>

<hr />


<a id="terminal"></a>
<h1>10. Terminal</h1>


<hr />


<a id="libraries_and_programs"></a>
<h1>11. Libraries and Programs</h1>


<hr />


<a id="c"></a>
<h1>12. C</h1>


<a id="c_file_extensions"></a>
<h2>12.1. File Extensions</h2>

	<table>
		<tr>
			<th></th>
			<th>Raise</th>
			<th>Cygwin</th>
			<th>Windows</th>
			<th>Standard</th>
		</tr>
		<tr>
			<td>Executable</td>
			<td>.exe</td>
			<td>.exe</td>
			<td>.exe</td>
			<td></td>
		</tr>
		<tr>
			<td>Object</td>
			<td>.o</td>
			<td>.o</td>
			<td>.obj</td>
			<td>.o</td>
		</tr>
		<tr>
			<td>Shared Library</td>
			<td>.so</td>
			<td>.so</td>
			<td>.dll</td>
			<td>.so</td>
		</tr>
		<tr>
			<td>Static Library</td>
			<td>.a</td>
			<td>.a</td>
			<td>.lib</td>
			<td>.a</td>
		</tr>
	<table>

<a id="c_compilers"></a>
<h2>12.2. Compilers</h2>

	<p>
		Raise supports the GCC, Clang, and MS cl.exe C compilers. The compiler
		 is abstracted away in a gereralized way, as to make it so you don't 
		have to worry about compiler specific functionality.
	</p>

	<p>
		You can select the best C compiler for your platform by
		using the <span class="fun">C.get_default_compiler</span> function.
	</p>

	<p>
		You can also select the compiler specifically by using the 
		<span class="fun">C.c_compilers</span> dictionary. Be careful
		as only compilers that were found by Raise will be in the dictionary.
	</p>

	<p>
	Example:
	</p>

	<pre><code data-language="python">
${template_info['c_compilers']['example']}
	</code></pre>

	<p>
	Example output:
	</p>

	<pre class="raise_output">
${template_info['c_compilers']['output']}
	</pre>

<a id="c_compiler_setup"></a>
<h2>12.3. Compiler Setup</h2>
	<p>
		After the compiler is selected, it can be configured 
		using the properties.
	</p>

	<ul>
		<li>debug: A bool that tells if it should use debugging symbols or not.</li>
		<li>optimize: A bool that tell if it should optimize or not.</li>
		<li>warnings_all: A bool that tells if it should show extra warning information.</li>
		<li>warnings_as_errors: A bool that tells if it should count warnings as errors.</li>
		<li>compile_time_flags: A list of compile time flags/macros/variables.</li>
	</ul>

	<p>
		After the compiler is setup the way you want, the setting MUST be saved in an 
		environmental variable. This is done with the 
		<span class="fun">C.save_compiler</span> function.
	</p>

	<p>
	Example:
	</p>

	<pre><code data-language="python">
${template_info['c_compiler_setup']['example']}
	</code></pre>

	<p>
	Example output:
	</p>

	<pre class="raise_output">
${template_info['c_compiler_setup']['output']}
	</pre>

<a id="c_building_object"></a>
<h2>12.4. Building Object</h2>

	<p>
		C object files can be built using the <span class="fun">C.build_object</span> function.
	</p>

	<p>
	Example:
	</p>

	<pre><code data-language="python">
${template_info['c_building_object']['example']}
	</code></pre>

	<p>
	Example output:
	</p>

	<pre class="raise_output">
${template_info['c_building_object']['output']}
	</pre>

<a id="c_building_program"></a>
<h2>12.5. Building Program</h2>

	<p>
		C programs can be built using the <span class="fun">C.build_program</span> function.
	</p>

	<p>
	Example:
	</p>

	<pre><code data-language="python">
${template_info['c_building_program']['example']}
	</code></pre>

	<p>
	Example output:
	</p>

	<pre class="raise_output">
${template_info['c_building_program']['output']}
	</pre>

<a id="c_building_shared_library"></a>
<h2>12.6. Building Shared Library</h2>

	<p>
		C shared library can be built using the <span class="fun">C.build_shared_library</span> function.
	</p>

	<p>
	Example:
	</p>

	<pre><code data-language="python">
${template_info['c_building_shared_library']['example']}
	</code></pre>

	<p>
	Example output:
	</p>

	<pre class="raise_output">
${template_info['c_building_shared_library']['output']}
	</pre>

<a id="c_program_installation"></a>
<h2>12.7. Program Installation</h2>

	<p>
		C programs can be installed with the <span class="fun">C.install_program</span> function.
	</p>

	<p>
	Example:
	</p>

	<pre><code data-language="python">
${template_info['c_program_installation']['example']}
	</code></pre>

	<p>
	Example output:
	</p>

	<pre class="raise_output">
${template_info['c_program_installation']['output']}
	</pre>

<a id="c_uninstall_program"></a>
<h2>12.8. Program Uninstallation</h2>

	<p>
		fixme
	</p>

	<p>
	Example:
	</p>

	<pre><code data-language="python">
${template_info['c_uninstall_program']['example']}
	</code></pre>

	<p>
	Example output:
	</p>

	<pre class="raise_output">
${template_info['c_uninstall_program']['output']}
	</pre>


<a id="c_library_installation"></a>
<h2>12.9. Library Installation</h2>

	<p>
		fixme
	</p>

	<p>
	Example:
	</p>

	<pre><code data-language="python">
${template_info['c_library_installation']['example']}
	</code></pre>

	<p>
	Example output:
	</p>

	<pre class="raise_output">
${template_info['c_library_installation']['output']}
	</pre>


<a id="c_library_uinstallation"></a>
<h2>12.10. Library Uninstallation</h2>

	<p>
		fixme
	</p>

	<p>
	Example:
	</p>

	<pre><code data-language="python">
${template_info['c_library_uinstallation']['example']}
	</code></pre>

	<p>
	Example output:
	</p>

	<pre class="raise_output">
${template_info['c_library_uinstallation']['output']}
	</pre>


<a id="c_header_installation"></a>
<h2>12.11. Header Installation</h2>

	<p>
		fixme
	</p>

	<p>
	Example:
	</p>

	<pre><code data-language="python">
${template_info['c_header_installation']['example']}
	</code></pre>

	<p>
	Example output:
	</p>

	<pre class="raise_output">
${template_info['c_header_installation']['output']}
	</pre>


<a id="c_header_uinstallation"></a>
<h2>12.12. Header Uninstall</h2>

	<p>
		fixme
	</p>

	<p>
	Example:
	</p>

	<pre><code data-language="python">
${template_info['c_header_uinstallation']['example']}
	</code></pre>

	<p>
	Example output:
	</p>

	<pre class="raise_output">
${template_info['c_header_uinstallation']['output']}
	</pre>


<a id="c_running_and_printing"></a>
<h2>12.13. Running and Printing</h2>

	<p>
		C programs can be ran with the <span class="fun">C.run_print</span> function.
	</p>

	<p>
	Example:
	</p>

	<pre><code data-language="python">
${template_info['c_running_and_printing']['example']}
	</code></pre>

	<p>
	Example output:
	</p>

	<pre class="raise_output">
${template_info['c_running_and_printing']['output']}
	</pre>

<hr />


<a id="c++"></a>
<h1>13. C++</h1>


<hr />


<a id="d"></a>
<h1>14. D</h1>


<a id="d_file_extensions"></a>
<h2>14.1. File Extensions</h2>

	<table>
		<tr>
			<th></th>
			<th>Raise</th>
			<th>Cygwin</th>
			<th>Windows</th>
			<th>Standard</th>
		</tr>
		<tr>
			<td>Executable</td>
			<td>.exe</td>
			<td>.exe</td>
			<td>.exe</td>
			<td></td>
		</tr>
		<tr>
			<td>Object</td>
			<td>.o</td>
			<td>.obj</td>
			<td>.obj</td>
			<td>.o</td>
		</tr>
		<tr>
			<td>Shared Library</td>
			<td>.so</td>
			<td>.dll</td>
			<td>.dll</td>
			<td>.so</td>
		</tr>
		<tr>
			<td>Static Library</td>
			<td>.a</td>
			<td>.lib</td>
			<td>.lib</td>
			<td>.a</td>
		</tr>
	<table>


<hr />


<a id="c_sharp"></a>
<h1>15. C#</h1>


<hr />


<a id="java"></a>
<h1>16. Java</h1>


<hr />


<a id="concurrency"></a>
<h1>17. Concurrency</h1>


<hr />


		<div id="footer">
			&copy; 2014 <a href="#authors_and_copyright">Raise Authors</a>
			<br />
			Raise is licensed under 
			<a href="http://bazaar.launchpad.net/~workhorsy/raise/main/view/head:/LICENSE" target="_blank"rel="external">The MIT License</a>
			<br />
			This website and all documentation are licensed under 
			<a href="http://creativecommons.org/licenses/by/3.0"rel="external">The Creative Commons Attribution License v3.0</a>
		</div>

		<script src="js/rainbow.js"></script>
		<script src="js/language/generic.js"></script>
		<script src="js/language/shell.js"></script>
		<script src="js/language/c.js"></script>
		<script src="js/language/python.js"></script>
	</body>
</html>

