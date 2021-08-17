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
import re

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
from RedfishCSDef import REDFISH_ARRAY_CS_TAIL
from RedfishCSDef import STRUCTURE_MEMBER_TUPLE_IS_STRUCTURE
from RedfishCSDef import STRUCTURE_MEMBER_TUPLE_IS_READONLY
from RedfishCSDef import STRUCTURE_MEMBER_TUPLE_IS_REQUIRED
from RedfishCSDef import STRUCTURE_MEMBER_TUPLE_ORG_KEY_NAME
from RedfishCSDef import IS_STRUCTURE
from RedfishCSDef import IS_REDFISH_CS_LINK_ARRAY
from RedfishCSDef import IS_NOT_REDFISH_CS_LINK_ARRAY
from RedfishCSDef import LOGFOR_CSTRUCTURE_TO_JSON_IS_ROOT
from RedfishCSDef import LOGFOR_CSTRUCTURE_TO_JSON_IS_LINK_ARRAY
from RedfishCSDef import LOGFOR_CSTRUCTURE_TO_JSON_IS_STRUCT_MEM_NAME
from RedfishCSDef import LOGFOR_CSTRUCTURE_TO_JSON_IS_STRUCT_MEM_NAME_DATATYPE
from RedfishCSDef import LOGFOR_CSTRUCTURE_TO_JSON_IS_STRUCT_MEM_NAME_JSON_KEY
from RedfishCSDef import LOGFOR_CSTRUCTURE_TO_JSON_ALIAS_STRUCTURE_NAME
from RedfishCSDef import LOGFOR_CSTRUCTURE_TO_JSON_RESOURCETYPE
from RedfishCSDef import LOGFOR_CSTRUCTURE_TO_JSON_VERSION

HPECopyright  = "//\n" \
                "// Auto-generated file by Redfish Schema C Structure Generator.\n" + \
                "// https://github.com/DMTF/Redfish-Schema-C-Struct-Generator.\n" + \
                "//\n" + \
                "//  (C) Copyright 2019-2021 Hewlett Packard Enterprise Development LP<BR>\n" + \
                "//\n" + \
                "// Copyright Notice:\n" + \
                "// Copyright 2019-2021 Distributed Management Task Force, Inc. All rights reserved.\n" + \
                "// License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-JSON-C-Struct-Converter/blob/master/LICENSE.md\n" +\
                "//\n"

CCodeErrorExitCode = C_SRC_TAB_SPACE + "if (Status != RedfishCS_status_success) {\n" +\
                     C_SRC_TAB_SPACE * 2 + "goto Error;\n" +\
                     C_SRC_TAB_SPACE + "}\n\n"

NatrualDataTypeArray = ["RedfishCS_Link","RedfishCS_char","RedfishCS_bool","RedfishCS_int64"]

class BreakForLoop(Exception):pass

