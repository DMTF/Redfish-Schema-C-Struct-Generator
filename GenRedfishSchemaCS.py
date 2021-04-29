#
# Redfish JSON resource to C structure converter source code generator.
#
# (C) Copyright 2018-2019 Hewlett Packard Enterprise Development LP
#
import os
import sys
import logging
import re
import uuid
import shutil
import json
import ToolLogger
import http.client
import textwrap
from urllib.parse import urlparse
from urllib import request as urlrequest

from RedfishCSDef import REDFISH_STRUCT_NAME_HEAD
from RedfishCSDef import REDFISH_STRUCT_NAME_TAIL
from RedfishCSDef import STRUCTURE_MEMBER_TUPLE_DATATYPE
from RedfishCSDef import STRUCTURE_MEMBER_TUPLE_DESCRIPTION
from RedfishCSDef import STRUCTURE_MEMBER_TUPLE_SECOND_PHASE_LIST
from RedfishCSDef import STRUCTURE_NAME_TUPLE_NAME
from RedfishCSDef import STRUCTURE_NAME_TUPLE_DESCRIPTION
from RedfishCSDef import IS_STRUCTURE
from RedfishCSDef import IS_NOT_STRUCTURE
from RedfishCSDef import IS_EMPTY_PROPERTY
from RedfishCSDef import IS_NOT_EMPTY_PROPERTY
from RedfishCSDef import REDFISH_SCHEMA_NAMING_NOVERSIONED
from RedfishCSDef import REDFISH_URI_NAMESPACE_TUPLE_RESOURCE_TYPE
from RedfishCSDef import REDFISH_URI_NAMESPACE_TUPLE_VERSION
from RedfishCSDef import REDFISH_URI_NAMESPACE_TUPLE_TYPE_ID
from RedfishCSDef import REDFISH_GET_DATATYPE_KEY
from RedfishCSDef import REDFISH_GET_DATATYPE_CS_TYPE
from RedfishCSDef import REDFISH_GET_DATATYPE_VALUE
from RedfishCSDef import STRUCTURE_MEMBER_NEED_SECOND_PHASE_PARSE
from RedfishCSDef import VERBOSE_ERROR   
from RedfishCSDef import VERBOSE_WARNING 
from RedfishCSDef import VERBOSE_INFO    
from RedfishCSDef import VERBOSE_ERROR_EXIT

from ToolLogger import TOOL_LOG_NONE
from ToolLogger import TOOL_LOG_TO_CONSOLE
from ToolLogger import TOOL_LOG_TO_FILE
from ToolLogger import TOOL_LOG_SIMPLE_PROGRESS_DOTS

from GenCRelatedFile import RedfishCS_CRelatedFile
from GenEdk2Files import RedfishCSEdk2
from GenMarkdown import RedfishCS_MarkdownFile

class BreakForLoop(Exception):pass

CurrentProcessingFile = ""
VerboseOn = False
ProxyHost = ""
ProxyPort = ""

RedfishCSDataType = {"char":"RedfishCS_char",
                     "bool":"RedfishCS_bool",
                     "signed char":"RedfishCS_int8",
                     "unsigned char":"RedfishCS_uint8",
                     "int":"RedfishCS_int16",
                     "unsigned int":"RedfishCS_uint16",
                     "long int":"RedfishCS_int32",
                     "unsigned long int":"RedfishCS_uint32",
                     "long long":"RedfishCS_int64",
                     "unsigned long long":"RedfishCS_uint64",
                     "double":"RedfishCS_double",
                     "float":"RedfishCS_float",
                     "char *":"RedfishCS_char *",
                     "bool *":"RedfishCS_bool *",
                     "signed char *":"RedfishCS_int8 *",
                     "unsigned char *":"RedfishCS_uint8 *",
                     "int *":"RedfishCS_int16 *",
                     "unsigned int *":"RedfishCS_uint16 *",
                     "long int *":"RedfishCS_int32 *",
                     "unsigned long int *":"RedfishCS_uint32 *",
                     "long long *":"RedfishCS_int64 *",
                     "unsigned long long *":"RedfishCS_uint64 *",
                     "double *":"RedfishCS_double *",
                     "float *":"RedfishCS_float *",
                    }
RedfishPropertyDataType =   {
                            "$ref": "RedfishCS_Link",
                            "anyOf": "RedfishCS_Link",
                            "string": RedfishCSDataType["char *"],
                            "boolean": RedfishCSDataType["bool *"],     
                            "number": RedfishCSDataType["long long *"],                                                       
                            "integer": RedfishCSDataType["long long *"],
                            "array": "RedfishCS_Link",
                            "object": "RedfishCS_Link",
                            "EmptyProperty": "RedfishCS_Link"
                            }
# List: Corresponding properties of C structure
#ObjectInSchema = {}

# Tuple : (Structure Name, Structure Description, )
StructureName = {}

# StructureMemberDataType : (Datatype, MemberDescription, [SecondPhaseTuple]*, OrgKeyName, IsStructure, IsReadOnly, ISEmptyProp)
#   SecondPhaseTuple : (StrucMemName, ResourceTypeRef, ResourceType, SchemaVersion)
StructureMemberDataType = {}

NonStructureMemberDataType = {}
ExternResourceType = {}

def PrintMessage (Level, Message):
    if VerboseOn:
        ToolLogInformation.LogIt (Level.upper() + "(" + CurrentProcessingFile + "): "+ Message)
    else:
        if Level != VERBOSE_INFO:
            ToolLogInformation.LogIt (Level.upper() + "(" + CurrentProcessingFile + "): "+ Message)

    if Level == VERBOSE_ERROR_EXIT:
        sys.exit ()

# This retrieve external metafile reference over HTTP
def GetSchemaFromHttp (GenRedfishCStructureListInstance, url, TryLocalDisk):
    if url not in ExternResourceType:
        PrintMessage (VERBOSE_INFO, "***Retrieving external metadata from " + url)        
        req = urlrequest.Request (url)
        if ProxyHost != "" and ProxyPort != "":
            req.set_proxy (ProxyHost + ":" + ProxyPort, 'http')
        try :
            response = urlrequest.urlopen(req)
            r = json.loads (response.read().decode('utf-8'))            
        except Exception as ex:
            PrintMessage (VERBOSE_WARNING, "Failed to get information from URL.\n")
            print ("Failed to get information from URL.\n")
            #print (type(ex))
            #print (ex.args)
            GenCsInst = GenRedfishCStructureListInstance.GenerateCSInstance
            fileName = url.split ("/")[len (url.split ("/")) - 1]
            AbsfileName = os.path.normcase(GenCsInst.ParseDir + "\\" + fileName)
            if TryLocalDisk == True and os.path.exists (AbsfileName):
                PrintMessage (VERBOSE_INFO, "Trying to read " + AbsfileName + " from current target directory")
                JsonFileIo = open (AbsfileName)       
                r = json.loads(JsonFileIo.read())
                JsonFileIo.close()
            else:
                PrintMessage (VERBOSE_ERROR_EXIT, "Can't find " + fileName + " from current target directory")
                PrintMessage (VERBOSE_ERROR_EXIT, "Internet connection or the local schema file is required for this tool.\n" + \
                              "Please check internet connection or HTTP Proxy settings.\n" + \
                              "For proxy setting, please refer to option -proxy_host and proxy_port")
        ExternResourceType [url] = r        
    return ExternResourceType [url]

