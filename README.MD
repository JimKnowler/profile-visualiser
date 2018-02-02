# Profile-Visualiser

Visualise profile data.

## Screenshots

<div style="width:100%;display:flex;">

![Screenshot 1](https://raw.githubusercontent.com/JimKnowler/profile-visualiser/master/docs/screenshot-1.png "Screenshot 1")

![Screenshot 2](https://raw.githubusercontent.com/JimKnowler/profile-visualiser/master/docs/screenshot-2.png "Screenshot 2")

![Screenshot 3](https://raw.githubusercontent.com/JimKnowler/profile-visualiser/master/docs/screenshot-3.png "Screenshot 3")

</div>

## Requirements

* Python2.7 (tested with win32)
* [PyGTK](http://www.pygtk.org/downloads.html)
  * On Windows, I would recommend the '[all-in-one installer](http://ftp.gnome.org/pub/GNOME/binaries/win32/pygtk/2.24/)'
* Tested on Windows 7, but would also expect this to run on Linux/MacOS

## Usage

* Generate a profile text file

* Start Visualiser at command line

``` python profiler.pyw --filename ../profile/ProfileSampleApp/profile.txt ```

* Pan - move your mouse while holding down mouse button 1 or 2

* Zoom - use your mouse wheel to zoom in/out

## Profile Data Format

The visualiser expects profile data in a specific text format.

The [C++ Profiler](https://github.com/JimKnowler/profile) generates this text format.

```
T 0 main
F 0 0 main
S 0 0 39469
F 0 1 void __cdecl runTest(void)
S 0 1 39523
F 0 2 start threads
S 0 2 39582
T 1 WorkerThread #1
F 1 0 WorkerThread #1
S 1 0 41191
F 1 1 void __cdecl mockFunction(int,int)
S 1 1 41312
F 1 2 int __cdecl getRandomNumber(int)
S 1 2 41357
F 1 3 mutex acquired
S 1 3 41413
E 1 3 41527
E 1 2 41574
T 2 WorkerThread #2
F 2 0 WorkerThread #2
```

### T = Thread

``` T 0 main ```

``` T <Thread ID> <Thread Label>\n ```

* 'Thread ID' should be unique for each thread

* 'Thread Label' is parsed as all remaining characters until the newline, so it can include spaces

### F = Function

``` F 1 3 void __cdecl runTest(void) ```

``` F <Thread ID> <Function ID> <Function Label>\n ```

* 'Thread ID' corresponds to the Thread ID of a Thread registered with ( **T** ) 

* 'Function ID' should be unique for each function within each thread
  * i.e. Each Thread can allocate Function IDs independently

* 'Function Label' is parsed as all remaining characters until the newline, so it can include spaces

*(note: this is also used to report a 'scope')*

### S = Start Sample

Log the time when a sample starts.

A Sample is a individual call to a function.

The 'Start Sample' and 'End Sample' log entries are used to log times at which functions are entered/left.

*For example: if a single function were to be called multiple times (including recursively) then you would expect that function to be registered once ( **F** ) and then multiple samples would start and end ( **S** + **E** ).*

``` S 1 3 41413 ```

``` S <Thread ID> <Function ID> <Clock Time in Microseconds> ```

* 'Thread ID' corresponds to the Thread ID of a Thread registered with ( **T** ) 

* 'Function ID' corresponds to the Function ID of a Function registered with ( **F** )

### E = End Sample

``` E 1 3 41527 ```

``` E <Thread ID> <Function ID> <Clock Time in Microseconds> ```

* 'Thread ID' corresponds to the Thread ID of a Thread registered with ( **T** ) 

* 'Function ID' corresponds to the Function ID of a Function registered with ( **F** )

