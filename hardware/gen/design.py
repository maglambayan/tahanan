"""Tahanan Hub rev A circuit definition.

One call to part()/R()/C() per fitted component. Net names are global.
Design calculations and the reason for each value are in docs/hardware/design-notes.md.
"""
from netlist import *

G = 'GND'
COUNT.update({'J': 5, 'U': 1, 'D': 1, 'Q': 1})   # J1-J5, U1, D1, Q1 are assigned by hand below
C100N = dict(mpn='CL05B104KO5NNNC', mfr='Samsung')
def c100n(a, b=G): return C('100nF', a, b, '0402', '16V', **C100N)
def c1u(a, b=G): return C('1uF', a, b, '0402', '16V', mpn='CL05A105KO5NNNC', mfr='Samsung', diel='X5R')
def c10u(a, b=G): return C('10uF', a, b, '0603', '10V', mpn='CL10A106KP8NNNC', mfr='Samsung', diel='X5R')
def c22u(a, b=G): return C('22uF', a, b, '0805', '10V', mpn='CL21A226MPQNNNE', mfr='Samsung', diel='X5R')
def c10u50(a, b=G): return C('10uF', a, b, '1210', '50V', mpn='CL32B106KBJNNNE', mfr='Samsung')
def led(colour, a, k):
    mpn = {'green': '150060GS75000', 'red': '150060RS75000', 'yellow': '150060YS75000', 'blue': '150060BS75000'}[colour]
    return part('D', 'Device:LED', {'A': a, 'K': k}, f'LED {colour}', 'LED_SMD:LED_0603_1608Metric', mpn, 'Wurth', f'LED {colour} 0603')
def tp(net, name):
    return part('TP', 'Connector:TestPoint', {1: net}, name, 'TestPoint:TestPoint_Pad_D1.5mm', '', '', f'Test pad {name}')
def bead(a, b, mpn='BLM18PG221SN1D', fp='Inductor_SMD:L_0603_1608Metric', val='220R@100MHz 1.4A', mfr='Murata'):
    return part('FB', 'Device:FerriteBead', {1: a, 2: b}, val, fp, mpn, mfr, 'Ferrite bead')
def button(net, name):
    return part('SW', 'Switch:SW_Push', {1: net, 2: G}, name, 'Button_Switch_SMD:SW_Tactile_SPST_NO_Straight_CK_PTS636Sx25SMTRLFS',
                'PTS636SM25FSMTRLFS', 'C&K', f'Tactile switch, top actuated: {name}')

# =====================================================================================
sheet('power_in', 'Power input: USB-C PD sink, input OR-ing',
      'USB-C PD sink: STUSB4500 autonomous controller. NVM must be programmed at factory test (PDO2 15V/3A, PDO3 20V/2.25A,\n'
      'POWER_ONLY_ABOVE_5V=1), see firmware/stusb4500. Q1 passes VBUS only after an explicit contract above 5V.\n'
      'OR-ing: two LM74700 ideal-diode controllers. The higher of VBUS_SW (15-20V) and V12_POE (12V) feeds VIN, so USB-C\n'
      'takes priority automatically and neither source can back-feed the other. System UVLO is 8V (EN divider on U5).')
part('J', 'Connector:USB_C_Receptacle_USB2.0_16P',
     {'VBUS': 'VBUS', 'GND': G, 'CC1': 'USBC_CC1', 'CC2': 'USBC_CC2', 'D+': 'USB2_DP', 'D-': 'USB2_DM', 'SBU1': 'NC', 'SBU2': 'NC', 'SHIELD': 'CHASSIS'},
     'USB-C PD', 'Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal', 'USB4105-GF-A', 'GCT',
     'USB Type-C receptacle, USB 2.0, 16 pin, top mount', alt='HRO TYPE-C-31-M-12 (different footprint)', ref='J1')
part('U', 'STUSB4500QTR',
     {'CC1': 'USBC_CC1', 'CC1DB': 'USBC_CC1', 'CC2': 'USBC_CC2', 'CC2DB': 'USBC_CC2', 'NC': 'NC', 'RESET': G, 'SCL': 'I2C1_SCL', 'SDA': 'I2C1_SDA',
      'DISCH': 'PD_DISCH', 'GND': G, 'ATTACH': 'NC', 'ADDR0': G, 'ADDR1': G, 'POWER_OK3': 'NC', 'GPIO': 'NC', 'VBUS_EN_SNK': 'PD_VBUS_EN_N',
      'A_B_SIDE': 'NC', 'VBUS_VS_DISCH': 'PD_VS_DISCH', 'ALERT': 'NC', 'POWER_OK2': 'NC', 'VREG_1V2': 'PD_1V2', 'VSYS': G, 'VREG_2V7': 'PD_2V7', 'VDD': 'VBUS'},
     mpn='STUSB4500QTR', mfr='STMicroelectronics', alt='STUSB4500LQTR (5V-only variant is NOT a substitute)', ref='U1')