# This retrieve external metafile reference from local disk.
def GetSchemaFromLocalThenHttp (GenRedfishCStructureListInstance, url):
    if url not in ExternResourceType:    
        GenCsInst = GenRedfishCStructureListInstance.GenerateCSInstance
        fileName = url.split ("/")[len (url.split ("/")) - 1]
        AbsfileName = os.path.normcase(GenCsInst.ParseDir + "\\" + fileName)
        if os.path.exists (AbsfileName):
            PrintMessage (VERBOSE_INFO, "Read " + AbsfileName + " from current target directory")
            JsonFileIo = open (AbsfileName)       
            r = json.loads(JsonFileIo.read())
            JsonFileIo.close()
            ExternResourceType [url] = r
        else:
            PrintMessage (VERBOSE_INFO, AbsfileName + " not found!\n")
            return GetSchemaFromHttp (GenRedfishCStructureListInstance, url, False)
    return ExternResourceType [url]

def IsKeyReadOnly (TypeNameValue):
    if "readonly" in TypeNameValue:
        if TypeNameValue["readonly"] == True:
            return True
        else:
            return False
    else:
        return False

def IsRedfishTypeObject (Value):
    if Value == "object":
        return True
    return False

def IsRedfishObject (Value):
    IsString = isinstance (Value, str)
    if IsString:
        return False
    else:
        List = Value
        if "type" not in List:
            return False
        if not IsRedfishTypeObject (List ["type"]):
            return False
        if "properties" not in List:
            return False
        else:
            return True

def GetRedfishTypeProperty (key, Value):
    if not isinstance(Value["type"], list):
        if Value["type"] == "array":
            # check items
            if "items" not in Value:
                PrintMessage (VERBOSE_ERROR_EXIT, "Value type can't be determined, no items for array type." + "*" + key + "*")
            ThisTupleList = list (GetRedfishValueTypePass1 (key, Value["items"]))
            ThisTupleList [REDFISH_GET_DATATYPE_VALUE] = "array"
            return ThisTupleList

        return ("type",RedfishPropertyDataType [Value["type"]], Value["type"])
    else:
        if len (Value["type"]) == 1 and "null" not in Value["type"]:
            return ("type",RedfishPropertyDataType [Value["type"][0]], Value["type"])

        elif len (Value["type"]) == 2 and "null" in Value["type"]:
            for Num in range (0, len (Value["type"])):
                if Value["type"] [Num] != "null":
                    return ("type",RedfishPropertyDataType [Value["type"] [Num]], Value["type"])

        elif len (Value["type"]) > 2:
            # This is various data types.
            return ("type","RedfishCS_Vague *", "*")

        else:
            PrintMessage (VERBOSE_ERROR_EXIT,"Value type can't be determined " + "*" + key + "*")                    

# Return tuple (RedfishDatatypeKey, CS Datatype, RedfishDatatype)
def GetRedfishValueTypePass1 (key, Value):
    if "$ref" in Value:
        return ("$ref",Value ["$ref"],"$ref")
    elif "anyOf" in Value:
        return ("anyOf",RedfishPropertyDataType ["anyOf"],"anyof")
    elif "type" in Value:
        return GetRedfishTypeProperty (key, Value)
    else:
        sys.exit()
    return {"": ""}

def GetRedfishValueType (key, Value):
    if "$ref" in Value:
        PrintMessage (VERBOSE_INFO, "Value type of "+ key + ": " + RedfishPropertyDataType ["$ref"] )
        return RedfishPropertyDataType ["$ref"]      
    elif "anyOf" in Value:
        PrintMessage (VERBOSE_INFO, "Value type of "+ key + ": " + RedfishPropertyDataType ["anyOf"] ) 
        return RedfishPropertyDataType ["anyOf"] 
    elif "type" in Value:
        PrintMessage (VERBOSE_INFO, "Value type of "+ key + ": " + RedfishPropertyDataType [Value["type"]])                
        return RedfishPropertyDataType [Value["type"]] 
    else:
        PrintMessage (VERBOSE_ERROR_EXIT, "Value type can't be determined " + "*" + key + "*")
    return ""

def IsReferToAnotherRedfishNamespace (ResourceTypeRef):
    RefSchemaList = ResourceTypeRef [0].split ('/')
    Namespace = RefSchemaList [len (RefSchemaList) - 1]
    Pattern = re.compile ('[0-9A-Za-z_ ]*[.]{1}[vV]*[0-9]+[_.]{1}[0-9]+[_.]{1}[0-9]+[.]{1}[0-9A-Za-z_ ]*', 0)
    if re.match (Pattern, Namespace) != None:
        # This refers to version controller Redfish name space.
        # Check if property name is the same with Resource type name
        PropKeyList = ResourceTypeRef [1].split ('/')
        if Namespace.split ('.')[0] == PropKeyList[len (PropKeyList) - 1]:
            return True
        else:
            return False

# Return tuple (ResourceType, Version, TypeId)
def GetRedfishMetadataNamespaceFromRefUri (Uri):
        ResourceTypeRef = Uri.split ("#")
        Metadata = ResourceTypeRef[0].split ('/')
        MetadataUri = Metadata [len (Metadata) - 1]
        if ".json" not in MetadataUri:
            PrintMessage (VERBOSE_ERROR_EXIT, "Not valid $Ref:" + Uri)
        MetadataUri = MetadataUri.replace (".json", "")
        ResourceType = MetadataUri.split('.')[0]
        Version = MetadataUri.replace (ResourceType, "")
        if len (Version.split ('.')) > 2:
            OldVersion = Version
            Version = Version.lstrip ('.')
            Version = 'v' + Version.replace ('.', '_')
            PrintMessage (VERBOSE_WARNING, "Schema version format error (GetRedfishMetadataNamespaceFromRefUri)" + " ***" + ResourceType + "" + OldVersion + "->" + ResourceType + "_" + Version)

        Version = Version.replace ('.', '')
        if Version == "":
            Version = REDFISH_SCHEMA_NAMING_NOVERSIONED
        
        if '-' in ResourceType:
            ResourceType = ResourceType.replace('-', '')
        return [ResourceType, Version, ResourceTypeRef[1].replace ("/definitions/", "")]


