#MicroPython Library for interfacing the TPS55289 Buck-Boost Converter with RP2040
"""
MIT License
Copyright (c) 2024 Krishna Swaroop

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
from machine import Pin


# Register Addresses for TPS55289
_TPS55289_REF_VOLTAGE_LSB_ADDR  = const(0x00)   # Reference Voltage LSB Register Address
_TPS55289_REF_VOLTAGE_MSB_ADDR  = const(0x01)   # Reference Voltage MSB Register Address
_TPS55289_IOUT_LIMIT_ADDR       = const(0x02)   # Current Limit Setting Register Address
_TPS55289_VOUT_SR_ADDR          = const(0x03)   # Slew Rate Setting Register Address
_TPS55289_VOUT_FS_ADDR          = const(0x04)   # Feedback Mechanism Selection Register Address
_TPS55289_CDC_ADDR              = const(0x05)   # Cable Compensation Setting Register Address
_TPS55289_MODE_ADDR             = const(0x06)   # Mode Control Register Address
_TPS55289_STATUS_ADDR           = const(0x07)   # Operating Status Register Address

# Constants
_INTFB_00                       = const(0.2256) # 2.5mV Step
_INTFB_01                       = const(0.1128) # 5mV Step
_INTFB_10                       = const(0.0752) # 7.5mV Step
_INTFB_11                       = const(0.0564) # 10mV Step


# Instantiation Template for the TPS55289 Device
# from machine import I2C and Pin
# import TPS55289
# TPS55289_I2C_BUS = I2C(0, scl=Pin(5), sda=Pin(4), freq=100_000)
# Channel1 = TPS55289(i2c=TPS55289_I2C_BUS, enablePin = 0, outputVoltage=5, currentLimit=0.35, feedbackMode=0b0)

# Methods can be used as Channel1.setOutputVoltage(5.0)


class TPS55289():
    def __init__(self, i2c, address=0x74, enablePin=0, outputVoltage=0.8, currentLimit=6.35, feedbackMode=0b0):
        # I2C Bus and Enable Pin Attributes
        self._i2c = i2c
        self._address = address
        self._enablePin = Pin(enablePin, Pin.OUT, Pin.PULL_DOWN,value=0)
        
        # Channel Details (Only Relevant to my project)
        self._channelNum = 1
        # Power Output Parameters
        self._outputVoltage = outputVoltage
        self._outputCurrentLimit = currentLimit
        self._feedbackMode = feedbackMode

        # Other necessary attributes
        self._REF_VOLTAGE_LSB   = 0b00000000
        self._REF_VOLTAGE_MSB   = 0B00000000
        self._IOUT_LIMIT        = 0b11100100
        self._VOUT_SR           = 0b00000001
        self._VOUT_FS           = 0b00000011
        self._CDC               = 0b11100000
        self._MODE              = 0b00100010
        self._STATUS            = 0b00000000

        # REF Register Parameters
        self._VREF              = 0b00000000000  
        # IOUT_LIMIT Register Parameters
        self._currentLimitEN    = 0b1
        self._currentLimitSet   = 0b1100100
        # VOUT_SR Register Parameters
        self._OCP_DELAY         = 0b00
        self._slewRate          = 0b01
        # VOUT_FS Register Parameters
        self._FB_MODE           = 0b0
        self._INTFB             = 0b11
        self._INTFB_Val         = 0.0564
        # CDC Regsiter Parameters
        self._SC_Mask           = 0b1
        self._OCP_MASK          = 0b1
        self._OVP_MASK          = 0b1
        self._CDC_OPTION        = 0b0
        self._CDC_SETTING       = 0b000
        # Mode Register Parameters
        self._OE                = 0b0
        self._FSWDBL            = 0b0
        self._HICCUP            = 0b1
        self._DISCHG            = 0b0
        self._FPWM              = 0b0
        
        self.init()

    def init(self):
        if self._i2c.scan().count(self._address) == 0:
            print("TPS55289 not found at I2C Address {:#x}\n".format(self._address))

        # Disabling the Converter
        # self._enablePin.off()       
        self.disable()
        # Set Output Voltage
        self.setOutputVoltage(self._outputVoltage)
        # Set Current Limit
        self.enableOutputCurrentLimit()
        self.setOutputCurrentLimit(self._outputCurrentLimit)
        # Set Slew Rate
        self.setOCPResponseTime(0b00)                           # 128uS Response Time Selected
        self.setSlewRate(0b01)                                  # 2.5mV/uS Slew Rate Selected
        # Set Feedback Mechanism
        self.setFeedbackMechanism("internal")                   # Internal Feedback Mechanism
        self.setStepSize(10.0)                                  # 10mV Step Size
        # Set CDC Register Parameters
        self.enableSCIndication()
        self.enableOCPIndication()
        self.enableOVPIndication()
        self.setCDCOption(0)                                    # Enabling Internal CDC Compensation Mechanism
        self.setCDCCompensation(0.0)
        self.FSWDoubling(0)
        self.enableHiccupMode()
        self.disableVOUTDischarge
        self.FSWOperatingMode(0)
        # Reading and outputting status of DC-DC Converter
        self.readStatusRegister("debug")

        # Enabling TPS55289 DC-DC Converter
        #self._enablePin.on()        # Enabling Converter after setting all values
        self.enable()# self._MODE |= (1<<7)

    def setRegister(self, register, registerAddress):
        self._i2c.writeto_mem(self._address, registerAddress, register, addrsize=8)
        

    def getRegister(self, registerAddress):
        return self._i2c.readfrom_mem(self._address, registerAddress,1)

    ###################################################################################
    # REF Register Methods
    
    # Method to set output voltage of DC-DC Converter in internal feedback mode
    # Valid Inputs: 0.8V to 22V
    def setOutputVoltage(self, voltage):
        # Check if Output Voltage Selected is valid
        if (voltage >= 0.8) & (voltage <= 22) == 0:
            print("Requested Output Voltage is out of bounds\n")
            pass
        # Disabling output before setting new output voltage
        #self.disable()
        # Figure out what bits need to be set for
        # the required output voltage
        self._outputVoltage = voltage
        VREF = self._outputVoltage*self._INTFB_Val
        self._VREF  |= ((int(1.7715*((VREF*1000) - 45)))+1)
        self._outputVoltage = self._VREF/self._INTFB
        # Setting Local Register values
        self._REF_VOLTAGE_LSB = self._VREF & 0xFF
        self._REF_VOLTAGE_MSB = (self._VREF >> 8) & 0b111

        # Updating on-device registers
        self.setRegister(self._REF_VOLTAGE_LSB, _TPS55289_REF_VOLTAGE_LSB_ADDR)
        self.setRegister(self._REF_VOLTAGE_MSB, _TPS55289_REF_VOLTAGE_MSB_ADDR)

        print("Voltage Set: {:2f} V\n".format(self._outputVoltage))
        # Enabling Output Voltage Channel
        #self.enable()
    
    ###################################################################################
    ###################################################################################
    # IOUT_LIMIT Register Methods
    
    def enableOutputCurrentLimit(self):
        self._currentLimitEN = 0b1
        self._IOUT_LIMIT |= (1 << 7)
        self.setRegister(self._IOUT_LIMIT, _TPS55289_IOUT_LIMIT_ADDR)
        print("Enabled Current Limit")

    def disableOutputCurrentLimit(self):
        self._currentLimitEN = 0b0
        self._IOUT_LIMIT &= ~(1 << 7)
        self.setRegister(self._IOUT_LIMIT, _TPS55289_IOUT_LIMIT_ADDR)
        print("Disabled Current Limit")

    def setOutputCurrentLimit(self, currentLimit):
        # Check if requested current limit is valid
        if (currentLimit%(0.05) != 0) | (currentLimit >= 0.0) | (currentLimit <= 6.35):
            print("Invalid Current Limit Setting\n")
            print("Valid Current Limits 0.0-6.35A\n")
            pass
        # Calculate what bits to set for required Current Limit
        sense_resistor = 0.01 # 10 milliohms
        self._outputCurrentLimit = currentLimit
        Vdiff = self._outputCurrentLimit*sense_resistor
        self._currentLimitSet = Vdiff/0.5


        # Set Register _TPS55289_IOUT_LIMIT with relevant bits
        pass
    ###################################################################################
    ###################################################################################
    # VOUT_SR Register Methods

    def setOCPResponseTime(self, OCPResponseTime):
        if OCPResponseTime == 0b00:
            self._OCP_DELAY = OCPResponseTime
            self._VOUT_SR &= ~(0b11 << 4)
            self._VOUT_SR |= (self._OCP_DELAY <<4)
            print("OCP Response Time set to: 128uS\n")
        elif OCPResponseTime == 0b01:
            self._OCP_DELAY = OCPResponseTime
            self._VOUT_SR &= ~(0b11 << 4)
            self._VOUT_SR |= (self._OCP_DELAY <<4)
            print("OCP Response Time set to: 1024*3 mS\n")
        elif OCPResponseTime == 0b10:
            self._OCP_DELAY = OCPResponseTime
            self._VOUT_SR &= ~(0b11 << 4)
            self._VOUT_SR |= (self._OCP_DELAY <<4)
            print("OCP Response Time set to: 1024*6 mS\n")
        elif OCPResponseTime == 0b11:
            self._OCP_DELAY = OCPResponseTime
            self._VOUT_SR &= ~(0b11 << 4)
            self._VOUT_SR |= (self._OCP_DELAY <<4)
            print("OCP Response Time set to: 1024*12 mS\n")
        else:
            print("Invalid Response Time Selected\n")
            print("Valid Times are 0b00-0b11\n")
            pass
        self.setRegister(self._VOUT_SR, _TPS55289_VOUT_SR_ADDR)



    def setSlewRate(self, slewRate):
        if slewRate == 0b00:
            self._SR = slewRate
            self._VOUT_SR &= ~(0b11 << 4)
            self._VOUT_SR |= (self._OCP_DELAY <<4)
            print("Slew Rate set to 1.25mV/uS\n")
        elif slewRate == 0b01:
            self._SR = slewRate
            self._VOUT_SR &= ~(0b11 << 4)
            self._VOUT_SR |= (self._OCP_DELAY <<4)
            print("Slew Rate set to 2.5mV/uS\n")
        elif slewRate == 0b10:
            self._SR = slewRate
            self._VOUT_SR &= ~(0b11 << 4)
            self._VOUT_SR |= (self._OCP_DELAY <<4)
            print("Slew Rate set to 5mV/uS\n")
        elif slewRate == 0b11:
            self._SR = slewRate
            self._VOUT_SR &= ~(0b11 << 4)
            self._VOUT_SR |= (self._OCP_DELAY <<4)
            print("Slew Rate set to 10mV/uS\n")
        else:
            print("Invalid Slew Rate Requested\n")
            print("Valid Rates are 0b00-0b11\n")
            pass
        self.setRegister(self._VOUT_SR, _TPS55289_VOUT_SR_ADDR)

    ###################################################################################
    # VOUT_FS Register Methods
    # Method to change feedback mechanism for DC-DC Converter
    def setFeedbackMechanism(self, Mechanism):
        if Mechanism == "external":
            self._FB_MODE = 1           # 1 uses external resistors for ratio
            print("Feedback Mechanism changed to External Mode\n")
        elif Mechanism == "internal":
            self._FB_MODE = 0           # 0 uses internal ratio
            print("Feedback Mechanism changed to Internal Mode\n")
        else:
            print("Invalid Feedback Mechanism Specified\n")
        self._VOUT_FS |= (self._FB_MODE << 7)   # FB is 7th bit of VOUT_FS register
        self.setRegister(self._VOUT_FS, _TPS55289_VOUT_FS_ADDR)
        
    # Method to change internal step size. Affects the Vout and Vref Calculation
    def setStepSize(self, stepSize):
        if stepSize == 2.5:
            self._INTFB     = 0b00
            self._INTFB_Val = _INTFB_00
            print("Internal Step Size Changed to 2.5mV\n")
        elif stepSize == 5.0:
            self._INTFB = 0b01
            self._INTFB_Val = _INTFB_01
            print("Internal Step Size Changed to 5mV\n")
        elif stepSize == 7.5:
            self._INTFB = 0b10
            self._INTFB_Val = _INTFB_10
            print("Internal Step Size Changed to 7.5mV\n")
        elif stepSize == 10.0:
            self._INTFB = 0b11
            self._INTFB_Val = _INTFB_11
            print("Internal Step Size Changed to 10mV\n")
        else:
            print("Invalid Step Size specified\n")
        self._VOUT_FS |= self._INTFB
        self.setRegister(self._VOUT_FS, _TPS55289_VOUT_FS_ADDR)
    ###################################################################################           
    ###################################################################################           
    # CDC Register Methods
    def enableSCIndication(self):
        self._SC_Mask   = 0b1
        self._CDC       |= (1 << 7)
        self.setRegister(self._CDC, _TPS55289_CDC_ADDR)
        print("Enabled Short Circuit Indication\n")

    def disableSCIndication(self):
        self._SC_Mask   = 0b0
        self._CDC       &= ~(1 << 7)
        self.setRegister(self._CDC, _TPS55289_CDC_ADDR)
        print("Disabled Short Circuit Indication\n")

    def enableOCPIndication(self):
        self._OCP_MASK    = 0b1
        self._CDC        |= (1 << 6)
        self.setRegister(self._CDC, _TPS55289_CDC_ADDR)
        print("Enabled Overcurrent Indication\n")

    def disableOCPIndication(self):
        self._OCP_Mask   = 0b0
        self._CDC       &= ~(1 << 6)
        self.setRegister(self._CDC, _TPS55289_CDC_ADDR)
        print("Disabled Overcurrent Indication\n")

    def enableOVPIndication(self):
        self._OVP_MASK    = 0b1
        self._CDC        |= (1 << 5)
        self.setRegister(self._CDC, _TPS55289_CDC_ADDR)
        print("Enabled Overvoltage Indication\n")

    def disableOVPIndication(self):
        self._OVP_Mask   = 0b0
        self._CDC       &= ~(1 << 5)
        self.setRegister(self._CDC, _TPS55289_CDC_ADDR)
        print("Disabled Overvoltage Indication\n")
    
    def setCDCOption(self, cdcOption):
        if cdcOption == 0: # internal CDC compensation
            self._CDC_OPTION = 0b0
            self._CDC        &= ~(1 << 3)
            print("Internal CDC Compensation Mode Selected\n")
        elif cdcOption == 1: # external CDC Compensation Mode
            self._CDC_OPTION = 0b1
            self._CDC        |= (1 << 3)
            print("External CDC Compensation Mode Selected\n")
        else:
            print("Invalid CDC Compensation Mode Requested")
        self.setRegister(self._CDC, _TPS55289_CDC_ADDR)

    def setCDCCompensation(self, Compensation=0.0):
        if Compensation == 0.0:
            self._CDC_SETTING = 0b000
            self._CDC &= ~(0b111)
            self._CDC |= self._CDC_SETTING
        elif Compensation == 0.1:
            self._CDC_SETTING = 0b001
            self._CDC &= ~(0b111)
            self._CDC |= self._CDC_SETTING
        elif Compensation == 0.2:
            self._CDC_SETTING = 0b010
            self._CDC &= ~(0b111)
            self._CDC |= self._CDC_SETTING
        elif Compensation == 0.3:
            self._CDC_SETTING = 0b011
            self._CDC &= ~(0b111)
            self._CDC |= self._CDC_SETTING
        elif Compensation == 0.4:
            self._CDC_SETTING = 0b100
            self._CDC &= ~(0b111)
            self._CDC |= self._CDC_SETTING
        elif Compensation == 0.5:
            self._CDC_SETTING = 0b101
            self._CDC &= ~(0b111)
            self._CDC |= self._CDC_SETTING
        elif Compensation == 0.6:
            self._CDC_SETTING = 0b110
            self._CDC &= ~(0b111)
            self._CDC |= self._CDC_SETTING
        elif Compensation == 0.7:
            self._CDC_SETTING = 0b111
            self._CDC &= ~(0b111)
            self._CDC |= self._CDC_SETTING
        else:
            print("Invalid Compensation requested\n")
            print("Valid Compensation voltages are 0.0-0.7")
            pass
        self.setRegister(self._CDC, _TPS55289_CDC_ADDR)
        print("CDC Compensation set to {} V\n".format(Compensation))


    ###################################################################################           
    ###################################################################################           
    # Mode Register Methods
    def enable(self):
        self._enablePin.on()
        self._OE    = 1
        self._MODE  |= (1 << 7) # 7th Bit of MODE Register is Qutput Enable
        self.setRegister(self._MODE,_TPS55289_MODE_ADDR)
        print("Channel-{} turned ON\n".format(self._channelNum))
        print("Voltage Set: {:2f} V\n".format(self._outputVoltage))
        print("Current Limit:{:2f}\n".format(self._outputCurrentLimit))


    def disable(self):
        self._enablePin.off()
        self._OE    = 0
        self._MODE &= ~(1 << 7)
        self.setRegister(self._MODE,_TPS55289_MODE_ADDR)
        print("Channel-{} turned OFF\n".format(self._channelNum))

    def FSWDoubling(self, input=0): 
        # input = 0 implies unchanged FSW during Buck-Boost
        # input = 1 implies doubled FSW during Buck-Boost
        if input == 0:
            self._FSWDBL = 0b0
            self._MODE &= ~(1 << 6)
            print("Frequency Unchanged\n")
        elif input == 1:
            self._FSWDBL = 0b1
            self._MODE |= (1 << 6)
            print("Frequency Doubled during Buck-Boost Operation\n")
        else:
            print("Invalid Frequency doubling mode selected\n")
        self.setRegister(self._MODE,_TPS55289_MODE_ADDR)

    def enableHiccupMode(self):
        self._HICCUP = 0b1
        self._MODE |= (1 << 5)
        self.setRegister(self._MODE,_TPS55289_MODE_ADDR)
        print("Enabled Hiccup Mode\n")

    def disableHiccupMode(self):
        self._HICCUP = 0b0
        self._MODE &= ~(1 << 5)
        self.setRegister(self._MODE,_TPS55289_MODE_ADDR)
        print("Disabled Hiccup Mode\n")

    def enableVOUTDischarge(self):
        self._DISCHG = 0b1
        self._MODE |= (1 << 4)
        self.setRegister(self._MODE,_TPS55289_MODE_ADDR)
        print("Enabled VOUT Discharge\n")

    def disableVOUTDischarge(self):
        self._DISCHG = 0b0
        self._MODE |= (1 << 4)
        self.setRegister(self._MODE,_TPS55289_MODE_ADDR)
        print("Disabled VOUT Discharge\n")

    def FSWOperatingMode(self, input=0):
        # 0 implies PFM operating mode at light load
        # 1 implies FPWM operating mode at light load
        if input == 0:
            self._FPWM  = 0
            self._MODE &= ~(1 << 1)
            print("PFM Operating Mode Selected at Light Load Condition\n")
        elif input == 1:
            self._FPWM  = 1
            self._MODE |= (1 << 1)
            print("FPWM Operating Mode Selected at Light Load Condition\n")
        else:
            print("Invalid Operating Mode Selected")
        self.setRegister(self._MODE, _TPS55289_MODE_ADDR)

    ###################################################################################           
    ###################################################################################           
    # Status Register Methods
    def readStatusRegister(self, debugOrMonitor="monitor"):
        self._STATUS = self.getRegister(_TPS55289_STATUS_ADDR)
        if (self._STATUS >> 4) & 0x07 != 0:
            self.disable()
            if bin(self._STATUS)[3] == 1:
                print("Short Circuit Detected on Output\n")
            elif bin(self._STATUS)[4] == 1:
                print("Overcurrent Event Detected\n")
            elif bin(self._STATUS)[5] == 1:
                print("Overvoltage Event Detected\n")
            else:
                pass
            print("Enable channel manually after resolving hardware issues\n")
        
        if debugOrMonitor == "debug":
            print("Short Circuit Status:{}\n".format(bin(self._STATUS)[3]))
            print("Overcurrent Status:{}\n".format(bin(self._STATUS)[4]))
            print("Overvoltage Status:{}\n".format(bin(self._STATUS)[5]))
            if (self._STATUS & 0x03) == 0:
                print("Operating Mode = Boost\n")
            elif (self._STATUS & 0x03) == 1:
                print("Operating Mode = Buck\n")
            elif (self._STATUS & 0x03) == 2:
                print("Operating Mode = Buck-Boost\n")
            else:
                print("DC-DC Converter is in invalid state\n")



                
        



    





        