c1u('PD_1V2'); c1u('PD_2V7'); C('4.7uF', 'VBUS', G, '0805', '50V', mpn='CL21A475KBQNNNE', mfr='Samsung', diel='X5R')
R('470', 'VBUS', 'PD_VS_DISCH'); R('1k', 'VBUS_SW', 'PD_DISCH', '0603')
part('D', 'Diode:SMAJ22A', {1: 'VBUS', 2: G}, 'SMAJ22A', mpn='SMAJ22A', mfr='Littelfuse', desc='TVS 22V unidirectional 400W SMA', ref='D1')
part('Q', 'DMP3013SFV', {'S': 'VBUS', 'G': 'PD_GATE', 'D': 'VBUS_SW'}, mpn='DMP3013SFV-7', mfr='Diodes Inc', desc='P-MOSFET -30V 13mOhm PowerDI3333-8', alt='Si7617DN', ref='Q1')
R('100k', 'VBUS', 'PD_GATE'); R('22k', 'PD_GATE', 'PD_VBUS_EN_N'); c100n('VBUS', 'PD_GATE').value = '100nF 50V'
PARTS[-1].mpn = 'CL10B104KB8NNNC'; PARTS[-1].fp = SIZES['0603']; PARTS[-1].desc = 'MLCC 100nF 50V X7R 0603'
part('D', 'Device:D_Zener', {'K': 'VBUS', 'A': 'PD_GATE'}, 'BZT52C10S 10V', 'Diode_SMD:D_SOD-323', 'BZT52C10S-7-F', 'Diodes Inc', 'Zener 10V 200mW SOD-323, Q1 gate clamp')
part('U', 'Power_Protection:USBLC6-2SC6', {'I/O1': 'USB2_DP', 'I/O2': 'USB2_DM', 'VBUS': 'VBUS', 'GND': G}, mpn='USBLC6-2SC6', mfr='STMicroelectronics')
C('10uF', 'VBUS_SW', G, '1210', '50V', mpn='CL32B106KBJNNNE', mfr='Samsung')
# ideal diode OR
for i, src in ((1, 'VBUS_SW'), (2, 'V12_POE')):
    part('U', 'LM74700', {'VCAP': f'OR{i}_VCAP', 'GND': G, 'EN': src, 'CATHODE': 'VIN', 'GATE': f'OR{i}_GATE', 'ANODE': src},
         'LM74700-Q1', mpn='LM74700QDBVRQ1', mfr='Texas Instruments', alt='LM74701-Q1')
    part('Q', 'CSD17581Q3A', {'S': src, 'G': f'OR{i}_GATE', 'D': 'VIN'}, mpn='CSD17581Q3A', mfr='Texas Instruments', desc='N-MOSFET 30V 3.8mOhm SON3.3x3.3', alt='CSD17577Q3A')
    c100n(f'OR{i}_VCAP', src).value = '100nF 50V'; PARTS[-1].mpn = 'CL10B104KB8NNNC'; PARTS[-1].fp = SIZES['0603']; PARTS[-1].desc = 'MLCC 100nF 50V X7R 0603'
c10u50('VIN'); c10u50('VIN')
part('C', 'Device:C_Polarized', {1: 'VIN', 2: G}, '100uF 35V', 'Capacitor_SMD:CP_Elec_6.3x7.7', 'EEE-FT1V101AP', 'Panasonic', 'Aluminium electrolytic 100uF 35V low-ESR')
tp('VIN', 'VIN'); tp('VBUS', 'VBUS'); tp(G, 'GND'); tp(G, 'GND')

# =====================================================================================
sheet('power_rails', 'Regulators and sequencing',
      'Sequence: VIN>8V -> +5V (U5) -> PG_5V enables +5V_USB (U6). CM5 starts from +5V; CM5_3V3 then enables +3V3 (U8).\n'
      '+3V3_NVME (U7) is enabled by PCIE_PWR_EN from the CM5. Nothing drives a CM5 pin before +5V is valid (CM5 datasheet 3.1).\n'
      'LMR336x0: VFB=1.0V. 5V: 100k/24.9k. 3.3V: 100k/43.2k. fsw=400kHz, L=6.8uH, CIN 2x10uF+220nF (datasheet table 9-1).')
def lmr(sym, tag, out, en, L, lmpn, rb):
    part('U', sym, {'GND': G, 'VIN': 'VIN', 'EN': en, 'PG': f'PG_{tag}', 'FB': f'FB_{tag}', 'VCC': f'VCC_{tag}', 'BOOT': f'BOOT_{tag}', 'SW': f'SW_{tag}'},
         mpn=sym + 'R', mfr='Texas Instruments', alt='LMR33640DDDAR (2.1MHz, needs smaller L)' if '40' in sym else 'LMR33640ADDAR')
    c10u50('VIN'); c10u50('VIN'); C('220nF', 'VIN', G, '0603', '50V', mpn='CL10B224KB8NNNC', mfr='Samsung')   # 220 nF high-frequency input capacitor, LMR33640 datasheet table 9-1
    c100n(f'BOOT_{tag}', f'SW_{tag}'); c1u(f'VCC_{tag}')
    part('L', 'Device:L', {1: f'SW_{tag}', 2: out}, L, 'Inductor_SMD:L_Bourns_SRP1038C_10.0x10.0mm', lmpn, 'Bourns', f'Shielded power inductor {L}')
    R('100k', out, f'FB_{tag}'); R(rb, f'FB_{tag}', G); C('22pF', out, f'FB_{tag}', '0402', '50V', mpn='CL05C220JB5NNNC', mfr='Samsung', diel='C0G')
    for _ in range(4): c22u(out)
    R('100k', out, f'PG_{tag}')
