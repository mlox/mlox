# Installing and running Perl command-line programs on Windows

Some of the utilities for this project ([tes3lint](Tes3lint), [tes3cmd](Tes3cmd)) are command-line programs written the programming language Perl and need to have Perl installed in order to work. If you are unfamiliar with Perl or with using Perl command-line scripts on Windows, this page will help get you started.

## Download and install Perl

I recommend [strawberry Perl](http://strawberryperl.com/), but ActiveState's Active Perl should work too. The first step is to just download the installer, run it and let it install Perl. These instructions assume you install Strawberry Perl to the default location (C:\strawberry), but you are welcome to install any version of Perl to any location you like, you'll just have to translate the rest of the instructions on this page to suit your choice.

## Open a terminal window

From the Start menu, choose `Start -> Run -> cmd.exe`, this should pop up a window containing a command-line prompt.

## Check that perl is in your PATH
 When you run a command line program in Windows, it uses the environment variable %PATH% to find where the exe lives so it can run it. When you install Strawberry Perl, it is supposed to put itself in your path. You can test this by executing this command line in a terminal window:

    echo %PATH%

You should see the following string somewhere in the output: C:\strawberry\c\bin;C:\strawberry\perl\bin

(The perl.exe lives in C:\strawberry\perl\bin)

If you do not, you may need to restart your system after installing Strawberry Perl. If you still do not see it in your PATH, you can set it from the Control Panel (for XP this would be):

`Start -> Settings -> Control Panel -> System -> Advanced -> Environment Variables`

Select the environment variable "Path" (or create one if you have to), then "edit" it and set the value to: `C:\strawberry\c\bin;C:\strawberry\perl\bin`

## Now try running one of the perl utilities

    perl tes3cmd help

If you were successful, this will print out the basic usage for this command. If you were unsuccessful, let's forget about the PATH, and just use the fully qualified pathname for perl:

    C:\strawberry\perl\bin\perl tes3cmd help

# Using a batch file "wrapper" to make the command more convenient

[tes3lint](Tes3lint) comes with some batch files "wrappers" that are intended to give you an idea on how to run the command, and to make it a little easier. Instead of having to type this command:

    perl tes3lint -a .....

You can just type this:

    tes3lintfull ...

Or, you may even want to create your own .bat file to run the command with the command line options you prefer and use that instead.

Let's make a batch file for tes3cmd to dump a plugin as text output. Create a file called dumpplug.bat in notepad containing:

    perl tes3cmd dump %1 > tes3cmd_dump.log
    more tes3cmd_dump.log
    pause

This will run tes3cmd to dump the contents of a plugin in readable (more or less) format, and use the "more" command to show a page at a time. The output is also stored in the file "tes3cmd_dump.log". You may need to substitute the complete path to Perl for "perl" if the perl.exe is not in your PATH. And you may need to substitute the complete path to tes3cmd for "tes3cmd" if it is not in the same directory as your new "dumpplug.bat".

# Using a shortcut for drag and drop

Now, if you are tired of running things from the command line, you can create a shortcut to one of the .bat files mentioned in the previous step. Just select the batch file in the Windows file system explorer, right click and choose "Create Shortcut". Now you can drag a plugin icon onto the shortcut icon, and it will process it and print its output, and you do not have to use the command line.

If you create a shortcut to the batch file you created in the previous step (dumpplug.bat), then all you need to do to generate a dumped output of the plugin is to drag the plugin onto the shortcut icon.

* * *

I hope that gets you started with Perl command line programs!