def DataTypeFromRef (GenRedfishCStructureListInstance, RefProperty, StrucMemberKeyName, StrucMemberDesc, OrgKeyName, TypeNameValue):
    ResourceTypeRef = RefProperty ["$ref"].split ("#")    
    if ResourceTypeRef [0] != "" and "http://" in ResourceTypeRef [0]:
        # This is external metadata
        # Check if $ref refers to anotehr version controlled Redfish namespace schema.
        if IsReferToAnotherRedfishNamespace (ResourceTypeRef) == True:
            StructureMemberDataType [StrucMemberKeyName] = (RedfishPropertyDataType ["$ref"], StrucMemberDesc, {},OrgKeyName, IS_NOT_STRUCTURE, IsKeyReadOnly(TypeNameValue), IS_NOT_EMPTY_PROPERTY)
            return

        if SearchlocalSchemaFirst == False: # Retrieve Redfish schema from HTTP
            ExtMetadata = GetSchemaFromHttp (GenRedfishCStructureListInstance, ResourceTypeRef [0], True)
        else: # Retrieve Redfish schema from disk (same directory path as current processing Redfish JSON schema)
            ExtMetadata = GetSchemaFromLocalThenHttp (GenRedfishCStructureListInstance, ResourceTypeRef [0])

        TypeNameInMetadata = ResourceTypeRef [1].rsplit('/')[len(ResourceTypeRef [1].rsplit('/')) - 1]
        if "definitions" in ExtMetadata and TypeNameInMetadata in ExtMetadata["definitions"]:
            # Only handles the data type declared in external matadata refernce has "type" key defined in property.
            # Data type declared in metadata has no "type" key will use RedfishCS_Link as C data type.
            ReturnValue = GetRedfishValueTypePass1 (TypeNameInMetadata, ExtMetadata["definitions"][TypeNameInMetadata])
            if ReturnValue [REDFISH_GET_DATATYPE_KEY] != "type":
                StructureMemberDataType [StrucMemberKeyName] = (RedfishPropertyDataType ["$ref"], StrucMemberDesc, {},OrgKeyName,IS_NOT_STRUCTURE,IsKeyReadOnly(TypeNameValue), IS_NOT_EMPTY_PROPERTY)
            else:
                if ReturnValue [REDFISH_GET_DATATYPE_VALUE] == "object":
                    NameSpacelist = GetRedfishMetadataNamespaceFromRefUri (RefProperty ["$ref"])
                    NameSpacelist[REDFISH_URI_NAMESPACE_TUPLE_VERSION] = NameSpacelist[REDFISH_URI_NAMESPACE_TUPLE_VERSION].upper ()
                    GenCSList = GenRedfishCStructureList (GenRedfishCStructureListInstance.GenerateCSInstance, \
                                    NameSpacelist [REDFISH_URI_NAMESPACE_TUPLE_RESOURCE_TYPE], \
                                    NameSpacelist[REDFISH_URI_NAMESPACE_TUPLE_VERSION])
                    GenCSList.ExtMetadataUrl = ResourceTypeRef [0]                    
                    GenCSList.GenrateStureture (TypeNameInMetadata, ExtMetadata["definitions"][TypeNameInMetadata])
                    GenCSList.GenStructureMemberPass1 ()
                    if NameSpacelist [REDFISH_URI_NAMESPACE_TUPLE_RESOURCE_TYPE] not in StructureName and \
                       NameSpacelist[REDFISH_URI_NAMESPACE_TUPLE_VERSION] not in StructureName [NameSpacelist [REDFISH_URI_NAMESPACE_TUPLE_RESOURCE_TYPE]]:
                        PrintMessage (VERBOSE_ERROR_EXIT,"Structure is not built for " + NameSpacelist[REDFISH_URI_NAMESPACE_TUPLE_RESOURCE_TYPE] + "_" + NameSpacelist[REDFISH_URI_NAMESPACE_TUPLE_VERSION])
                    else:
                        StructureMemberDataType [StrucMemberKeyName] = \
                          (StructureName[NameSpacelist [REDFISH_URI_NAMESPACE_TUPLE_RESOURCE_TYPE]][NameSpacelist [REDFISH_URI_NAMESPACE_TUPLE_VERSION]][NameSpacelist[REDFISH_URI_NAMESPACE_TUPLE_TYPE_ID]][0] + " *", StrucMemberDesc,{},OrgKeyName,IS_STRUCTURE,IsKeyReadOnly(TypeNameValue),IS_NOT_EMPTY_PROPERTY)
                    GenCSList.ExtMetadataUrl = ""
                else:
                    StructureMemberDataType [StrucMemberKeyName] = (ReturnValue [REDFISH_GET_DATATYPE_CS_TYPE], StrucMemberDesc, {},OrgKeyName,IS_NOT_STRUCTURE, IsKeyReadOnly(TypeNameValue),IS_NOT_EMPTY_PROPERTY)
        else:
            PrintMessage (VERBOSE_ERROR,"typeName " + TypeNameInMetadata + " not in " + ResourceTypeRef [0])
            #sys.exit();                        
    else:
        # This is data type from local metadata
        if "#/definitions" not in RefProperty ["$ref"]:
            PrintMessage (VERBOSE_ERROR_EXIT,"#/definitions not exist for local data type reference($ref)")
        ResourceTypeRef = RefProperty ["$ref"].replace ("#/definitions/", "")
        ResourceTypeRef.replace ("/","_")
        StrucMem = GenRedfishCStructureListInstance.ResourceType + "_" + GenRedfishCStructureListInstance.SchemaVersion + "_" + ResourceTypeRef

        # Check if this local reference refers to the external metadata
        if GenRedfishCStructureListInstance.ExtMetadataUrl != "":
            DataTypeFromRef (GenRedfishCStructureListInstance, \
                            {"$ref":GenRedfishCStructureListInstance.ExtMetadataUrl + RefProperty ["$ref"]},\
                            StrucMem, \
                            StrucMemberDesc,\
                            OrgKeyName,\
                            TypeNameValue
                            )

        if StrucMem in StructureMemberDataType:
            StructureMemberDataType [StrucMemberKeyName] = (StructureMemberDataType [StrucMem][STRUCTURE_MEMBER_TUPLE_DATATYPE], StrucMemberDesc,\
                                                              {},\
                                                              OrgKeyName,\
                                                              IS_STRUCTURE,\
                                                              IsKeyReadOnly(TypeNameValue),\
                                                              IS_NOT_EMPTY_PROPERTY)
        elif ResourceTypeRef in StructureName[GenRedfishCStructureListInstance.ResourceType][GenRedfishCStructureListInstance.SchemaVersion]:
            StructureMemberDataType [StrucMemberKeyName] = (StructureName[GenRedfishCStructureListInstance.ResourceType][GenRedfishCStructureListInstance.SchemaVersion][ResourceTypeRef][STRUCTURE_NAME_TUPLE_NAME] + " *", StrucMemberDesc,\
                                                              {}, \
                                                              OrgKeyName,\
                                                              IS_STRUCTURE,\
                                                              IsKeyReadOnly(TypeNameValue),\
                                                              IS_NOT_EMPTY_PROPERTY)
        else:
            # Type Identifier is not an object
            # Check "type" of this Type Identifier
            StructureMemberDataType [StrucMemberKeyName] = (STRUCTURE_MEMBER_NEED_SECOND_PHASE_PARSE, \
                                                            StrucMemberDesc, \
                                                              (StrucMem,
                                                              ResourceTypeRef, \
                                                              GenRedfishCStructureListInstance.ResourceType,\
                                                              GenRedfishCStructureListInstance.SchemaVersion),\
                                                              OrgKeyName,\
                                                              IS_NOT_STRUCTURE,\
                                                              IsKeyReadOnly(TypeNameValue),\
                                                              IS_NOT_EMPTY_PROPERTY
                                                              )
            PrintMessage (VERBOSE_INFO,"#/definitions not exist for local data type reference. Set to second phase parsing required.")
            #sys.exit ()

