<!DOCTYPE html>

<html xmlns="http://www.w3.org/1999/xhtml" >
	<head>
		<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
		<title>Raise 0.3 Documentation</title>
		<link type="text/css" rel="Stylesheet" href="styles.css" />
		<link href="themes/obsidian.css" rel="stylesheet" type="text/css" media="screen" />
	</head>

	<body>

<h1>Raise 0.3 Documentation</h1>

<p>
A small build automation tool that ships with your software.
<p>

<p>
&copy; 2014 <a href="#authors_and_copyright">Raise Authors</a>
</p>

<p>
Last updated on January 12th 2014
</p>

<p>
<a href=https://launchpad.net/raise">https://launchpad.net/raise</a>
</p>


<hr />


<h3>Table of Contents</h3>

<ol>
	<li><a href="#introduction">Introduction</a></li>
	<ol>
		<li><a href="#license">License
		<li><a href="#authors_and_copyright">Authors and Copyright</a></li>
		<li><a href="#contact_and_bugs">Contact and Bugs</a></li>
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
	</ol>
	<li><a href="#fundamentals">Fundamentals</a></li>
	<ol>
		<li><a href="#emoticons">Emoticons</a></li>
	</ol>
	<li><a href="#basics">Basics</a></li>
	<ol>
		<li><a href="#functions_that_must_succeed">Functions that must succeed</a></li>
		<li><a href="#functions_that_may_fail">Functions that may fail</a></li>
		<li><a href="#commands_that_must_succeed">Commands that must succeed</a></li>
		<li><a href="#commands_that_may_fail">Commands that may fail</a></li>
		<li><a href="#commands_and_printing_the_result">Commands and printing the result</a></li>
		<li><a href="#commands_and_getting_the_result">Commands and getting the result</a></li>
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
		<li><span class="fixme">FIXME</span></li>
	</ol>
	<li><a href="#c++">C++</a></li>
	<ol>
		<li><span class="fixme">FIXME</span></li>
	</ol>
	<li><a href="#d">D</a></li>
	<ol>
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
<h2>1.1 License</h2>

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
Fully supported and developed primarily on Linux. Tested primarily on Ubuntu, Debian, Linux Mint, Fedora, and Centos.
</p>

<a id="freebsd_support"></a>
<h2>5.2. FreeBSD</h2>

<p>
Fully supported.
</p>

<a id="windows_support"></a>
<h2>5.3. Windows</h2>

<p>
Partially supported. Tested on Windows XP, and 7. There are still issues with building and finding C/C++ libraries on Windows. It is recommended that Windows users use Cygwin.
</p>

<a id="cygwin_support"></a>
<h2>5.4. Cygwin</h2>

<p>
Fully Supported.
</p>

<a id="os_x_support"></a>
<h2>5.5. OS X</h2>

<p>
Not supported or tested. 
</p>

<p>
As of November 2nd 2013 there is no way to purchase OS X 10.9 without using the Mac App Store (running on OS X only), or buying dedicated hardware. I will not be fixing this until Apple allows me to buy a full install disk of the current release, and install it in a virtual machine without hacks.
</p>

<p>
If other contributors want to donate a machine, or add this feature themselves, they are welcome to do it.
</p>

<a id="open_indiana_support"></a>
<h2>5.6. Open Indiana</h2>

<p>
Not supported.
</p>

<p>
Was not able to get it to work. As of October 17th 2013 (oi_151a_prestable8) 
they are still 
<a href="http://wiki.openindiana.org/oi/Compiler+Migration">migrating from SunStudio</a> 
to GCC/Clang. A basic C/C++ "Hello World" program does not compile. 
</p>

<a id="haiku_support"></a>
<h2>5.7. Haiku</h2>

<p>
Not supported.
</p>

<p>
Was not able to get it to work. As of October 17th 2013 (R1 Alpha 4.1) The 
Python version uses all memory, and crashes. 
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


<a id="file_system"></a>
<h1>8. File System</h1>

<a id="fs_change_dir"></a>
<h2>8.1. Change Dir</h2>

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
<h2>8.2. Move File</h2>

	<p>
	<span class="fun">move_file(<span class="arg">source</span>, <span class="arg">dest</span>)</span><br />
	Uses the standard Python <span class="fun">shutil.move</span> function to move the file
	<span class="arg">source</span> to <span class="arg">dest</span>.
	</p>

	<p>
	Example:
	</p>

	<pre><code data-language="python">
FS.move_file('one', 'two'):
	</code></pre>

	<p>
	Example output:
	</p>

	<pre class="raise_output">
Moving the file 'one' to 'two' ...                                           <span class="smile">:)</span>
	</pre>

<a id="fs_copy_file"></a>
<h2>8.3. Copy File</h2>
	def copy_file(source, dest):
	<span class="fixme">FIXME</span>

<a id="fs_copy_new_file"></a>
<h2>8.4. Copy New File</h2>
	def copy_new_file(source, dest):
	<span class="fixme">FIXME</span>

<a id="fs_copy_dir"></a>
<h2>8.5. Copy Dir</h2>
	def copy_dir(source, dest, symlinks = False):
	<span class="fixme">FIXME</span>

<a id="fs_make_dir"></a>
<h2>8.6. Make Dir</h2>
	def make_dir(source, ignore_failure = False):
	<span class="fixme">FIXME</span>

<a id="fs_remove_dir"></a>
<h2>8.7. Remove Dir</h2>
	def remove_dir(name, and_children = False):
	<span class="fixme">FIXME</span>

<a id="fs_remove_file"></a>
<h2>8.9. Remove File</h2>
	def remove_file(name, ignore_failure = False):
	<span class="fixme">FIXME</span>

<a id="fs_remove_binaries"></a>
<h2>8.10. Remove Binaries</h2>
	def remove_binaries(name):
	<span class="fixme">FIXME</span>

<a id="fs_symlink"></a>
<h2>8.11. Symlink</h2>
	def symlink(source, link_name):
	<span class="fixme">FIXME</span>

<hr />


<a id="terminal"></a>
<h1>9. Terminal</h1>


<hr />


<a id="libraries_and_programs"></a>
<h1>10. Libraries and Programs</h1>


<hr />


<a id="C"></a>
<h1>11. C</h1>


<hr />


<a id="c++"></a>
<h1>12. C++</h1>


<hr />


<a id="d"></a>
<h1>13. D</h1>


<hr />


<a id="c_sharp"></a>
<h1>14. C#</h1>


<hr />


<a id="java"></a>
<h1>15. Java</h1>


<hr />


<a id="concurrency"></a>
<h1>16. Concurrency</h1>


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

