#
# Redfish JSON resource to C structure converter source code generator.
#
# Copyright Notice:
# Copyright 2021 DMTF. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tacklebox/blob/master/LICENSE.md
#
import os
import sys
import textwrap

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
from RedfishCSDef import C_SRC_TAB_SPACE
from RedfishCSDef import MEMBER_DESCRIPTION_CHARS
from RedfishCSDef import STRUCTURE_MEMBER_TUPLE_IS_STRUCTURE
from RedfishCSDef import STRUCTURE_MEMBER_TUPLE_IS_READONLY
from RedfishCSDef import STRUCTURE_MEMBER_TUPLE_IS_REQUIRED
from RedfishCSDef import STRUCTURE_MEMBER_TUPLE_ORG_KEY_NAME
from RedfishCSDef import IS_STRUCTURE
from RedfishCSDef import REDFISH_ARRAY_CS_TAIL
from RedfishCSDef import REDFISH_NON_STRUCTURE_ARRAY_CS_TAIL

MARKDOWN_CODE_SPACE = "    "
MarkdownTableHeader = "|Field |C Structure Data Type|Description |Required Property|Read only Property\n" + "| ---  | --- | --- | --- | ---\n"

RedfishCSDataTypeMarkdownDesc = {"RedfishCS_char":"String pointer to ",
                                 "RedfishCS_bool":"Boolean pointer to ",
                                 "RedfishCS_int8":"Signed char pointer to ",
                                 "RedfishCS_uint8":"Unsigned char poitner to ",
                                 "RedfishCS_int16":"16-bit signed integer pointer to ",
                                 "RedfishCS_uint16":"16-bit unsigned integer poitner to ",
                                 "RedfishCS_int32":"32-bit signed long integer pointer to ",
                                 "RedfishCS_uint32":"32-bit unsigned long integer pointer to",
                                 "RedfishCS_int64":"64-bit long long interger pointer to ",
                                 "RedfishCS_uint64":"64-bit unsigned long long interger pointer to ",
                                 "RedfishCS_double":"Double floating-point pointer to ",
                                 "RedfishCS_float":"Floating-point pointer to ",
                                 "RedfishCS_Link":"Structure link list to ",
                                 "RedfishCS_Vague":"RedfishCS_Vague structure to "
                                 }