# GenRedfishCStructureList class
# Generate list of Redfish schema to C structure
class GenRedfishCStructureList:
    def __init__ (self, GenerateCSInstance, ResourceType, SchemaVersion):
        self.ResourceType = ResourceType
        self.SchemaVersion = SchemaVersion.upper()
        self.SchemaRef = ""
        self.ExtMetadataUrl = ""
        self.ObjectInSchema = {}
        self.GenerateCSInstance = GenerateCSInstance
        self.RequiredProperties = {}      
    
    def IfObjectInProcess (self, key):
        return  self.ObjectInSchema [self.ResourceType][self.SchemaVersion][key][2]

    def SetObjectInProcess (self, key):
        tupleList = list(self.ObjectInSchema [self.ResourceType][self.SchemaVersion][key])
        tupleList[2] = True
        self.ObjectInSchema [self.ResourceType][self.SchemaVersion][key] = tupleList

    def IfObjectProcessed (self, key):
        return  self.ObjectInSchema [self.ResourceType][self.SchemaVersion][key][1]

    def SetObjectProcessed  (self, key):
        tupleList = list(self.ObjectInSchema [self.ResourceType][self.SchemaVersion][key])        
        tupleList[1] = True
        self.ObjectInSchema [self.ResourceType][self.SchemaVersion][key] = tupleList

    def GenrateStureture (self, DefinitionKey, DefinitionValue):
        if IsRedfishObject (DefinitionValue):         
            Desc = ""
            Name = REDFISH_STRUCT_NAME_HEAD + self.ResourceType + "_" + self.SchemaVersion + "_" + DefinitionKey + REDFISH_STRUCT_NAME_TAIL
            if self.ResourceType not in StructureName:
                StructureName [self.ResourceType] = {}
            if self.SchemaVersion not in StructureName [self.ResourceType]:
                StructureName [self.ResourceType][self.SchemaVersion] = {}
            
            if "description" in DefinitionValue:
                Desc = DefinitionValue["description"]

            StructureName [self.ResourceType][self.SchemaVersion][DefinitionKey] = (Name, Desc)

            if self.ResourceType not in self.ObjectInSchema:
                self.ObjectInSchema [self.ResourceType] = {}
            if self.SchemaVersion not in self.ObjectInSchema [self.ResourceType]:
                self.ObjectInSchema [self.ResourceType][self.SchemaVersion] = {}            
            self.ObjectInSchema [self.ResourceType][self.SchemaVersion][DefinitionKey] = (DefinitionValue["properties"], False, False)

            if DefinitionValue["properties"] != {}: # if peoperties is not empty
                for key in sorted (self.ObjectInSchema [self.ResourceType][self.SchemaVersion][DefinitionKey][0].keys()) :
                    self.GenrateStureture (DefinitionKey + "_" + key, self.ObjectInSchema [self.ResourceType][self.SchemaVersion][DefinitionKey][0][key])

            # Get required properties.
            if IsRedfishObject (DefinitionValue) and "required" in DefinitionValue:
                if self.SchemaRef == DefinitionKey:
                    self.RequiredProperties = DefinitionValue ["required"]

        else:
            # This is not an object
            if "type" in DefinitionValue:
                if self.ResourceType not in NonStructureMemberDataType:
                    NonStructureMemberDataType [self.ResourceType] = {}
                if self.SchemaVersion not in NonStructureMemberDataType [self.ResourceType]:
                    NonStructureMemberDataType [self.ResourceType][self.SchemaVersion] = {}
                NonStructureMemberDataType [self.ResourceType][self.SchemaVersion][DefinitionKey] = GetRedfishTypeProperty (DefinitionKey, DefinitionValue)

    def GenStructureMemberPass1 (self):
        for key in self.ObjectInSchema[self.ResourceType][self.SchemaVersion]:
            if self.IfObjectInProcess(key) or self.IfObjectProcessed (key):
                continue
            self.SetObjectInProcess (key)
            TypeName = self.ObjectInSchema [self.ResourceType][self.SchemaVersion][key][0]
            if TypeName == {}: # Is empty properties.
                self.SetObjectProcessed (key)
                continue
            for value in sorted(TypeName.keys()):
                StrcutMemberDesc = ""
                if "description" in TypeName[value]:
                    StrcutMemberDesc = TypeName[value]["description"]
                StrucMemberKeyName = self.ResourceType + "_" + self.SchemaVersion + "_" + key + "_" + value
                # Check if value data type is a structure
                if key + "_" + value in StructureName[self.ResourceType][self.SchemaVersion]:
                    StructureMemberDataType [StrucMemberKeyName] = \
                       (StructureName [self.ResourceType][self.SchemaVersion][key + "_" + value][STRUCTURE_NAME_TUPLE_NAME] + " *",\
                       StrcutMemberDesc,
                       {},\
                       value,\
                       IS_STRUCTURE,\
                       IsKeyReadOnly (TypeName[value]),\
                       IS_NOT_EMPTY_PROPERTY
                       )
                    PrintMessage (VERBOSE_INFO, StrucMemberKeyName + "-->" + StructureMemberDataType [StrucMemberKeyName][STRUCTURE_MEMBER_TUPLE_DATATYPE])
                elif not IsRedfishObject (TypeName[value]):
                    ReturnValue = GetRedfishValueTypePass1 (value, TypeName[value])
                    if ReturnValue [REDFISH_GET_DATATYPE_KEY] == "$ref":
                        DataTypeFromRef (self, {"$ref":ReturnValue[REDFISH_GET_DATATYPE_CS_TYPE]}, StrucMemberKeyName, StrcutMemberDesc, value, TypeName[value])
                    elif ReturnValue [REDFISH_GET_DATATYPE_KEY]  == "anyOf":
                        # Only handles "anyof" with one "$ref" and the "$ref" refers to data type has "type" key defined in
                        # metadata.
                        # The schema doen's meet above conditions use RedfishCS_Link as C data type.
                        NumberOfAnyofRef = 0;
                        if "anyOf" not in TypeName[value] and ReturnValue [REDFISH_GET_DATATYPE_VALUE] == "array":
                            # anyof is in items
                            if "items" not in TypeName[value]:
                                PrintMessage (VERBOSE_ERROR_EXIT,"No items defined in array object")
                            TypeName[value]["anyOf"] = TypeName[value]["items"]["anyOf"]

                        for index in range (0, len (TypeName[value]["anyOf"])):
                            if "$ref" in TypeName[value]["anyOf"][index]:
                                NumberOfAnyofRef += 1
                                RefIndex = index;
                        if NumberOfAnyofRef > 1:
                            StructureMemberDataType [StrucMemberKeyName] = (ReturnValue [REDFISH_GET_DATATYPE_CS_TYPE], StrcutMemberDesc, {}, value, IS_NOT_STRUCTURE, IsKeyReadOnly (TypeName[value]),IS_NOT_EMPTY_PROPERTY)
                        else:
                            # Check data type in metadata
                            DataTypeFromRef (self, TypeName[value]["anyOf"][RefIndex], StrucMemberKeyName, StrcutMemberDesc, value, TypeName[value])
                    elif ReturnValue[REDFISH_GET_DATATYPE_KEY] == "type":
                        StructureMemberDataType [StrucMemberKeyName] = (ReturnValue [REDFISH_GET_DATATYPE_CS_TYPE], StrcutMemberDesc, {}, value, IS_NOT_STRUCTURE, IsKeyReadOnly (TypeName[value]),IS_NOT_EMPTY_PROPERTY)
                    else:
                        PrintMessage (VERBOSE_ERROR_EXIT,"GetRedfishValueTypePass1 retuns fail.")
                    if StrucMemberKeyName not in StructureMemberDataType:
                        # This is the empty property.
                        StructureMemberDataType [StrucMemberKeyName] = (RedfishPropertyDataType ["EmptyProperty"], StrcutMemberDesc, {}, value, IS_NOT_STRUCTURE, IsKeyReadOnly (TypeName[value]),IS_EMPTY_PROPERTY)

                    PrintMessage (VERBOSE_INFO, StrucMemberKeyName + "-->" + StructureMemberDataType [StrucMemberKeyName][STRUCTURE_MEMBER_TUPLE_DATATYPE])
            self.SetObjectProcessed (key)

    def GenStructureMemberPass2(self):
        for key in StructureMemberDataType:
            if StructureMemberDataType [key][0] == STRUCTURE_MEMBER_NEED_SECOND_PHASE_PARSE:
                SecondPhaseList = StructureMemberDataType [key][STRUCTURE_MEMBER_TUPLE_SECOND_PHASE_LIST]
                if SecondPhaseList [0] in StructureMemberDataType:
                    StructureMemberDataType [key][0] = StructureMemberDataType [SecondPhaseList [0]][STRUCTURE_MEMBER_TUPLE_DATATYPE]
                elif SecondPhaseList[1] in StructureName[SecondPhaseList [2]][SecondPhaseList [3]]:
                    StructureMemberDataType [key][0] = \
                        StructureName[SecondPhaseList [2]][SecondPhaseList [3]][SecondPhaseList[1]][STRUCTURE_NAME_TUPLE_NAME] + " *"
                else:
                    if SecondPhaseList [2] not in NonStructureMemberDataType or \
                       SecondPhaseList [3] not in NonStructureMemberDataType [SecondPhaseList [2]] or \
                       SecondPhaseList [1] not in NonStructureMemberDataType [SecondPhaseList [2]][SecondPhaseList [3]]:
                        PrintMessage (VERBOSE_WARNING, "Can't find proper structure member data type in 2nd phase:" + key)
                    else:
                        List = list(StructureMemberDataType [key])
                        List [0] = NonStructureMemberDataType [SecondPhaseList [2]][SecondPhaseList [3]][SecondPhaseList [1]][1]
                        StructureMemberDataType [key] = List
