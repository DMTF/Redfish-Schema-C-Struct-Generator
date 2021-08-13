#
# Redfish JSON resource to C structure converter source code generator.
#
# (C) Copyright 2018-2019 Hewlett Packard Enterprise Development LP
#
import os
import sys
import textwrap
import uuid

from RedfishCSDef import REDFISH_STRUCT_NAME_HEAD
from RedfishCSDef import REDFISH_STRUCT_NAME_TAIL
from RedfishCSDef import STRUCTURE_MEMBER_TUPLE_DATATYPE
from RedfishCSDef import STRUCTURE_MEMBER_TUPLE_DESCRIPTION
from RedfishCSDef import STRUCTURE_NAME_TUPLE_NAME
from RedfishCSDef import STRUCTURE_NAME_TUPLE_DESCRIPTION
from RedfishCSDef import REDFISH_SCHEMA_NAMING_NOVERSIONED
from RedfishCSDef import REDFISH_GET_DATATYPE_KEY
from RedfishCSDef import REDFISH_GET_DATATYPE_CS_TYPE
from RedfishCSDef import REDFISH_GET_DATATYPE_VALUE

from RedfishCSDef import TAB_SPACE
from RedfishCSDef import MEMBER_DESCRIPTION_CHARS

HPECopyright  = "//\n" \
                "// Auto-generated file by Redfish Schema C Structure Generator.\n" + \
                "// https://github.com/DMTF/Redfish-Schema-C-Struct-Generator.\n" + \
                "//\n" + \
                "//  (C) Copyright 2019-2021 Hewlett Packard Enterprise Development LP<BR>\n" + \
                "//  SPDX-License-Identifier: BSD-2-Clause-Patent\n" + \
                "//\n" + \
                "// Auto-generated file by Redfish Schema C Structure Generator.\n" + \
                "// https://github.com/DMTF/Redfish-Schema-C-Struct-Generator.\n" + \
                "// Copyright Notice:\n" + \
                "// Copyright 2019-2021 Distributed Management Task Force, Inc. All rights reserved.\n" + \
                "// License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-JSON-C-Struct-Converter/blob/master/LICENSE.md\n" + \
                "//\n"

DMTFCopyright = "//----------------------------------------------------------------------------\n" + \
                "// Copyright Notice:\n" \
                "// Copyright 2019-2021 Distributed Management Task Force, Inc. All rights reserved.\n" + \
                "// License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-JSON-C-Struct-Converter/blob/master/LICENSE.md\n" + \
                "//----------------------------------------------------------------------------\n"

Edk2InfFileCopyright = "#\n" + \
                       "#  (C) Copyright 2019-2021 Hewlett Packard Enterprise Development LP<BR>\n" + \
                       "#  SPDX-License-Identifier: BSD-2-Clause-Patent\n" + \
                       "#\n" + \
                       "# Auto-generated file by Redfish Schema C Structure Generator.\n" + \
                       "# https://github.com/DMTF/Redfish-Schema-C-Struct-Generator.\n" + \
                       "# Copyright Notice:\n" + \
                       "# Copyright 2019-2021 Distributed Management Task Force, Inc. All rights reserved.\n" + \
                       "# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-JSON-C-Struct-Converter/blob/master/LICENSE.md\n" + \
                       "#\n"

Edk2InfFileTemp = "[Defines]\n" + \
                  "INF_VERSION                    = 0x00010006\n" + \
                  "BASE_NAME                      = !**LIBRARY_CLASS**!\n" + \
                  "FILE_GUID                      = " + " !**FILE_GUID**!" + "\n" + \
                  "MODULE_TYPE                    = BASE\n" + \
                  "VERSION_STRING                 = 1.0\n" + \
                  "LIBRARY_CLASS                  = !**LIBRARY_CLASS**! | DXE_DRIVER UEFI_APPLICATION UEFI_DRIVER\n" + \
                  "#\n" + \
                  "# The following information is for reference only and not required by the build tools.\n" + \
                  "#\n" + \
                  "#  VALID_ARCHITECTURES           = IA32 X64 IPF EBC RISCV64\n" + \
                  "#\n\n"