lmr('LMR33640ADDA', '5V', '+5V', 'EN_5V', '6.8uH', 'SRP1038CC-6R8M', '24.9k')
R('100k', 'VIN', 'EN_5V'); R('18k', 'EN_5V', G)
lmr('LMR33640ADDA', '5VUSB', '+5V_USB', 'PG_5V', '6.8uH', 'SRP1038CC-6R8M', '24.9k')
lmr('LMR33630ADDA', '3V3N', '+3V3_NVME', 'PCIE_PWR_EN', '6.8uH', 'SRP1038CC-6R8M', '43.2k')
R('100k', 'PCIE_PWR_EN', G)
part('U', 'AP63203WU', {'FB': '+3V3', 'EN': 'CM5_3V3', 'IN': '+5V', 'GND': G, 'SW': 'SW_3V3', 'BST': 'BST_3V3'}, mpn='AP63203WU-7', mfr='Diodes Inc', alt='AP63205WU-7 is 5V, not a substitute')
c10u('+5V'); c100n('BST_3V3', 'SW_3V3')
part('L', 'Device:L', {1: 'SW_3V3', 2: '+3V3'}, '4.7uH', 'Inductor_SMD:L_Bourns-SRN4018', 'SRN4018-4R7M', 'Bourns', 'Shielded power inductor 4.7uH 2A')
c22u('+3V3'); c22u('+3V3')
part('U', 'AP2112K-1.8', {'VIN': '+3V3', 'GND': G, 'EN': '+3V3', 'VOUT': '+1V8'}, mpn='AP2112K-1.8TRG1', mfr='Diodes Inc')
c1u('+3V3'); c1u('+1V8')
for n in ('+5V', '+5V_USB', '+3V3', '+3V3_NVME', '+1V8', 'V12_POE'): tp(n, n)

# =====================================================================================
sheet('cm5', 'Compute Module 5 and system control',
      'J3 carries module pins 1-100, J13 pins 101-200 (pad n = module pin 100+n). Stacking height 3.0mm.\n'
      'CC1/CC2 are not used: PD is handled by U1, so set PSU_MAX_CURRENT=5000 in the bootloader EEPROM config.\n'
      'GPIO map: 2/3 I2C1, 4-7 UART2 Zigbee, 8-11 UART3 Thread, 12/13 UART4 console, 14/15 UART0 Z-Wave socket,\n'
      '16 codec reset, 17 user button, 18-21 I2S, 22/23 Zigbee RST/BOOT, 24/25 Thread RST/BOOT, 26 user LED, 27 mic-enabled sense.')
A = {'GND': G, '5V': '+5V', 'CM5_3.3V': 'CM5_3V3', 'GPIO_VREF': 'CM5_3V3', 'CM5_1.8V': 'NC', 'VBAT': 'VBAT'}
for i in range(4):
    A[f'Ethernet_Pair{i}_P'] = f'ETH_P{i}_P'; A[f'Ethernet_Pair{i}_N'] = f'ETH_P{i}_N'
A.update({'Ethernet_nLED3': 'ETH_LED3_N', 'Ethernet_nLED2': 'ETH_LED2_N', 'Ethernet_SYNC_OUT': 'NC', 'Fan_Tacho': 'FAN_TACH', 'Fan_PWM': 'FAN_PWM',
          'EEPROM_nWP': 'EEPROM_NWP', 'LED_nACT': 'LED_ACT_N', 'LED_nPWR': 'LED_PWR_N', 'ID_SC': 'NC', 'ID_SD': 'NC', 'SCL0': 'NC', 'SDA0': 'NC',
          'WL_nDisable': 'NC', 'BT_nDisable': 'NC', 'PWR_Button': 'PWR_BTN_N', 'nRPIBOOT': 'RPIBOOT_N', 'CC1': 'NC', 'CC2': 'NC',
          'CAM_GPIO0': 'POE_BT_N', 'CAM_GPIO1': 'NC', 'PMIC_Enable': 'NC', 'SD_VDD_OVERRIDE': 'NC', 'SD_PWR_ON': 'NC',
          'GPIO2': 'I2C1_SDA', 'GPIO3': 'I2C1_SCL', 'GPIO4': 'ZB_H2M_TXD', 'GPIO5': 'ZB_M2H_TXD', 'GPIO6': 'ZB_M2H_RTS', 'GPIO7': 'ZB_H2M_RTS',
          'GPIO8': 'TH_H2M_TXD', 'GPIO9': 'TH_M2H_TXD', 'GPIO10': 'TH_M2H_RTS', 'GPIO11': 'TH_H2M_RTS', 'GPIO12': 'DBG_TXD', 'GPIO13': 'DBG_RXD',
          'GPIO14': 'ZW_H2M_TXD', 'GPIO15': 'ZW_M2H_TXD', 'GPIO16': 'AUD_RST_N', 'GPIO17': 'USER_BTN_N', 'GPIO18': 'I2S_BCLK', 'GPIO19': 'I2S_WS',
          'GPIO20': 'I2S_SDI', 'GPIO21': 'I2S_SDO', 'GPIO22': 'ZB_RST_N', 'GPIO23': 'ZB_BOOT_N', 'GPIO24': 'TH_RST_N', 'GPIO25': 'TH_BOOT_N',
          'GPIO26': 'USER_LED', 'GPIO27': 'MIC_ON'})