#
# RedfishSchemaFile class
# 
class RedfishSchemaFile:
    def __init__(self, GenRedfishSchemaCs, File):
        self.FileAboslutePath = os.path.normpath(File)
        self.ResourceType =""
        self.SchemaVersion = ""
        self.CfileName = ""
        self.CIncludeFile = ""
        self.CIncludeFileText = ""
        self.SchemaRef = ""
 
        if os.path.exists(self.FileAboslutePath) == True:
            # Extract namespace of Redfish resource from file name.
            self.ResourceType = os.path.split(self.FileAboslutePath)[1].split ('.')[0]
            if '-' in self.ResourceType:
                self.ResourceType = self.ResourceType.replace ('-', '')
            self.SchemaVersion = os.path.split(self.FileAboslutePath)[1].split ('.')[1]
            if self.SchemaVersion == "json":
                # This schema has no verion control.
                self.SchemaVersion  = REDFISH_SCHEMA_NAMING_NOVERSIONED

            self.CfileName = self.ResourceType + "." + self.SchemaVersion + ".c"
            if self.SchemaVersion == REDFISH_SCHEMA_NAMING_NOVERSIONED:
                self.CIncludeFile = "Redfish_" + self.ResourceType + "_CS.h"
                self.Edk2CIncludeFile = "Redfish_" + self.ResourceType + "_CS.h"      
            else:
                self.CIncludeFile = "Redfish_" + self.ResourceType + "_" + self.SchemaVersion + "_CS.h"
                self.Edk2CIncludeFile = "Redfish_" + self.ResourceType + "_" + self.SchemaVersion + "_CS.h"
            # Read Redfish schema.
            PrintMessage (VERBOSE_INFO,"Read Redfish schema" + self.FileAboslutePath)
            self.JsonFileIo = open (self.FileAboslutePath)
            self.JsonRaw = self.JsonFileIo.read()
            self.JsonObj = json.loads (self.JsonRaw)
            self.JsonFileIo.close()
            if not "$ref" in self.JsonObj:
                PrintMessage (VERBOSE_WARNING,"$ref not found, skip this Redfish schema")
            else:
                Ref = self.JsonObj ["$ref"]
                self.SchemaRef = Ref.lstrip("#/definitions/")
                print("Generate C files of *" + self.ResourceType + "." + self.SchemaVersion + "* from file: " + self.FileAboslutePath + "\n")
                if ToolLogMode == TOOL_LOG_TO_FILE:
                    PrintMessage (VERBOSE_INFO, "Generate C files of *" + self.ResourceType + "." + self.SchemaVersion + "* from file: " + self.FileAboslutePath + "\n")
        else:
            PrintMessage (VERBOSE_ERROR_EXIT,"File not found " + self.FileAboslutePath)

