#!/usr/bin/env python
# encoding=utf-8
__author__ = 'cpf'
import os
import subprocess
import argparse

DOT_PATH = "dot"


class InstructionType:
    GOTO = "goto"
    GOTOLABEL = ":goto"
    CONJUMP = "if-"
    CONLABEL = ":cond"
    RETURN = "return"
    UNKNOWN = "null"

    @staticmethod
    def getInsType(ins):
        if ins.startswith(InstructionType.GOTO):
            return InstructionType.GOTO
        if ins.startswith(InstructionType.GOTOLABEL):
            return InstructionType.GOTOLABEL
        if ins.startswith(InstructionType.CONJUMP):
            return InstructionType.CONJUMP
        if ins.startswith(InstructionType.CONLABEL):
            return InstructionType.CONLABEL
        if ins.startswith(InstructionType.RETURN):
            return InstructionType.RETURN
        return InstructionType.UNKNOWN


class Instruction:
    def __init__(self, ins, lineNum):
        """
        :param ins:
        :param lineNum:the line number of this instruction in smali file
        """
        self.ins = ins
        self.lineNum = lineNum
        self.type = InstructionType.getInsType(ins)
        self.children = []
        self.parents = []

    def getType(self):
        return self.type

    def getIns(self):
        return self.ins

    def getLineNum(self):
        return self.lineNum

    def addChild(self, child):
        self.children.append(child)

    def addParent(self, parent):
        self.parents.append(parent)

    def getChildrenAbove(self):
        """
        get children whose line number is smaller than this instruction
        :return:
        """
        return [child for child in self.children if int(child.getLineNum()) < int(self.lineNum)]

    def getParentAbove(self):
        """
        get parents whose line number is smaller than this instruction
        :return:
        """
        return [parent for parent in self.parents if int(parent.getLineNum()) < int(self.lineNum)]


class Method:
    def __init__(self, methodName):
        self.methodName = methodName
        self.instructions = []
        self.labelDict = {}  # {label:Instruction}
        self.jumpToLabelDict = {}  # {label:[Instruction]} the Instruction may jump to label,but label doesn't show up yet

    def addIns(self, ins, lineNum):
        instruction = Instruction(ins, lineNum)

        if instruction.getType() == InstructionType.GOTOLABEL or instruction.getType() == InstructionType.CONLABEL:  # label
            if ins in self.labelDict:
                raise Exception("there are same label:%s in method:%s" % (ins, self.methodName))

            if ins in self.jumpToLabelDict:  # the label shows up
                for eachNode in self.jumpToLabelDict[ins]:
                    eachNode.addChild(instruction)
                    instruction.addParent(eachNode)
                self.jumpToLabelDict.pop(ins, None)

            self.labelDict[ins] = instruction
            self.instructions.append(instruction)

        elif instruction.getType() == InstructionType.GOTO or instruction.getType() == InstructionType.CONJUMP:  # jump
            label = ins[ins.index(":"):]  # the label this instruction may jump to
            if label in self.labelDict:  # the label already shows up before
                instruction.addChild(self.labelDict[label])
                self.labelDict[label].addParent(instruction)
            else:  # the label doesn't shows up yet
                if label in self.jumpToLabelDict:
                    self.jumpToLabelDict[label].append(instruction)
                else:
                    self.jumpToLabelDict[label] = [instruction]

            self.instructions.append(instruction)

        elif instruction.getType() == InstructionType.RETURN:
            self.instructions.append(instruction)


class ClassInSmali:
    def __init__(self):
        self.className = None
        self.methodDict = {}

    def setClassName(self, className):
        if not self.className:
            self.className = className
        else:
            raise Exception("More than one class in smali file!")

    def addMethod(self, methodName):
        if methodName in self.methodDict:
            raise Exception("there are methods with same name\nmethod name = %s" % methodName)
        self.methodDict[methodName] = Method(methodName)

    def addMethodIns(self, methodName, Ins, lineNum):
        if methodName not in self.methodDict:
            raise Exception("method->%s does not exist" % methodName)
        self.methodDict[methodName].addIns(Ins, lineNum)


