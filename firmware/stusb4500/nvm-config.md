# STUSB4500 (U1) non-volatile configuration

The controller negotiates USB Power Delivery on its own, using a profile stored in its NVM. The factory
default profile would request 20 V at 1 A, which is not what this board needs, so every board must be
programmed once at factory test. The board is powered from the bench 12 V test point (V12_POE) or from PoE
while this is done, so the USB-C port is not needed to program it.

| Parameter | Value | Reason |
|---|---|---|
| SNK_PDO_NUMB | 3 | use all three profiles |
| PDO1 | 5 V, 1.5 A | mandatory, never used to power the system |
| PDO2 | 15 V, 3.0 A | 45 W, preferred on 15 V-only chargers |
| PDO3 | 20 V, 2.25 A | 45 W, highest priority |
| Voltage tolerance | +/-5 % under, +10 % over on PDO2 and PDO3 | default monitoring window |
| I_SNK_PDO_FLEX | not used | |
| POWER_ONLY_ABOVE_5V | 1 | Q1 stays off on a 5 V-only source, so the port cannot brown out the rails |
| USB_COMM_CAPABLE | 1 | USB 2.0 data is wired to the CM5 |
| VBUS_DISCH_DISABLE | 0 | |
| REQ_SRC_CURRENT | 0 | request the sink PDO current |
| POWER_OK_CFG | configuration 2 | POWER_OK2/3 are not connected |
| GPIO_CFG | ERROR_RECOVERY | pin not connected |

Tools: ST's STSW-STUSB002 GUI with a NUCLEO board, or any STUSB4500 NVM library, on I2C address 0x28
(`/dev/i2c-1` on the hub). Verify after programming by reading the NVM back and by attaching a 45 W
charger: VBUS_SW must sit at 20 V, or 15 V on a charger without a 20 V profile.

Status: parameters defined, programming script not written, not yet exercised on hardware.