# GenRedfishSchemaCS class
class GenRedfishSchemaCs:
    def __init__(self):
        self.File = ""
        self.OuputDirectory = ""
        self.ParseDir = ""
        # Clean up previous data.
        #if ObjectInSchema != {}:        
        #    ObjectInSchema.clear()
        if StructureName != {}:
            StructureName.clear()
        if StructureMemberDataType != {}:            
            StructureMemberDataType.clear()
        if NonStructureMemberDataType != {}:       
            NonStructureMemberDataType.clear()           

    def GenerateCS (self):
        SchemaFile = RedfishSchemaFile(self, self.File)
        if "$ref" not in SchemaFile.JsonObj:
            return
        if "definitions" not in SchemaFile.JsonObj:
            PrintMessage (VERBOSE_ERROR_EXIT,"No definitions key in " + SchemaFile.FileAboslutePath + "!")
        else:   
            SchemaFile.SchemaDefinition = SchemaFile.JsonObj ["definitions"]
            RedfishCs = GenRedfishCStructureList (self, SchemaFile.ResourceType, SchemaFile.SchemaVersion)
            RedfishCs.SchemaRef = SchemaFile.SchemaRef
            for key in SchemaFile.SchemaDefinition:
                if "anyOf" in SchemaFile.SchemaDefinition[key]:
                    anyOfList = SchemaFile.SchemaDefinition[key]["anyOf"]
                    for anyOfIndex in range (0, len(anyOfList)):
                        RedfishCs.GenrateStureture (key, anyOfList[anyOfIndex])             
                else:
                    RedfishCs.GenrateStureture (key, SchemaFile.SchemaDefinition[key])

            if len(RedfishCs.ObjectInSchema) != 0 and SchemaFile.SchemaRef in StructureName [RedfishCs.ResourceType][RedfishCs.SchemaVersion]:
                RedfishCs.GenStructureMemberPass1 ()
                RedfishCs.GenStructureMemberPass2 () # Handle "NEED_2ND_PHASE" strucutre member.

                # Generate C include file
                GenCS_Cfiles = RedfishCS_CRelatedFile (self, SchemaFile, RedfishCs, StructureName, StructureMemberDataType, NonStructureMemberDataType)
                GenCS_Cfiles.GenCSIncludefile ()
                GenCS_Cfiles.GenCSCfile ()

                #Generate EDK2 open source definitions
                if GenEdk2Binding:
                    GenCSEdk2 = RedfishCSEdk2 (self, SchemaFile, RedfishCs, StructureName, StructureMemberDataType, NonStructureMemberDataType, GenCS_Cfiles, OutputDir)
                    GenCSEdk2.Edk2AdditionalLibClass = Edk2AdditionalLibClass
                    GenCSEdk2.Edk2AdditionalPackage = Edk2AdditionalPackage
                    GenCSEdk2.Edk2RedfishJsonCsPackagePath = Edk2RedfishJsonCsPackagePath 
                    GenCSEdk2.Edk2RedfishJsonCsDriverAdditionalPackage = Edk2RedfishJsonCsDriverAdditionalPackage
                    GenCSEdk2.Edk2RedfishJsonCsDriverAdditionalLibrary = Edk2RedfishJsonCsDriverAdditionalLibrary
                    GenCSEdk2.Edk2DebugEnable = Edk2DebugEnable

                    GenCSEdk2.GenCSEdk2Files ()
                    GenCSEdk2.GenEdk2InfFile ()
                    GenCSEdk2.GenEdk2RedfishIntpFile ()
                    del GenCSEdk2

                # Generate Markdown file
                GenCS_Markdown = RedfishCS_MarkdownFile (self, SchemaFile, RedfishCs, StructureName, StructureMemberDataType, NonStructureMemberDataType, GenCS_Cfiles)
                GenCS_Markdown.GenMarkdown ()             

                del GenCS_Cfiles

            else:
                PrintMessage (VERBOSE_WARNING,"No C structure and source code to generate for :"+ SchemaFile.FileAboslutePath)

def GenerateCmake():
    ResourceType = {}

    CmakeFileDir = os.path.normpath(OutputDir + "/src")
    CmakeFileDirBuild = os.path.normpath(OutputDir + "/src/_build")
    CmakeFileFile = os.path.normpath(OutputDir + "/src/_build/CMakeLists.txt")
    CommonLibStr = "file(GLOB REDFISH_JSON_CS_LIB_SRC ${REDFISH_JSON_CS_LIB_SRC_ROOT}/*.c)\n\n"
    AddLibStr ="     ${REDFISH_JSON_CS_LIB_SRC}\n"
    if not os.path.exists (CmakeFileDirBuild):
        os.makedirs(CmakeFileDirBuild)

    if not os.path.exists (CmakeFileFile):
        fo = open(CmakeFileFile,"w")
        fo.write ("cmake_minimum_required(VERSION 2.6)\n\n")
        fo.write ("set(REDFISH_JSON_CS_LIB_SRC_ROOT ${CMAKE_CURRENT_SOURCE_DIR}/..)\n")
        fo.write ("set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/bin)\n\n")
        fo.write ("include_directories (${REDFISH_JSON_CS_LIB_SRC_ROOT}/../include/)\n")
        fo.write ("include_directories (${REDFISH_JSON_CS_LIB_SRC_ROOT}/)\n")
        if CmakeAdditionalIncludeDir != "":
            AddIncList = CmakeAdditionalIncludeDir.split(';')
            for index in range (0, len(AddIncList)):
                fo.write ("include_directories (\"" + AddIncList [index] + "\")\n")

        fo.write (CommonLibStr)
        fo.write ("source_group(\"Common Library Sources\" FILES ${REDFISH_JSON_CS_LIB_SRC})\n\n")
        fo.write ("add_library(RedfishCS STATIC\n")
        fo.write (AddLibStr)
        fo.write (")\n")

        fo.write ("if(CMAKE_COMPILER_IS_GNUCC)\n")
        fo.write ("add_definitions(-Wall -Wextra -Wdeclaration-after-statement -ggdb3)\n")
        fo.write ("endif()\n")
        fo.close()
    _buildDir = CmakeFileDir + os.path.normpath("/_build")
    
    for root, dirs, files in os.walk(CmakeFileDir):
        for fileindex in range (0, len(files)):
            if "_build" in root:
                continue
            if ".c" in files[fileindex] and root != CmakeFileDir and root != _buildDir:
                if "/" in root:
                    ResourceVersionList = root.replace (CmakeFileDir + "/", '').split('/')
                else:
                    ResourceVersionList = root.replace (CmakeFileDir + "\\", '').split('\\')

                if ResourceVersionList[0] not in ResourceType:
                    ResourceType[ResourceVersionList[0]] = {}
                if len(ResourceVersionList) != 1:
                    if ResourceVersionList[1] not in ResourceType[ResourceVersionList[0]]:
                        ResourceType[ResourceVersionList[0]][ResourceVersionList[1]] = {}
                    ResourceType[ResourceVersionList[0]][ResourceVersionList[1]] = files[fileindex]
    cmakeFileStr = ""
    cmakeAddLibStr = ""
    for ResType in sorted (ResourceType):
        cmakeFileStr += "file(GLOB " + "REDFISH_JSON_CS_" + ResType.upper() + "_SRC\n"
        for ResVersinon in sorted (ResourceType[ResType]):
            cmakeFileStr += "    ${REDFISH_JSON_CS_LIB_SRC_ROOT}/" + ResType +"/" + ResVersinon + "/" + ResourceType[ResType][ResVersinon] + "\n"
        cmakeFileStr += ")\n\n"
        cmakeAddLibStr += "    ${REDFISH_JSON_CS_" + ResType.upper() + "_SRC}\n"

    fi = open(CmakeFileFile,"r")
    cmakeFile = fi.read()
    fi.close()
    index = cmakeFile.find(CommonLibStr)
    cmakeFile = cmakeFile [:index + len(CommonLibStr)] + cmakeFileStr + cmakeFile [index + len(CommonLibStr):]

    index = cmakeFile.find(AddLibStr)
    cmakeFile = cmakeFile [:index + len(AddLibStr)] + cmakeAddLibStr + cmakeFile [index + len(AddLibStr):]
    fo = open(CmakeFileFile,"w")
    fo.write (cmakeFile)
    fo.close()
    return