class RedfishCS_MarkdownFile:
    def __init__ (self, RedfishCSInstance, SchemaFileInstance, RedfishCSStructList, StructureName, StructureMemberDataType, NonStructureMemberDataType, GenCS_Cfiles):
        self.GenRedfishSchemaCs = RedfishCSInstance
        self.RedfishSchemaFile = SchemaFileInstance
        self.RedfishCsList = RedfishCSStructList
        self.StructureName = StructureName
        self.StructureMemberDataType = StructureMemberDataType
        self.NonStructureMemberDataType = NonStructureMemberDataType
        self.GenCS_Cfiles = GenCS_Cfiles
        self.MarkdownFileName = ""
        self.ArrayStructMember = {}        

    def FormatingMarkdownStructMemberDataType (self, StrStructureMemberDataType, ResourceType, SchemaVersion, key):
        strToRet = StrStructureMemberDataType.replace (" *", "")
        IsArray = 0
        if len (strToRet.split(REDFISH_SCHEMA_NAMING_NOVERSIONED)) == 2:
            strToRet = strToRet.split(REDFISH_SCHEMA_NAMING_NOVERSIONED)[0].strip ('_' ) + \
                    strToRet.split(REDFISH_SCHEMA_NAMING_NOVERSIONED)[1]

        # Check if this member is an array.
        if ResourceType not in self.NonStructureMemberDataType:
            return strToRet,IsArray
        if SchemaVersion not in self.NonStructureMemberDataType [ResourceType]:
            return strToRet,IsArray

        key = key.replace (ResourceType + '_', "").replace (SchemaVersion + '_', "")
        for Mem in self.NonStructureMemberDataType[ResourceType][SchemaVersion]:
            Tuple =self.NonStructureMemberDataType[ResourceType][SchemaVersion][Mem];
            if Mem == key and \
               isinstance (Tuple [REDFISH_GET_DATATYPE_VALUE], str) and \
               Tuple [REDFISH_GET_DATATYPE_VALUE] == "array":

                if strToRet == "RedfishCS_Link":
                    return strToRet, 0 # Dont need arry structure for RedfishCS_Link               

                if REDFISH_STRUCT_NAME_TAIL in strToRet:
                    NewMemName = strToRet.replace(REDFISH_STRUCT_NAME_TAIL, "") + REDFISH_ARRAY_CS_TAIL
                    IsArray = 1
                else:
                    NewMemName = strToRet + REDFISH_NON_STRUCTURE_ARRAY_CS_TAIL
                    IsArray = 2

                if ResourceType not in self.ArrayStructMember:
                    self.ArrayStructMember [ResourceType] = {}
                if SchemaVersion not in self.ArrayStructMember [ResourceType]:
                    self.ArrayStructMember [ResourceType][SchemaVersion] = {}
                if key not in self.ArrayStructMember [ResourceType][SchemaVersion]:
                    self.ArrayStructMember [ResourceType][SchemaVersion][key] = (NewMemName, strToRet)
                return NewMemName, IsArray

        return strToRet, 0

    def FormatingStructMemberName (Self, StrStructureMemberName):
        strToRet = StrStructureMemberName.replace ("@", "").replace ('.', '_').lstrip('#')        
        return strToRet
        
    def IsRequiredStr (self,StructureMemberDataType, key):
        if key not in StructureMemberDataType:
            return "---"

        if StructureMemberDataType[key][STRUCTURE_MEMBER_TUPLE_ORG_KEY_NAME] in self.RedfishCsList.RequiredProperties:
            return "Yes"
        else:
            return "No"

    def IsReadOnlyStr (self,StructureMemberDataType, key):
        if key not in StructureMemberDataType:
            return "---"

        if StructureMemberDataType[key][STRUCTURE_MEMBER_TUPLE_IS_READONLY] == True:
            return "Yes"
        else:
            return "No"

    def DataTypeDesc (self,StructMemDataType, StructureMemberDataType, key, ArrayType):
        if StructMemDataType in RedfishCSDataTypeMarkdownDesc:
            if key in StructureMemberDataType:
                return RedfishCSDataTypeMarkdownDesc[StructMemDataType] + "**" + StructureMemberDataType[key][STRUCTURE_MEMBER_TUPLE_ORG_KEY_NAME] + "** property."                
            else:
                if key == "Prop":
                    return RedfishCSDataTypeMarkdownDesc[StructMemDataType] + "OEM defined property"
                else:
                    return "---"     
        else:
            if ArrayType == 0: # Non array
                if key in StructureMemberDataType and StructureMemberDataType[key][STRUCTURE_MEMBER_TUPLE_IS_STRUCTURE] == IS_STRUCTURE:
                    return "Structure points to " + "**" + StructureMemberDataType[key][STRUCTURE_MEMBER_TUPLE_ORG_KEY_NAME] + "** property."
                else:
                    return "---"                    
            else:
                if ArrayType == 1: # =1 Structure array
                    Object = StructMemDataType.replace (REDFISH_ARRAY_CS_TAIL,"").split('_')
                    ObjectName = Object[len(Object)-1]
                    return "Structure array points to one or more than one " + "**" + StructMemDataType + "** structures for property " + "**" + StructureMemberDataType[key][STRUCTURE_MEMBER_TUPLE_ORG_KEY_NAME] + "**."
                else:             # -2 Non Structure array
                    Object = StructMemDataType.replace (REDFISH_NON_STRUCTURE_ARRAY_CS_TAIL,"").split('_')
                    ObjectName = Object[len(Object)-1]
                    return "Structure array points to one or more than one " + "**" + StructureMemberDataType[key][STRUCTURE_MEMBER_TUPLE_DATATYPE] + "**" + " for property " + "**" + StructureMemberDataType[key][STRUCTURE_MEMBER_TUPLE_ORG_KEY_NAME] + "**."


    # This generates structure member definition.
    def GenMarkdownStructMemDefinition (self, ResourceType, SchemaVersion, StrucName, IsRoot):
        StructureName = self.StructureName
        StructureMemberDataType = self.StructureMemberDataType
                 
        typedef = ""
        self.StructTableText =  MarkdownTableHeader
        if SchemaVersion == REDFISH_SCHEMA_NAMING_NOVERSIONED:
            Name = StructureName [ResourceType][SchemaVersion][StrucName][STRUCTURE_NAME_TUPLE_NAME].replace (REDFISH_SCHEMA_NAMING_NOVERSIONED + "_", "")
            typedef += MARKDOWN_CODE_SPACE + "typedef struct " + "_" + Name  + " {\n"
        else:
            typedef += MARKDOWN_CODE_SPACE + "typedef struct " + "_" + StructureName [ResourceType][SchemaVersion][StrucName][STRUCTURE_NAME_TUPLE_NAME]  + " {\n"            
        StructMemHead = StructureName [ResourceType][SchemaVersion][StrucName][STRUCTURE_NAME_TUPLE_NAME].replace (REDFISH_STRUCT_NAME_HEAD, "")
        StructMemHead = StructMemHead.replace(REDFISH_STRUCT_NAME_TAIL, "")

        # First add header member for root structure.
        if IsRoot:
            typedef += (MARKDOWN_CODE_SPACE + TAB_SPACE + "RedfishCS_Header" + " " + TAB_SPACE + "Header;\n")
            self.StructTableText += "|**Header**|RedfishCS_Header|Redfish C structure header|---|---\n"
        
        # Loop to generate structure member
        MemFound = False
        for key in sorted (StructureMemberDataType.keys ()):
            if key.find(StructMemHead) != -1:
                if key.replace (StructMemHead, "") != "":
                    Member = key.replace (StructMemHead, "").lstrip('_')
                    if len (Member.split ('_')) == 1:
                        Member = self.FormatingStructMemberName (Member)
                        StructMemDataType, ArrayType = self.FormatingMarkdownStructMemberDataType (StructureMemberDataType [key][STRUCTURE_MEMBER_TUPLE_DATATYPE], ResourceType, SchemaVersion, key)

                        if StructureMemberDataType [key][STRUCTURE_MEMBER_TUPLE_DATATYPE].find(' *') == -1:
                            typedef += (MARKDOWN_CODE_SPACE + TAB_SPACE + StructMemDataType + " " + Member + ";\n")
                        else:
                            typedef += (MARKDOWN_CODE_SPACE + TAB_SPACE + StructMemDataType + " " + "*" + Member + ";\n")
                        MemFound = True
                        self.StructTableText += "|**"+ Member +"**" + \
                                                "|" + StructMemDataType +\
                                                "| " + self.DataTypeDesc (StructMemDataType, StructureMemberDataType, key, ArrayType) +\
                                                "| " + self.IsRequiredStr (StructureMemberDataType, key) +\
                                                "| " + self.IsReadOnlyStr (StructureMemberDataType, key) + "\n"
        if not MemFound:
            # No member found, means the properties for this data type is "{}"
            typedef += (MARKDOWN_CODE_SPACE + TAB_SPACE + "RedfishCS_Link" + " " + "Prop" + ";\n")
            self.StructTableText += "|**"+ "Prop" +"**" + \
                                    "|" + "RedfishCS_Link" +\
                                    "| " + self.DataTypeDesc ("RedfishCS_Link", StructureMemberDataType, "Prop", 0) +\
                                    "| " + self.IsRequiredStr (StructureMemberDataType, "Prop") +\
                                    "| " + self.IsReadOnlyStr (StructureMemberDataType, "Prop") + "\n"            
                                    
        if SchemaVersion == REDFISH_SCHEMA_NAMING_NOVERSIONED:
            Name = StructureName [ResourceType][SchemaVersion][StrucName][STRUCTURE_NAME_TUPLE_NAME].replace (REDFISH_SCHEMA_NAMING_NOVERSIONED + "_", "")
            typedef += (MARKDOWN_CODE_SPACE + "} " + Name + ";\n\n")            
        else:            
            typedef += (MARKDOWN_CODE_SPACE + "} " + StructureName [ResourceType][SchemaVersion][StrucName][STRUCTURE_NAME_TUPLE_NAME] + ";\n\n")
        return typedef + self.StructTableText
        

    def GenMarkdown (self):
        RedfishCs = self.RedfishCsList
        GenCS_Cfiles = self.GenCS_Cfiles
        StructureName = self.StructureName
        StructureMemberDataType = self.StructureMemberDataType

        if GenCS_Cfiles.CRedfishRootStrucutreResrouceVersion == "":
            VersionDirTail = ""
        else:
            VersionDirTail = "." + GenCS_Cfiles.CRedfishRootStrucutreResrouceVersion        

        if RedfishCs.SchemaVersion != REDFISH_SCHEMA_NAMING_NOVERSIONED:
            MarkdownText = "# Definition of " + RedfishCs.ResourceType + "." + RedfishCs.SchemaVersion + " and functions<br><br>"
        else:
            MarkdownText = "# Definition of " + RedfishCs.ResourceType + " and functions<br><br>"

        #Generate structure definitions
        for ResourceTypeLoop in sorted (StructureName.keys()):
            for SchemaVersionLoop in sorted (StructureName [ResourceTypeLoop].keys()):        
                for StrucName in sorted(StructureName [ResourceTypeLoop][SchemaVersionLoop].keys()):
                    if StrucName != self.RedfishSchemaFile.SchemaRef or \
                       ResourceTypeLoop != RedfishCs.ResourceType or \
                       SchemaVersionLoop != RedfishCs.SchemaVersion:
                        MarkdownText += "\n\n## " + StrucName +"\n"
                        typedef = self.GenMarkdownStructMemDefinition (ResourceTypeLoop, SchemaVersionLoop, StrucName, False)
                        MarkdownText += typedef

        # Generate the structure for array.
        NewInsertforwardTypedef = ""
        ArrayStructAdded = []
        for ResourceTypeLoop in self.ArrayStructMember:
            for SchemaVersionLoop in self.ArrayStructMember [ResourceTypeLoop]:
                for KeyLoop in self.ArrayStructMember [ResourceTypeLoop][SchemaVersionLoop]:
                    NewStructName  = self.ArrayStructMember [ResourceTypeLoop][SchemaVersionLoop][KeyLoop][0]
                    if NewStructName not in ArrayStructAdded:
                        MarkdownText += "\n\n## " + NewStructName +"\n"
                        MarkdownText += MARKDOWN_CODE_SPACE + "typedef struct " + "_" + NewStructName + " " + " {\n"
                        MarkdownText += MARKDOWN_CODE_SPACE + TAB_SPACE + "RedfishCS_Link" + " *Next;\n"
                        MarkdownText += MARKDOWN_CODE_SPACE + TAB_SPACE + self.ArrayStructMember [ResourceTypeLoop][SchemaVersionLoop][KeyLoop][1] + " *ArrayValue;\n"
                        MarkdownText += MARKDOWN_CODE_SPACE + "} "+ NewStructName + ";\n\n"
                        ArrayStructAdded.append (NewStructName)
            

        # Generate the root structure for this schema.
        for ResourceTypeLoop in sorted (StructureName.keys()):
            for SchemaVersionLoop in sorted (StructureName [ResourceTypeLoop].keys()):       
                for StrucName in sorted(StructureName [ResourceTypeLoop][SchemaVersionLoop].keys()):
                   if StrucName == self.RedfishSchemaFile.SchemaRef and \
                       ResourceTypeLoop == RedfishCs.ResourceType and \
                       SchemaVersionLoop == RedfishCs.SchemaVersion:
                        MarkdownText += "\n\n## " + StrucName +"\n"
                        typedef = self.GenMarkdownStructMemDefinition (ResourceTypeLoop, SchemaVersionLoop, StrucName, True)
                        MarkdownText += typedef
                        self.CRedfishRootStrucutreResrouceType = ResourceTypeLoop
                        self.CRedfishRootStrucutreResrouceVersion = SchemaVersionLoop
                        if self.CRedfishRootStrucutreResrouceVersion == REDFISH_SCHEMA_NAMING_NOVERSIONED:
                            self.CRedfishRootStrucutreResrouceVersion = ""
                        self.CRedfishRootStrucutreTypeName = StrucName                        
                        break


        SchemaVer = ""
        if RedfishCs.SchemaVersion != REDFISH_SCHEMA_NAMING_NOVERSIONED:
            SchemaVer = RedfishCs.SchemaVersion
        MarkdownText += "## Redfish " + RedfishCs.ResourceType + " " + SchemaVer + " to C Structure Function\n"
        StructPointerName = StructureName [RedfishCs.ResourceType][RedfishCs.SchemaVersion][self.RedfishSchemaFile.SchemaRef][STRUCTURE_NAME_TUPLE_NAME]
        if SchemaVer =="":
            StructPointerName = StructPointerName.replace (REDFISH_SCHEMA_NAMING_NOVERSIONED + "_", "")
        MarkdownText += MARKDOWN_CODE_SPACE + "RedfishCS_status\n"
        MarkdownText += MARKDOWN_CODE_SPACE + self.GenCS_Cfiles.CRedfishRootFunctionName  + " (RedfishCS_char *JsonRawText, " + StructPointerName + " **ReturnedCS);\n\n"

        MarkdownText += "## C Structure to Redfish " + RedfishCs.ResourceType + " " + SchemaVer + " JSON Function\n"
        MarkdownText += MARKDOWN_CODE_SPACE + "RedfishCS_status\n"
        MarkdownText += MARKDOWN_CODE_SPACE + self.GenCS_Cfiles.CToRedfishFunctionName  + " (" + StructPointerName + " *CSPtr, RedfishCS_char **JsonText);\n\n"

        MarkdownText += "## Destory Redfish " + RedfishCs.ResourceType + " " + SchemaVer + " C Structure Function\n"
        MarkdownText += MARKDOWN_CODE_SPACE + "RedfishCS_status\n"
        MarkdownText += MARKDOWN_CODE_SPACE + self.GenCS_Cfiles.CRedfishDestoryFunctionName  + " (" + StructPointerName + " *CSPtr);\n\n"        
               

        # Write to file
        MarkdownFile = os.path.normpath(self.GenRedfishSchemaCs.OuputDirectory + "/src" + "/" + \
                                    GenCS_Cfiles.CRedfishRootStrucutreResrouceType + "/" + \
                                    GenCS_Cfiles.CRedfishRootStrucutreResrouceType + VersionDirTail + "/README.md")        
        try:
            fo = open(MarkdownFile,"w")
        except:
            ToolLogInformation.LogIt ("Create MArkdown file fail!")
            sys.exit()

        fo.write (MarkdownText)
        fo.close()
        return
