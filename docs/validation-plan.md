# Hardware and software validation plan

No test in this plan has been run. There is no hardware yet. The design is not complete until every
test marked **gate** passes on at least five assembled units.

Equipment: bench supply 60 V 3 A, electronic load, 802.3bt PSE with Type 3 and Type 4 ports, 802.3at
PSE, USB-PD analyser, 45 W and 65 W PD chargers, 5 V-only charger, oscilloscope 1 GHz with differential
probe, spectrum analyser or 802.15.4 sniffer, thermal camera, thermocouples, thermal chamber,
audio analyser or calibrated microphone, Ethernet traffic generator.

## 1. Bare board and first power (before fitting the CM5)

| ID | Test | Pass criterion | Gate |
|---|---|---|---|
| BRD-01 | Bare-board electrical test at the fabricator | 100 % nets pass | yes |
| BRD-02 | Impedance coupons | 90, 100, 50 ohm within 10 % | yes |
| BRD-03 | Isolation: 1500 V impulse and 500 V DC insulation, PoE primary to GND | no breakdown, over 100 Mohm | yes |
| BRD-04 | Rail resistance to ground, unpowered | no shorts on any rail | yes |
| PWR-01 | 12 V on V12_POE pad, current-limited. Check VIN, +5V, +5V_USB | 5.0 V within 3 %, UVLO at 8.0 V within 0.5 V | yes |
| PWR-02 | Program U1 over I2C, read back | matches `nvm-config.md` | yes |

## 2. Power

| ID | Test | Pass criterion | Gate |
|---|---|---|---|
| PWR-03 | Sequencing capture: VIN, +5V, CM5_3V3, +3V3, +3V3_NVME | order as designed, monotonic +5V, no pin driven before +5V | yes |
| PWR-04 | Each regulator at 0, 50, 100 % load: ripple, load step, efficiency | ripple under 50 mV, step within 5 %, efficiency over 88 % | yes |
| PWR-05 | USB-C with 45 W and 65 W chargers, both cable orientations | 20 V or 15 V contract, unit boots | yes |
| PWR-06 | USB-C with a 5 V-only charger | Q1 stays off, no rail activity | yes |
| PWR-07 | PoE from Type 3, Type 4 and 802.3at sources, plus a midspan injector on each pairset | detection, classification, stable 12 V. Type 4 flag correct | yes |
| PWR-08 | Source switching: add and remove USB-C while on PoE, and the reverse, under load | no reset, no reverse current over 1 mA into either source | yes |
| PWR-09 | Maximum load for 2 h: CPU stress, SSD write loop, both USB ports at 0.9 A, audio, all radios transmitting | no brown-out, input power recorded for both sources | yes |
| PWR-10 | USB port short circuit and overload | port limits near 1.2 A, +5V unaffected | yes |
| PWR-11 | Inrush on USB-C attach and PoE power-up | within USB-PD and 802.3bt limits | yes |

## 3. Interfaces

| ID | Test | Pass criterion | Gate |
|---|---|---|---|
| IF-01 | Ethernet link at 1000, 100, 10 Mb/s, with 100 m cable | link up, iperf3 over 900 Mb/s at 1000 | yes |
| IF-02 | Ethernet 24 h traffic while PoE powered at full load | zero CRC errors | yes |
| IF-03 | NVMe: enumerate, fio read/write, 24 h soak, 2242 and 2280 drives from three vendors | Gen 2 link, no errors | yes |
| IF-04 | USB 3.0 both ports: SuperSpeed enumeration, throughput, eye or compliance pattern | 5 Gb/s link, no downgrades | yes |
| IF-05 | USB 2.0 device mode through J1 with `usbboot` | module enumerates | yes |
| IF-06 | Buttons, LEDs, mute switch, fan PWM and tachometer, RTC holdover, console | all function | yes |
| IF-07 | Boot order: NVMe present, NVMe removed with USB drive, both absent | boots NVMe, then USB, then retries | yes |