def PrintHelp():
    print("GenRedfishSchemaCS [-all=Directory] [-errorStop] [-file=] [-proxy_host=]")
    print("                   [-proxy_port=] [-ExtRefLocalFirst] [-outputdir=] [-v]")
    print("                   [logfile] [-edk2] [-Edk2AdditionalLibClass=] [-Edk2Debug]")
    print("                   [-Edk2AdditionalPackage=] [-Edk2RedfishJsonCsPackagePath]")
    print("                   [-Edk2RedfishJsonCsDriverAdditionalPackage=] [-Edk2RedfishJsonCsDriverAdditionalLibrary]")
    print("  -all=[Directory]           : Process all Redfish scheman under the given")
    print("                               directoy or the current working directory.")
    print("  -errorStop                 : Stop processing all Redfish schemans. This")
    print("                               option only works against to -all.")
    print("  -file=                     : Process the specific Redfish schema file with")
    print("                               absolute directory path.")
    print("  -outputdir=                : Output file directory")
    print("  -cmakeAdditionalIncludeDir : CMake additional include file directory. The")
    print("                               directories assigned to this option are added to")
    print("                               CMake \"include_directories\" macro.")
    print("                               Use semicolon as separator if there are multiple")
    print("                               addtional include directories")
    print("  -proxy_host=               : proxy host name")
    print("  -proxy_port=               : proxy port number")
    print("  -ExtRefLocalFirst          : Search Redfish schema from local disk then")
    print("                               through HTTP for the external JSON schema")
    print("                               reference.")
    print("  -v                         : Throw messages during C structure generation")
    print("  -logfile                   : Message log to file. (RedfishCS.log)")
    print("  -edk2                      : Generate EDK2 opensource definition")
    print("     -Edk2Debug : Disable Optimize build option for debugging purpose")
    print("     -Edk2AdditionalLibClass=: Along with \"-edk2\", additinoal library classes")
    print("                               added to EDK2 INF file of each")
    print("                               Redfish-JSON-C-Struct-Converter library.")
    print("                               Use semicolon as separator if multiple library")
    print("                               classes are used in INF file.")
    print("                               For example: Lib1;Lib2")
    print("     -Edk2AdditionalPackage=:  Along with \"-edk2\", additinoal EDK2 packages")
    print("                               added to EDK2 INF file of each")
    print("                               Redfish-JSON-C-Struct-Converter library.")
    print("                               Use semicolon as separator if multiple EDK2")
    print("                               packages are used in INF file.")
    print("                               For example: Pachage1;Package2")
    print("     -Edk2RedfishJsonCsPackagePath: Along with \"-edk2\", target EDK2 package")
    print("                                    for the generated EDK2")
    print("                                    Redfish-JSON-C-Struct-Converter source")
    print("                                    files. For example: Edk2RedfishPkg")
    print("                                    Edk2RedfishJsonCsPackagePath is used for")
    print("                                    generating correct file path of")
    print("                                    Redfish-JSON-C-Struct-Converter EDK2 ")
    print("                                    libraries and drivers in below file when")
    print("                                    use -edk2 options.")
    print("    -Edk2RedfishJsonCsDriverAdditionalPackage: Along with \"-edk2\", additinoal")
    print("                                               EDK2 packages for building EFI")
    print("                                               Redfish to C Structure DXE ")
    print("                                               Driver. Use semicolon as separator if ")
    print("                                               multiple EDK2 packages are used in")
    print("                                               INF file.")
    print("    -Edk2RedfishJsonCsDriverAdditionalLibrary: Along with \"-edk2\", additinoal")
    print("                                               EDK2 libraries for building EFI")
    print("                                               Redfish to C Structure DXE Driver.")
    print("                                               Use semicolon as separator if ")
    print("                                               multiple library classes are used")
    print("                                               in INF file.")
    print("                  1) RedfishCsIntp/RedfishSchemaCsInterpreter_Component.dsc:")
    print("                     Components to build")
    print("                  2) RedfishCsIntp/RedfishSchemaCsInterpreter_Lib.dsc:")
    print("                     Libraries to build")      
    return

def PrintHelpMessageExit (str):
    print (str)
    PrintHelp()
    sys.exit()

# GenRedfishSchemaCS [-all Directory] [-File] [-proxy_host =] [-proxy_port = ] [-v] [-edk2]
# -all Directory: process all Redfish scheman under the given directoy.
# -file : Process the specific Redfish schema file with absolute directory path
FileOnly = False
DirectoryFiles = False
ParseDirectory = ""
GenEdk2Binding = False
OutputDir = os.getcwd()
ErrorStop = False
SearchlocalSchemaFirst = False
ToolLogMode = TOOL_LOG_TO_CONSOLE
CmakeAdditionalIncludeDir = ""

# For EDk2 open source
Edk2CAdditionalLibClass = "# Your additioanl Libraries"
Edk2AdditionalPackage = "# Your additional Packages"
Edk2RedfishJsonCsPackagePath = "RedfishCsIntpPkg"

# Test Redfish property
#JsonFileIo = open ("BiosAR.json")
#Lines = JsonFileIo.readlines()
#for i in range(0, len(Lines)): 
#    Lines[i] = Lines[i].replace("\\\"","\"")
#    Lines[i] = Lines[i].replace("\"","\\\"")
#    Lines[i] = Lines[i].replace("\n","")
#    Lines[i] = "\"" + Lines[i] + "\\n\" \\\n"
#Lines[0] = "CHAR8 AttributeReg_text[] =  " + Lines[0]     
#JsonFileIo.close()
#JsonFileIo = open ("AttributeReg100.h_","w")
#JsonFileIo.writelines (Lines)
#JsonFileIo.close()
# Test Redfish property