Edk2InfSourceSectionTemp = "[Sources]\n" + \
                           "  !**PREFIX_FORWARD_DIR**!../../include/RedfishDataTypeDef.h\n" + \
                           "  !**PREFIX_FORWARD_DIR**!../../src/RedfishCsCommon.c\n" + \
                           "  !**PREFIX_FORWARD_DIR**!../../src/RedfishCsMemory.c\n\n"
Edk2InfPackageSectionTemp = "[Packages]\n" + \
                            "  MdePkg/MdePkg.dec\n" + \
                            "  !**ADDITIONAL_PACKAGE**!\n\n" # + \
                            #"  StdLib/StdLib.dec\n\n"

Edk2InfLibSectionTemp    = "[LibraryClasses]\n" + \
                           "  BaseLib\n" + \
                           "  BaseMemoryLib\n" + \
                           "  DebugLib\n" + \
                           "  MemoryAllocationLib\n" + \
                           "  !**ADDITIONAL_LIBRARIES**!\n\n" 

Edk2BindingDir = "/edk2library"
Edk2BuildOptionSectionTemp    = "[BuildOptions]\n" + \
  "  #\n" + \
  "  # Disables the following Visual Studio compiler warnings\n" + \
  "  # so we do not break the build with /WX option:\n" + \
  "  #   C4706: assignment within conditional expression\n" + \
  "  #\n" + \
   "  MSFT:*_*_*_CC_FLAGS = /wd4706\n"

