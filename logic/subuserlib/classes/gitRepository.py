#!/usr/bin/env python
# This file should be compatible with both Python 2 and 3.
# If it is not, please file a bug report.

"""
This is a Class which allows one to manipulate a git repository.
"""

#external imports
import os
import tempfile
#internal imports
import subuserlib.subprocessExtras as subprocessExtras
from subuserlib.classes.fileStructure import FileStructure

class GitRepository():
  def __init__(self,path):
    self.__path = path

  def getPath(self):
    return self.__path
  
  def run(self,args):
    """
    Run git with the given command line arguments.
    """
    return subprocessExtras.call(["git"]+args,cwd=self.getPath())
  
  def runCollectOutput(self,args):
    """
    Run git with the given command line arguments and return a tuple with (returncode,output).
    """
    return subprocessExtras.callCollectOutput(["git"]+args,cwd=self.getPath())

  def getFileStructureAtCommit(self,commit):
    """
    Get a ``FileStructure`` object which relates to the given git commit.
    """
    return GitFileStructure(self,commit)

  def commit(self,message):
    """
    Run git commit with the given commit message.
    """
    try:
      tempFile = tempfile.NamedTemporaryFile("w",encoding="utf-8")
    except TypeError: # Older versions of python have broken tempfile implementation for which you cannot set the encoding.
      tempFile = tempfile.NamedTemporaryFile("w")
      message = message.encode('ascii', 'ignore').decode('ascii')
    with tempFile as tempFile:
      tempFile.write(message)
      tempFile.flush()
      return self.run(["commit","--file",tempFile.name])

  def checkout(self,hash,files=[]):
    """
    Run git checkout
    """
    self.run(["checkout",hash]+files)

class GitFileStructure(FileStructure):
  def __init__(self,gitRepository,commit):
    self.__gitRepository = gitRepository
    self.__commit = commit

  def getCommit(self):
    return self.__commit

  def getRepository(self):
    return self.__gitRepository

  def lsTree(self, subfolder, extraArgs=[]):
    """
    Returns a list of tuples of the form:
    (mode,type,hash,path)
 
    Coresponding to the items found in the subfolder.
    """
    if not subfolder.endswith("/"):
      subfolder += "/"
    if subfolder == "/":
      subfolder = "./"
    (returncode,output) = self.getRepository().runCollectOutput(["ls-tree"]+extraArgs+[self.getCommit(),subfolder])
    if returncode != 0:
      return [] # This commenting out is intentional. It is simpler to just return [] here than to check if the repository is properly initialized everywhere else.
    lines = output.splitlines()
    items = []
    for line in lines:
      mode,objectType,rest = line.split(" ",2)
      objectHash,path = rest.split("\t",1)
      items.append((mode,objectType,objectHash,path))
    return items

  def ls(self, subfolder, extraArgs=[]):
    """
    Returns a list of file and folder paths.
    Paths are relative to the repository as a whole.
    """
    items = self.lsTree(subfolder,extraArgs)
    paths = []
    for item in items:
      paths.append(item[3])
    return paths

  def lsFiles(self,subfolder):
    """
    Returns a list of paths to files in the subfolder.
    Paths are relative to the repository as a whole.
    """
    return list(set(self.ls(subfolder)) - set(self.lsFolders(subfolder)))

  def lsFolders(self,subfolder):
    """
    Returns a list of paths to folders in the subfolder.
    Paths are relative to the repository as a whole.
    """
    return self.ls(subfolder,extraArgs=["-d"])

  def exists(self,path):
    try:
      self.read(path)
      return True
    except OSError:
      return False

  def read(self,path):
    """
    Returns the contents of the given file at the given commit.
    """
    (errorcode,content) = self.getRepository().runCollectOutput(["show",self.getCommit()+":"+path])
    if errorcode != 0:
      raise OSError("Git show exited with error "+str(errorcode)+". File does not exist.")
    return content

  def getMode(self,path):
    allObjects = self.lsTree("./",extraArgs=["-r"])
    for treeObject in allObjects:
      if treeObject[3] == path:
        return int(treeObject[0],8)