for n in ('CLK', 'CMD', 'DAT0', 'DAT1', 'DAT2', 'DAT3', 'DAT4', 'DAT5', 'DAT6', 'DAT7'): A['SD_' + n] = 'NC'
CONN = dict(fp='Connector_Hirose_DF40:Hirose_DF40HC(3.0)-100DS-0.4V_2x50_P0.4mm', mpn='DF40HC(3.0)-100DS-0.4V(51)', mfr='Hirose',
            alt='Amphenol 10164227-1004A1RLF (4.0mm stack; confirm land pattern and change standoffs to 4.0mm)')
part('J', 'CM5_A', A, 'CM5 pins 1-100', desc='100-pin 0.4mm board-to-board receptacle, 3.0mm stack, mates with CM5', ref='J3', **CONN)
B = {'GND': G, 'USB_OTG_ID': 'NC', 'PCIe_CLK_nREQ': 'PCIE_CLKREQ_N', 'USB_N': 'USB2_DM', 'USB_P': 'USB2_DP', 'PCIE_nWAKE': 'PCIE_WAKE_N',
     'PCIE_PWR_EN': 'PCIE_PWR_EN', 'PCIe_nRST': 'PCIE_RST_N', 'PCIe_CLK_P': 'PCIE_CLK_P', 'PCIe_CLK_N': 'PCIE_CLK_N', 'VBUS_EN': 'USB_VBUS_EN',
     'PCIe_RX_P': 'PCIE_RX_P', 'PCIe_RX_N': 'PCIE_RX_N', 'PCIe_TX_P': 'PCIE_TX_P', 'PCIe_TX_N': 'PCIE_TX_N'}
for p in (0, 1):
    for s, d in (('RX_N', 'RX_N'), ('RX_P', 'RX_P'), ('TX_N', 'TX_N'), ('TX_P', 'TX_P'), ('DP', 'DP'), ('DM', 'DM')):
        B[f'USB3-{p}-{s}'] = f'USB3_{p}_{d}'
import json as _j
for k, v in _j.load(open(os.path.join(HERE, 'cm5_pins.json'))).items():
    if int(k) > 100 and v[0] not in B: B[v[0]] = 'NC'      # HDMI, MIPI: not used on this product
part('J', 'CM5_B', B, 'CM5 pins 101-200', desc='100-pin 0.4mm board-to-board receptacle, 3.0mm stack, mates with CM5', ref='J13', **CONN)
for _ in range(4): c22u('+5V')
c100n('+5V'); c100n('CM5_3V3'); c1u('CM5_3V3')
R('4.7k', '+3V3', 'I2C1_SDA'); R('4.7k', '+3V3', 'I2C1_SCL')
button('PWR_BTN_N', 'POWER'); button('RPIBOOT_N', 'RPIBOOT'); button('USER_BTN_N', 'USER')
R('1k', '+3V3', 'LEDP_A'); led('red', 'LEDP_A', 'LED_PWR_N'); R('1k', '+3V3', 'LEDA_A'); led('green', 'LEDA_A', 'LED_ACT_N')
R('1k', 'USER_LED', 'LEDU_A'); led('blue', 'LEDU_A', G)
part('BT', 'Device:Battery_Cell', {'+': 'VBAT', '-': G}, 'CR1220', 'Battery:BatteryHolder_Keystone_3000_1x12mm', '3000', 'Keystone', 'Coin cell holder 12mm, RTC backup')
part('J', 'Conn_01x04_MountingPin', {1: '+5V', 2: 'FAN_PWM', 3: G, 4: 'FAN_TACH', 'MP': G}, 'FAN', 'Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal',
     'SM04B-SRSS-TB', 'JST', '4-pin 1.0mm fan header, Raspberry Pi 5 fan pinout')
part('J', 'Connector_Generic:Conn_01x03', {1: G, 2: 'DBG_TXD', 3: 'DBG_RXD'}, 'CONSOLE 3V3', 'Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical',
     '61300311121', 'Wurth', '3-pin header, serial console (UART4, 3.3V)')
tp('EEPROM_NWP', 'EEPROM_nWP'); tp('CM5_3V3', 'CM5_3V3')
for i in range(4):
    part('H', 'Mechanical:MountingHole_Pad', {1: G}, 'M2.5 standoff 3mm', 'Mounting_Wuerth:Mounting_Wuerth_WA-SMSI-M2.5_H3mm_9774030151', '9774030151R', 'Wurth', 'SMT spacer M2.5 internal thread, 3.0mm, CM5 mounting')