class RedfishCSEdk2:
    def __init__ (self, RedfishCSInstance, SchemaFileInstance, RedfishCSStructList, StructureName, StructureMemberDataType, NonStructureMemberDataType, GenCS_Cfiles, OutputDir):
        self.CSCFilesInstance = GenCS_Cfiles
        self.GenRedfishSchemaCs = RedfishCSInstance
        self.RedfishSchemaFile = SchemaFileInstance
        self.RedfishCsList = RedfishCSStructList
        self.StructureName = StructureName
        self.StructureMemberDataType = StructureMemberDataType
        self.NonStructureMemberDataType = NonStructureMemberDataType
        self.Edk2OutputDir = os.path.normpath(OutputDir + Edk2BindingDir)
        self.Edk2RedfishIntpOutputDir = os.path.normpath(OutputDir + "/RedfishCsIntp")
        self.Edk2RedfishIntpTempFilesDir = os.path.normpath(os.getcwd() + "/_Edk2OpenSourceTempFiles")        
        self.Edk2RedfishIntpTempDxeC = ""
        self.Edk2RedfishIntpTempDxeInf = ""
        self.Edk2RedfishIntpTempInclude = ""
        self.Edk2RedfishIntpComponentDsc = ""        
        self.Edk2RedfishIntpLibDsc = ""          
        self.Edk2RedfishintpKeywordsDict = {}
        self.Edk2CStructureName = ""

        self.Edk2AdditionalLibClass = ""
        self.Edk2AdditionalPackage = ""
        self.Edk2RedfishJsonCsPackagePath = ""

        self.InfFilePath = ""
        self.LibClass = ""
        self.Edk2CsIncludeFileRelativePath = ""

    def GenCSEdk2Files(self):
        self.GenEdk2IncludeFile ()

    def GenEdk2IncludeFile(self):
        RedfishCs = self.RedfishCsList

        if RedfishCs.SchemaVersion == REDFISH_SCHEMA_NAMING_NOVERSIONED:
            SchemaVersion = ""
            PrefixForwardDir = ""
        else:
            SchemaVersion = "_" + RedfishCs.SchemaVersion.upper()
            PrefixForwardDir = "../"

        self.RedfishSchemaFile.Edk2IncludeFileText = HPECopyright + "\n"
        self.RedfishSchemaFile.Edk2IncludeFileText += ("#ifndef " + "EFI_" + REDFISH_STRUCT_NAME_HEAD.upper() + \
                            RedfishCs.ResourceType.upper() + \
                            SchemaVersion + \
                            "_" + "CSTRUCT_H_" + "\n")
        self.RedfishSchemaFile.Edk2IncludeFileText += ("#define " + "EFI_" + REDFISH_STRUCT_NAME_HEAD.upper() + \
                            RedfishCs.ResourceType.upper() + \
                            SchemaVersion + \
                            "_" + "CSTRUCT_H_" + "\n")
        self.RedfishSchemaFile.Edk2IncludeFileText += "\n"
        self.RedfishSchemaFile.Edk2IncludeFileText += "#include \"" + PrefixForwardDir + "../../include/RedfishDataTypeDef.h\"\n"
        self.RedfishSchemaFile.Edk2IncludeFileText += "#include \"" + PrefixForwardDir + "../../include/" + self.CSCFilesInstance.CIncludeFileName + "\"\n"

        Edk2CsType = "EFI_REDFISH_" + self.CSCFilesInstance.CRedfishRootStrucutreResrouceType.upper() + SchemaVersion + REDFISH_STRUCT_NAME_TAIL
        self.Edk2CStructureName = Edk2CsType
        self.RedfishSchemaFile.Edk2IncludeFileText += "\n"
        self.RedfishSchemaFile.Edk2IncludeFileText += "typedef " + self.CSCFilesInstance.CRedfishRootStructureName + " " + Edk2CsType + ";\n"
        self.RedfishSchemaFile.Edk2IncludeFileText += "\n"

        self.RedfishSchemaFile.Edk2IncludeFileText += "RedfishCS_status\n"
        self.RedfishSchemaFile.Edk2IncludeFileText += self.CSCFilesInstance.CRedfishRootFunctionName  + " (RedfishCS_char *JsonRawText, " + Edk2CsType + " **ReturnedCs);\n\n"
        self.RedfishSchemaFile.Edk2IncludeFileText += "RedfishCS_status\n"
        self.RedfishSchemaFile.Edk2IncludeFileText += self.CSCFilesInstance.CToRedfishFunctionName  + " (" + Edk2CsType + " *CSPtr, RedfishCS_char **JsonText);\n\n"
        self.RedfishSchemaFile.Edk2IncludeFileText += "RedfishCS_status\n"
        self.RedfishSchemaFile.Edk2IncludeFileText += self.CSCFilesInstance.CRedfishDestoryFunctionName  + " (" + Edk2CsType + " *CSPtr);\n\n"                                                        
        self.RedfishSchemaFile.Edk2IncludeFileText += "RedfishCS_status\n"
        self.RedfishSchemaFile.Edk2IncludeFileText += self.CSCFilesInstance.CRedfishDestoryJsonFunctionName  + " (RedfishCS_char *JsonText);\n\n"           
    
        self.RedfishSchemaFile.Edk2IncludeFileText += "#endif\n"

        if SchemaVersion != "":
            OutputDir = os.path.normpath(self.Edk2OutputDir + "/" + RedfishCs.ResourceType + "/" + RedfishCs.SchemaVersion.lower())
        else:
            OutputDir = os.path.normpath(self.Edk2OutputDir + "/" + RedfishCs.ResourceType)
            
        # Write to file
        if not os.path.exists (OutputDir):
            os.makedirs(OutputDir)
        try:
            Edk2IncFile = os.path.normpath(OutputDir + "/" + self.RedfishSchemaFile.Edk2CIncludeFile)
            fo = open(Edk2IncFile,"w")
        except:
            ToolLogInformation.LogIt ("Create EDK2 Include file fail!")
            sys.exit()

        fo.write (self.RedfishSchemaFile.Edk2IncludeFileText)
        fo.close()

    def GenEdk2InfFile(self):
        RedfishCs = self.RedfishCsList

        if RedfishCs.SchemaVersion == REDFISH_SCHEMA_NAMING_NOVERSIONED:
            PrefixForwardDir = ""
            Edk2InfFileName = "Lib.inf"
            OutputDir = os.path.normpath(self.Edk2OutputDir + "/" + RedfishCs.ResourceType + "/" + Edk2InfFileName)
            self.Edk2CsIncludeFileRelativePath = RedfishCs.ResourceType
        else:
            PrefixForwardDir = "../"
            Edk2InfFileName = "Lib.inf"
            OutputDir = os.path.normpath(self.Edk2OutputDir + "/" + RedfishCs.ResourceType + "/" + RedfishCs.SchemaVersion.lower() + "/" + Edk2InfFileName)
            self.Edk2CsIncludeFileRelativePath = RedfishCs.ResourceType + "/" + RedfishCs.SchemaVersion.lower()
        self.InfFilePath = OutputDir      

        # Create INF file
        if os.path.exists (OutputDir):
            fi = open(OutputDir,"r")
            PreInfList = fi.readlines()
            fi.close()
            for index in range (0, len (PreInfList)):
                if "FILE_GUID" in PreInfList[index]:
                    FileGuidList = PreInfList[index].split('=')
                    Guid = FileGuidList [1].replace (' ', '').replace ('\n', '')
        else:
            Guid = str(uuid.uuid4())    

        # Replace keywords.
        ThisEdk2InfPackageSectionTemp = Edk2InfPackageSectionTemp.replace ("!**ADDITIONAL_PACKAGE**!", self.Edk2AdditionalPackage)
        ThisEdk2InfLibSectionTemp = Edk2InfLibSectionTemp.replace ("!**ADDITIONAL_LIBRARIES**!", self.Edk2AdditionalLibClass)
        if RedfishCs.SchemaVersion == REDFISH_SCHEMA_NAMING_NOVERSIONED:
            self.LibClass = RedfishCs.ResourceType + "Lib"
            ThisEdk2InfFileTemp = Edk2InfFileTemp.replace ("!**LIBRARY_CLASS**!", self.LibClass).replace("!**FILE_GUID**!",Guid.upper())
        else:
            self.LibClass = RedfishCs.ResourceType + RedfishCs.SchemaVersion.upper() + "Lib"
            ThisEdk2InfFileTemp = Edk2InfFileTemp.replace ("!**LIBRARY_CLASS**!", self.LibClass).replace("!**FILE_GUID**!",Guid.upper())

        # Generate INF File GUID, dont change GUID if INF file already exist.

        Edk2InfSourceSectionTempNew = Edk2InfSourceSectionTemp.replace("!**PREFIX_FORWARD_DIR**!",PrefixForwardDir)
        self.InfText = Edk2InfFileCopyright + ThisEdk2InfFileTemp + Edk2InfSourceSectionTempNew + ThisEdk2InfPackageSectionTemp + ThisEdk2InfLibSectionTemp + Edk2BuildOptionSectionTemp
        if self.Edk2DebugEnable:
            self.InfText += " /Od\n\n"
        else:
            self.InfText += "\n\n"

        fo = open(OutputDir,"w")            
        SrcFile = PrefixForwardDir + "../.." + self.CSCFilesInstance.CSourceFileRelativeDir + "/" + self.CSCFilesInstance.CSourceFile
        index =self.InfText.find ("src/RedfishCsMemory.c\n")
        if index != -1:
            self.InfText = self.InfText [:index + len("src/RedfishCsMemory.c\n")] + \
                           "  " + SrcFile + "\n\n" + \
                           self.InfText [index +  + len("src/RedfishCsMemory.c\n"):]        
        fo.write (self.InfText)
        fo.close()

    def Replacekeyworkds (self, ContentLines):
        for index in range(0, len(ContentLines)):
            for Keyword in self.Edk2RedfishintpKeywordsDict.keys ():
                if Keyword in ContentLines[index]:
                    ContentLines[index] = ContentLines[index].replace (Keyword, self.Edk2RedfishintpKeywordsDict[Keyword])
        return ContentLines


    def GenEdk2RedfishIntpFile(self):
        RedfishCs = self.RedfishCsList        
        RedfishCsInterpreter_Include_Dir = self.Edk2RedfishIntpOutputDir + os.path.normpath("/Include/RedfishJsonStructure/" + self.Edk2CsIncludeFileRelativePath)
        RedfishCsInterpreter_Source_Dir = self.Edk2RedfishIntpOutputDir + os.path.normpath("/Converter")
        if not os.path.exists (self.Edk2RedfishIntpOutputDir):                
            os.makedirs(RedfishCsInterpreter_Include_Dir)
            os.makedirs(RedfishCsInterpreter_Source_Dir)

        if RedfishCs.SchemaVersion == REDFISH_SCHEMA_NAMING_NOVERSIONED:
            SchemaVersion = ""
            SchemaVersionCapital = ""
            SchemaVersionUnderscore = ""
            SchemaVersionCapitalUnderscore =""
            SchemaVersionMajor = REDFISH_SCHEMA_NAMING_NOVERSIONED
            SchemaVersionMinor = REDFISH_SCHEMA_NAMING_NOVERSIONED
            SchemaVersionErrata = REDFISH_SCHEMA_NAMING_NOVERSIONED    
            PrefixForwardDir = ""                    
        else:
            SchemaVersion = RedfishCs.SchemaVersion.lower()
            SchemaVersionCapital = RedfishCs.SchemaVersion.upper()
            SchemaVersionUnderscore = "_" + RedfishCs.SchemaVersion.lower()
            SchemaVersionCapitalUnderscore = "_" + RedfishCs.SchemaVersion.upper()          
            SchemaVersionList = SchemaVersion.replace("v", "").split("_")
            SchemaVersionMajor = SchemaVersionList[0]
            SchemaVersionMinor = SchemaVersionList[1]
            SchemaVersionErrata = SchemaVersionList[2]
            PrefixForwardDir = "../"

        RedfishCsInterpreter_Source_Schema_dir = RedfishCsInterpreter_Source_Dir + os.path.normpath("/" + RedfishCs.ResourceType + "/" + SchemaVersion)
        if not os.path.exists (RedfishCsInterpreter_Source_Schema_dir):
            os.makedirs(RedfishCsInterpreter_Source_Schema_dir)        

        if not os.path.exists (RedfishCsInterpreter_Include_Dir):
            os.makedirs(RedfishCsInterpreter_Include_Dir)          

        if SchemaVersion == "":
            RedfishCsSchemaDxe_C_File = RedfishCs.ResourceType + "_Dxe.c"
            RedfishCsSchemaDxe_INF_File = "Redfish" + RedfishCs.ResourceType + "_Dxe.inf"            
            RedfishCsSchemaDxe_INCLUDE_File = "Efi" + RedfishCs.ResourceType + ".h"
        else:
            RedfishCsSchemaDxe_C_File = RedfishCs.ResourceType + SchemaVersionCapitalUnderscore + "_Dxe.c"
            RedfishCsSchemaDxe_INF_File = "Redfish" + RedfishCs.ResourceType + SchemaVersionCapitalUnderscore + "_Dxe.inf"
            RedfishCsSchemaDxe_INCLUDE_File = "Efi" + RedfishCs.ResourceType + SchemaVersionCapital + ".h"

        self.Edk2RedfishIntpComponentDsc = "RedfishSchemaCsInterpreter_Component.dsc"
        self.Edk2RedfishIntpLibDsc = "RedfishSchemaCsInterpreter_Lib.dsc"

        self.Edk2RedfishIntpTempDxeC = self.Edk2RedfishIntpTempFilesDir + os.path.normpath("/RedfishCsDxe.temp")
        self.Edk2RedfishIntpTempDxeInf = self.Edk2RedfishIntpTempFilesDir + os.path.normpath("/RedfishCsInf.temp")
        self.Edk2RedfishIntpTempInclude = self.Edk2RedfishIntpTempFilesDir + os.path.normpath("/RedfishCsInclude.temp")  
      
        fi = open(self.Edk2RedfishIntpTempDxeC,"r")
        Edk2RedfishIntpTempDxeCLines = fi.readlines()
        fi.close()
        fi = open(self.Edk2RedfishIntpTempDxeInf,"r")
        Edk2RedfishIntpTempDxeInfLine = fi.readlines()
        fi.close()  
        fi = open(self.Edk2RedfishIntpTempInclude,"r")
        Edk2RedfishIntpTempIncludeLines = fi.readlines()
        fi.close()

        if os.path.exists (os.path.normpath(RedfishCsInterpreter_Source_Schema_dir + "/" + RedfishCsSchemaDxe_INF_File)):
            fi = open(os.path.normpath(RedfishCsInterpreter_Source_Schema_dir + "/" + RedfishCsSchemaDxe_INF_File),"r")
            PreInfList = fi.readlines()
            fi.close()
            for index in range (0, len (PreInfList)):
                if "FILE_GUID" in PreInfList[index]:
                    FileGuidList = PreInfList[index].split('=')
                    Guid = FileGuidList [1].replace (' ', '').replace ('\n', '')
        else:
            Guid = str(uuid.uuid4())         

        #Create dict for overwriting keywords in source files.
        self.Edk2RedfishintpKeywordsDict = {}
        self.Edk2RedfishintpKeywordsDict["!**RESOURCE_TYPE**!"] = RedfishCs.ResourceType
        self.Edk2RedfishintpKeywordsDict["!**RESOURCE_TYPE_CAPITAL**!"] = RedfishCs.ResourceType.upper()
        self.Edk2RedfishintpKeywordsDict["!**SCHEMA_VERSION**!"] = SchemaVersion
        self.Edk2RedfishintpKeywordsDict["!**SCHEMA_VERSION_CAPITAL**!"] = SchemaVersionCapital
        self.Edk2RedfishintpKeywordsDict["!**SCHEMA_VERSION_UNDERSCORE**!"] = SchemaVersionUnderscore
        self.Edk2RedfishintpKeywordsDict["!**SCHEMA_VERSION_CAPITAL_UNDERSCORE**!"] = SchemaVersionCapitalUnderscore        
        self.Edk2RedfishintpKeywordsDict["!**FILE_GUID**!"] = Guid
        self.Edk2RedfishintpKeywordsDict["!**SCHEMA_VERSION_MAJOR_STRING**!"] = SchemaVersionMajor
        self.Edk2RedfishintpKeywordsDict["!**SCHEMA_VERSION_MINOR_STRING**!"] = SchemaVersionMinor
        self.Edk2RedfishintpKeywordsDict["!**SCHEMA_VERSION_ERRATA_STRING**!"] = SchemaVersionErrata
        self.Edk2RedfishintpKeywordsDict["!**EDK2_REDFISH_CS_NAME**!"] =  self.Edk2CStructureName       
        self.Edk2RedfishintpKeywordsDict["!**EDK2_REDFISH_JSON_TO_CS_FUNC_NAME**!"] =  self.CSCFilesInstance.CRedfishRootFunctionName
        self.Edk2RedfishintpKeywordsDict["!**EDK2_REDFISH_DESTORY_CS_FUNC_NAME**!"] =  self.CSCFilesInstance.CRedfishDestoryFunctionName
        self.Edk2RedfishintpKeywordsDict["!**EDK2_REDFISH_CS_TO_JSON_FUNC_NAME**!"] =  self.CSCFilesInstance.CToRedfishFunctionName
        self.Edk2RedfishintpKeywordsDict["!**EDK2_REDFISH_DESTORY_JSON_FUNC_NAME**!"] =  self.CSCFilesInstance.CRedfishDestoryJsonFunctionName 
        self.Edk2RedfishintpKeywordsDict["!**EDK2_REDFISH_CS_RELATIVE_PATH**!"] =  self.Edk2CsIncludeFileRelativePath   
        self.Edk2RedfishintpKeywordsDict["!**LIBRARY_CLASS**!"] =  self.LibClass  
        self.Edk2RedfishintpKeywordsDict["!**PREFIX_FORWARD_DIR**!"] = PrefixForwardDir
        self.Edk2RedfishintpKeywordsDict["!**EDK2_BINDINGS_DIR**!"] = Edk2BindingDir
        if self.Edk2DebugEnable:
            self.Edk2RedfishintpKeywordsDict["!**EDK2_DEBUG**!"] = ""
        else:
            self.Edk2RedfishintpKeywordsDict["!**EDK2_DEBUG**!"] = "#"
        if SchemaVersion == "":
            self.Edk2RedfishintpKeywordsDict["!**IS_VERSION_CONTROLLED_BOOLEAN**!"] = "FALSE"
        else:
            self.Edk2RedfishintpKeywordsDict["!**IS_VERSION_CONTROLLED_BOOLEAN**!"] = "TRUE"
        self.Edk2RedfishintpKeywordsDict["!**ADDITIONAL_PACKAGE**!"] = self.Edk2RedfishJsonCsDriverAdditionalPackage
        self.Edk2RedfishintpKeywordsDict["!**ADDITIONAL_LIBRARY_CLASS**!"] = self.Edk2RedfishJsonCsDriverAdditionalLibrary                   
       
        if not os.path.exists (self.Edk2RedfishIntpOutputDir + os.path.normpath("/" + self.Edk2RedfishIntpComponentDsc)):
            fo = open(self.Edk2RedfishIntpOutputDir + os.path.normpath("/" + self.Edk2RedfishIntpComponentDsc),"w")
            fo.close()
        if not os.path.exists (self.Edk2RedfishIntpOutputDir + os.path.normpath("/" + self.Edk2RedfishIntpLibDsc)):            
            fo = open(self.Edk2RedfishIntpOutputDir + os.path.normpath("/" + self.Edk2RedfishIntpLibDsc),"w")
            fo.close()

        fo = open(self.Edk2RedfishIntpOutputDir + os.path.normpath("/" + self.Edk2RedfishIntpComponentDsc),"a")
        if SchemaVersion == "":
            fo.write("  " + self.Edk2RedfishJsonCsPackagePath + "RedfishClientPkg/Converter/" + RedfishCs.ResourceType + "/" + RedfishCsSchemaDxe_INF_File + "\n")
        else:
            fo.write("  " + self.Edk2RedfishJsonCsPackagePath + "RedfishClientPkg/Converter/" + RedfishCs.ResourceType + "/" + SchemaVersion + "/" + RedfishCsSchemaDxe_INF_File + "\n")
        fo.close()

        fo = open(self.Edk2RedfishIntpOutputDir + os.path.normpath("/" + self.Edk2RedfishIntpLibDsc),"a")
        if SchemaVersion == "":
            fo.write("  " + self.LibClass + "|" + self.Edk2RedfishJsonCsPackagePath + "RedfishClientPkg/ConverterLib" + Edk2BindingDir + "/" + RedfishCs.ResourceType + "/Lib.inf" + "\n")
        else:
            fo.write("  " + self.LibClass + "|" + self.Edk2RedfishJsonCsPackagePath + "RedfishClientPkg/ConverterLib" + Edk2BindingDir + "/" + RedfishCs.ResourceType + "/" + SchemaVersion + "/Lib.inf" + "\n")
        fo.close()        

        fo = open(os.path.normpath(RedfishCsInterpreter_Source_Schema_dir + "/" + RedfishCsSchemaDxe_C_File),"w")
        Edk2RedfishIntpTempDxeCLines = self.Replacekeyworkds(Edk2RedfishIntpTempDxeCLines)
        fo.writelines (Edk2RedfishIntpTempDxeCLines)
        fo.close()

        fo = open(os.path.normpath(RedfishCsInterpreter_Source_Schema_dir + "/" + RedfishCsSchemaDxe_INF_File),"w")
        Edk2RedfishIntpTempDxeInfLine = self.Replacekeyworkds(Edk2RedfishIntpTempDxeInfLine)        
        fo.writelines (Edk2RedfishIntpTempDxeInfLine)
        fo.close()

        fo = open(os.path.normpath(RedfishCsInterpreter_Include_Dir + "/" + RedfishCsSchemaDxe_INCLUDE_File),"w")    
        Edk2RedfishIntpTempIncludeLines = self.Replacekeyworkds(Edk2RedfishIntpTempIncludeLines)        
        fo.writelines (Edk2RedfishIntpTempIncludeLines)        
        fo.close()        