#
# Redfish JSON resource to C structure converter source code generator.
#
# (C) Copyright 2018 Hewlett Packard Enterprise Development LP
#

import sys, os, logging
import datetime

##
# Common definitions
#
TOOL_LOG_NONE = 0
TOOL_LOG_TO_CONSOLE = 1
TOOL_LOG_TO_FILE = 2
TOOL_LOG_SIMPLE_PROGRESS_DOTS = 3

TOOL_LOG_ON = True
TOOL_LOG_OFF = False


## Class of logger for logging messages.
#
# This class is for logging message to console, file or etc.
#
class ToolLog(object):
    # Logtype 
    # TurnOn = Boolean 
    
    ## Initial the ToolLog class. 
    #
    # Initial the information of ToolLog class
    #
    #   @param[in] LogType Tool log type, see the common definitions
    #    
    def __init__(self, LogType, LogFilePath):
        self.Logtype = LogType
        self.TurnOn = True
        self.PreviousLogType = LogType  
        self.CurrentSimpleDotMessages = 0
        self.CurrentSimpleDotsCarryReturn = 0
        self.SimpleDotMessages = 30
        self.SimpleDotsCarryReturn = 80
        if self.Logtype == TOOL_LOG_TO_FILE:
            self.LogFilePath = LogFilePath
            if os.path.exists (self.LogFilePath) == True:
                fdo = open (self.LogFilePath, "a") 
            else:
                fdo = open (self.LogFilePath, "w")    
            fdo.writelines ("\n\n======= " + str(datetime.datetime.now()) + " =============\n")
            fdo.close()
        
    ## Log the message
    #
    # This function logs the message according
    # to the ToolLog.LogType
    #
    #   @param[in] message Message to log.
    #         
    def LogIt (self, message):
        if self.TurnOn == False:
            return        
        if self.Logtype == TOOL_LOG_NONE:
            return
        elif self.Logtype == TOOL_LOG_SIMPLE_PROGRESS_DOTS:
            #
            # log as the progress dots.
            #             
            self.CurrentSimpleDotMessages += 1
            if self.CurrentSimpleDotMessages == self.SimpleDotMessages:            
                sys.stdout.write ('.')
                self.CurrentSimpleDotMessages = 0
                self.CurrentSimpleDotsCarryReturn += 1
                if self.CurrentSimpleDotsCarryReturn == self.SimpleDotsCarryReturn:
                    self.CurrentSimpleDotsCarryReturn = 0
                    sys.stdout.write ('\n')                    
        elif self.Logtype == TOOL_LOG_TO_CONSOLE:
            #
            # log to console.
            #            
            print (message)
        elif self.Logtype == TOOL_LOG_TO_FILE:
            #
            # log to file.
            #
            if self.LogFilePath == "":
                self.LogFilePath = "RedfishCs.log"

            if os.path.exists (self.LogFilePath) == True:
                fdo = open (self.LogFilePath, "a")
            else:
                fdo = open (self.LogFilePath, "w")
                if fdo == 0:
                    self.LogFilePath == ""
                    return
            fdo.writelines (message + "\n")
            fdo.close()
                
            
    ## Turn on/off the log
    #
    # This function turns on/off the log
    # to the ToolLog.LogType
    #
    #   @param[in] TurnOn Set to True for turning on the log.
    #         
    def LogTurnOnOff (self, TurnOn):
        if TurnOn == True:
            self.Logtype = self.PreviousLogType
            self.TurnOn = True
        else:
            self.PreviousLogType = self.Logtype 
            self.TurnOn = False            
        
       