## 4. Wireless

| ID | Test | Pass criterion | Gate |
|---|---|---|---|
| RF-01 | Wi-Fi 2.4 and 5 GHz association, throughput at 1 m and 10 m, PCB and external antenna | within 20 % of a CM5 IO board reference | yes |
| RF-02 | BLE scan and connect | matches reference | yes |
| RF-03 | Zigbee: conducted power and frequency at J9, then form a network with 20 devices | within module datasheet, stable 24 h | yes |
| RF-04 | Thread: radiated power, border router with Matter devices | stable 24 h | yes |
| RF-05 | Z-Wave module on J11: inclusion and range | matches module on a Raspberry Pi | no |
| RF-06 | Antenna match and efficiency in the enclosure, pi network tuned | return loss better than 10 dB | yes |
| RF-07 | **Simultaneous operation**: Wi-Fi 2.4 GHz traffic at full rate, BLE scanning, Zigbee and Thread traffic, Z-Wave, USB 3.0 and NVMe active | Zigbee and Thread packet error under 1 % with Wi-Fi on 5 GHz, and recorded for 2.4 GHz | yes |
| RF-08 | Receiver desense scan with USB 3.0 and NVMe active | under 3 dB | yes |

## 5. Audio

| ID | Test | Pass criterion | Gate |
|---|---|---|---|
| AU-01 | Codec enumerates, clocks correct, playback and capture at 16 and 48 kHz | no xruns in 1 h | yes |
| AU-02 | Speaker output power and distortion into 4 ohm | 2 W at under 1 % THD+N | yes |
| AU-03 | Microphone sensitivity, noise floor, frequency response in the enclosure | within 3 dB of the microphone datasheet, 100 Hz to 8 kHz | yes |
| AU-04 | Echo cancellation: wake word during playback at 70 dBA | over 90 % detection at 3 m | yes |
| AU-05 | Mute switch | capture is silent, state reported, software cannot re-enable | yes |
| AU-06 | Class-D interference into Zigbee, Thread and the microphone | no measurable change | yes |

## 6. Thermal and environmental

| ID | Test | Pass criterion | Gate |
|---|---|---|---|
| TH-01 | Idle, enclosure closed, 25 °C, both sources | all parts under ratings, case under 45 °C | yes |
| TH-02 | Typical load, 40 °C ambient, no fan | no CPU throttling, SSD under 70 °C, Ag5810 within derating | yes |
| TH-03 | Maximum load with the fan, 40 °C ambient | no throttling for 2 h | yes |
| TH-04 | Maximum load without the fan | record time to throttle. Defines the passive limit | no |
| TH-05 | Cold start at 0 °C, power cycling 500 times | boots every time | yes |

## 7. Software

| ID | Test | Pass criterion | Gate |
|---|---|---|---|
| SW-01 | Image builds reproducibly from `build.sh` | two builds give identical file lists | yes |
| SW-02 | All devices in the hardware support table enumerate after a clean install | yes | yes |
| SW-03 | OS update and forced rollback | returns to the previous slot | yes |
| SW-04 | Each recovery procedure in `recovery-and-update.md` | completes as written | yes |
| SW-05 | Radio firmware update over UART, with interruption | recovers through the bootloader | yes |
| SW-06 | Reduced-power mode on an 802.3at source | USB port power stays off, no brown-out | yes |

## 8. Compliance pre-scan

| ID | Test | Gate |
|---|---|---|
| EMC-01 | Radiated and conducted emissions pre-scan, EN 55032 Class B, both power sources | yes |
| EMC-02 | ESD at all connectors and buttons, 4 kV contact, 8 kV air | yes |
| EMC-03 | Surge and fast transients on the Ethernet port | yes |
| REG-01 | Confirm module certifications still apply with the chosen antennas, plan final radio testing | yes |

Record results in `docs/validation-results/` with unit serial numbers, firmware versions and raw data.
