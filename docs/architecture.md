# System architecture

Tahanan Hub rev A is a carrier board for the Raspberry Pi Compute Module 5 in a 167 x 112 x 31 mm
enclosure. The single source of truth for the circuit is `hardware/gen/design.py`.

## Block diagram

```mermaid
flowchart LR
  subgraph PWR[Power]
    USBC[J1 USB-C] --> PD[U1 STUSB4500 PD sink] --> Q1[Q1 VBUS switch] --> OR1[U3+Q2 ideal diode]
    RJ[J2 RJ45 with magnetics] -->|centre taps| BR[2x Schottky bridge] --> POE[U17 Ag5810 802.3bt PD, isolated 12 V] --> OR2[U4+Q3 ideal diode]
    OR1 --> VIN((VIN 12-20 V)); OR2 --> VIN
    VIN --> B5[U5 buck +5V 4 A]; VIN --> B5U[U6 buck +5V_USB 4 A]; VIN --> B3N[U7 buck +3V3_NVME 3 A]
    B5 --> B33[U8 buck +3V3 2 A] --> L18[U9 LDO +1V8]
  end
  subgraph CPU[Compute]
    CM5[Raspberry Pi CM5: BCM2712, RAM, GbE PHY, Wi-Fi 5 + BLE]
  end
  B5 --> CM5
  RJ <-->|4 pairs MDI, 100 ohm| CM5
  CM5 <-->|PCIe x1 Gen 2| M2[J4 M.2 Key M NVMe]; B3N --> M2
  CM5 <-->|2x USB 3.0| USBA[J5 dual USB-A]; B5U --> SW[U10 TPS2561] --> USBA
  CM5 <-->|USB 2.0| USBC
  CM5 <-->|UART2 + RTS/CTS, reset, boot| ZB[U19 MGM240P Zigbee] --> UFL[J9 U.FL, external antenna]
  CM5 <-->|UART3 + RTS/CTS, reset, boot| TH[U20 MGM240P Thread, built-in antenna]
  CM5 <-->|UART0| ZW[J11 Z-Wave module socket]
  CM5 <-->|I2S, I2C1| CODEC[U21 TLV320AIC3100 codec + class-D]
  MIC[MK1 MEMS mic] --> CODEC --> SPK[J12 speaker 4 ohm]
  CM5 --- UI[Buttons, LEDs, fan J6, RTC cell, console J7]
  POE -. Type 4 detect via optocoupler U18 .-> CM5
```

## Interfaces

| Function | Implementation | Connector |
|---|---|---|
| Ethernet | 1000BASE-T, PHY on CM5, Würth 7499511001A jack with magnetics | J2 |
| PoE | 802.3bt powered device, Silvertel Ag5810, 1500 V isolation | J2 |
| USB-C power | USB PD sink, 15 V or 20 V contract, 45 W charger minimum | J1 |
| Wi-Fi and Bluetooth | 2.4 and 5 GHz 802.11ac, BLE 5.0, on CM5. PCB antenna or U.FL | on module |
| Zigbee | MGM240P (EFR32MG24), +20 dBm, external antenna | J9 to RP-SMA |
| Thread and Matter | MGM240P as OpenThread radio co-processor. Matter runs over Thread, Wi-Fi and Ethernet | built-in antenna |
| Z-Wave | Socket for a Raspberry Pi header Z-Wave 800 module | J11 |
| Storage | M.2 Key M, 2242 and 2280, NVMe | J4, bottom side |
| USB host | 2x USB 3.0 Type-A, about 1.2 A limit each | J5 |
| Audio | TLV320AIC3100 codec, one analog MEMS microphone, 2.5 W class-D into 4 ohm | MK1, J12 |
| Service | 3.3 V serial console, RPIBOOT button, SWD pads for both radios | J7, SW2, J8, J10 |

## Design decisions worth knowing

- **Two 802.15.4 radios.** Zigbee and Thread each get a dedicated radio and UART. Sharing one radio
  between the two stacks halves airtime for each and is the less reliable configuration.
- **Z-Wave as a plug-in module.** Z-Wave frequency and certification are regional. A socket keeps one
  board for all regions and uses modules that are already certified.
- **Input selection by voltage.** Both sources feed VIN through ideal-diode controllers. USB-C (15 or
  20 V) is always above PoE (12 V), so it takes the load when present. Neither can feed the other.
- **PD contract gates the USB-C input.** Q1 only closes after a contract above 5 V, so a 5 V-only
  charger cannot half-power the rails.
- **Codec is the audio clock master.** Capture and playback share one clock, which keeps the echo
  canceller's reference aligned with the microphone signal.
- **Hardware microphone mute.** SW4 removes microphone power. Software can read the state but cannot
  override it.

## GPIO map

| GPIO | Use | GPIO | Use |
|---|---|---|---|
| 2, 3 | I2C1: codec 0x18, PD controller 0x28 | 16 | Codec reset, active low |
| 4-7 | UART2 Zigbee: TX, RX, CTS, RTS | 17 | User button, active low |
| 8-11 | UART3 Thread: TX, RX, CTS, RTS | 18-21 | I2S: BCLK, WS, data in, data out |
| 12, 13 | UART4 console: TX, RX | 22, 23 | Zigbee reset, bootloader entry |
| 14, 15 | UART0 Z-Wave: TX, RX | 24, 25 | Thread reset, bootloader entry |
| 26 | User LED | 27 | Microphone-enabled sense |
| 34 (CAM_GPIO0) | PoE Type 4 detect, active low | | |

## Radio coexistence

Three 2.4 GHz transmitters share one enclosure: Wi-Fi and BLE on the CM5, Zigbee, and Thread.

- Placement: the Thread antenna is at the front-left corner, the CM5 antenna at the right edge about
  125 mm away, and the Zigbee antenna is external.
- No packet-traffic-arbitration wiring exists between the radios, because the CM5 does not expose
  coexistence signals. Coexistence relies on separation and channel planning.
- Recommended deployment: Ethernet for the uplink, Wi-Fi on 5 GHz, Zigbee on channel 15, 20 or 25,
  Thread on a channel at least 15 MHz away from Zigbee.
- Heavy 2.4 GHz Wi-Fi traffic from the hub itself will raise 802.15.4 packet loss. This must be
  quantified in validation test RF-07.