class RedfishCS_CRelatedFile:
    def RemoveStructureNameHead (Self, StructureName):
        StructMemHeadList = StructureName.split('_');
        StructMemHead = StructMemHeadList[0].replace (REDFISH_STRUCT_NAME_HEAD, "")
        for StructMemHeadListIndex in range (1, len (StructMemHeadList)):
            StructMemHead += '_' + StructMemHeadList[StructMemHeadListIndex] 
        return StructMemHead      

    def IsKeyRequiredError (self, StructureMemberDataType, StructDataTypeKey, Member, IsRootStruc):
        if IsRootStruc:
            if StructureMemberDataType[StructDataTypeKey][STRUCTURE_MEMBER_TUPLE_ORG_KEY_NAME] in self.RequiredProperties:
                return "goto Error;"
            else:
                if "@odata.type" == StructureMemberDataType[StructDataTypeKey][STRUCTURE_MEMBER_TUPLE_ORG_KEY_NAME]:
                    return "goto Error;"
                else:
                    return "/*This is not the required property.*/"
        else:
            return "/*This is not the required property.*/"

    def CCodeGenString (self, StructureMemberDataType, StructDataTypeKey, Member, IsRootStruc):
        if IsRootStruc:
            JsonPtr = "JsonObj"
            RetPtr = "&Cs->"
        else:
            JsonPtr = "TempJsonObj"
            RetPtr = "&(*Dst)->"
        StrFunText = C_SRC_TAB_SPACE + "Status = GetRedfishPropertyStr (Cs, " + JsonPtr + ", " + \
                     "\"" + StructureMemberDataType[StructDataTypeKey][STRUCTURE_MEMBER_TUPLE_ORG_KEY_NAME] + "\", " +\
                      RetPtr + Member + \
                      ");\n"
        StrFunText += C_SRC_TAB_SPACE + "if (Status != RedfishCS_status_success && Status != RedfishCS_status_not_found) {goto Error;}\n"+\
                      C_SRC_TAB_SPACE + "else {if (Status == RedfishCS_status_not_found)" + "{" + self.IsKeyRequiredError(StructureMemberDataType, StructDataTypeKey, Member, IsRootStruc) + "}}\n\n"
     
        return StrFunText

    def CCodeGenInt64 (self, StructureMemberDataType, StructDataTypeKey, Member, IsRootStruc):
        if IsRootStruc:
            JsonPtr = "JsonObj"
            RetPtr = "&Cs->"
        else:
            JsonPtr = "TempJsonObj"
            RetPtr = "&(*Dst)->"

        StrFunText = C_SRC_TAB_SPACE + "Status = GetRedfishPropertyInt64 (Cs, " + JsonPtr + ", " + \
                     "\"" + StructureMemberDataType[StructDataTypeKey][STRUCTURE_MEMBER_TUPLE_ORG_KEY_NAME] + "\", " +\
                      RetPtr + Member + \
                      ");\n"
        StrFunText += C_SRC_TAB_SPACE + "if (Status != RedfishCS_status_success && Status != RedfishCS_status_not_found) {goto Error;}\n"+\
                      C_SRC_TAB_SPACE + "else {if (Status == RedfishCS_status_not_found)" + "{" + self.IsKeyRequiredError(StructureMemberDataType, StructDataTypeKey, Member, IsRootStruc) + "}}\n\n"
     
        return StrFunText

    def CCodeGenBoolean (self, StructureMemberDataType, StructDataTypeKey, Member, IsRootStruc):
        if IsRootStruc:
            JsonPtr = "JsonObj"
            RetPtr = "&Cs->"
        else:
            JsonPtr = "TempJsonObj"
            RetPtr = "&(*Dst)->"

        StrFunText = C_SRC_TAB_SPACE + "Status = GetRedfishPropertyBoolean (Cs, " + JsonPtr + ", " + \
                     "\"" + StructureMemberDataType[StructDataTypeKey][STRUCTURE_MEMBER_TUPLE_ORG_KEY_NAME] + "\", " +\
                      RetPtr + Member + \
                      ");\n"
        StrFunText += C_SRC_TAB_SPACE + "if (Status != RedfishCS_status_success && Status != RedfishCS_status_not_found) {goto Error;}\n"+\
                      C_SRC_TAB_SPACE + "else {if (Status == RedfishCS_status_not_found)" + "{" + self.IsKeyRequiredError(StructureMemberDataType, StructDataTypeKey, Member, IsRootStruc) + "}}\n\n"
     
        return StrFunText

    def CCodeGenVague (self, StructureMemberDataType, StructDataTypeKey, Member, IsRootStruc):
        if IsRootStruc:
            JsonPtr = "JsonObj"
            RetPtr = "&Cs->"
        else:
            JsonPtr = "TempJsonObj"
            RetPtr = "&(*Dst)->"

        StrFunText = C_SRC_TAB_SPACE + "Status = GetRedfishPropertyVague (Cs, " + JsonPtr + ", " + \
                     "\"" + StructureMemberDataType[StructDataTypeKey][STRUCTURE_MEMBER_TUPLE_ORG_KEY_NAME] + "\", " +\
                      RetPtr + Member + \
                      ");\n"
        StrFunText += C_SRC_TAB_SPACE + "if (Status != RedfishCS_status_success && Status != RedfishCS_status_not_found) {goto Error;}\n"+\
                      C_SRC_TAB_SPACE + "else {if (Status == RedfishCS_status_not_found)" + "{" + self.IsKeyRequiredError(StructureMemberDataType, StructDataTypeKey, Member, IsRootStruc) + "}}\n\n"
                     
        return StrFunText

    def CCodeGenLink (self, StructureMemberDataType, StructDataTypeKey, Member, IsRootStruc):
        if IsRootStruc:
            JsonPtr = "JsonObj"
            StrucPtr = "&Cs->"            
        else:
            JsonPtr = "TempJsonObj"
            StrucPtr = "&(*Dst)->"            

        StrFunText = C_SRC_TAB_SPACE + "InitializeLinkHead (" + StrucPtr + Member + ");\n"
        StrFunText += C_SRC_TAB_SPACE + "Status = CreateCsUriOrJsonByNode (Cs, " + JsonPtr + ", \"" +\
                     StructureMemberDataType[StructDataTypeKey][STRUCTURE_MEMBER_TUPLE_ORG_KEY_NAME] + "\"," +\
                     " Cs->Header.ThisUri, " + StrucPtr + Member + ");\n"
        StrFunText += C_SRC_TAB_SPACE + "if (Status != RedfishCS_status_success && Status != RedfishCS_status_not_found) {goto Error;}\n"+\
                      C_SRC_TAB_SPACE + "else {if (Status == RedfishCS_status_not_found)" + "{" + self.IsKeyRequiredError(StructureMemberDataType, StructDataTypeKey, Member, IsRootStruc) + "}}\n\n"
     
        return StrFunText

    def CCodeGenLinkArray (self, StructureMemberDataType, StructDataTypeKey, Member, IsRootStruc):
        if IsRootStruc:
            JsonPtr = "JsonObj"
            StrucPtr = "&Cs->"            
        else:
            JsonPtr = "TempJsonObj"
            StrucPtr = "&(*Dst)->"            

        StrFunText = C_SRC_TAB_SPACE + "InitializeLinkHead (" + StrucPtr + Member + ");\n"
        StrFunText += C_SRC_TAB_SPACE + "Status = CreateCsUriOrJsonByNodeArray (Cs, " + JsonPtr + ", \"" +\
                     StructureMemberDataType[StructDataTypeKey][STRUCTURE_MEMBER_TUPLE_ORG_KEY_NAME] + "\"," +\
                     " Cs->Header.ThisUri, " + StrucPtr + Member + ");\n"
        StrFunText += C_SRC_TAB_SPACE + "if (Status != RedfishCS_status_success && Status != RedfishCS_status_not_found) {goto Error;}\n"+\
                      C_SRC_TAB_SPACE + "else {if (Status == RedfishCS_status_not_found)" + "{" + self.IsKeyRequiredError(StructureMemberDataType, StructDataTypeKey, Member, IsRootStruc) + "}}\n\n"
           
        return StrFunText

    def GenNaturalDataTypeArrayChar (self):
        StrFunText = "//\n"
        StrFunText += "//Generate C structure for Redfish_char_Array.\n"
        StrFunText += "//\n"
        StrFunText += "static RedfishCS_status GenRedfishCS_char_Array_Element (void *Cs, json_t *JsonArrayObj, RedfishCS_uint64 ArraySize, RedfishCS_char_Array *DstBuffer)\n{\n" + \
         C_SRC_TAB_SPACE + "json_t *TempJsonObj;\n" + \
         C_SRC_TAB_SPACE + "RedfishCS_uint64 Index;\n" + \
         C_SRC_TAB_SPACE + "RedfishCS_status Status;\n" + \
         C_SRC_TAB_SPACE + "RedfishCS_char_Array *ThisElement;\n\n" + \
         C_SRC_TAB_SPACE + "if (DstBuffer == NULL) {\n" + \
         C_SRC_TAB_SPACE * 2 + "return RedfishCS_status_invalid_parameter;\n" + \
         C_SRC_TAB_SPACE + "}\n" + \
         C_SRC_TAB_SPACE + "ThisElement = DstBuffer;\n" + \
         C_SRC_TAB_SPACE + "for (Index = 0; Index < ArraySize; Index ++) {\n" + \
         C_SRC_TAB_SPACE * 2 + "TempJsonObj = json_array_get (JsonArrayObj, (RedfishCS_int)Index);\n" + \
         C_SRC_TAB_SPACE * 2 + "Status = allocateDuplicateStr (Cs, (char *)json_string_value(TempJsonObj), (RedfishCS_void **)&ThisElement->ArrayValue);\n" + \
         C_SRC_TAB_SPACE * 2 + "if (Status != RedfishCS_status_success){\n" + \
         C_SRC_TAB_SPACE * 3 + "goto Error;\n" + \
         C_SRC_TAB_SPACE * 2 + "}\n" + \
         C_SRC_TAB_SPACE * 2 + "ThisElement = ThisElement->Next;\n" + \
         C_SRC_TAB_SPACE + "}\n" + \
         "Error:;\n" + \
         C_SRC_TAB_SPACE + "return Status;\n" + \
         "}\n"
        self.CFuncText.append (StrFunText)

    def GenNaturalDataTypeArrayBool (self):
        StrFunText = "//\n"
        StrFunText += "//Generate C structure for RedfishCS_bool_Array.\n"
        StrFunText += "//\n"
        StrFunText += "static RedfishCS_status GenRedfishCS_bool_Array_Element (void *Cs, json_t *JsonArrayObj, RedfishCS_uint64 ArraySize, RedfishCS_bool_Array *DstBuffer)\n{\n" + \
         C_SRC_TAB_SPACE + "json_t *TempJsonObj;\n" + \
         C_SRC_TAB_SPACE + "RedfishCS_uint64 Index;\n" + \
         C_SRC_TAB_SPACE + "RedfishCS_status Status;\n" + \
         C_SRC_TAB_SPACE + "RedfishCS_bool_Array *ThisElement;\n\n" + \
         C_SRC_TAB_SPACE + "if (DstBuffer == NULL) {\n" + \
         C_SRC_TAB_SPACE * 2 + "return RedfishCS_status_invalid_parameter;\n" + \
         C_SRC_TAB_SPACE + "}\n" + \
         C_SRC_TAB_SPACE + "ThisElement = DstBuffer;\n" + \
         C_SRC_TAB_SPACE + "for (Index = 0; Index < ArraySize; Index ++) {\n" + \
         C_SRC_TAB_SPACE * 2 + "TempJsonObj = json_array_get (JsonArrayObj, (RedfishCS_int)Index);\n" + \
         C_SRC_TAB_SPACE * 2 + "if (TempJsonObj == NULL){\n" + \
         C_SRC_TAB_SPACE * 3 + "goto Error;\n" + \
         C_SRC_TAB_SPACE * 2 + "}\n" + \
         C_SRC_TAB_SPACE * 2 + "Status = allocateRecordCsMemory(Cs, sizeof(RedfishCS_bool), (RedfishCS_void **)&ThisElement->ArrayValue);\n" + \
         C_SRC_TAB_SPACE * 2 + "if (Status != RedfishCS_status_success){\n" + \
         C_SRC_TAB_SPACE * 3 + "goto Error;\n" + \
         C_SRC_TAB_SPACE * 2 + "}\n" + \
         C_SRC_TAB_SPACE * 2 + "ThisElement = ThisElement->Next;\n" + \
         C_SRC_TAB_SPACE + "}\n" + \
         "Error:;\n" + \
         C_SRC_TAB_SPACE + "return Status;\n" + \
         "}\n"     
        self.CFuncText.append (StrFunText)

    def GenNaturalDataTypeArrayInt64 (self):
        StrFunText = "//\n"
        StrFunText += "//Generate C structure for RedfishCS_int64_Array.\n"
        StrFunText += "//\n"
        StrFunText += "static RedfishCS_status GenRedfishCS_int64_Array_Element (void *Cs, json_t *JsonArrayObj, RedfishCS_uint64 ArraySize, RedfishCS_int64_Array *DstBuffer)\n{\n" + \
         C_SRC_TAB_SPACE + "json_t *TempJsonObj;\n" + \
         C_SRC_TAB_SPACE + "RedfishCS_uint64 Index;\n" + \
         C_SRC_TAB_SPACE + "RedfishCS_status Status;\n" + \
         C_SRC_TAB_SPACE + "RedfishCS_int64_Array *ThisElement;\n\n" + \
         C_SRC_TAB_SPACE + "if (DstBuffer == NULL) {\n" + \
         C_SRC_TAB_SPACE * 2 + "return RedfishCS_status_invalid_parameter;\n" + \
         C_SRC_TAB_SPACE + "}\n" + \
         C_SRC_TAB_SPACE + "ThisElement = DstBuffer;\n" + \
         C_SRC_TAB_SPACE + "for (Index = 0; Index < ArraySize; Index ++) {\n" + \
         C_SRC_TAB_SPACE * 2 + "TempJsonObj = json_array_get (JsonArrayObj, (RedfishCS_int)Index);\n" + \
         C_SRC_TAB_SPACE * 2 + "if (TempJsonObj == NULL){\n" + \
         C_SRC_TAB_SPACE * 3 + "goto Error;\n" + \
         C_SRC_TAB_SPACE * 2 + "}\n" + \
         C_SRC_TAB_SPACE * 2 + "Status = allocateRecordCsMemory(Cs, sizeof(RedfishCS_uint64), (RedfishCS_void **)&ThisElement->ArrayValue);\n" + \
         C_SRC_TAB_SPACE * 2 + "if (Status != RedfishCS_status_success){\n" + \
         C_SRC_TAB_SPACE * 3 + "goto Error;\n" + \
         C_SRC_TAB_SPACE * 2 + "}\n" + \
         C_SRC_TAB_SPACE * 2 + "ThisElement = ThisElement->Next;\n" + \
         C_SRC_TAB_SPACE + "}\n" + \
         "Error:;\n" + \
         C_SRC_TAB_SPACE + "return Status;\n" + \
         "}\n"      
        self.CFuncText.append (StrFunText)

    def CCodeGenStringJson (self, StructureName, MemberName, CStructPointer, IsArrayStruct):
        JsonKey = self.LogForCStructureToJson[StructureName][LOGFOR_CSTRUCTURE_TO_JSON_IS_STRUCT_MEM_NAME][MemberName][LOGFOR_CSTRUCTURE_TO_JSON_IS_STRUCT_MEM_NAME_JSON_KEY]
        Str = C_SRC_TAB_SPACE + "// " + JsonKey + " \n"
        if IsArrayStruct:
            Str = C_SRC_TAB_SPACE * 2 + "// " + JsonKey + " \n"
            Str +=  C_SRC_TAB_SPACE * 2 + "if (InsertJsonStringObj (ArrayMember, \"" + JsonKey + "\", NextArrayItem->" + MemberName + ") != RedfishCS_status_success) {goto Error;}\n\n"
        else:
            Str = C_SRC_TAB_SPACE + "// " + JsonKey + " \n"
            Str +=  C_SRC_TAB_SPACE + "if (InsertJsonStringObj (CsJson, \"" + JsonKey + "\", CSPtr->" + MemberName + ") != RedfishCS_status_success) {goto Error;}\n\n"
        return Str

    def CCodeGenLinkJson (self, StructureName, MemberName, CStructPointer, IsArrayStruct):
        JsonKey = self.LogForCStructureToJson[StructureName][LOGFOR_CSTRUCTURE_TO_JSON_IS_STRUCT_MEM_NAME][MemberName][LOGFOR_CSTRUCTURE_TO_JSON_IS_STRUCT_MEM_NAME_JSON_KEY]
        Str = C_SRC_TAB_SPACE + "// " + JsonKey + " \n"
        if IsArrayStruct:
            Str = C_SRC_TAB_SPACE * 2+ "// " + JsonKey + " \n"
            Str +=  C_SRC_TAB_SPACE * 2 + "if (InsertJsonLinkObj (ArrayMember, \"" + JsonKey + "\", &NextArrayItem->" + MemberName + ") != RedfishCS_status_success) {goto Error;}\n\n"
        else:
            Str = C_SRC_TAB_SPACE + "// " + JsonKey + " \n"
            Str +=  C_SRC_TAB_SPACE + "if (InsertJsonLinkObj (CsJson, \"" + JsonKey + "\", &CSPtr->" + MemberName + ") != RedfishCS_status_success) {goto Error;}\n\n"
        return Str

    def CCodeGenInt64Json (self, StructureName, MemberName, CStructPointer, IsArrayStruct):
        JsonKey = self.LogForCStructureToJson[StructureName][LOGFOR_CSTRUCTURE_TO_JSON_IS_STRUCT_MEM_NAME][MemberName][LOGFOR_CSTRUCTURE_TO_JSON_IS_STRUCT_MEM_NAME_JSON_KEY]
        Str = C_SRC_TAB_SPACE + "// " + JsonKey + " \n"

        if IsArrayStruct:
            Str = C_SRC_TAB_SPACE * 2+ "// " + JsonKey + " \n"
            Str +=  C_SRC_TAB_SPACE * 2 + "if (InsertJsonInt64Obj (ArrayMember, \"" + JsonKey + "\", NextArrayItem->" + MemberName + ") != RedfishCS_status_success) {goto Error;}\n\n"
        else:
            Str = C_SRC_TAB_SPACE + "// " + JsonKey + " \n"
            Str +=  C_SRC_TAB_SPACE + "if (InsertJsonInt64Obj (CsJson, \"" + JsonKey + "\", CSPtr->" + MemberName + ") != RedfishCS_status_success) {goto Error;}\n\n"
        return Str

    def CCodeGenBooleanJson (self, StructureName, MemberName, CStructPointer, IsArrayStruct):
        JsonKey = self.LogForCStructureToJson[StructureName][LOGFOR_CSTRUCTURE_TO_JSON_IS_STRUCT_MEM_NAME][MemberName][LOGFOR_CSTRUCTURE_TO_JSON_IS_STRUCT_MEM_NAME_JSON_KEY]
        if IsArrayStruct:
            Str = C_SRC_TAB_SPACE * 2 + "// " + JsonKey + " \n"
            Str +=  C_SRC_TAB_SPACE * 2 + "if (InsertJsonBoolObj (ArrayMember, \"" + JsonKey + "\", NextArrayItem->" + MemberName + ") != RedfishCS_status_success) {goto Error;}\n\n"
        else:
            Str = C_SRC_TAB_SPACE + "// " + JsonKey + " \n"
            Str +=  C_SRC_TAB_SPACE + "if (InsertJsonBoolObj (CsJson, \"" + JsonKey + "\", CSPtr->" + MemberName + ") != RedfishCS_status_success) {goto Error;}\n\n"
        return Str

    def CCodeGenVagueJson (self, StructureName, MemberName, CStructPointer, IsArrayStruct):
        JsonKey = self.LogForCStructureToJson[StructureName][LOGFOR_CSTRUCTURE_TO_JSON_IS_STRUCT_MEM_NAME][MemberName][LOGFOR_CSTRUCTURE_TO_JSON_IS_STRUCT_MEM_NAME_JSON_KEY]
        if IsArrayStruct:
            Str = C_SRC_TAB_SPACE * 2 + "// " + JsonKey + " \n"
            Str +=  C_SRC_TAB_SPACE * 2 + "if (InsertJsonVagueObj (ArrayMember, \"" + JsonKey + "\", NextArrayItem->" + MemberName + ") != RedfishCS_status_success) {goto Error;}\n\n"
        else:
            Str = C_SRC_TAB_SPACE + "// " + JsonKey + " \n"
            Str +=  C_SRC_TAB_SPACE + "if (InsertJsonVagueObj (CsJson, \"" + JsonKey + "\", CSPtr->" + MemberName + ") != RedfishCS_status_success) {goto Error;}\n\n"
        return Str       

    def CCodeGenStringArrayJson (self, StructureName, MemberName, CStructPointer, IsArrayStruct):
        JsonKey = self.LogForCStructureToJson[StructureName][LOGFOR_CSTRUCTURE_TO_JSON_IS_STRUCT_MEM_NAME][MemberName][LOGFOR_CSTRUCTURE_TO_JSON_IS_STRUCT_MEM_NAME_JSON_KEY]
        Str = C_SRC_TAB_SPACE + "// " + JsonKey + " \n"        
        if IsArrayStruct:
            Str = C_SRC_TAB_SPACE * 2 + "// " + JsonKey + " \n"
            Str +=  C_SRC_TAB_SPACE * 2 + "if (InsertJsonStringArrayObj (ArrayMember, \"" + JsonKey + "\", NextArrayItem->" + MemberName + ") != RedfishCS_status_success) {goto Error;}\n\n"
        else:
            Str = C_SRC_TAB_SPACE + "// " + JsonKey + " \n"
            Str +=  C_SRC_TAB_SPACE + "if (InsertJsonStringArrayObj (CsJson, \"" + JsonKey + "\", CSPtr->" + MemberName + ") != RedfishCS_status_success) {goto Error;}\n\n"
        return Str

    def CCodeGenInt64ArrayJson (self, StructureName, MemberName, CStructPointer, IsArrayStruct):
        JsonKey = self.LogForCStructureToJson[StructureName][LOGFOR_CSTRUCTURE_TO_JSON_IS_STRUCT_MEM_NAME][MemberName][LOGFOR_CSTRUCTURE_TO_JSON_IS_STRUCT_MEM_NAME_JSON_KEY]
        Str = C_SRC_TAB_SPACE + "// " + JsonKey + " \n"

        if IsArrayStruct:
            Str = C_SRC_TAB_SPACE * 2+ "// " + JsonKey + " \n"
            Str +=  C_SRC_TAB_SPACE * 2 + "if (InsertJsonInt64ArrayObj (ArrayMember, \"" + JsonKey + "\", NextArrayItem->" + MemberName + ") != RedfishCS_status_success) {goto Error;}\n\n"
        else:
            Str = C_SRC_TAB_SPACE + "// " + JsonKey + " \n"
            Str +=  C_SRC_TAB_SPACE + "if (InsertJsonInt64ArrayObj (CsJson, \"" + JsonKey + "\", CSPtr->" + MemberName + ") != RedfishCS_status_success) {goto Error;}\n\n"
        return Str

    def CCodeGenBooleanArrayJson (self, StructureName, MemberName, CStructPointer, IsArrayStruct):
        JsonKey = self.LogForCStructureToJson[StructureName][LOGFOR_CSTRUCTURE_TO_JSON_IS_STRUCT_MEM_NAME][MemberName][LOGFOR_CSTRUCTURE_TO_JSON_IS_STRUCT_MEM_NAME_JSON_KEY]
        if IsArrayStruct:
            Str = C_SRC_TAB_SPACE * 2 + "// " + JsonKey + " \n"
            Str +=  C_SRC_TAB_SPACE * 2 + "if (InsertJsonBoolArrayObj (ArrayMember, \"" + JsonKey + "\", NextArrayItem->" + MemberName + ") != RedfishCS_status_success) {goto Error;}\n\n"
        else:
            Str = C_SRC_TAB_SPACE + "// " + JsonKey + " \n"
            Str +=  C_SRC_TAB_SPACE + "if (InsertJsonBoolArrayObj (CsJson, \"" + JsonKey + "\", CSPtr->" + MemberName + ") != RedfishCS_status_success) {goto Error;}\n\n"
        return Str

    def CCodeGenLinkArrayJson (self, StructureName, MemberName, CStructPointer, IsArrayStruct):
        JsonKey = self.LogForCStructureToJson[StructureName][LOGFOR_CSTRUCTURE_TO_JSON_IS_STRUCT_MEM_NAME][MemberName][LOGFOR_CSTRUCTURE_TO_JSON_IS_STRUCT_MEM_NAME_JSON_KEY]
        if IsArrayStruct:
            Str = C_SRC_TAB_SPACE * 2 + "// " + JsonKey + " \n"
            Str +=  C_SRC_TAB_SPACE * 2 + "if (InsertJsonLinkArrayObj (ArrayMember, \"" + JsonKey + "\", &NextArrayItem->" + MemberName + ") != RedfishCS_status_success) {goto Error;}\n\n"
        else:
            Str = C_SRC_TAB_SPACE + "// " + JsonKey + " \n"
            Str +=  C_SRC_TAB_SPACE + "if (InsertJsonLinkArrayObj (CsJson, \"" + JsonKey + "\", &CSPtr->" + MemberName + ") != RedfishCS_status_success) {goto Error;}\n\n"
        return Str      
        
        return ""        
         
    def RemoveTailCSPattern (self, Content):
        Pattern = REDFISH_STRUCT_NAME_TAIL + " "
        Found = re.search (Pattern, Content)
        if Found != None:
            ContentSplit = Content.split (Pattern)
            NewContent = ContentSplit[0] + " " + ContentSplit[1] 
            return NewContent
        Pattern = REDFISH_STRUCT_NAME_TAIL + "$"
        Found = re.search (Pattern, Content)
        if Found != None:
            NewContent = Content.rstrip (REDFISH_STRUCT_NAME_TAIL)
            return NewContent
        Pattern = REDFISH_STRUCT_NAME_TAIL + "[A-za-Z0-9]+"
        if Found != None:
            Content = Content
            return Content        
        Content = Content
        return Content    

    def CCodeGenStructArrayElementFuncNameCode (self, StructureMemberDataType, ResourceType, SchemaVersion, TypeName, key, StructArrayMemDataType, StrucName, GenElementFunc, IsRootStruc):
        if IsRootStruc:
            JsonPtr = "JsonObj"
            StrucPtr = "&Cs->"
        else:
            JsonPtr = "TempJsonObj"
            StrucPtr = "&(*Dst)->"

        StrFunText = ""
        StructArrayMemDataTypeName = StructArrayMemDataType.replace("_Array_CS", REDFISH_STRUCT_NAME_TAIL)
        StrFunText += "static RedfishCS_status " + GenElementFunc + "(" + self.CRedfishRootStructureName + " *Cs, json_t *JsonObj, RedfishCS_uint64 Index,  " + \
                     StructArrayMemDataTypeName + " **Dst)\n{\n" + \
                     C_SRC_TAB_SPACE + "RedfishCS_status Status;\n" + \
                     C_SRC_TAB_SPACE + "json_t *TempJsonObj;\n\n" + \
                     C_SRC_TAB_SPACE + "Status = RedfishCS_status_success;\n" + \
                     C_SRC_TAB_SPACE + "TempJsonObj = json_array_get (JsonObj, (RedfishCS_int)Index);\n" + \
                     C_SRC_TAB_SPACE + "if (TempJsonObj == NULL) {\n" + \
                     C_SRC_TAB_SPACE * 2 + "return RedfishCS_status_not_found;\n" + \
                     C_SRC_TAB_SPACE + "}\n" +\
                     C_SRC_TAB_SPACE + "Status = allocateRecordCsZeroMemory(Cs, sizeof(" + StructArrayMemDataTypeName + "), (RedfishCS_void **)Dst);\n" + \
                     C_SRC_TAB_SPACE + "if (Status != RedfishCS_status_success){\n" + \
                     C_SRC_TAB_SPACE * 2 + "goto Error;\n" + \
                     C_SRC_TAB_SPACE + "}\n"

        # Loop to generate code for structure member.
        TempText, IsEmptyProp =  self.GenStructureMemberCCode (ResourceType, SchemaVersion, TypeName, StrucName, False, True)                     
        if IsEmptyProp:
            # This is empty property. CreateCsJsonByNode() is used implicitely to get JSON property . CsTypeJson variable is required.
            SearchStr = "RedfishCS_status Status;\n"
            i = StrFunText.find(SearchStr)
            StrFunText = StrFunText[:i + len (SearchStr)] + C_SRC_TAB_SPACE + "RedfishCS_Type_JSON_Data *CsTypeJson;\n" + StrFunText[i + len (SearchStr):]

        StrFunText += TempText
        StrFunText += C_SRC_TAB_SPACE + "return RedfishCS_status_success;\n"
        StrFunText += "Error:;\n"
        StrFunText += C_SRC_TAB_SPACE + "return Status;\n}\n"        
        self.CFuncText.append (StrFunText)

    def CCodeGenCallNaturalDataTypeArrayFunName (self, ResourceType, SchemaVersion, TypeName, StructureMemberDataType, StructDataTypeKey, StructArrayMemDataType, Member, IsRootStruc):
        if IsRootStruc:
            JsonPtr = "JsonObj"
            StrucPtr = "&Cs->"
        else:
            JsonPtr = "TempJsonObj"
            StrucPtr = "&(*Dst)->"

        StructFuncName = StructArrayMemDataType
        StrFunText = C_SRC_TAB_SPACE + "Status = Gen" + StructFuncName + "Cs (Cs, " + JsonPtr + ", \"" +\
                     StructureMemberDataType[StructDataTypeKey][STRUCTURE_MEMBER_TUPLE_ORG_KEY_NAME] + "\", " + StrucPtr + \
                     Member + ");\n"
        StrFunText += C_SRC_TAB_SPACE + "if (Status != RedfishCS_status_success && Status != RedfishCS_status_not_found) {goto Error;}\n"+\
                      C_SRC_TAB_SPACE + "else {if (Status == RedfishCS_status_not_found)" + "{" + self.IsKeyRequiredError(StructureMemberDataType, StructDataTypeKey, Member, IsRootStruc) + "}}\n\n"
        return StrFunText, "Gen" + StructArrayMemDataType + "Cs"

    def CCodeGenNaturalDataTypeArrayFuncNameCode (self, StructureMemberDataType, ResourceType, SchemaVersion, TypeName, key, StructMemDataType, FuncName, IsRootStruc):
        if FuncName in self.StructFuncName:
            FuncDeclare = "static RedfishCS_status " + FuncName + "(" + self.CRedfishRootStructureName + " *Cs, json_t *JsonObj, char *Key, " + \
                                                StructMemDataType + " **Dst);\n"
            if FuncDeclare not in self.StructFuncNameTypedef:
                self.StructFuncNameTypedef.append(FuncDeclare)
            return        
        self.StructFuncName.append(FuncName)            
        StrFunText = "//\n"
        StrFunText += "//Generate C structure for " + StructMemDataType + "\n"
        StrFunText += "//\n"         
        StrFunText += "static RedfishCS_status " + FuncName + "(" + self.CRedfishRootStructureName + " *Cs, json_t *JsonObj, char *Key, " + \
                     StructMemDataType + " **Dst)\n{\n" + \
                     C_SRC_TAB_SPACE + "RedfishCS_status Status;\n" +\
                     C_SRC_TAB_SPACE + "json_t *TempJsonObj;\n" + \
                     C_SRC_TAB_SPACE + "RedfishCS_uint64 ArraySize;\n\n" + \
                     C_SRC_TAB_SPACE + "Status = RedfishCS_status_success;\n" + \
                     C_SRC_TAB_SPACE + "TempJsonObj = json_object_get(JsonObj, Key);\n" + \
                     C_SRC_TAB_SPACE + "if (TempJsonObj == NULL) {\n" + \
                     C_SRC_TAB_SPACE * 2 + "return RedfishCS_status_not_found;\n" +\
                     C_SRC_TAB_SPACE + "}\n\n" + \
                     C_SRC_TAB_SPACE + "if (json_is_array(TempJsonObj) != RedfishCS_boolean_true) {\n"+\
                     C_SRC_TAB_SPACE * 2 + "return RedfishCS_status_invalid_parameter;\n"+\
                     C_SRC_TAB_SPACE + "}\n\n"+\
                     C_SRC_TAB_SPACE + "ArraySize = json_array_size (TempJsonObj);\n"+\
                     C_SRC_TAB_SPACE + "Status = allocateArrayRecordCsMemory(Cs, sizeof (" + StructMemDataType + "), ArraySize, (RedfishCS_void **)Dst);\n"+\
                     C_SRC_TAB_SPACE + "if (Status != RedfishCS_status_success){\n" +\
                     C_SRC_TAB_SPACE * 2 + "goto Error;\n" + \
                     C_SRC_TAB_SPACE + "}\n" +\
                     C_SRC_TAB_SPACE + "if (*Dst == NULL) {\n" +\
                     C_SRC_TAB_SPACE * 2 + "// Empty array\n" + \
                     C_SRC_TAB_SPACE * 2 + "return RedfishCS_status_success;\n" + \
                     C_SRC_TAB_SPACE + "}\n" + \
                     C_SRC_TAB_SPACE + "Status = Gen" + StructMemDataType + "_Element (Cs, TempJsonObj, ArraySize, *Dst);\n" +\
                     C_SRC_TAB_SPACE + "if (Status != RedfishCS_status_success){\n" + \
                     C_SRC_TAB_SPACE * 2 + "goto Error;\n" + \
                     C_SRC_TAB_SPACE + "}\n"
        StrFunText += "Error:;\n"
        StrFunText += C_SRC_TAB_SPACE + "return Status;\n}\n"
        # Gen array elememt
        if StructMemDataType == "RedfishCS_char_Array":
            self.GenNaturalDataTypeArrayChar ()
        elif StructMemDataType == "RedfishCS_bool_Array":
            self.GenNaturalDataTypeArrayBool ()
        elif StructMemDataType == "RedfishCS_int64_Array":
            self.GenNaturalDataTypeArrayInt64 ()
        else:
            print("***ERROR*** Unsupported natural datatype array: " + StructMemDataType + "\n")
            sys.exit()
        self.CFuncText.append (StrFunText)
        return

    def CCodeGenCallStructArrayFunName (self, ResourceType, SchemaVersion, TypeName, StructureMemberDataType, StructDataTypeKey, StructArrayMemDataType, Member, IsRootStruc):
        if IsRootStruc:
            JsonPtr = "JsonObj"
            StrucPtr = "&Cs->"
        else:        
            JsonPtr = "TempJsonObj"
            StrucPtr = "&(*Dst)->"

        #StructFuncName = self.RemoveStructureNameHead (StructArrayMemDataType).rstrip(REDFISH_STRUCT_NAME_TAIL)
        StructFuncName = self.RemoveTailCSPattern (self.RemoveStructureNameHead (StructArrayMemDataType))

        StructFuncName = StructFuncName.replace (ResourceType + "_", "").replace (SchemaVersion + "_", "")
        StrFunText = C_SRC_TAB_SPACE + "Status = Gen" + StructFuncName + "Cs (Cs, " + JsonPtr + ", \"" +\
                     StructureMemberDataType[StructDataTypeKey][STRUCTURE_MEMBER_TUPLE_ORG_KEY_NAME] + "\", " + StrucPtr + \
                     Member + ");\n"
        StrFunText += C_SRC_TAB_SPACE + "if (Status != RedfishCS_status_success && Status != RedfishCS_status_not_found) {goto Error;}\n"+\
                      C_SRC_TAB_SPACE + "else {if (Status == RedfishCS_status_not_found)" + "{" + self.IsKeyRequiredError(StructureMemberDataType, StructDataTypeKey, Member, IsRootStruc) + "}}\n\n"
                          
        return StrFunText, "Gen" + StructFuncName + "Cs"        

    def CCodeGenCallStructFunName (self, ResourceType, SchemaVersion, TypeName, StructureMemberDataType, StructDataTypeKey, Member, IsRootStruc):
        if IsRootStruc:
            JsonPtr = "JsonObj"
            StrucPtr = "&Cs->"
        else:
            JsonPtr = "TempJsonObj"
            StrucPtr = "&(*Dst)->"

        #StructFuncName = self.RemoveStructureNameHead (StructureMemberDataType[StructDataTypeKey][STRUCTURE_MEMBER_TUPLE_DATATYPE]).rstrip(REDFISH_STRUCT_NAME_TAIL)
        StructFuncName = self.RemoveTailCSPattern (self.RemoveStructureNameHead (StructureMemberDataType[StructDataTypeKey][STRUCTURE_MEMBER_TUPLE_DATATYPE]))
        StructFuncName = StructFuncName.replace(ResourceType + "_", "").replace (SchemaVersion + "_", "").replace (TypeName + "_", "").replace (" *", "")
        # Check if funciton name already exist.
        NewFuncName = "Gen" + StructFuncName + "Cs"
        if NewFuncName in self.CfunctionsCreated:
            # [0] : Schema name
            # [1] : Schema version
            # [2] : Instance of the duplication
            if self.CfunctionsCreated[NewFuncName][0] != ResourceType or self.CfunctionsCreated[NewFuncName][1] != SchemaVersion:
                self.CfunctionsCreated[NewFuncName][2] = self.CfunctionsCreated[NewFuncName][2] + 1
                NewFuncName = "Gen" + StructFuncName + "_" + str(self.CfunctionsCreated[NewFuncName][2]) + "_" + "Cs"

        #StrFunText = C_SRC_TAB_SPACE + "Status = Gen" + StructFuncName + "Cs (Cs, " + JsonPtr + ", \"" +\
        StrFunText = C_SRC_TAB_SPACE + "Status = " + NewFuncName + " (Cs, " + JsonPtr + ", \"" +\
                     StructureMemberDataType[StructDataTypeKey][STRUCTURE_MEMBER_TUPLE_ORG_KEY_NAME] + "\", " + StrucPtr + \
                     Member + ");\n"
        StrFunText += C_SRC_TAB_SPACE + "if (Status != RedfishCS_status_success && Status != RedfishCS_status_not_found) {goto Error;}\n"+\
                      C_SRC_TAB_SPACE + "else {if (Status == RedfishCS_status_not_found)" + "{" + self.IsKeyRequiredError(StructureMemberDataType, StructDataTypeKey, Member, IsRootStruc) + "}}\n\n"
        #return StrFunText, "Gen" + StructFuncName + "Cs"
        return StrFunText, NewFuncName

    def CCodeGenStructArrayFuncNameCode(self, StructureMemberDataType, ResourceType, SchemaVersion, TypeName, key, StructArrayMemDataType, StrucName, FuncName, IsRootStruc):                      
        if FuncName in self.StructFuncName:
            FuncDeclare = "static RedfishCS_status " + FuncName + "(" + self.CRedfishRootStructureName + " *Cs, json_t *JsonObj, char *Key, " + \
                                                StructArrayMemDataType + " **Dst);\n"
            if FuncDeclare not in self.StructFuncNameTypedef:
                self.StructFuncNameTypedef.append(FuncDeclare)
            return        
        self.StructFuncName.append(FuncName)            
        GenElementFunc = FuncName.replace("Cs", "_ElementCs")
        StrFunText = "//\n"
        StrFunText += "//Generate C structure for " + StructArrayMemDataType + "\n"
        StrFunText += "//\n"         
        StrFunText += "static RedfishCS_status " + FuncName + "(" + self.CRedfishRootStructureName + " *Cs, json_t *JsonObj, char *Key, " + \
                     StructArrayMemDataType + " **Dst)\n{\n" + \
                     C_SRC_TAB_SPACE + "RedfishCS_status Status;\n" +\
                     C_SRC_TAB_SPACE + "json_t *TempJsonObj;\n" + \
                     C_SRC_TAB_SPACE + "RedfishCS_uint64 ArraySize;\n" + \
                     C_SRC_TAB_SPACE + "RedfishCS_uint64 Index;\n" + \
                     C_SRC_TAB_SPACE + StructArrayMemDataType +" *ThisElement;\n\n" + \
                     C_SRC_TAB_SPACE + "Status = RedfishCS_status_success;\n" + \
                     C_SRC_TAB_SPACE + "TempJsonObj = json_object_get(JsonObj, Key);\n" + \
                     C_SRC_TAB_SPACE + "if (TempJsonObj == NULL) {\n" + \
                     C_SRC_TAB_SPACE * 2 + "return RedfishCS_status_not_found;\n" +\
                     C_SRC_TAB_SPACE + "}\n\n" + \
                     C_SRC_TAB_SPACE + "if (json_is_array(TempJsonObj) != RedfishCS_boolean_true) {\n"+\
                     C_SRC_TAB_SPACE * 2 + "return RedfishCS_status_invalid_parameter;\n"+\
                     C_SRC_TAB_SPACE + "}\n\n"+\
                     C_SRC_TAB_SPACE + "ArraySize = json_array_size (TempJsonObj);\n"+\
                     C_SRC_TAB_SPACE + "Status = allocateArrayRecordCsMemory(Cs, sizeof (" + StructArrayMemDataType + "), ArraySize, (RedfishCS_void **)Dst);\n"+\
                     C_SRC_TAB_SPACE + "if (Status != RedfishCS_status_success){\n" +\
                     C_SRC_TAB_SPACE * 2 + "goto Error;\n" + \
                     C_SRC_TAB_SPACE + "}\n" +\
                     C_SRC_TAB_SPACE + "if (*Dst == NULL) {\n" +\
                     C_SRC_TAB_SPACE * 2 + "// Empty array\n" + \
                     C_SRC_TAB_SPACE * 2 + "return RedfishCS_status_success;\n" + \
                     C_SRC_TAB_SPACE + "}\n" + \
                     C_SRC_TAB_SPACE + "ThisElement = *Dst;\n" +\
                     C_SRC_TAB_SPACE + "for (Index = 0; Index < ArraySize; Index ++) {\n" + \
                     C_SRC_TAB_SPACE * 2 + "Status = " + GenElementFunc + "(Cs, TempJsonObj, Index, &ThisElement->ArrayValue);\n" + \
                     C_SRC_TAB_SPACE * 2 + "if (Status != RedfishCS_status_success){\n" + \
                     C_SRC_TAB_SPACE * 3 + "goto Error;\n" + \
                     C_SRC_TAB_SPACE * 2 + "}\n" + \
                     C_SRC_TAB_SPACE * 2 + "ThisElement = ThisElement->Next;\n" + \
                     C_SRC_TAB_SPACE + "}\n"
        StrFunText += "Error:;\n"
        StrFunText += C_SRC_TAB_SPACE + "return Status;\n}\n"        
        self.CCodeGenStructArrayElementFuncNameCode (StructureMemberDataType, ResourceType, SchemaVersion, TypeName, key, StructArrayMemDataType, StrucName, GenElementFunc, IsRootStruc)
        self.CFuncText.append (StrFunText)        
        return

    def CCodeGenStructFuncNameCode (self, StructureMemberDataType, ResourceType, SchemaVersion, TypeName, key, StrucName, FuncName, IsRootStruc):
        if FuncName in self.StructFuncName:
            FuncDeclare = "static RedfishCS_status " + FuncName + "(" + self.CRedfishRootStructureName + " *Cs, json_t *JsonObj, char *Key, " + \
                                                StructureMemberDataType [key][STRUCTURE_MEMBER_TUPLE_DATATYPE].replace("_NOVERSIONED", "") + "*Dst);\n"
            if FuncDeclare not in self.StructFuncNameTypedef:
                self.StructFuncNameTypedef.append(FuncDeclare)
            return

        self.StructFuncName.append(FuncName)
        StrFunText = "//\n"
        StrFunText += "//Generate C structure for " +StructureMemberDataType [key][STRUCTURE_MEMBER_TUPLE_ORG_KEY_NAME] + "\n"
        StrFunText += "//\n"         
        StrFunText += "static RedfishCS_status " + FuncName + "(" + self.CRedfishRootStructureName + " *Cs, json_t *JsonObj, char *Key, " + \
                     StructureMemberDataType [key][STRUCTURE_MEMBER_TUPLE_DATATYPE].replace("_NOVERSIONED", "") + "*Dst)\n{\n" + \
                     C_SRC_TAB_SPACE + "RedfishCS_status Status;\n" +\
                     C_SRC_TAB_SPACE + "json_t *TempJsonObj;\n\n" + \
                     C_SRC_TAB_SPACE + "Status = RedfishCS_status_success;\n" + \
                     C_SRC_TAB_SPACE + "TempJsonObj = json_object_get(JsonObj, Key);\n" + \
                     C_SRC_TAB_SPACE + "if (TempJsonObj == NULL) {\n" + \
                     C_SRC_TAB_SPACE * 2 + "return RedfishCS_status_not_found;\n" +\
                     C_SRC_TAB_SPACE + "}\n" + \
                     C_SRC_TAB_SPACE + "Status = allocateRecordCsMemory(Cs, sizeof(" + StructureMemberDataType [key][STRUCTURE_MEMBER_TUPLE_DATATYPE].replace("_NOVERSIONED", "").replace(" *","") + "), (RedfishCS_void **)Dst);\n" + \
                     C_SRC_TAB_SPACE + "if (Status != RedfishCS_status_success){\n" +\
                     C_SRC_TAB_SPACE * 2 + "goto Error;\n" + \
                     C_SRC_TAB_SPACE + "}\n"

        # Loop to generate code for structure member.
        TempText, IsEmptyProp =  self.GenStructureMemberCCode (ResourceType, SchemaVersion, TypeName, StrucName, False, False)                     
        if IsEmptyProp:
            # This is empty property. CreateCsJsonByNode() is used implicitely to get JSON property . CsTypeJson variable is required.
            SearchStr = "RedfishCS_status Status;\n"
            i = StrFunText.find(SearchStr)
            StrFunText = StrFunText[:i + len (SearchStr)] + C_SRC_TAB_SPACE + "RedfishCS_Type_JSON_Data *CsTypeJson;\n" \
                                                          + C_SRC_TAB_SPACE + "RedfishCS_Type_EmptyProp_CS_Data *CsTypeEmptyPropCS;\n" \
                                                          + C_SRC_TAB_SPACE + "RedfishCS_uint32 NunmOfEmptyPropProperties;\n" \
                                                          + StrFunText[i + len (SearchStr):]

        StrFunText += TempText
        StrFunText += "Error:;\n"
        StrFunText += C_SRC_TAB_SPACE + "return Status;\n}\n"
        self.CFuncText.append (StrFunText)
        return

    def CCodeEmptyProp (Self, IsArrayElementEmptyProp):
        FuncText = C_SRC_TAB_SPACE + "InitializeLinkHead (&(*Dst)->Prop);\n\n"
        if not IsArrayElementEmptyProp:
            FuncText += C_SRC_TAB_SPACE + "//\n"
            FuncText += C_SRC_TAB_SPACE + "// Try to create C structure if the property is\n"
            FuncText += C_SRC_TAB_SPACE + "// declared as empty property in schema. The supported property type\n"
            FuncText += C_SRC_TAB_SPACE + "// is string, integer, real, number and boolean.\n"
            FuncText += C_SRC_TAB_SPACE + "//\n"
            FuncText += C_SRC_TAB_SPACE + "if (CheckEmptyPropJsonObject(TempJsonObj, &NunmOfEmptyPropProperties)) {\n"
            FuncText += C_SRC_TAB_SPACE * 2 + "Status = CreateEmptyPropCsJson(Cs, JsonObj, Key, Cs->Header.ThisUri, &CsTypeEmptyPropCS, NunmOfEmptyPropProperties);\n"
            FuncText += C_SRC_TAB_SPACE * 2 + "if (Status != RedfishCS_status_success) {\n"
            FuncText += C_SRC_TAB_SPACE * 3 + "goto Error;\n"
            FuncText += C_SRC_TAB_SPACE * 2 + "}\n"
            FuncText += C_SRC_TAB_SPACE * 2 + "InsertTailLink(&(*Dst)->Prop, &CsTypeEmptyPropCS->Header.LinkEntry);\n"
            FuncText += C_SRC_TAB_SPACE + "} else {\n"

            FuncText += C_SRC_TAB_SPACE * 2 + "Status = CreateCsJsonByNode (Cs, JsonObj, Key, Cs->Header.ThisUri, &CsTypeJson);\n" # Get JSON property by using key
            FuncText += C_SRC_TAB_SPACE * 2 + "if (Status != RedfishCS_status_success) {\n" + \
                        C_SRC_TAB_SPACE * 3 + "goto Error;\n" + \
                        C_SRC_TAB_SPACE * 2 + "}\n" + \
                        C_SRC_TAB_SPACE * 2 + "InsertTailLink(&(*Dst)->Prop, &CsTypeJson->Header.LinkEntry);\n"
            FuncText += C_SRC_TAB_SPACE + "}\n"                
        else:
            FuncText += C_SRC_TAB_SPACE  + "Status = CreateCsJsonByNode (Cs, TempJsonObj, NULL, Cs->Header.ThisUri, &CsTypeJson);\n" # Dump TempJsonObj directly.
            FuncText += C_SRC_TAB_SPACE  + "if (Status != RedfishCS_status_success) {\n" + \
                    C_SRC_TAB_SPACE * 2 + "goto Error;\n" + \
                    C_SRC_TAB_SPACE  + "}\n" + \
                    C_SRC_TAB_SPACE  + "InsertTailLink(&(*Dst)->Prop, &CsTypeJson->Header.LinkEntry);\n"

        return FuncText

    def __init__ (self, RedfishCSInstance, SchemaFileInstance, RedfishCSStructList, StructureName, StructureMemberDataType, NonStructureMemberDataType, CfunctionsCreated):
        self.GenRedfishSchemaCs = RedfishCSInstance
        self.RedfishSchemaFile = SchemaFileInstance
        self.RedfishCsList = RedfishCSStructList
        self.StructureName = StructureName
        self.StructureMemberDataType = StructureMemberDataType
        self.NonStructureMemberDataType = NonStructureMemberDataType        
        self.ArrayStructMember = {}
        self.CfunctionsCreated = CfunctionsCreated

        # 
        # LOGFOR_CSTRUCTURE_TO_JSON_IS_ROOT = 0
        # LOGFOR_CSTRUCTURE_TO_JSON_IS_LINK_ARRAY = 1
        # LOGFOR_CSTRUCTURE_TO_JSON_IS_STRUCT_MEM_NAME = 2
        #   LOGFOR_CSTRUCTURE_TO_JSON_IS_STRUCT_MEM_NAME_DATATYPE = 0
        #   LOGFOR_CSTRUCTURE_TO_JSON_IS_STRUCT_MEM_NAME_JSON_KEY = 1
        # LOGFOR_CSTRUCTURE_TO_JSON_ALIAS_STRUCTURE_NAME = 3
        #
        self.LogForCStructureToJson = {}
        
        self.CIncludeFileName = ""
        self.CRedfishRootStrucutreResrouceType =""
        self.CRedfishRootStrucutreResrouceVersion =""        
        self.CRedfishRootStrucutreTypeName =""         
        self.CRedfishRootStructureName = ""
        self.CSourceFileRelativeDir = ""
        self.CSourceFile = ""
        self.CCodeGenFun = {"RedfishCS_char": self.CCodeGenString,
                            "RedfishCS_Link": self.CCodeGenLink,
                            "RedfishCS_Link_Array": self.CCodeGenLinkArray, # "RedfishCS_Link_Array" is generated by IS_REDFISH_CS_LINK_ARRAY flag.
                            "RedfishCS_int64": self.CCodeGenInt64,
                            "RedfishCS_bool": self.CCodeGenBoolean,
                            "RedfishCS_Vague": self.CCodeGenVague
                           }
        self.CCodeGenJsonFun = {"RedfishCS_char": self.CCodeGenStringJson,
                                "RedfishCS_Link": self.CCodeGenLinkJson,
                                "RedfishCS_int64": self.CCodeGenInt64Json,
                                "RedfishCS_bool": self.CCodeGenBooleanJson,
                                "RedfishCS_Vague": self.CCodeGenVagueJson
                              }
        self.CCodeGenJsonNaturalArrayFun = {"RedfishCS_char_Array": self.CCodeGenStringArrayJson,
                                            "RedfishCS_Link_Array": self.CCodeGenLinkArrayJson, # "RedfishCS_Link_Array" is generated by IS_REDFISH_CS_LINK_ARRAY flag.
                                            "RedfishCS_int64_Array": self.CCodeGenInt64ArrayJson,
                                            "RedfishCS_bool_Array": self.CCodeGenBooleanArrayJson
                              }

        self.RequiredProperties = self.RedfishCsList.RequiredProperties
        self.StructFuncName = []
        self.StructFuncNameTypedef = []
        # Function name
        self.CRedfishRootFunctionName = ""
        self.CToRedfishFunctionName = ""
        self.CRedfishDestoryFunctionName = ""
        self.CRedfishDestoryJsonFunctionName = ""

    def RemoveResourceTypeAndVersion(self, key, ResourceType, SchemaVersion):
        if key.count (ResourceType) > 1:
            return key.lstrip (ResourceType + '_').replace (SchemaVersion + '_', "")
        else:
            return key.replace (ResourceType + '_', "").replace (SchemaVersion + '_', "")

    #   Return 2 values,
    #      StringMemberDataType : String of member data type
    #      IsRedfishCSLinkArray : True,  this is array of RedfishCS_Link. Otherwise it's not
    # 
    def FormatingStructMemberDataType (self, StrStructureMemberDataType, ResourceType, SchemaVersion, key):
        strToRet = StrStructureMemberDataType.replace (" *", "")
        if len (strToRet.split(REDFISH_SCHEMA_NAMING_NOVERSIONED)) == 2:
            strToRet = strToRet.split(REDFISH_SCHEMA_NAMING_NOVERSIONED)[0].strip ('_' ) + \
                    strToRet.split(REDFISH_SCHEMA_NAMING_NOVERSIONED)[1]

        # Check if this member is an array.
        if ResourceType not in self.NonStructureMemberDataType:
            return strToRet, IS_NOT_REDFISH_CS_LINK_ARRAY
        if SchemaVersion not in self.NonStructureMemberDataType [ResourceType]:
            return strToRet, IS_NOT_REDFISH_CS_LINK_ARRAY

        key = self.RemoveResourceTypeAndVersion(key, ResourceType, SchemaVersion)
        #key = key.replace (ResourceType + '_', "").replace (SchemaVersion + '_', "")
        for Mem in self.NonStructureMemberDataType[ResourceType][SchemaVersion]:
            Tuple =self.NonStructureMemberDataType[ResourceType][SchemaVersion][Mem];
            if Mem == key and \
               isinstance (Tuple [REDFISH_GET_DATATYPE_VALUE], str) and \
               Tuple [REDFISH_GET_DATATYPE_VALUE] == "array":

                if strToRet == "RedfishCS_Link":
                    return strToRet, IS_REDFISH_CS_LINK_ARRAY # Dont need arry structure for RedfishCS_Link               

                # ARRAY_CS replaces _CS at the end of structure name type
                if REDFISH_STRUCT_NAME_TAIL in strToRet:
                    #NewMemName = strToRet.rstrip(REDFISH_STRUCT_NAME_TAIL) + REDFISH_ARRAY_CS_TAIL
                    NewMemName = self.RemoveTailCSPattern (strToRet) + REDFISH_ARRAY_CS_TAIL
                else:
                    NewMemName = strToRet + "_Array"
                    if NewMemName not in self.CCodeGenJsonNaturalArrayFun:
                        print ("Nither C Structure Array or natural data type array :" + NewMemName)
                        sys.exit ()
                    else:                        
                        return NewMemName, IS_NOT_REDFISH_CS_LINK_ARRAY

                if ResourceType not in self.ArrayStructMember:
                    self.ArrayStructMember [ResourceType] = {}
                if SchemaVersion not in self.ArrayStructMember [ResourceType]:
                    self.ArrayStructMember [ResourceType][SchemaVersion] = {}
                if key not in self.ArrayStructMember [ResourceType][SchemaVersion]:
                    self.ArrayStructMember [ResourceType][SchemaVersion][key] = (NewMemName, strToRet)
                return NewMemName, IS_NOT_REDFISH_CS_LINK_ARRAY     

        return strToRet, IS_NOT_REDFISH_CS_LINK_ARRAY

    def FormatingStructMemberName (Self, StrStructureMemberName):
        strToRet = StrStructureMemberName.replace ("@", "").replace ('.', '_').lstrip('#')        
        return strToRet

    # This is the preparation for CSTructure to JSON function.
    def LogCStructureToJson (self, StrucName, StructMemDataType, JsonKey, StructureMemberName, IsRoot, IsRedfishCsLinkArray, AliasStructName, ResourceType, Version):
        UseAliasName = False
        if StrucName not in self.LogForCStructureToJson:
            self.LogForCStructureToJson [StrucName] = (IsRoot, IsRedfishCsLinkArray, {}, AliasStructName, ResourceType, Version)
        else:       
            # check if same name but differnt namespace            
            if ResourceType != self.LogForCStructureToJson [StrucName][LOGFOR_CSTRUCTURE_TO_JSON_RESOURCETYPE] or  Version != self.LogForCStructureToJson [StrucName][LOGFOR_CSTRUCTURE_TO_JSON_VERSION]:
                # Same StrucName but differnt namespace, use AliasStructName as StrucName and StrucName as AliasStructName
                # so it can be found in GenCStructToJsonCCodeForStructure method.
                self.LogForCStructureToJson [AliasStructName] = (IsRoot, IsRedfishCsLinkArray, {}, StrucName, ResourceType, Version)
                UseAliasName = True

        #if StructureMemberName not in self.LogForCStructureToJson [StrucName][2]:
        #    self.LogForCStructureToJson [StrucName][2][StructureMemberName] = 
        if IsRedfishCsLinkArray:
            if UseAliasName != True:
                self.LogForCStructureToJson [StrucName] [LOGFOR_CSTRUCTURE_TO_JSON_IS_STRUCT_MEM_NAME] [StructureMemberName] = (StructMemDataType + "_Array", JsonKey)
            else:
                self.LogForCStructureToJson [AliasStructName] [LOGFOR_CSTRUCTURE_TO_JSON_IS_STRUCT_MEM_NAME] [StructureMemberName] = (StructMemDataType + "_Array", JsonKey)
        else:
            if UseAliasName != True:            
                self.LogForCStructureToJson [StrucName] [LOGFOR_CSTRUCTURE_TO_JSON_IS_STRUCT_MEM_NAME] [StructureMemberName] = (StructMemDataType, JsonKey)
            else:
                self.LogForCStructureToJson [AliasStructName] [LOGFOR_CSTRUCTURE_TO_JSON_IS_STRUCT_MEM_NAME] [StructureMemberName] = (StructMemDataType, JsonKey)

    def GenCStructureJSonStructureCode (self, ResourceType, SchemaVersion, StructureMemberDataType, NestedStructName, key, PrecedentKey, CStructPointer):
        StructnameShort = StructureMemberDataType.replace (REDFISH_STRUCT_NAME_HEAD + ResourceType + "_", "")
        #StructnameShort = StructnameShort.rstrip(REDFISH_STRUCT_NAME_TAIL)
        StructnameShort = self.RemoveTailCSPattern (StructnameShort)
        if SchemaVersion == REDFISH_SCHEMA_NAMING_NOVERSIONED:
            StructnameShort = StructnameShort.replace(SchemaVersion + "_", "")

        Pattern = re.compile ('[_]*[vV]*[0-9]+[_]{1}[0-9]+[_]{1}[0-9]+[_]*', 0)
        StructnameShort = re.sub(Pattern, "_", StructnameShort)
        StructnameShort = StructnameShort.lstrip("_")
        StructnameShort = StructnameShort.rstrip("_")

        CodeStr = self.GenCStructToJsonCCodeForStructure (ResourceType, SchemaVersion, StructnameShort, NestedStructName, PrecedentKey, CStructPointer + "->" + key, False)
        if "RedfishCS_status CS_To_JSON_" + PrecedentKey in self.CStructureToJsonStructureExistFunc:
            # Funciton already exist.
            return
        self.CStructureToJsonStructureExistFunc.append ("RedfishCS_status CS_To_JSON_" + PrecedentKey)

        self.CStructureToJsonStructureFuncions += "static RedfishCS_status CS_To_JSON_" + PrecedentKey  + "(json_t *CsJson, char *Key, " + StructureMemberDataType + " *CSPtr)\n"
        self.CStructureToJsonStructureFuncions += "{\n"
        self.CStructureToJsonStructureFuncions += C_SRC_TAB_SPACE + "if (CSPtr == NULL) {\n"
        self.CStructureToJsonStructureFuncions += C_SRC_TAB_SPACE * 2 + "return RedfishCS_status_success;\n"
        self.CStructureToJsonStructureFuncions += C_SRC_TAB_SPACE + "}\n"

        if CodeStr != "":
            self.CStructureToJsonStructureFuncions += CodeStr
        else:
            self.CStructureToJsonStructureFuncions += C_SRC_TAB_SPACE + "// Check if this is RedfishCS_Type_CS_EmptyProp.\n"
            self.CStructureToJsonStructureFuncions += C_SRC_TAB_SPACE + "CsEmptyPropLinkToJson(CsJson, Key, &CSPtr->Prop);\n"
            self.CStructureToJsonStructureFuncions += C_SRC_TAB_SPACE + "// No JSON property for this structure.\n"

        self.CStructureToJsonStructureFuncions += C_SRC_TAB_SPACE + "return RedfishCS_status_success;\n"        
        if CodeStr != "":
            self.CStructureToJsonStructureFuncions += "Error:;\n"
            self.CStructureToJsonStructureFuncions += C_SRC_TAB_SPACE + "return RedfishCS_status_unsupported;\n"
        self.CStructureToJsonStructureFuncions += "}\n"
        return   

    def GenCStructureJSonStructureArrayCode (self, ResourceType, SchemaVersion, StructureMemberDataType, NestedStructName, ArrayStructWrapperName, key, PrecedentKey, CStructPointer):
        StructnameShort = StructureMemberDataType.replace (REDFISH_STRUCT_NAME_HEAD + ResourceType + "_", "")
        #StructnameShort = StructnameShort.rstrip(REDFISH_STRUCT_NAME_TAIL)
        StructnameShort = self.RemoveTailCSPattern (StructnameShort)
        if SchemaVersion != REDFISH_SCHEMA_NAMING_NOVERSIONED:
            StructnameShort = StructnameShort.replace(SchemaVersion + "_", "")

        Pattern = re.compile ('[_]*[vV]*[0-9]+[_]{1}[0-9]+[_]{1}[0-9]+[_]*', 0)
        StructnameShort = re.sub(Pattern, "_", StructnameShort)
        StructnameShort = StructnameShort.lstrip("_")
        StructnameShort = StructnameShort.rstrip("_")

        CodeStr = self.GenCStructToJsonCCodeForStructure (ResourceType, SchemaVersion, StructnameShort, NestedStructName, PrecedentKey, CStructPointer + "->" + key, True)
        if "RedfishCS_status CS_To_JSON_" + PrecedentKey in self.CStructureToJsonStructureExistFunc:
            # Funciton already exist.
            return
        self.CStructureToJsonStructureExistFunc.append ("RedfishCS_status CS_To_JSON_" + PrecedentKey)
        
        self.CStructureToJsonStructureFuncions += "static RedfishCS_status CS_To_JSON_" + PrecedentKey  + "(json_t *CsJson, char *Key, " + ArrayStructWrapperName + " *CSPtr)\n"
        self.CStructureToJsonStructureFuncions += "{\n"

        if CodeStr != "":
            self.CStructureToJsonStructureFuncions += C_SRC_TAB_SPACE + "json_t *ArrayJson;\n"
            self.CStructureToJsonStructureFuncions += C_SRC_TAB_SPACE + "json_t *ArrayMember;\n"
            self.CStructureToJsonStructureFuncions += C_SRC_TAB_SPACE + ArrayStructWrapperName + " *NextArray;\n"
            self.CStructureToJsonStructureFuncions += C_SRC_TAB_SPACE + StructureMemberDataType + " *NextArrayItem;\n\n"
            self.CStructureToJsonStructureFuncions += C_SRC_TAB_SPACE + "if (CSPtr == NULL) {\n"
            self.CStructureToJsonStructureFuncions += C_SRC_TAB_SPACE * 2 + "return RedfishCS_status_success;\n"
            self.CStructureToJsonStructureFuncions += C_SRC_TAB_SPACE + "}\n"
            self.CStructureToJsonStructureFuncions += C_SRC_TAB_SPACE + "ArrayJson = json_array();\n"
            self.CStructureToJsonStructureFuncions += C_SRC_TAB_SPACE + "if (ArrayJson == NULL) {\n"
            self.CStructureToJsonStructureFuncions += C_SRC_TAB_SPACE * 2 + "return RedfishCS_status_unsupported;\n"
            self.CStructureToJsonStructureFuncions += C_SRC_TAB_SPACE + "}\n"         
            self.CStructureToJsonStructureFuncions += C_SRC_TAB_SPACE + "NextArray = CSPtr;\n"
            self.CStructureToJsonStructureFuncions += C_SRC_TAB_SPACE + "do {\n"
            self.CStructureToJsonStructureFuncions += C_SRC_TAB_SPACE * 2 + "ArrayMember = json_object();\n"
            self.CStructureToJsonStructureFuncions += C_SRC_TAB_SPACE * 2 + "if (ArrayMember == NULL) {\n"
            self.CStructureToJsonStructureFuncions += C_SRC_TAB_SPACE * 3 + "return RedfishCS_status_unsupported;\n"
            self.CStructureToJsonStructureFuncions += C_SRC_TAB_SPACE * 2 + "}\n\n"
            self.CStructureToJsonStructureFuncions += C_SRC_TAB_SPACE * 2 + "NextArrayItem = NextArray->ArrayValue;\n"
            self.CStructureToJsonStructureFuncions += CodeStr
            self.CStructureToJsonStructureFuncions += C_SRC_TAB_SPACE * 2 + "if (json_array_append_new (ArrayJson, ArrayMember) != 0) {goto Error;}\n"
            self.CStructureToJsonStructureFuncions += C_SRC_TAB_SPACE * 2 + "NextArray = NextArray->Next;\n"
            self.CStructureToJsonStructureFuncions += C_SRC_TAB_SPACE + "} while (NextArray != NULL);\n"
            self.CStructureToJsonStructureFuncions += C_SRC_TAB_SPACE + "json_object_set_new (CsJson, Key, ArrayJson);\n\n"
        else:
            self.CStructureToJsonStructureFuncions += C_SRC_TAB_SPACE + "// No JSON property for this structure.\n"

        self.CStructureToJsonStructureFuncions += C_SRC_TAB_SPACE + "return RedfishCS_status_success;\n"        
        if CodeStr != "":
            self.CStructureToJsonStructureFuncions += "Error:;\n"
            self.CStructureToJsonStructureFuncions += C_SRC_TAB_SPACE + "return RedfishCS_status_unsupported;\n"
        self.CStructureToJsonStructureFuncions += "}\n"
        return          

    def GenCStructToJsonCCodeForStructure (self, ResourceType, SchemaVersion, StructureName, NestedStructName, PrecedentKey, CStructPointer, IsArrayStruct):
        CodeStr = ""
        StructureNameRef = StructureName
        if StructureNameRef not in self.LogForCStructureToJson:
            for StructNameKey in self.LogForCStructureToJson.keys():
                if StructureNameRef == self.LogForCStructureToJson[StructNameKey][LOGFOR_CSTRUCTURE_TO_JSON_ALIAS_STRUCTURE_NAME]:
                    StructureNameRef = StructNameKey;
                    break

        if StructureNameRef not in self.LogForCStructureToJson:
            if "_Array" not in StructureNameRef:
                return "" # No structure for this StructureNameRef. It coudl be {}

            if StructureNameRef not in self.CCodeGenJsonNaturalArrayFun:
                ArrayStructName = CStructPointer.replace ("->", "_").lstrip("_")
                if "_" not in ArrayStructName:
                    if ResourceType + "_" + ArrayStructName not in self.ArrayStructMember [ResourceType][SchemaVersion]:
                        print ("Array structure not found in ArrayStructMember for converting to JSON: " + StructureNameRef)
                        sys.exit()
                    else:
                        ArrayStructName = ResourceType + "_" + ArrayStructName

                NewNestedStructName = NestedStructName
                if NestedStructName == "":
                    NewNestedStructName = StructureNameRef.replace("_Array", "")
                else:
                    NewNestedStructName = NestedStructName + "_" + StructureNameRef.replace("_Array", "")

                # Loop to check if structure array declared in ArrayStructMember
                # Structure name + member name is the key record in ArrayStructName for the nested structure.
                NewArrayStructName = NestedStructName + "_" + CStructPointer.split("->")[len (CStructPointer.split("->")) - 1]
                ####NewArrayStructName = ArrayStructName
                #for ArrayStructNameIndex in range (0, len (ArrayStructName.split ("_"))- 1):
                for ArrayStructNameIndex in range (0, len (NewArrayStructName.split ("_"))):
                    if NewArrayStructName in self.ArrayStructMember [ResourceType][SchemaVersion]:
                        ArrayStructName = self.ArrayStructMember [ResourceType][SchemaVersion][NewArrayStructName][1]
                        ArrayStructWrapperName = self.ArrayStructMember [ResourceType][SchemaVersion][NewArrayStructName][0] 
                        # Remove last member reference from CStructPointer, because  GenCStructToJsonCCodeForStructure is invoked again for handling array.
                        NewCStructPointer = ""
                        for MemberNum in range (1,len (CStructPointer.split ("->"))-1):
                            NewCStructPointer += "->" + CStructPointer.split ("->")[MemberNum]
                        # Generate function call for array JSON
                        self.GenCStructureJSonStructureArrayCode (ResourceType, SchemaVersion, ArrayStructName, NewNestedStructName, ArrayStructWrapperName, StructureNameRef.replace("_Array", ""), PrecedentKey, NewCStructPointer)
                        return
                    else:
                        NewArrayStructNameList = NewArrayStructName.split("_")
                        NewArrayStructName = ""
                        for NewArrayStructNameListIndex in range (1, len(NewArrayStructNameList) - 1):
                            NewArrayStructName += NewArrayStructNameList[NewArrayStructNameListIndex] + "_"
                        NewArrayStructName += NewArrayStructNameList[len(NewArrayStructNameList) - 1]
                        #NewArrayStructName = NewArrayStructName.lstrip (NewArrayStructName.split("_")[0] + "_")
                print ("Array structure not found in ArrayStructMember for converting to JSON: " + StructureNameRef)
                sys.exit()

        for key in sorted (self.LogForCStructureToJson[StructureNameRef][LOGFOR_CSTRUCTURE_TO_JSON_IS_STRUCT_MEM_NAME].keys ()):
            StructureMemberDataType = self.LogForCStructureToJson[StructureNameRef][LOGFOR_CSTRUCTURE_TO_JSON_IS_STRUCT_MEM_NAME][key][LOGFOR_CSTRUCTURE_TO_JSON_IS_STRUCT_MEM_NAME_DATATYPE]
            if StructureMemberDataType in self.CCodeGenJsonFun:
                CodeStr += self.CCodeGenJsonFun [StructureMemberDataType](StructureNameRef, key, CStructPointer, IsArrayStruct)
            elif StructureMemberDataType in self.CCodeGenJsonNaturalArrayFun:
                CodeStr += self.CCodeGenJsonNaturalArrayFun [StructureMemberDataType](StructureNameRef, key, CStructPointer, IsArrayStruct)             
            else:
                # Check if StructureMemberDataType in any structure data type
                StructureFound = False
                try:
                    #for StructureNameKey in self.LogForCStructureToJson:
                    for StructureMemberNameKey in self.LogForCStructureToJson[StructureNameRef][LOGFOR_CSTRUCTURE_TO_JSON_IS_STRUCT_MEM_NAME]:
                        if StructureMemberDataType == self.LogForCStructureToJson[StructureNameRef][LOGFOR_CSTRUCTURE_TO_JSON_IS_STRUCT_MEM_NAME][StructureMemberNameKey][LOGFOR_CSTRUCTURE_TO_JSON_IS_STRUCT_MEM_NAME_DATATYPE] and \
                            key == StructureMemberNameKey:
                            # This is structure type.
                            JsonKey = self.LogForCStructureToJson[StructureNameRef][LOGFOR_CSTRUCTURE_TO_JSON_IS_STRUCT_MEM_NAME][StructureMemberNameKey][LOGFOR_CSTRUCTURE_TO_JSON_IS_STRUCT_MEM_NAME_JSON_KEY]
                                
                            if IsArrayStruct:
                                CodeStr += C_SRC_TAB_SPACE * 2 + "// " + JsonKey + "\n"
                                CodeStr += C_SRC_TAB_SPACE * 2 + "if (CS_To_JSON_" + PrecedentKey + StructureMemberNameKey  + \
                                                     "(ArrayMember, " + "\"" + JsonKey + "\"" + ", NextArrayItem->" + StructureMemberNameKey + ") != RedfishCS_status_success) {goto Error;}\n\n"                                
                            else:
                                CodeStr += C_SRC_TAB_SPACE + "// " + JsonKey + "\n"
                                CodeStr += C_SRC_TAB_SPACE + "if (CS_To_JSON_" + PrecedentKey + StructureMemberNameKey  + "(CsJson, " + "\"" + JsonKey + "\"" + ", CSPtr->" + StructureMemberNameKey + ") != RedfishCS_status_success) {goto Error;}\n\n"

                            NewNestedStructName = NestedStructName
                            if NestedStructName == "":
                                NewNestedStructName = StructureNameRef
                            else:
                                NewNestedStructName = NestedStructName + "_" + StructureNameRef
                                                                                                           
                            #if key in self.LogForCStructureToJson:
                            #    NewResourceType = self.LogForCStructureToJson[key][LOGFOR_CSTRUCTURE_TO_JSON_RESOURCETYPE]
                            #    NewResourceVersion = self.LogForCStructureToJson[key][LOGFOR_CSTRUCTURE_TO_JSON_VERSION]
                            #    if NewResourceType != "" and NewResourceVersion != "":                                  
                            #        ResourceType = NewResourceType
                            #        SchemaVersion = NewResourceVersion
                            #else:
                            if self.LogForCStructureToJson[StructureNameRef][LOGFOR_CSTRUCTURE_TO_JSON_RESOURCETYPE] == "" or self.LogForCStructureToJson[StructureNameRef][LOGFOR_CSTRUCTURE_TO_JSON_VERSION] == "":
                                print ("Array structure has no schema ResourceType or ResourceVersion")
                                sys.exit()
                            ResourceType = self.LogForCStructureToJson[StructureNameRef][LOGFOR_CSTRUCTURE_TO_JSON_RESOURCETYPE]
                            SchemaVersion = self.LogForCStructureToJson[StructureNameRef][LOGFOR_CSTRUCTURE_TO_JSON_VERSION]
                            self.GenCStructureJSonStructureCode (ResourceType, SchemaVersion, StructureMemberDataType, NewNestedStructName, StructureMemberNameKey, PrecedentKey + StructureMemberNameKey, CStructPointer)
                            StructureFound = True
                            raise BreakForLoop

                except BreakForLoop:
                    pass

                if StructureFound != True:
                    print ("Unsupported structure member data type for converting to JSON: " + StructureMemberDataType)
        return CodeStr

    def GenCStructToJsonCCode (self, ResourceType, SchemaVersion):
        for key in self.LogForCStructureToJson:
            if self.LogForCStructureToJson [key][LOGFOR_CSTRUCTURE_TO_JSON_IS_ROOT] != True:
                continue
            else:
                # This is root structure.
                return  self.GenCStructToJsonCCodeForStructure (ResourceType, SchemaVersion, key, "", "", "", False)
        print ("No structure to be converted to JSON!") 
        return ""
            

    # This generates structure member definition.
    def GenStructMemDefinition (self, ResourceType, SchemaVersion, StrucName, IsRoot):
        MaxStrucDataTypeLen = 0
        MaxStrucNameLen = 0    
        CommentPos = 0    
        StructureName = self.StructureName
        StructureMemberDataType = self.StructureMemberDataType
                
        # Genraste strucutre comment
        typedef = ""
        if StructureName [ResourceType][SchemaVersion][StrucName][STRUCTURE_NAME_TUPLE_DESCRIPTION] != "":
            DescLine = textwrap.wrap (StructureName [ResourceType][SchemaVersion][StrucName][STRUCTURE_NAME_TUPLE_DESCRIPTION] , 79)
            typedef = "//\n";
            for line in range (0, len (DescLine)):
                typedef  += ("// " + DescLine [line] + "\n")
            typedef += "//\n";
    
        if SchemaVersion == REDFISH_SCHEMA_NAMING_NOVERSIONED:
            Name = StructureName [ResourceType][SchemaVersion][StrucName][STRUCTURE_NAME_TUPLE_NAME].replace (REDFISH_SCHEMA_NAMING_NOVERSIONED + "_", "")
            if self.RedfishSchemaFile.SchemaRef not in Name: # Add #ifndef for the command strucuture used for different schema, such as RedfishResource_Oem_CS
                typedef += "#ifndef "+ Name + "_\n" + \
                           "#define "+ Name + "_\n" + \
                           "typedef struct " + "_" + Name  + " {\n"
            else:
                typedef += "typedef struct " + "_" + Name  + " {\n"

        else:
            Name = StructureName [ResourceType][SchemaVersion][StrucName][STRUCTURE_NAME_TUPLE_NAME]
            if self.RedfishSchemaFile.SchemaRef not in Name: # Add #ifndef for the command strucuture used for different schema, such as RedfishResource_Oem_CS
                typedef += "#ifndef "+ Name + "_\n" + \
                           "#define "+ Name + "_\n" + \
                           "typedef struct " + "_" + Name  + " {\n"
            else:     
                typedef += "typedef struct " + "_" + Name  + " {\n"            

        #StructMemHead = StructureName [ResourceType][SchemaVersion][StrucName][STRUCTURE_NAME_TUPLE_NAME].replace (REDFISH_STRUCT_NAME_HEAD, "")
        StructMemHead = self.RemoveStructureNameHead (StructureName [ResourceType][SchemaVersion][StrucName][STRUCTURE_NAME_TUPLE_NAME])
        #StructMemHead = StructMemHead.rstrip(REDFISH_STRUCT_NAME_TAIL)
        StructMemHead = self.RemoveTailCSPattern (StructMemHead)

        # Loop to see the maximum length of structure member data type string for the code cosmetics.
        for key in sorted (StructureMemberDataType.keys ()):
            if key.find(StructMemHead) != -1:
                if key.replace (StructMemHead, "") != "":
                    Member = key.replace (StructMemHead, "").lstrip('_')
                    if len (Member.split ('_')) == 1:
                        StructMemDataType, IsRedfishCsLinkArray = self.FormatingStructMemberDataType (StructureMemberDataType [key][STRUCTURE_MEMBER_TUPLE_DATATYPE], ResourceType, SchemaVersion, key)
                        if MaxStrucDataTypeLen < len (StructMemDataType):
                            MaxStrucDataTypeLen = len (StructMemDataType)
        if IsRoot:
            if len("RedfishCS_Header") > MaxStrucDataTypeLen:
                MaxStrucDataTypeLen = len("RedfishCS_Header")

        # Loop to see the maximum length of structure member name string for the code cosmetics.                            
        for key in sorted (StructureMemberDataType.keys ()):
            if key.find(StructMemHead) != -1:
                if key.replace (StructMemHead, "") != "":
                    Member = key.replace (StructMemHead, "").lstrip('_')
                    if len (Member.split ('_')) == 1:
                        Member = self.FormatingStructMemberName (Member)
                        if StructureMemberDataType [key][STRUCTURE_MEMBER_TUPLE_DATATYPE].find(' *') != -1:
                            Member = "*" + Member
                        if MaxStrucNameLen < len (Member):
                            MaxStrucNameLen = len (Member)
        if IsRoot:
            if len("Header") > MaxStrucNameLen:
                MaxStrucNameLen = len("Header")

        CommentPos = MaxStrucDataTypeLen + MaxStrucNameLen + 2 * len (TAB_SPACE)

        # First add header member for root structure.
        if IsRoot:
            spaces = 0
            if MaxStrucDataTypeLen > len ("RedfishCS_Header"):
                spaces = MaxStrucDataTypeLen - len ("RedfishCS_Header")        
            typedef += (TAB_SPACE + "RedfishCS_Header" + spaces * " " + TAB_SPACE + "Header;\n")
        
        # Loop to generate structure member
        spaces = 0
        MemFound = False
        for key in sorted (StructureMemberDataType.keys ()):
            if key.find(StructMemHead) != -1:
                if key.replace (StructMemHead, "") != "":
                    Member = key.replace (StructMemHead, "").lstrip('_')
                    if len (Member.split ('_')) == 1:
                        JsonKey = Member
                        Member = self.FormatingStructMemberName (Member)
                        StructMemDataType, IsRedfishCsLinkArray = self.FormatingStructMemberDataType (StructureMemberDataType [key][STRUCTURE_MEMBER_TUPLE_DATATYPE], ResourceType, SchemaVersion, key)
                        # Log member information for CStructure to JSON function.
                        StructNameOrg = StructureName [ResourceType][SchemaVersion][StrucName][STRUCTURE_NAME_TUPLE_NAME]
                        StructNameOrg = StructNameOrg.replace (SchemaVersion + "_", "")
                        #StructNameOrg = StructNameOrg.rstrip (REDFISH_STRUCT_NAME_TAIL)
                        StructNameOrg = self.RemoveTailCSPattern (StructNameOrg)

                        # Record resource tyep and version
                        Pattern = re.compile ('[_]*[vV]*[0-9]+[_]{1}[0-9]+[_]{1}[0-9]+[_]*', 0)
                        keyResourceAndVersion_Resource = ""
                        keyResourceAndVersion_Version = ""
                        if re.search (Pattern, key) != None:
                            keyResourceAndVersion_Version = re.findall (Pattern, key)[0]
                            keyResourceAndVersion = key.split (keyResourceAndVersion_Version)
                            keyResourceAndVersion_Version = keyResourceAndVersion_Version.lstrip('_')
                            keyResourceAndVersion_Version = keyResourceAndVersion_Version.rstrip('_')                            
                            keyResourceAndVersion_Resource = keyResourceAndVersion[0]                            
                        elif REDFISH_SCHEMA_NAMING_NOVERSIONED in key:                  
                            keyResourceAndVersion = key.split ('_' + REDFISH_SCHEMA_NAMING_NOVERSIONED + '_')
                            keyResourceAndVersion_Resource = keyResourceAndVersion[0]
                            keyResourceAndVersion_Version = REDFISH_SCHEMA_NAMING_NOVERSIONED                     

                        self.LogCStructureToJson (StrucName, StructMemDataType, JsonKey, Member,  IsRoot, IsRedfishCsLinkArray, StructNameOrg, keyResourceAndVersion_Resource, keyResourceAndVersion_Version)

                        if MaxStrucDataTypeLen > len (StructMemDataType):
                            spaces = MaxStrucDataTypeLen - len (StructMemDataType)
                        else:
                            spaces = 0
                        # Generate comment for strucutre member
                        MemDesc = StructureMemberDataType [key][STRUCTURE_MEMBER_TUPLE_DESCRIPTION]
                        MemDescLine = [""]
                        if MemDesc != "":
                            MemDescLine = textwrap.wrap (MemDesc, MEMBER_DESCRIPTION_CHARS)
                            for line in range (0, len (MemDescLine)):
                                MemDescLine[line] = TAB_SPACE + "// " + MemDescLine [line]

                        if StructureMemberDataType [key][STRUCTURE_MEMBER_TUPLE_DATATYPE].find(' *') == -1:
                            ThieMemberLine = (TAB_SPACE + StructMemDataType + spaces*" " + TAB_SPACE + Member + ";")
                            PaddingSpace = 0;
                            if len (ThieMemberLine) < CommentPos:
                                PaddingSpace = CommentPos - len (ThieMemberLine)
                            typedef += (ThieMemberLine + ' ' * PaddingSpace + MemDescLine [0] + "\n")
                        else:
                            ThieMemberLine = (TAB_SPACE + StructMemDataType + spaces*" " + TAB_SPACE + "*" + Member + ";")
                            PaddingSpace = 0;
                            if len (ThieMemberLine) < CommentPos:
                                PaddingSpace = CommentPos - len (ThieMemberLine)
                            typedef += (ThieMemberLine + ' ' * PaddingSpace + MemDescLine [0]+ "\n")
                        # Generate the rest of comment lines.
                        if len (MemDescLine) > 1:
                            for line in range (1, len (MemDescLine)):
                                typedef += (" " * CommentPos + MemDescLine [line] + "\n")

                        MemFound = True
        if not MemFound:
            # No member found, means the properties for this data type is "{}"
            typedef += (TAB_SPACE + "RedfishCS_Link" + TAB_SPACE + "Prop" + ";\n")
        if SchemaVersion == REDFISH_SCHEMA_NAMING_NOVERSIONED:
            Name = StructureName [ResourceType][SchemaVersion][StrucName][STRUCTURE_NAME_TUPLE_NAME].replace (REDFISH_SCHEMA_NAMING_NOVERSIONED + "_", "")
            if self.RedfishSchemaFile.SchemaRef not in Name: # Add #ifndef for the command strucuture used for different schema, such as RedfishResource_Oem_CS
                typedef += ("} " + Name + ";\n" + "#endif\n" + "\n") 
            else:
                typedef += ("} " + Name + ";\n\n") 
          
        else:
            Name = StructureName [ResourceType][SchemaVersion][StrucName][STRUCTURE_NAME_TUPLE_NAME]
            if self.RedfishSchemaFile.SchemaRef not in Name: # Add #ifndef for the command strucuture used for different schema, such as RedfishResource_Oem_CS
                typedef += ("} " + Name + ";\n" + "#endif\n" + "\n") 
            else:
                typedef += ("} " + Name + ";\n\n")
                
        return typedef

    # This generates Redfish schema C include file
    def GenCSIncludefile (self):
        RedfishCs = self.RedfishCsList
        StructureName = self.StructureName
        StructureMemberDataType = self.StructureMemberDataType

        self.RedfishSchemaFile.CIncludeFileText = HPECopyright + "\n"
        self.RedfishSchemaFile.CIncludeFileText += ("#ifndef " + REDFISH_STRUCT_NAME_HEAD + \
                            RedfishCs.ResourceType.capitalize() + \
                            "_" + RedfishCs.SchemaVersion.capitalize() + \
                            "_" + "CSTRUCT_H_" + "\n")
        self.RedfishSchemaFile.CIncludeFileText += ("#define " + REDFISH_STRUCT_NAME_HEAD + \
                            RedfishCs.ResourceType.capitalize() + \
                            "_" + RedfishCs.SchemaVersion.capitalize() + \
                            "_" + "CSTRUCT_H_" + "\n")
        self.RedfishSchemaFile.CIncludeFileText += "\n"
        self.RedfishSchemaFile.CIncludeFileText += "#include \"RedfishCsCommon.h\"\n"
        self.RedfishSchemaFile.CIncludeFileText += "\n"

        # Generate typedef
        for ResourceTypeLoop in sorted (StructureName.keys()):
            for SchemaVersionLoop in sorted (StructureName [ResourceTypeLoop].keys()):                
                for StrucName in sorted(StructureName [ResourceTypeLoop][SchemaVersionLoop].keys()):
                    if SchemaVersionLoop == REDFISH_SCHEMA_NAMING_NOVERSIONED:
                        typedef = "typedef struct " + "_" + REDFISH_STRUCT_NAME_HEAD + ResourceTypeLoop + "_" + StrucName + REDFISH_STRUCT_NAME_TAIL +\
                                    " " + REDFISH_STRUCT_NAME_HEAD + ResourceTypeLoop + "_" + StrucName + REDFISH_STRUCT_NAME_TAIL + ";\n"
                        TypedefSturctName = REDFISH_STRUCT_NAME_HEAD + ResourceTypeLoop + "_" + StrucName + REDFISH_STRUCT_NAME_TAIL
                    else:
                        typedef = "typedef struct " + "_" + REDFISH_STRUCT_NAME_HEAD + ResourceTypeLoop +  "_" + SchemaVersionLoop + "_" + StrucName + REDFISH_STRUCT_NAME_TAIL +\
                                    " " + REDFISH_STRUCT_NAME_HEAD + ResourceTypeLoop + "_" + SchemaVersionLoop + "_" + StrucName + REDFISH_STRUCT_NAME_TAIL + ";\n"
                        TypedefSturctName = REDFISH_STRUCT_NAME_HEAD + ResourceTypeLoop + "_" + SchemaVersionLoop + "_" + StrucName + REDFISH_STRUCT_NAME_TAIL

                    if self.RedfishSchemaFile.SchemaRef not in typedef: # Add #ifndef for the command strucuture used for different schema, such as RedfishResource_Oem_CS
                        typedef = "#ifndef "+ TypedefSturctName + "_\n" + typedef + "#endif\n\n"

                    self.RedfishSchemaFile.CIncludeFileText += typedef

        #Generate structure definitions
        for ResourceTypeLoop in sorted (StructureName.keys()):
            for SchemaVersionLoop in sorted (StructureName [ResourceTypeLoop].keys()):        
                for StrucName in sorted(StructureName [ResourceTypeLoop][SchemaVersionLoop].keys()):
                    if StrucName != self.RedfishSchemaFile.SchemaRef or \
                       ResourceTypeLoop != RedfishCs.ResourceType or \
                       SchemaVersionLoop != RedfishCs.SchemaVersion:
                        typedef = self.GenStructMemDefinition (ResourceTypeLoop, SchemaVersionLoop, StrucName, False)
                        self.RedfishSchemaFile.CIncludeFileText += typedef

        # Generate the root structure for this schema.
        for ResourceTypeLoop in sorted (StructureName.keys()):
            for SchemaVersionLoop in sorted (StructureName [ResourceTypeLoop].keys()):       
                for StrucName in sorted(StructureName [ResourceTypeLoop][SchemaVersionLoop].keys()):
                   if StrucName == self.RedfishSchemaFile.SchemaRef and \
                       ResourceTypeLoop == RedfishCs.ResourceType and \
                       SchemaVersionLoop == RedfishCs.SchemaVersion:

                        typedef = self.GenStructMemDefinition (ResourceTypeLoop, SchemaVersionLoop, StrucName, True)
                        self.RedfishSchemaFile.CIncludeFileText += typedef
                        self.CRedfishRootStrucutreResrouceType = ResourceTypeLoop
                        self.CRedfishRootStrucutreResrouceVersion = SchemaVersionLoop
                        if self.CRedfishRootStrucutreResrouceVersion == REDFISH_SCHEMA_NAMING_NOVERSIONED:
                            self.CRedfishRootStrucutreResrouceVersion = ""
                        self.CRedfishRootStrucutreTypeName = StrucName                        
                        break                        
        
        # Generate the structure for array.
        NewInsertforwardTypedef = ""
        ArrayStructAdded = []
        for ResourceTypeLoop in self.ArrayStructMember:
            for SchemaVersionLoop in self.ArrayStructMember [ResourceTypeLoop]:
                for KeyLoop in self.ArrayStructMember [ResourceTypeLoop][SchemaVersionLoop]:
                    NewStructName  = self.ArrayStructMember [ResourceTypeLoop][SchemaVersionLoop][KeyLoop][0]
                    if NewStructName not in ArrayStructAdded:
                        if "Redfish" + self.RedfishSchemaFile.ResourceType not in NewStructName: # Check if this is schema-specific array.
                            self.RedfishSchemaFile.CIncludeFileText += "#ifndef "+ NewStructName + "_\n" + \
                           "#define "+ NewStructName + "_\n"                        
                        
                        self.RedfishSchemaFile.CIncludeFileText += "typedef struct " + "_" + NewStructName + " " + " {\n"
                        self.RedfishSchemaFile.CIncludeFileText += "    " + NewStructName + "    *Next;\n"
                        self.RedfishSchemaFile.CIncludeFileText += "    " + self.ArrayStructMember [ResourceTypeLoop][SchemaVersionLoop][KeyLoop][1] + "    *ArrayValue;\n"
                        self.RedfishSchemaFile.CIncludeFileText += "} "+NewStructName + ";\n"
                        if "Redfish" + self.RedfishSchemaFile.ResourceType not in NewStructName: # Check if this is schema-specific array.
                            self.RedfishSchemaFile.CIncludeFileText += "#endif\n"
                        self.RedfishSchemaFile.CIncludeFileText += "\n"

                        if "Redfish" + self.RedfishSchemaFile.ResourceType not in NewStructName: # Check if this is schema-specific array.
                            NewInsertforwardTypedef += "#ifndef "+ NewStructName + "_\n"

                        NewInsertforwardTypedef += "typedef struct _" + NewStructName + " " + NewStructName + ";\n"

                        if "Redfish" + self.RedfishSchemaFile.ResourceType not in NewStructName: # Check if this is schema-specific array.
                            NewInsertforwardTypedef += "#endif\n"

                        ArrayStructAdded.append (NewStructName)

        StructPointerName = StructureName [RedfishCs.ResourceType][RedfishCs.SchemaVersion][self.RedfishSchemaFile.SchemaRef][STRUCTURE_NAME_TUPLE_NAME]
        ToCsFunName = "Json_" + RedfishCs.ResourceType + "_" + RedfishCs.SchemaVersion + "_To_CS"
        if RedfishCs.SchemaVersion == REDFISH_SCHEMA_NAMING_NOVERSIONED:
            StructPointerName = StructPointerName.replace (REDFISH_SCHEMA_NAMING_NOVERSIONED + "_", "")
            ToCsFunName = ToCsFunName.replace (REDFISH_SCHEMA_NAMING_NOVERSIONED + "_", "")
        self.RedfishSchemaFile.CIncludeFileText += "RedfishCS_status\n"
        self.RedfishSchemaFile.CIncludeFileText += ToCsFunName  + " (char *JsonRawText, " + StructPointerName + " **ReturnedCS);\n\n"

        if RedfishCs.SchemaVersion == REDFISH_SCHEMA_NAMING_NOVERSIONED:
            ToJsonFunName = "CS_To_" + RedfishCs.ResourceType + "_JSON"
        else:
            ToJsonFunName = "CS_To_" + RedfishCs.ResourceType + "_" + RedfishCs.SchemaVersion + "_JSON"
        self.RedfishSchemaFile.CIncludeFileText += "RedfishCS_status\n"
        self.RedfishSchemaFile.CIncludeFileText += ToJsonFunName  + " (" + StructPointerName + " *CSPtr, char **JsonText);\n\n"

        if RedfishCs.SchemaVersion == REDFISH_SCHEMA_NAMING_NOVERSIONED:
            DestoryFunName = "Destroy" + RedfishCs.ResourceType + REDFISH_STRUCT_NAME_TAIL
        else:
            DestoryFunName = "Destroy" + RedfishCs.ResourceType + "_" + RedfishCs.SchemaVersion + REDFISH_STRUCT_NAME_TAIL
        self.RedfishSchemaFile.CIncludeFileText += "RedfishCS_status\n"
        self.RedfishSchemaFile.CIncludeFileText += DestoryFunName  + " (" + StructPointerName + " *CSPtr);\n\n"             

        if RedfishCs.SchemaVersion == REDFISH_SCHEMA_NAMING_NOVERSIONED:
            DestoryJsonFunName = "Destroy" + RedfishCs.ResourceType + "_Json"
        else:
            DestoryJsonFunName = "Destroy" + RedfishCs.ResourceType + "_" + RedfishCs.SchemaVersion + "_Json"
        self.RedfishSchemaFile.CIncludeFileText += "RedfishCS_status\n"
        self.RedfishSchemaFile.CIncludeFileText += DestoryJsonFunName  + " (RedfishCS_char *JsonText);\n\n"          

        #self.RedfishSchemaFile.CIncludeFileText += (StructPointerName +  " *\n")            
        #self.RedfishSchemaFile.CIncludeFileText += (ToCsFunName  + " (char *JsonRawText);\n\n")

        self.RedfishSchemaFile.CIncludeFileText += "#endif\n"

        self.CRedfishRootStructureName = StructPointerName
        self.CRedfishRootFunctionName = ToCsFunName
        self.CToRedfishFunctionName = ToJsonFunName
        self.CRedfishDestoryFunctionName = DestoryFunName             
        self.CRedfishDestoryJsonFunctionName = DestoryJsonFunName

        #Insert forward typedef for new added structure for array
        if self.ArrayStructMember != {}: 
            index =self.RedfishSchemaFile.CIncludeFileText.find ("typedef struct _")
            if index != -1:
                self.RedfishSchemaFile.CIncludeFileText = self.RedfishSchemaFile.CIncludeFileText [:index] + \
                                                          NewInsertforwardTypedef + \
                                                          self.RedfishSchemaFile.CIncludeFileText [index:]
    
        # Write to file
        IncludeDir = os.path.normpath(self.GenRedfishSchemaCs.OuputDirectory + "/include")
        if not os.path.exists (IncludeDir):
            os.makedirs(IncludeDir)
        try:
            IncFile = os.path.normpath(IncludeDir + "/" + self.RedfishSchemaFile.CIncludeFile)
            fo = open(IncFile,"w")
        except:
            ToolLogInformation.LogIt ("Create Include file fail!")
            sys.exit()

        self.CIncludeFileName = self.RedfishSchemaFile.CIncludeFile
        fo.write (self.RedfishSchemaFile.CIncludeFileText)
        fo.close()

    # Gen C code for each member in structure.
    def GenStructureMemberCCode (self, ResourceType, SchemaVersion, TypeName, StrucName, IsRootStruc, IsArrayElement):
        StructureName = self.StructureName
        StructureMemberDataType = self.StructureMemberDataType        

        StrucNameList = StrucName.split('_')
        # Loop to check each structure member
        if len (StrucName.split ('_')) > 1 and TypeName == StrucName.split ('_')[0]: # This is the object defined under ResourceType,SchemaVersion,TypeName
            #StructMemHead = StructureName [ResourceType][SchemaVersion][StrucName][STRUCTURE_NAME_TUPLE_NAME].replace (REDFISH_STRUCT_NAME_HEAD, "")
            StructMemHead = self.RemoveStructureNameHead (StructureName [ResourceType][SchemaVersion][StrucName][STRUCTURE_NAME_TUPLE_NAME])

        elif len (StrucNameList) > 1 and TypeName not in StrucNameList [len(StrucNameList) - 1]: # This is the nested object defined under ResourceType,SchemaVersion,TypeName
            if TypeName not in StrucNameList: # Structure name is difer than structure member name
                if TypeName in StructureName [ResourceType][SchemaVersion]:
                    #StructMemHead = StructureName [ResourceType][SchemaVersion][TypeName][STRUCTURE_NAME_TUPLE_NAME].replace (REDFISH_STRUCT_NAME_HEAD, "")
                    StructMemHead = self.RemoveStructureNameHead (StructureName [ResourceType][SchemaVersion][TypeName][STRUCTURE_NAME_TUPLE_NAME])
                else:
                    # No member found, means the properties for this data type is "{}"
                    return self.CCodeEmptyProp (IsArrayElement), True                        
            else: # Structure name is same as structure member name
                for index in range (0, len(StrucNameList)):
                    if TypeName in StrucNameList[index]:
                        break

                NestedTypeName = ""
                for index2 in range (index, len(StrucNameList)):
                    NestedTypeName += StrucNameList[index2] + "_"
                NestedTypeName = NestedTypeName.rstrip ('_')
                if NestedTypeName in StructureName [ResourceType][SchemaVersion]:
                    StructMemHead = StructureName [ResourceType][SchemaVersion][NestedTypeName][STRUCTURE_NAME_TUPLE_NAME].replace (REDFISH_STRUCT_NAME_HEAD, "")
                else:
                    # No member found, means the properties for this data type is "{}"
                    return self.CCodeEmptyProp (IsArrayElement), True                

        elif TypeName in StructureName [ResourceType][SchemaVersion]: # This is the object defined in #/definitions/
            #StructMemHead = StructureName [ResourceType][SchemaVersion][TypeName][STRUCTURE_NAME_TUPLE_NAME].replace (REDFISH_STRUCT_NAME_HEAD, "")
            StructMemHead = self.RemoveStructureNameHead (StructureName [ResourceType][SchemaVersion][TypeName][STRUCTURE_NAME_TUPLE_NAME])
             
        else:
            # No member found, means the properties for this data type is "{}"
            return self.CCodeEmptyProp (IsArrayElement), True

        #StructMemHead = StructMemHead.rstrip(REDFISH_STRUCT_NAME_TAIL)
        StructMemHead = self.RemoveTailCSPattern (StructMemHead)
        CodeGenerated = ""
        MemberFound = False
        for key in sorted (StructureMemberDataType.keys ()):
            if key.find(StructMemHead) != -1:
                if key.replace (StructMemHead, "") != "":
                    MemberFound = True
                    Member = key.replace (StructMemHead, "").lstrip('_')
                    if len (Member.split ('_')) == 1:
                        Member = self.FormatingStructMemberName (Member)
                        StructMemDataType, IsRedfishCsLinkArray = self.FormatingStructMemberDataType (StructureMemberDataType [key][STRUCTURE_MEMBER_TUPLE_DATATYPE], ResourceType, SchemaVersion, key)
                        CodeGenerated += C_SRC_TAB_SPACE + "// " + StructureMemberDataType [key][STRUCTURE_MEMBER_TUPLE_ORG_KEY_NAME] + "\n"
                        IsArrayStruct = False
                        
                        if IsRedfishCsLinkArray:
                            StructMemDataType = StructMemDataType + "_Array"

                        if StructMemDataType in self.CCodeGenFun:
                            CodeGenerated += self.CCodeGenFun [StructMemDataType](StructureMemberDataType, key, Member, IsRootStruc)
                        else:                            
                            if "Array" in StructMemDataType or StructureMemberDataType [key][STRUCTURE_MEMBER_TUPLE_IS_STRUCTURE]:
                                if "Array" in StructMemDataType:
                                    if StructMemDataType.replace("_Array","") in NatrualDataTypeArray:
                                        FuncText, FuncName = self.CCodeGenCallNaturalDataTypeArrayFunName (ResourceType, SchemaVersion, TypeName, StructureMemberDataType, key, StructMemDataType, Member, IsRootStruc)
                                        CodeGenerated += FuncText
                                        self.CCodeGenNaturalDataTypeArrayFuncNameCode (StructureMemberDataType, ResourceType, SchemaVersion, TypeName, key, StructMemDataType, FuncName, IsRootStruc)                                         
                                        continue
                                    else:
                                        try:
                                            for ArrayResourceTypeKey in self.ArrayStructMember.keys():
                                                for ArraySchemaVersionKey in self.ArrayStructMember[ArrayResourceTypeKey].keys():
                                                    for ArrayStructkeyName in self.ArrayStructMember[ArrayResourceTypeKey][ArraySchemaVersionKey].keys():
                                                        if StructMemDataType in self.ArrayStructMember[ArrayResourceTypeKey][ArraySchemaVersionKey][ArrayStructkeyName][0]:
                                                            StructArrayMemDataType = StructMemDataType
                                                            StructMemDataType = self.ArrayStructMember[ArrayResourceTypeKey][ArraySchemaVersionKey][ArrayStructkeyName][1]
                                                            IsArrayStruct = True
                                                            raise BreakForLoop
                                            print ("Unsupported C function for array: " + StructMemDataType) 
                                            sys.exit()

                                        except BreakForLoop:
                                            pass                                                    

                                #StructDataType = self.RemoveStructureNameHead (StructMemDataType).rstrip(REDFISH_STRUCT_NAME_TAIL)
                                StructDataType = self.RemoveTailCSPattern (self.RemoveStructureNameHead (StructMemDataType))
                                NewResourceType = StructDataType.split('_')[0]
                                if REDFISH_SCHEMA_NAMING_NOVERSIONED in StructureMemberDataType [key][STRUCTURE_MEMBER_TUPLE_DATATYPE]:
                                    NewSchemaVersion = REDFISH_SCHEMA_NAMING_NOVERSIONED
                                    NewTypeName = StructDataType.replace(NewResourceType + "_","") 
                                else:
                                    NewSchemaVersion = StructDataType.split('_')[1] + '_' + StructDataType.split('_')[2] + '_' + StructDataType.split('_')[3]
                                    NewTypeName = StructDataType.replace(NewResourceType + "_" + NewSchemaVersion + "_", "") 
                                    #NewTypeName = NewTypeName.split('_')[0]

                                if IsArrayStruct:
                                    FuncText, FuncName = self.CCodeGenCallStructArrayFunName (NewResourceType, NewSchemaVersion, NewTypeName, StructureMemberDataType, key, StructArrayMemDataType, Member, IsRootStruc)
                                else:
                                    FuncText, FuncName = self.CCodeGenCallStructFunName (NewResourceType, NewSchemaVersion, NewTypeName, StructureMemberDataType, key, Member, IsRootStruc)                                        
                                CodeGenerated += FuncText
                                # Log C functions created
                                # [0] : Schema name
                                # [1] : Schema version
                                # [2] : Instance of the duplication
                                if FuncName in self.CfunctionsCreated:
                                    if self.CfunctionsCreated [FuncName][0] != NewResourceType or self.CfunctionsCreated [FuncName][1] != NewSchemaVersion:
                                        print("***ERROR*** Duplicated function is created: " + FuncName + " in " + NewResourceType + NewSchemaVersion + "\n")
                                        sys.exit()
                                else:
                                    self.CfunctionsCreated [FuncName] = [NewResourceType, NewSchemaVersion, 0]

                                if IsArrayStruct:
                                    self.CCodeGenStructArrayFuncNameCode (StructureMemberDataType, NewResourceType, NewSchemaVersion, NewTypeName, key, StructArrayMemDataType, StrucName + "_" + Member, FuncName, IsRootStruc)                                    
                                else:                                
                                    self.CCodeGenStructFuncNameCode (StructureMemberDataType, NewResourceType, NewSchemaVersion, NewTypeName, key, StrucName + "_" + Member, FuncName, IsRootStruc)                               
                            else:
                                print ("Unsupported C function for this data type: " + StructMemDataType)
        if not MemberFound:
            CodeGenerated += self.CCodeEmptyProp(IsArrayElement)
            return CodeGenerated, True

        return CodeGenerated, False

            
    # This generate Redfish to C structure C file
    def GenCSCfile (self):
        RedfishCs = self.RedfishCsList
        StructureName = self.StructureName
        StructureMemberDataType = self.StructureMemberDataType

        # Find the root structure for this schema.
        try:
            for ResourceTypeLoop in sorted (StructureName.keys()):
                for SchemaVersionLoop in sorted (StructureName [ResourceTypeLoop].keys()):       
                    for StrucName in sorted(StructureName [ResourceTypeLoop][SchemaVersionLoop].keys()):
                        if StrucName == self.RedfishSchemaFile.SchemaRef and \
                         ResourceTypeLoop == RedfishCs.ResourceType and \
                         SchemaVersionLoop == RedfishCs.SchemaVersion:
                            self.CRedfishRootStrucutreResrouceType = ResourceTypeLoop
                            self.CRedfishRootStrucutreResrouceVersion = SchemaVersionLoop
                            if self.CRedfishRootStrucutreResrouceVersion == REDFISH_SCHEMA_NAMING_NOVERSIONED:
                                self.CRedfishRootStrucutreResrouceVersion = ""
                                self.CRedfishCFile = ResourceTypeLoop + ".c"   
                            else:
                                self.CRedfishCFile = ResourceTypeLoop + "." + SchemaVersionLoop + ".c"                            
                            self.CRedfishRootStrucutreTypeName = StrucName                    
                            raise BreakForLoop
        except BreakForLoop:
            pass

        self.CTextFile = HPECopyright + "\n"
        self.CTextFile += ("#include" + "\"" + self.CIncludeFileName + "\"\n")
        self.CTextFile += ("#include <stdlib.h>\n")
        self.CTextFile += ("#include <string.h>\n")
        self.CTextFile += ("#include <jansson.h>\n")

        self.CTextFile += ("\n") 
        self.CTextFile += ("RedfishCS_bool SupportedRedfishResource (RedfishCS_char *Odata_Type, RedfishCS_char *NameSpace, RedfishCS_char *Version, RedfishCS_char *DataType);\n")        
        self.CTextFile += ("RedfishCS_status CreateCsUriByNode (RedfishCS_void *Cs, json_t *JsonOj, RedfishCS_char *NodeName, RedfishCS_char *ParentUri, RedfishCS_Type_Uri_Data **CsTypeUriData);\n")
        self.CTextFile += ("RedfishCS_status CreateCsJsonByNode (RedfishCS_void *Cs, json_t *JsonOj, RedfishCS_char *NodeName, RedfishCS_char *ParentUri, RedfishCS_Type_JSON_Data **CsTypeJsonData);\n")
        self.CTextFile += ("RedfishCS_status CreateCsUriOrJsonByNode (RedfishCS_void *Cs, json_t *JsonObj, RedfishCS_char *NodeName, RedfishCS_char *ParentUri, RedfishCS_Link *LinkHead);\n")
        self.CTextFile += ("RedfishCS_status CreateCsUriOrJsonByNodeArray (RedfishCS_void *Cs, json_t *JsonObj, RedfishCS_char *NodeName, RedfishCS_char *ParentUri, RedfishCS_Link *LinkHead);\n")
        self.CTextFile += ("RedfishCS_status CreateJsonPayloadAndCs (char *JsonRawText, char *ResourceType, char *ResourceVersion, char *TypeName, json_t **JsonObjReturned, void **Cs, int size);\n")
        self.CTextFile += ("RedfishCS_status GetRedfishPropertyStr (RedfishCS_void *Cs, json_t *JsonObj, char *Key, RedfishCS_char **DstBuffer);\n")
        self.CTextFile += ("RedfishCS_status GetRedfishPropertyBoolean (RedfishCS_void *Cs, json_t *JsonObj, char *Key, RedfishCS_bool **DstBuffer);\n")
        self.CTextFile += ("RedfishCS_status GetRedfishPropertyVague (RedfishCS_void *Cs, json_t *JsonObj, char *Key, RedfishCS_Vague **DstBuffer);\n")        
        self.CTextFile += ("RedfishCS_status DestoryCsMemory (RedfishCS_void *rootCs);\n")
        self.CTextFile += ("RedfishCS_status GetRedfishPropertyInt64 (RedfishCS_void *Cs, json_t *JsonObj, char *Key, RedfishCS_int64 **Dst);\n")
        self.CTextFile += ("RedfishCS_status InsertJsonStringObj (json_t *JsonObj, char *Key, char *StringValue);\n")
        self.CTextFile += ("RedfishCS_status InsertJsonLinkObj (json_t *JsonObj, char *Key, RedfishCS_Link *Link);\n")        
        self.CTextFile += ("RedfishCS_status InsertJsonInt64Obj (json_t *ParentJsonObj, char *Key, RedfishCS_int64 *Int64Value);\n")   
        self.CTextFile += ("RedfishCS_status InsertJsonBoolObj (json_t *ParentJsonObj, char *Key, RedfishCS_bool *BoolValue);\n")   
        self.CTextFile += ("RedfishCS_status InsertJsonStringArrayObj (json_t *JsonObj, char *Key, RedfishCS_char_Array *StringValueArray);\n")
        self.CTextFile += ("RedfishCS_status InsertJsonLinkArrayObj (json_t *JsonObj, char *Key, RedfishCS_Link *LinkArray);\n")        
        self.CTextFile += ("RedfishCS_status InsertJsonInt64ArrayObj (json_t *ParentJsonObj, char *Key, RedfishCS_int64_Array *Int64ValueArray);\n")   
        self.CTextFile += ("RedfishCS_status InsertJsonBoolArrayObj (json_t *ParentJsonObj, char *Key, RedfishCS_bool_Array *BoolValueArray);\n")
        self.CTextFile += ("RedfishCS_status InsertJsonVagueObj (json_t *ParentJsonObj, char *Key, RedfishCS_Vague *VagueValue);\n")
        self.CTextFile += ("RedfishCS_bool CheckEmptyPropJsonObject(json_t *JsonObj, RedfishCS_uint32 *NumOfProperty);\n")
        self.CTextFile += ("RedfishCS_status CreateEmptyPropCsJson(RedfishCS_void *Cs, json_t *JsonOj, RedfishCS_char *NodeName, RedfishCS_char *ParentUri, RedfishCS_Type_EmptyProp_CS_Data **CsTypeEmptyPropCS, RedfishCS_uint32 NunmOfProperties);\n")
        self.CTextFile += ("RedfishCS_status CsEmptyPropLinkToJson(json_t *CsJson, char *Key, RedfishCS_Link *Link);\n\n")                        

        self.CFuncText = []
        FunText = ""
        CSToJSonCode = ""

        #Redfish C Structure to JSON
        self.CurrentIndentNumber = 1
        self.CStructureToJsonStructureFuncions = ""
        self.CStructureToJsonStructureExistFunc = []
        CSToJSonCode += "//\n"
        if RedfishCs.SchemaVersion == REDFISH_SCHEMA_NAMING_NOVERSIONED:
            CSToJSonCode += "// C structure to JSON for " + RedfishCs.ResourceType + "." + StrucName + "\n"
        else:
            CSToJSonCode += "// C structure to JSON for " + RedfishCs.ResourceType + "." + RedfishCs.SchemaVersion + "." + StrucName + "\n"
        CSToJSonCode += "//\n"         
        CSToJSonCode += "RedfishCS_status " + self.CToRedfishFunctionName + "(" + self.CRedfishRootStructureName + " *CSPtr, RedfishCS_char **JsonText)\n"
        CSToJSonCode += "{\n"
        CSToJSonCode += C_SRC_TAB_SPACE + "json_t  *CsJson;\n\n"        

        CSToJSonCode += C_SRC_TAB_SPACE + "if (CSPtr == NULL || JsonText == NULL || CSPtr->Header.ResourceType != RedfishCS_Type_CS) {\n"
        CSToJSonCode += C_SRC_TAB_SPACE * 2 + "return RedfishCS_status_invalid_parameter;\n"
        CSToJSonCode += C_SRC_TAB_SPACE + "}\n"
        CSToJSonCode += C_SRC_TAB_SPACE + "CsJson = json_object();\n"
        CSToJSonCode += C_SRC_TAB_SPACE + "if (CsJson == NULL) {\n"
        CSToJSonCode += C_SRC_TAB_SPACE * 2 + "return RedfishCS_status_unsupported;\n"
        CSToJSonCode += C_SRC_TAB_SPACE + "}\n"

        # Loop through structure to generate JSON string
        CSToJSonCode += self.GenCStructToJsonCCode (RedfishCs.ResourceType, RedfishCs.SchemaVersion)

        CSToJSonCode += C_SRC_TAB_SPACE + "*JsonText = (RedfishCS_char *)json_dumps(CsJson, JSON_INDENT(2 * " + str(self.CurrentIndentNumber)  + ") | JSON_ENSURE_ASCII);\n"
        CSToJSonCode += C_SRC_TAB_SPACE + "json_decref(CsJson);\n"
        CSToJSonCode += C_SRC_TAB_SPACE + "return RedfishCS_status_success;\n"
        CSToJSonCode += "Error:;\n"
        CSToJSonCode += C_SRC_TAB_SPACE + "json_decref(CsJson);\n"
        CSToJSonCode += C_SRC_TAB_SPACE + "return RedfishCS_status_unsupported;\n"
        CSToJSonCode += "}\n\n"

        FunText += self.CStructureToJsonStructureFuncions + "\n" + CSToJSonCode

        #Destory C Structure function.
        FunText += "//\n"
        if RedfishCs.SchemaVersion == REDFISH_SCHEMA_NAMING_NOVERSIONED:        
            FunText += "// Destory C Structure for " + RedfishCs.ResourceType + "." + StrucName + "\n"
        else:
            FunText += "// Destory C Structure for " + RedfishCs.ResourceType + "." + RedfishCs.SchemaVersion + "." + StrucName + "\n"
        FunText += "//\n"         
        FunText += "RedfishCS_status " + self.CRedfishDestoryFunctionName + "(" + self.CRedfishRootStructureName + " *CSPtr)\n"
        FunText += "{\n"
        FunText += C_SRC_TAB_SPACE + "RedfishCS_status Status;\n\n"        
        FunText += C_SRC_TAB_SPACE + "Status = DestoryCsMemory ((RedfishCS_void *)CSPtr);\n"
        FunText += C_SRC_TAB_SPACE + "return Status;\n"
        FunText += "}\n\n"

        #Destory JSON text function.
        FunText += "//\n"
        if RedfishCs.SchemaVersion == REDFISH_SCHEMA_NAMING_NOVERSIONED:        
            FunText += "// Destory JSON text for " + RedfishCs.ResourceType + "." + StrucName + "\n"
        else:
            FunText += "// Destory JSON text for " + RedfishCs.ResourceType + "." + RedfishCs.SchemaVersion + "." + StrucName + "\n"
        FunText += "//\n"         
        FunText += "RedfishCS_status " + self.CRedfishDestoryJsonFunctionName + "(RedfishCS_char *JsonText)\n"
        FunText += "{\n"   
        FunText += C_SRC_TAB_SPACE + "free ((RedfishCS_void *)JsonText);\n"
        FunText += C_SRC_TAB_SPACE + "return RedfishCS_status_success;\n"
        FunText += "}\n\n"

        # Gen main function.
        FunText += "//\n"
        FunText += "//Generate C structure for " + RedfishCs.ResourceType + "." + RedfishCs.SchemaVersion + "." + StrucName + "\n"
        FunText += "//\n"                
        FunText += ("RedfishCS_status\n" + self.CRedfishRootFunctionName + "(RedfishCS_char *JsonRawText, " + self.CRedfishRootStructureName + " **ReturnedCs)" + "\n{\n")
        FunText += C_SRC_TAB_SPACE + "RedfishCS_status  Status;\n"
        FunText += C_SRC_TAB_SPACE + "json_t *JsonObj;\n"
        FunText += C_SRC_TAB_SPACE + self.CRedfishRootStructureName + " *Cs;\n\n"

        version = SchemaVersionLoop;
        if version == REDFISH_SCHEMA_NAMING_NOVERSIONED:
            version == ""
        FunText += C_SRC_TAB_SPACE + "Status = CreateJsonPayloadAndCs (JsonRawText," +\
                   " \"" + ResourceTypeLoop + "\"," +\
                   " \"" + version.lower() + "\"," +\
                   " \"" + StrucName + "\"," +\
                   " &JsonObj, (RedfishCS_void **)&Cs, sizeof (" +\
                   self.CRedfishRootStructureName +"));\n"
        FunText += CCodeErrorExitCode

        # Gen code, start from root structure.
        TempText, IsEmptyProp = self.GenStructureMemberCCode (ResourceTypeLoop, SchemaVersionLoop, self.RedfishSchemaFile.SchemaRef, StrucName, True, False)
        FunText += TempText
        FunText += C_SRC_TAB_SPACE + "json_decref(JsonObj);\n"
        FunText += C_SRC_TAB_SPACE + "*ReturnedCs = Cs;\n"
        FunText += C_SRC_TAB_SPACE + "return RedfishCS_status_success;\n"
        FunText += "Error:;\n"
        FunText += C_SRC_TAB_SPACE + "json_decref(JsonObj);\n"
        FunText += C_SRC_TAB_SPACE + self.CRedfishDestoryFunctionName + " (Cs);\n"
        FunText += C_SRC_TAB_SPACE + "return Status;\n"        
        FunText += "}\n"
        self.CFuncText.append (FunText)

        # function declaration
        for index in range (0, len(self.StructFuncNameTypedef)):
            self.CTextFile += self.StructFuncNameTypedef [index]

        # Merge funcitons
        for index in range (0, len (self.CFuncText)):
            self.CTextFile += self.CFuncText[index]
        
        # Create directory for this C file
        if self.CRedfishRootStrucutreResrouceVersion == "":
            VersionDirTail = ""
        else:
            VersionDirTail = "." + self.CRedfishRootStrucutreResrouceVersion
        CFileDir = os.path.normpath(self.GenRedfishSchemaCs.OuputDirectory + "/src" + "/" + \
                                    self.CRedfishRootStrucutreResrouceType + "/" + \
                                    self.CRedfishRootStrucutreResrouceType + VersionDirTail)
        if not os.path.exists (CFileDir):
            os.makedirs(CFileDir)
        try:
            CFile = os.path.normpath(CFileDir + "/" + self.CRedfishCFile)
            fo = open(CFile,"w")
        except:
            ToolLogInformation.LogIt ("Create C file fail!")
            sys.exit()

        fo.write (self.CTextFile)
        fo.close()
        self.CSourceFileRelativeDir = ("/src" + "/" + \
                                    self.CRedfishRootStrucutreResrouceType + "/" + \
                                    self.CRedfishRootStrucutreResrouceType + VersionDirTail)
        self.CSourceFile = self.CRedfishCFile      