for i in range(4):
    part('H', 'Mechanical:MountingHole_Pad', {1: G}, 'M3 mounting hole', 'MountingHole:MountingHole_3.2mm_M3_Pad_Via', '', '', 'Board mounting hole M3, plated, grounded')

# =====================================================================================
sheet('storage_usb', 'NVMe (M.2 Key M) and USB 3.0 host ports',
      'PCIe x1: TX AC-coupling capacitors are on the CM5, RX capacitors are on the SSD. Route as 90 ohm pairs (CM5 datasheet 2.3).\n'
      'USB VBUS: TPS2561 dual switch, about 1.2A per port (R_ILIM 47k). Each port has 150uF bulk as USB requires 120uF minimum.')
M = {'GND': G, '3.3V': '+3V3_NVME', 'DAS/~{DSS}/~{LED1}': 'M2_LED_N', 'DEVSLP': 'NC', 'PERn0/SATA-B+': 'PCIE_RX_N', 'PERp0/SATA-B-': 'PCIE_RX_P',
     'PETn0/SATA-A-': 'PCIE_TX_N', 'PETp0/SATA-A+': 'PCIE_TX_P', '~{PERST}': 'PCIE_RST_N', '~{CLKREQ}': 'PCIE_CLKREQ_N', 'REFCLKn': 'PCIE_CLK_N',
     '~{PEWAKE}': 'PCIE_WAKE_N', 'REFCLKp': 'PCIE_CLK_P', 'SUSCLK': 'NC', 'PEDET': 'NC'}
for l in (1, 2, 3):
    for s in ('PERn', 'PERp', 'PETn', 'PETp'): M[f'{s}{l}'] = 'NC'
part('J', 'Bus_M.2_Socket_M', M, 'M.2 Key M', 'Connector_PCBEdge:TE_M.2_M_2x38-1MP_P0.5mm', '2199119-4', 'TE Connectivity', 'M.2 Key M socket 0.5mm pitch, NVMe SSD', ref='J4')
for _ in range(3): c22u('+3V3_NVME')
c100n('+3V3_NVME'); c100n('+3V3_NVME')
R('1k', '+3V3_NVME', 'LEDM_A'); led('yellow', 'LEDM_A', 'M2_LED_N')
part('H', 'Mechanical:MountingHole_Pad', {1: G}, 'M.2 standoff 2280', 'Mounting_Wuerth:Mounting_Wuerth_WA-SMSI-M2_H2.5mm_9774025243', '9774025243R', 'Wurth', 'SMT spacer M2, M.2 2280 retention')
part('H', 'Mechanical:MountingHole_Pad', {1: G}, 'M.2 standoff 2242', 'Mounting_Wuerth:Mounting_Wuerth_WA-SMSI-M2_H2.5mm_9774025243', '9774025243R', 'Wurth', 'SMT spacer M2, M.2 2242 retention')
U = {'SHIELD': 'CHASSIS'}
for n, p in ((1, 0), (2, 1)):
    U.update({f'VBUS{n}': f'USB_VBUS{n}', f'D{n}-': f'USB3_{p}_DM', f'D{n}+': f'USB3_{p}_DP', f'GND{n}': G, f'SSRX{n}-': f'USB3_{p}_RX_N', f'SSRX{n}+': f'USB3_{p}_RX_P',
              f'DRAIN{n}': G, f'SSTX{n}-': f'USB3_{p}_TX_N', f'SSTX{n}+': f'USB3_{p}_TX_P'})
part('J', 'USB3_A_Stacked', U, 'USB 3.0 x2', 'Connector_USB:USB3_A_Molex_48406-0001_Horizontal_Stacked', '48406-0001', 'Molex', 'Dual stacked USB 3.0 Type-A receptacle', ref='J5')
part('U', 'TPS2561', {'GND': G, 'IN': '+5V_USB', 'EN1': 'USB_VBUS_EN', 'EN2': 'USB_VBUS_EN', '~{FAULT2}': 'NC', 'ILM': 'USB_ILIM', 'OUT2': 'USB_VBUS2', 'OUT1': 'USB_VBUS1',
                      '~{FAULT1}': 'NC', 'PAD': G}, 'TPS2561DRC', types={'OUT1': 'power_out', 'OUT2': 'power_out'}, mpn='TPS2561DRCR', mfr='Texas Instruments', alt='TPS2561ADRCR')