class DrawFlowDiagram:
    def __init__(self, smaliFilePath, pictureFormat, methodsToDraw, outputDir):
        self.smaliFilePath = smaliFilePath
        self.pictureFormat = pictureFormat
        # if methodsToDraw is empty, draw all methods' flow graphs, otherwise, only draw flow graphs of methods that are in methodsToDraw
        self.methodsToDraw = methodsToDraw
        self.outputDir = outputDir
        self.classInSmali = ClassInSmali()
        self.curMethodName = None

    def run(self):
        self.__parseClassInSmali()
        self.__draw()

    def __parseClassInSmali(self):
        with open(self.smaliFilePath) as smaliFile:
            for lineIndex, line in enumerate(smaliFile):
                line = line.strip()
                if not line:
                    continue

                lineInfos = line.split()
                if lineInfos[0] == ".class":
                    self.classInSmali.setClassName(lineInfos[-1])
                    continue

                if lineInfos[0] == ".method":
                    self.curMethodName = lineInfos[-1]
                    if not self.methodsToDraw or \
                                    self.curMethodName in self.methodsToDraw or \
                                    self.curMethodName[0:self.curMethodName.index("(")] in self.methodsToDraw:
                        self.classInSmali.addMethod(self.curMethodName)
                    else:
                        self.curMethodName = None
                    continue

                if lineInfos[0] == ".end method":
                    self.curMethodName = None
                    continue

                if self.curMethodName:
                    self.classInSmali.addMethodIns(self.curMethodName, line, lineIndex + 1)
                    continue

    def __draw(self):
        for method in self.classInSmali.methodDict.values():
            try:
                self.__drawMethodFlowDiagram(method)
            except Exception, ex:
                print "\n\tDraw method flow graph error!\n\terror message:%s\n\tmethod name:%s\n" % (str(ex), method.methodName)

    def __drawMethodFlowDiagram(self, method):
        methodName = method.methodName
        dot_str = """digraph G{\n
                \tstart[label="start"]\n
                """
        for index, ins in enumerate(method.instructions):
            if index == 0:
                dot_str += '\tnode[shape=record];\n'
                dot_str += self.__getDotStrForNode(ins)
                dot_str += '\tstart->node_%s\n' % (ins.getLineNum())
            else:
                dot_str += self.__getDotStrForNode(ins)
                edgeColor = "black"
                lastInsType = method.instructions[index - 1].getType()
                if lastInsType == InstructionType.CONJUMP:
                    edgeColor = "red"
                elif lastInsType == InstructionType.GOTO or lastInsType == InstructionType.RETURN:
                    edgeColor = "white"
                dot_str += self.__getDotStrForEdge(method.instructions[index - 1].getLineNum(), ins.getLineNum(), edgeColor)

                for child in ins.getChildrenAbove():
                    if ins.getType() == InstructionType.CONJUMP:
                        dot_str += self.__getDotStrForEdge(ins.getLineNum(), child.getLineNum(), "green")
                    elif ins.getType() == InstructionType.GOTO:
                        dot_str += self.__getDotStrForEdge(ins.getLineNum(), child.getLineNum(), "orange")

                for parent in ins.getParentAbove():
                    if parent.getType() == InstructionType.CONJUMP:
                        dot_str += self.__getDotStrForEdge(parent.getLineNum(), ins.getLineNum(), "green")
                    elif parent.getType() == InstructionType.GOTO:
                        dot_str += self.__getDotStrForEdge(parent.getLineNum(), ins.getLineNum(), "orange")

        dot_str += "}"

        self.__parseDotToPciture(dot_str, methodName)

    def __parseDotToPciture(self, dot_str, methodName):
        tempDotFileName = "%s.dot" % methodName.replace("/", ".")
        tmpDotFile = open(tempDotFileName, "w")
        tmpDotFile.write(dot_str)
        tmpDotFile.close()
        outputSvgFileName = os.path.join(self.outputDir, "%s.%s" % (methodName.replace("/", "."), self.pictureFormat))
        args = [DOT_PATH, "-T%s" % self.pictureFormat, tempDotFileName, "-o", outputSvgFileName]
        dot_process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        ret = dot_process.communicate()
        os.remove(tempDotFileName)
        if ret[-1]:
            raise Exception(ret[-1])
        print "draw method(%s) flow graph succeed!" % methodName

    @staticmethod
    def __getDotStrForEdge(fromLineNum, toLineNum, edgeColor):
        dot_str = '\tedge[color=' + edgeColor + ']\n'
        dot_str += '\tnode_%s->node_%s\n' % (fromLineNum, toLineNum)
        dot_str += '\tedge[color=black]\n'
        return dot_str


    @staticmethod
    def __getDotStrForNode(instruction):
        if instruction.getIns().startswith("return"):
            dot_str = '\tnode_%s [label="<f0>%s|<f1>%s",style=filled,fillcolor=yellow];\n' % (instruction.getLineNum(), instruction.getLineNum(), instruction.getIns())
        else:
            dot_str = '\tnode_%s [label="<f0>%s|<f1>%s"];\n' % (instruction.getLineNum(), instruction.getLineNum(), instruction.getIns())
        return dot_str


def main():
    argumentParser = argparse.ArgumentParser(description="Draw methods flow graphs!")
    argumentParser.add_argument("-s", dest="smali_file_path", required=True, help="The smali file path.")
    argumentParser.add_argument("-f", dest="picture_format", default="png", choices=["png", "jpg", "svg"], help="the picture formate. Defult is png.")
    argumentParser.add_argument("-m", dest="methods_to_draw",
                                help="The method name or method signature. Different methods split with #, such as func#func1(I)Z#func(Ljava/lang/String;)V. If doesn't specify this parameter,it will draw all methods flow graphs.")
    argumentParser.add_argument("-o", dest="output_dir", default=os.getcwd(), help="The output flow graphs' directory. Defult is current directory.")
    args = argumentParser.parse_args()

    smaliFilePath = args.smali_file_path
    pictureFormat = args.picture_format
    methodsToDraw = args.methods_to_draw
    outputDir = args.output_dir

    if not os.path.exists(smaliFilePath):
        print "\nError: %s doesn't exist.\n" % smaliFilePath
        return

    if not os.path.exists(outputDir):
        print "\nError: Output directory doesn't exist.\n\toutput directory:%s\n" % outputDir
        return

    if methodsToDraw:
        methodsToDraw = [method.strip() for method in methodsToDraw.split("#")]

    drawFlowDiagram = DrawFlowDiagram(smaliFilePath, pictureFormat, methodsToDraw, outputDir)
    drawFlowDiagram.run()


if __name__ == '__main__':
    main()