print ("\n\nHPE Redfish Schema to C Structure Generator Copyrights 2018-2021 v1.2_schema2020.4")

if "-logfile" in sys.argv:
    ToolLogInformation = ToolLogger.ToolLog (TOOL_LOG_TO_FILE, "RedfishCs.log")
else:
    ToolLogInformation = ToolLogger.ToolLog (TOOL_LOG_TO_CONSOLE, "")  

for argIndex in range (1, len(sys.argv)):       
    if "-v" in sys.argv [argIndex]:
        VerboseOn = True

    elif "-outputdir" in sys.argv [argIndex]:
        List = sys.argv [argIndex].split ('=')        
        if len (List) == 1:
            PrintHelpMessageExit ("Please assign output directory\n")                            
        OutputDir = List [1]         

    elif "-cmakeAdditionalIncludeDir=" in sys.argv [argIndex]:
        List = sys.argv [argIndex].split ('=')
        if len (List) == 1:
            PrintHelpMessageExit ("Please assign addirional include for CMAKE \"include_directories\".\n")   
        CmakeAdditionalIncludeDir = List [1]

    elif "-proxy_host=" in sys.argv [argIndex]:
        List = sys.argv [argIndex].split ('=')
        if len (List) == 1:
            PrintHelpMessageExit ("Please assign proxy host\n")   
        ProxyHost = List [1]

    elif "proxy_port=" in sys.argv [argIndex]:          
        List = sys.argv [argIndex].split ('=')        
        if len (List) == 1:
            PrintHelpMessageExit ("Please assign proxy port\n")                       
        ProxyPort = List [1]

    elif "-all" in sys.argv [argIndex]:
        List = sys.argv [argIndex].split ('=')
        DirectoryFiles = True
        if len (List) == 1:
            ParseDirectory = os.getcwd()
        else:
            ParseDirectory = List [1]

    elif "errorStop" in sys.argv [argIndex]:
        ErrorStop = True;

    elif "-file=" in sys.argv [argIndex]:
        List = sys.argv [argIndex].split ('=')
        FileOnly = True
        FileName = List [1]
        ParseDirectory = os.getcwd()

    elif "ExtRefLocalFirst" in sys.argv [argIndex]:
        SearchlocalSchemaFirst = True

    elif "-edk2" in sys.argv [argIndex]:
        GenEdk2Binding = True
        Edk2DebugEnable = False
        Edk2AdditionalLibClass = ""
        Edk2AdditionalPackage =""
        Edk2RedfishJsonCsPackagePath = ""
        Edk2RedfishJsonCsDriverAdditionalPackage = ""
        Edk2RedfishJsonCsDriverAdditionalLibrary = ""
        for argIndex2 in range (1, len(sys.argv)):  
            if "-Edk2Debug" in sys.argv [argIndex2]:
                Edk2DebugEnable = True
            if "-Edk2AdditionalLibClass=" in sys.argv [argIndex2]:
                List = sys.argv [argIndex2].split ('=')
                Edk2AdditionalLibClass = List [1]
                Edk2AdditionalLibClass = Edk2AdditionalLibClass.replace(";", "\n  ")
            if "-Edk2AdditionalPackage=" in sys.argv [argIndex2]:
                List = sys.argv [argIndex2].split ('=')
                Edk2AdditionalPackage = List [1]
                Edk2AdditionalPackage = Edk2AdditionalPackage.replace(";", "\n  ")
            if "-Edk2RedfishJsonCsPackagePath" in sys.argv [argIndex2]:
                List = sys.argv [argIndex2].split ('=')
                Edk2RedfishJsonCsPackagePath = List [1]
            if "-Edk2RedfishJsonCsDriverAdditionalPackage" in sys.argv [argIndex2]:
                List = sys.argv [argIndex2].split ('=')
                Edk2RedfishJsonCsDriverAdditionalPackage = List [1]
                Edk2RedfishJsonCsDriverAdditionalPackage = Edk2RedfishJsonCsDriverAdditionalPackage.replace(";", "\n  ")
            if "-Edk2RedfishJsonCsDriverAdditionalLibrary" in sys.argv [argIndex2]:
                List = sys.argv [argIndex2].split ('=')
                Edk2RedfishJsonCsDriverAdditionalLibrary = List [1]                      
                Edk2RedfishJsonCsDriverAdditionalLibrary = Edk2RedfishJsonCsDriverAdditionalLibrary.replace(";", "\n  ")                
                 
    elif "-Edk2AdditionalLibClass=" in sys.argv [argIndex] or \
         "-Edk2AdditionalPackage=" in sys.argv [argIndex] or \
         "-Edk2RedfishJsonCsPackagePath" in sys.argv [argIndex] or \
         "-Edk2RedfishJsonCsDriverAdditionalPackage" in sys.argv [argIndex] or \
         "-Edk2RedfishJsonCsDriverAdditionalLibrary" in sys.argv [argIndex] or \
         "-Edk2Debug"  in sys.argv [argIndex]:
         continue

    elif "-logfile" in sys.argv [argIndex]:
        ToolLogMode = TOOL_LOG_TO_FILE

    else:
        PrintHelpMessageExit ("")   

if FileOnly and DirectoryFiles:
    PrintHelpMessageExit ("Can't assign both -file and -all\n")       

if not FileOnly and not DirectoryFiles:
    PrintHelpMessageExit ("Please assign -file or -all\n")       

if FileOnly:
#try:
    GenCS = GenRedfishSchemaCs ()     
    GenCS.File = FileName
    CurrentProcessingFile = GenCS.File
    GenCS.OuputDirectory = OutputDir
    GenCS.ParseDir = os.path.dirname(FileName)
    GenCS.GenerateCS()
    GenerateCmake()
#except Exception as ex:
#    PrintMessage (VERBOSE_ERROR,"Failed to generate C structure for :" + GenCS.File)  
#    print (ex)        
    sys.exit(0)

if DirectoryFiles:
    if not os.path.isdir(ParseDirectory):
        PrintMessage (VERBOSE_ERROR_EXIT,"Directory is not exist.\n")

    for root, dirs, files in os.walk(ParseDirectory):
        for fn in files:
            try:
                GenCS = GenRedfishSchemaCs ()
                GenCS.File = ParseDirectory + "//" + fn
                CurrentProcessingFile = fn               
                GenCS.OuputDirectory = OutputDir
                GenCS.ParseDir = ParseDirectory
                GenCS.GenerateCS();
                del GenCS
            except Exception as ex:
                PrintMessage (VERBOSE_ERROR,"Failed to generate C structure for :" + GenCS.File)
                print (ex)
                if ErrorStop:
                    sys.exit()
    GenerateCmake()
    sys.exit(0)            