R('47k', 'USB_ILIM', G); R('100k', 'USB_VBUS_EN', G); c10u('+5V_USB'); c100n('+5V_USB')
for n, p in ((1, 0), (2, 1)):
    part('C', 'Device:C_Polarized', {1: f'USB_VBUS{n}', 2: G}, '150uF 6.3V', 'Capacitor_Tantalum_SMD:CP_EIA-3528-21_Kemet-B', 'T520B157M006ATE070', 'KEMET', 'Polymer tantalum 150uF 6.3V 70mOhm')
    c100n(f'USB_VBUS{n}')
    part('U', 'TPD4E05U06DQA', {'D1+': f'USB3_{p}_RX_P', 'D1-': f'USB3_{p}_RX_N', 'D2+': f'USB3_{p}_TX_P', 'D2-': f'USB3_{p}_TX_N', 'GND': G, 'NC': 'NC'},
         mpn='TPD4E05U06DQAR', mfr='Texas Instruments', desc='4-channel ESD array 0.5pF, USB 3.0 SuperSpeed pairs')
    part('U', 'TPD2EUSB30', {'D+': f'USB3_{p}_DP', 'D-': f'USB3_{p}_DM', 'GND': G}, mpn='TPD2EUSB30DRTR', mfr='Texas Instruments', desc='2-channel ESD array, USB 2.0 D+/D-')

# =====================================================================================
sheet('ethernet_poe', 'Gigabit Ethernet and 802.3bt PoE powered device',
      'ISOLATION: every net on the cable side of U17 (V1-V4, VPOE_*, POE_VIN_*, POE_T4DET, POE_OPTO_A) is the PoE primary domain.\n'
      'Keep 2.5mm creepage to all other copper and no planes under it (net class PoE_Primary). Rated 1500V impulse (Ag5810 datasheet 4).\n'
      'Two Schottky bridges (eight PMEG10020) accept power on either or both pairsets and either polarity. U17 presents Class 7; the\n'
      'jack is rated 600mA per centre tap, which bounds PoE input at 60W PSE power. Opto U18 tells Linux when a Type 4 PSE is present.')
part('J', 'RJ45_WE_7499511001A',
     {'D1+': 'ETH_P0_P', 'D1-': 'ETH_P0_N', 'CD1': 'ETH_CT0', 'D2+': 'ETH_P1_P', 'D2-': 'ETH_P1_N', 'CD2': 'ETH_CT1', 'D3+': 'ETH_P2_P', 'D3-': 'ETH_P2_N', 'CD3': 'ETH_CT2',
      'D4+': 'ETH_P3_P', 'D4-': 'ETH_P3_N', 'CD4': 'ETH_CT3', 'V1': 'POE_V1', 'V2': 'POE_V2', 'V3': 'POE_V3', 'V4': 'POE_V4', 'SHIELD': 'CHASSIS'},
     'RJ45 GbE PoE', mpn='7499511001A', mfr='Wurth Elektronik', alt='Link-PP LPJG0926HENL (different footprint)', ref='J2')
for i in range(4): c100n(f'ETH_CT{i}')
for a, b in ((0, 1), (2, 3)):
    part('U', 'TPD4E05U06DQA', {'D1+': f'ETH_P{a}_P', 'D1-': f'ETH_P{a}_N', 'D2+': f'ETH_P{b}_P', 'D2-': f'ETH_P{b}_N', 'GND': G, 'NC': 'NC'},
         mpn='TPD4E05U06DQAR', mfr='Texas Instruments', desc='4-channel ESD array 0.5pF, Ethernet MDI pairs')
for v in ('POE_V1', 'POE_V2', 'POE_V3', 'POE_V4'):
    for a, k in ((v, 'VPOE_P'), ('VPOE_N', v)):
        part('D', 'PMEG10020ELR', {'A': a, 'K': k}, mpn='PMEG10020ELRX', mfr='Nexperia', desc='Schottky 100V 2A SOD-123W, PoE input bridge', alt='SS210')
part('D', 'Diode:SMAJ58A', {1: 'VPOE_P', 2: 'VPOE_N'}, 'SMAJ58A', mpn='SMAJ58A', mfr='Littelfuse', desc='TVS 58V unidirectional 400W SMA (pin 1 cathode to VPOE_P)')
C('100nF', 'VPOE_P', 'VPOE_N', '0805', '100V', mpn='CL21B104KCFNNNE', mfr='Samsung')
PB = dict(mpn='FBMH3225HM102NT', fp='Inductor_SMD:L_1210_3225Metric', val='1k@100MHz 2A', mfr='Taiyo Yuden')
bead('VPOE_P', 'POE_VIN_P', **PB); bead('VPOE_N', 'POE_VIN_N', **PB)
part('U', 'Ag5810', {'VIN+': 'POE_VIN_P', 'VIN-': 'POE_VIN_N', 'TYP2-DET': 'NC', 'TYP4-DET': 'POE_T4DET', 'SA1': 'NC', 'SA2': 'NC', 'VOUT1': 'V12_POE', 'VOUT2': 'V12_POE',
                    '0V1': G, '0V2': G, 'ADJ': 'NC'}, mpn='Ag5810', mfr='Silvertel', alt='Ag5800 (85W, larger footprint)')
