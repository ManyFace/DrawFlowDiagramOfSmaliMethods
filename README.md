# DrawFlowDiagramOfSmaliMethods
  when analysing an APK in reverse process, we usually use apktool(http://ibotpeaches.github.io/Apktool/) to decompile 
the APK and then get smali codes. Although some tools,such as dex-to-jar, can convert smali codes to java codes which is more readable, those tools may not work if the method is complicate enough or confused. In this case, you can use this project
to draw the basic flow diagram of method to understand the execution flow quickly.

The flow diagram is based on unconditional jump(goto) and conditional jump(if) instructions.
<br>

##Dependency
1. python2.7 <br>
* Graphviz(http://www.graphviz.org/) <br>

##Platform
* You can run this program on Linux. <br>
* As for windows, you can change the variable DOT_PATH in drawFlowDiagramOfSmaliMethods.py.<br> Since output file name is named by method's name correspondingly, if method's name contains illegal characters of file name, the flow diagram of this method will not be generated.

##Usage
(Make sure you install python2.7 and Graphviz before running this program)
* type "python drawFlowDiagramOfSmaliMethods.py -h" in cmdline will show help message.
![](https://github.com/ManyFace/DrawFlowDiagramOfSmaliMethods/blob/master/res/help.PNG)
1. -s smali_file_path is indispensable, it specifies which smali file you want to parse.
2. -f {png,jpg,svg} specifies the format of output picture file containing flow diagram generated
3. -m methods_to_draw specifies the methods which you want to draw flow diagrams of. Different methods split with #, such as
                      func#func1\\(I\\)Z. If you doesn't specify this parameter,it will draw all methods' flow diagrams.
4. -o output_dir specifies the directory of output flow diagrams. Defult is current directory.

Example:
* python python drawFlowDiagramOfSmaliMethods.py -s Check.smali   //generate flow diagrams of all methods in Check.smali
* python python drawFlowDiagramOfSmaliMethods.py -s Check.smali -f png -m check -o /home/cpf/output

##Output Flow Diagrams
1.example 1<br>
![](https://github.com/ManyFace/DrawFlowDiagramOfSmaliMethods/blob/master/res/access%24_T11306(Ljava.lang.Object%3BLjava.lang.String%3B)Ljava.lang.String%3B.png)
<br>
2.example 2<br>
![](https://github.com/ManyFace/DrawFlowDiagramOfSmaliMethods/blob/master/res/check(Ljava.lang.String%3B)Z.png)
<br>
Note:<br>
* The number in the diagrams increasing from top to bottom is the line number of this instruction.<br>
Figure legends:<br>
1.Yellow rectangle indicates return instruction.<br>
2.Orange edge indicates unconditional jump<br>
3.Red edge indicates conditional jump if condition is false. That means it will execute all instructions between from node and end node<br>
4.Green edge indicates conditional jump if condition is true<br>


