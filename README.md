# Micropython-TPS55289
Micropython driver for **TPS55289 I2C Controlled Buck-Boost Converter** from Texas Instruments.  
This driver includes methods to control various settings such as output voltage, current limit, slew rate etc.
Product Page: https://www.ti.com/product/TPS55289  
  
# TPS55289 Parameters

| Parameter               | Description                                     | Rating                   |
|-------------------------|-------------------------------------------------|--------------------------|
| **Input Voltage Range** | Voltage range that can be applied to VIN pin.   | 3V to 30V              |
| **Output Voltage Range**| Voltage range that can be obtained at VOUT pin. | 0.8V to 22V              |
| **Output Current Limit**| Maximum allowable output current.               | Up to 6.35A              |
| **Slew Rate**           | Rate at which the output voltage changes.       | Up to 10mV/μs            |
| **Feedback Mechanism**   | Method used for feedback (internal/external).   | Internal (0) or External (1) |
| **Operating Modes**     | Modes of operation (Boost, Buck, Buck-Boost).   | Boost (00), Buck (01), Buck-Boost (10) |
| **Hiccup Mode**         | Response to fault conditions (Enabled/Disabled).| Enabled (1), Disabled (0) |


*Note: Ratings and options may vary based on the specific variant of the TPS55289 and the operating conditions.*

## Development Progress
- [x] Intial Code Development
- [x] Hardware Design
- [ ] Board Fabrication
- [ ] Testing
- [ ] Release 1.0

Please note that this project currently is just to keep track of development. The code hasn't been tested as of this
point. I will keep this repository updated with regards to bugs. Let me know if anyone has had a chance to test this out using the Evaluation Kit(TPS55289EVM) and Raspberry Pico!

## Usage

1. Import the necessary modules:

    ```python
    from machine import Pin
    from machine import I2C
    import TPS55289
    ```

2. Create an instance of the TPS55289 class:

    ```python
    I2C_BUS = I2C(0, scl=Pin(5), sda=Pin(4), freq=100_000)
    Converter = TPS55289(i2c=I2C_BUS, enablePin=0, outputVoltage=5, currentLimit=0.35, feedbackMode=0b0)
    ```

3. Use the methods to control the TPS55289:

    ```python
    Converter.setOutputVoltage(5.0)
    Converter.enableOutputCurrentLimit()
    Converter.setOutputCurrentLimit(6.0)
    ```
  
## Class: TPS55289

### Methods

#### ` setOutputVoltage(voltage: float) -> None `

Sets the output voltage of the DC-DC Converter. Valid input range: 0.8V to 22V.

#### `enableOutputCurrentLimit() -> None`

Enables the output current limit of the DC-DC Converter.

#### `disableOutputCurrentLimit() -> None`

Disables the output current limit of the DC-DC Converter.

#### `setOutputCurrentLimit(currentLimit: float) -> None`

Sets the output current limit of the DC-DC Converter. Valid input range: 0.0A to 6.35A.

#### `setOCPResponseTime(OCPResponseTime: int) -> None`

Sets the overcurrent protection (OCP) response time.

#### `setSlewRate(slewRate: int) -> None`

Sets the slew rate of the DC-DC Converter.

#### `setFeedbackMechanism(Mechanism: str) -> None`

Sets the feedback mechanism of the DC-DC Converter.

#### `setStepSize(stepSize: float) -> None`

Sets the internal step size for feedback.

#### `enableSCIndication() -> None`

Enables short-circuit indication.

#### `disableSCIndication() -> None`

Disables short-circuit indication.

#### `enableOCPIndication() -> None`

Enables overcurrent indication.

#### `disableOCPIndication() -> None`

Disables overcurrent indication.

#### `enableOVPIndication() -> None`

Enables overvoltage indication.

#### `disableOVPIndication() -> None`

Disables overvoltage indication.

#### `setCDCOption(cdcOption: int) -> None`

Sets the CDC compensation mode.

#### `setCDCCompensation(Compensation: float) -> None`

Sets the CDC compensation value.

#### `enable() -> None`

Enables the TPS55289 DC-DC Converter.

#### `disable() -> None`

Disables the TPS55289 DC-DC Converter.

#### `readStatusRegister(debugOrMonitor: str) -> None`