R('27k', 'POE_VIN_P', 'POE_OPTO_A', '1206', desc='Resistor 27k 1% 1206 0.25W, opto LED current limit from 57V')
part('U', 'LTV-817S', {1: 'POE_OPTO_A', 2: 'POE_T4DET', 3: G, 4: 'POE_BT_N'}, mpn='LTV-817S', mfr='Lite-On', desc='Optocoupler 5kV, PoE Type 4 detect across the isolation barrier', alt='PC817X (SMD), TLP785')
R('10k', '+3V3', 'POE_BT_N')
for _ in range(2):
    part('C', 'Device:C_Polarized', {1: 'V12_POE', 2: G}, '1000uF 16V', 'Capacitor_SMD:CP_Elec_10x10.5', 'EEE-FT1C102AP', 'Panasonic', 'Aluminium electrolytic 1000uF 16V, required by Ag5810')
    C('10uF', 'V12_POE', G, '1206', '25V', mpn='CL31B106KAHNNNE', mfr='Samsung')
R('1M', 'CHASSIS', G, '1206'); C('4.7nF', 'CHASSIS', G, '1812', '2kV', mpn='C1812C472KGRACTU', mfr='KEMET')
R('330', '+3V3', 'LEDE1_A'); led('green', 'LEDE1_A', 'ETH_LED3_N'); R('330', '+3V3', 'LEDE2_A'); led('yellow', 'LEDE2_A', 'ETH_LED2_N')

# =====================================================================================
sheet('radios', 'Zigbee, Thread and Z-Wave',
      'U19 Zigbee coordinator (EZSP NCP) with external antenna on J9. U20 OpenThread RCP with built-in antenna (Matter over Thread).\n'
      'Separate radios so Zigbee and Thread never share airtime. UART with RTS/CTS, 115200 or 460800 baud. BOOT low at reset enters the\n'
      'Gecko bootloader for firmware update over UART. J8/J10 are unpopulated SWD pads for factory programming and recovery.\n'
      'J11 accepts a Raspberry Pi GPIO-header Z-Wave 800 module (pins 1-10 of the 40-pin header: Aeotec Z-Pi 800, Zooz ZAC93).')
def mgm(tag, mpn, rf, val):
    n = {'GND': G, 'VDD': '+3V3', 'PC00': f'{tag}_M2H_TXD', 'PC01': f'{tag}_H2M_TXD', 'PC02': f'{tag}_M2H_RTS', 'PC03': f'{tag}_H2M_RTS', 'PB00': f'{tag}_BOOT_N',
         'RESETn': f'{tag}_RST_N', 'PA01': f'{tag}_SWCLK', 'PA02': f'{tag}_SWDIO', 'RFOUT': rf}
    for g in ('PB04', 'PB03', 'PB02', 'PB01', 'PA00', 'PA03', 'PA04', 'PA05', 'PA06', 'PA07', 'PA08', 'PD03', 'PD02', 'PD01', 'PD00', 'PC04', 'PC05', 'PC06', 'PC07'): n[g] = 'NC'
    part('U', 'MGM240P', n, val, mpn=mpn, mfr='Silicon Labs', alt='MGM240PB32VNA3 / MGM240PB32VNN3 pending certification check')
    c10u('+3V3'); c100n('+3V3')
    part('J', 'Connector_Generic:Conn_01x05', {1: '+3V3', 2: f'{tag}_SWDIO', 3: f'{tag}_SWCLK', 4: f'{tag}_RST_N', 5: G}, f'{tag} SWD',
         'Connector_PinHeader_1.27mm:PinHeader_1x05_P1.27mm_Vertical', '', '', 'SWD pads, not fitted', dnp=True)
mgm('ZB', 'MGM240PA32VNN3', 'ZB_RF_A', 'MGM240P Zigbee (RF pin)')
R('0', 'ZB_RF_A', 'ZB_RF_B', desc='0 ohm 0402, series element of antenna matching pi network')
C('DNP', 'ZB_RF_A', G, '0402', '50V', dnp=True, diel='C0G'); C('DNP', 'ZB_RF_B', G, '0402', '50V', dnp=True, diel='C0G')
part('J', 'Connector:Conn_Coaxial', {'In': 'ZB_RF_B', 'Ext': G}, 'U.FL Zigbee', 'Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical', 'U.FL-R-SMT-1(80)', 'Hirose', 'U.FL coaxial receptacle 50 ohm')
mgm('TH', 'MGM240PA32VNA3', 'NC', 'MGM240P Thread (antenna)')
part('J', 'Connector_Generic:Conn_02x05_Odd_Even', {1: '+3V3', 2: '+5V', 3: 'NC', 4: '+5V', 5: 'NC', 6: G, 7: 'NC', 8: 'ZW_H2M_TXD', 9: G, 10: 'ZW_M2H_TXD'}, 'Z-Wave module socket',
     'Connector_PinSocket_2.54mm:PinSocket_2x05_P2.54mm_Vertical', 'SSW-105-01-G-D', 'Samtec', '2x5 2.54mm socket, Raspberry Pi header pins 1-10 for Z-Wave 800 module')
c100n('+3V3'); c10u('+5V')

# =====================================================================================
sheet('audio', 'Audio codec, microphone and speaker output',
      'TLV320AIC3100 is the I2S clock master, clocked by Y1 (12.288MHz = 256 x 48kHz); the CM5 I2S port is the clock consumer.\n'
      'One shared clock for capture and playback keeps the echo-cancellation reference sample-accurate. I2C address 0x18.\n'
      'MK1 is a bottom-port analog MEMS mic mounted on the bottom side over a 1.0mm acoustic hole. SW4 removes microphone\n'
      'power in hardware (privacy) and GPIO27 reports the state. Class-D output: 2.5W into 4 ohm from +5V.')
part('U', 'TLV320AIC3100',
     {'IOVSS': G, 'IOVDD': '+3V3', 'DVDD': '+1V8', 'DOUT': 'I2S_SDI', 'DIN': 'I2S_SDO', 'WCLK': 'I2S_WS', 'BCLK': 'I2S_BCLK', 'MCLK': 'AUD_MCLK', 'SDA': 'I2C1_SDA', 'SCL': 'I2C1_SCL',
      'VOL/MICDET': G, 'MICBIAS': 'NC', 'MIC1LP': 'MIC_IN_P', 'MIC1RP': 'NC', 'MIC1LM': 'MIC_IN_N', 'AVSS': G, 'AVDD': '+3V3A', 'DVSS': G, 'SPKM': 'SPK_M', 'SPKVSS': G,
      'SPKVDD': '+5V_SPK', 'SPKP': 'SPK_P', 'HPL': 'NC', 'HPVDD': '+3V3A', 'HPVSS': G, 'HPR': 'NC', '~{RESET}': 'AUD_RST_N', 'GPIO1': 'NC', 'EP': G},
     mpn='TLV320AIC3100IRHBR', mfr='Texas Instruments', alt='TLV320AIC3110IRHBR (stereo class-D, same driver)')
bead('+3V3', '+3V3A'); bead('+5V', '+5V_SPK', mpn='BLM21PG221SN1D', fp='Inductor_SMD:L_0805_2012Metric', val='220R@100MHz 2A')
for n in ('+3V3', '+1V8', '+3V3A', '+3V3A'): c100n(n); 
c1u('+3V3'); c1u('+1V8'); c10u('+3V3A'); c22u('+5V_SPK'); c100n('+5V_SPK'); c100n('+5V_SPK')
R('10k', 'AUD_RST_N', G)
part('Y', 'ECS-2520MV-xxx-xx', {'Tri-State': '+3V3', 'GND': G, 'OUT': 'AUD_OSC', 'VDD': '+3V3'}, '12.288MHz', mpn='ECS-2520MVLC-122.8-BN-TR', mfr='ECS', desc='CMOS oscillator 12.288MHz 2.5x2.0mm',
     alt='SiTime SIT2001BI-S2-33E-12.288000')
R('33', 'AUD_OSC', 'AUD_MCLK'); c100n('+3V3')
part('MK', 'IM73A135V01', {'OUT+': 'MIC_OUT_P', 'OUT-': 'MIC_OUT_N', 'V_{DD}': 'MIC_VDD', 'GND': G}, mpn='IM73A135V01XTSA1', mfr='Infineon', desc='Analog MEMS microphone, 73dB SNR, differential, bottom port, IP57',
     alt='Knowles SPH8878LR5H-1 (different footprint)')
C('1uF', 'MIC_OUT_P', 'MIC_IN_P', '0402', '16V', mpn='CL05A105KO5NNNC', mfr='Samsung', diel='X5R'); C('1uF', 'MIC_OUT_N', 'MIC_IN_N', '0402', '16V', mpn='CL05A105KO5NNNC', mfr='Samsung', diel='X5R')
part('SW', 'Switch:SW_SPDT', {'A': '+3V3A', 'B': 'MIC_VDD', 'C': G}, 'MIC MUTE', 'Button_Switch_SMD:SW_SPDT_CK_JS102011SAQN', 'JS102011SAQN', 'C&K', 'Slide switch SPDT, hardware microphone mute')
c100n('MIC_VDD'); c1u('MIC_VDD'); R('10k', 'MIC_VDD', 'MIC_ON'); R('100k', 'MIC_ON', G)
bead('SPK_P', 'SPK_OUT_P'); bead('SPK_M', 'SPK_OUT_M')
C('1nF', 'SPK_OUT_P', G, '0402', '50V', mpn='CL05B102KB5NNNC', mfr='Samsung'); C('1nF', 'SPK_OUT_M', G, '0402', '50V', mpn='CL05B102KB5NNNC', mfr='Samsung')
part('J', 'Connector_Generic:Conn_01x02', {1: 'SPK_OUT_P', 2: 'SPK_OUT_M'}, 'SPEAKER 4R 3W', 'Connector_JST:JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal', 'S2B-PH-K-S', 'JST', '2-pin 2.0mm header, speaker')
for i in range(4):
    part('FID', 'Mechanical:Fiducial', {}, 'Fiducial', 'Fiducial:Fiducial_1mm_Mask2mm', '', '', 'Fiducial mark')

if __name__ == '__main__':
    e = check()
    print(len(PARTS), 'parts,', len(nets()), 'nets')
    for x in e: print('  !', x)
    from collections import Counter
    print(Counter(p.sheet for p in PARTS))
