#!/usr/bin/env python3
"""Program and verify the STUSB4500 (U1) non-volatile memory for the Tahanan Hub.

The profile is the one in nvm-config.md: PDO1 5 V 1.5 A, PDO2 15 V 3.0 A, PDO3 20 V 2.25 A,
POWER_ONLY_ABOVE_5V = 1, USB_COMM_CAPABLE = 1. Every other field keeps the value read from the
device, so a part with factory defaults ends up exactly as nvm-config.md describes.

    program_nvm.py selftest             no hardware: check the field packing against the factory image
    program_nvm.py read                 dump and decode the NVM of the fitted part
    program_nvm.py write                read, modify, write, read back and compare
    program_nvm.py write --dry-run      show what would be written, write nothing

Options: --bus /dev/i2c-1   --addr 0x28

Run on the hub (or any Linux host wired to I2C1) with the board powered from PoE or the 12 V test
point. No Python packages are needed. A new contract is negotiated with the new profile only after
the controller is reset, so unplug and replug the USB-C source, or power-cycle the board.

STATUS: NOT RUN ON HARDWARE. The register sequence and the NVM field map follow ST's reference
programming code for the STUSB4500 (STSW-STUSB003) and the SparkFun STUSB4500 library, written out
from memory. `selftest` proves the packing reproduces the factory-default profile (5 V 1.5 A,
15 V 1.5 A, 20 V 1.0 A), which is evidence the map is right but not proof. Check the first board
with ST's own tool (STSW-STUSB002) before using this script on a production line.
"""
import argparse
import fcntl
import os
import sys
import time

I2C_SLAVE = 0x0703
REG_RW_BUFFER = 0x53
REG_FTP_CUST_PASSWORD = 0x95
REG_FTP_CTRL_0 = 0x96
REG_FTP_CTRL_1 = 0x97
PASSWORD = 0x47
PWR, RST_N, REQ, SECT = 0x80, 0x40, 0x10, 0x07
OP_READ, OP_WRITE_PL, OP_WRITE_SER, OP_ERASE_SECTOR, OP_PROG_SECTOR, OP_SOFT_PROG_SECTOR = 0x00, 0x01, 0x02, 0x05, 0x06, 0x07
ALL_SECTORS = 0x1F

# Factory NVM image of an unprogrammed STUSB4500, five sectors of eight bytes.
FACTORY = [
    [0x00, 0x00, 0xB0, 0xAA, 0x00, 0x45, 0x00, 0x00],
    [0x10, 0x40, 0x9C, 0x1C, 0xFF, 0x01, 0x3C, 0xDF],
    [0x02, 0x40, 0x0F, 0x00, 0x32, 0x00, 0xFC, 0xF1],
    [0x00, 0x19, 0x56, 0xAF, 0xF5, 0x35, 0x5F, 0x00],
    [0x00, 0x4B, 0x90, 0x21, 0x43, 0x00, 0x40, 0xFB],
]

# The Tahanan profile. Voltages in volts, currents in amperes.
PROFILE = {
    'pdo_count': 3,
    'pdo1_current': 1.5,
    'pdo2_voltage': 15.0, 'pdo2_current': 3.0,
    'pdo3_voltage': 20.0, 'pdo3_current': 2.25,
    'usb_comm_capable': 1,
    'power_only_above_5v': 1,
    'req_src_current': 0,
}


def current_code(amps):
    """4-bit current code. 0 selects the flexible current, which this board does not use."""
    if amps < 0.5 or amps > 5.0:
        raise ValueError('current %.2f A is outside 0.5 to 5.0 A' % amps)
    code = amps * 4 - 1 if amps <= 3.0 else amps * 2 + 5
    if abs(code - round(code)) > 1e-9:
        raise ValueError('current %.2f A is not on the 0.25 A (to 3 A) or 0.5 A (above 3 A) grid' % amps)
    return int(round(code))


def current_amps(code):
    if code == 0:
        return None
    return code * 0.25 + 0.25 if code < 11 else code * 0.5 - 2.5


def decode(s):
    """Return the fields this script cares about from a five-sector image."""
    return {
        'pdo_count': (s[3][2] & 0x06) >> 1,
        'pdo1_current': current_amps((s[3][2] & 0xF0) >> 4),
        'pdo2_voltage': (((s[4][1] << 2) | (s[4][0] >> 6)) & 0x3FF) / 20.0,
        'pdo2_current': current_amps(s[3][4] & 0x0F),
        'pdo3_voltage': (((s[4][3] & 0x03) << 8) | s[4][2]) / 20.0,
        'pdo3_current': current_amps((s[3][5] & 0xF0) >> 4),
        'usb_comm_capable': s[3][2] & 0x01,
        'external_power': (s[3][2] & 0x08) >> 3,
        'power_only_above_5v': (s[4][6] & 0x08) >> 3,
        'req_src_current': (s[4][6] & 0x10) >> 4,
        'power_ok_cfg': (s[4][4] & 0x60) >> 5,
        'gpio_cfg': (s[1][0] & 0x30) >> 4,
    }


def encode(base, p):
    """Return a copy of the image `base` with the fields in `p` replaced."""
    s = [list(row) for row in base]
    if not 1 <= p['pdo_count'] <= 3:
        raise ValueError('pdo_count must be 1 to 3')
    s[3][2] = (s[3][2] & ~0x06 & 0xFF) | (p['pdo_count'] << 1)
    s[3][2] = (s[3][2] & 0x0F) | (current_code(p['pdo1_current']) << 4)
    s[3][4] = (s[3][4] & 0xF0) | current_code(p['pdo2_current'])
    s[3][5] = (s[3][5] & 0x0F) | (current_code(p['pdo3_current']) << 4)
    for key in ('pdo2_voltage', 'pdo3_voltage'):
        if not 5.0 <= p[key] <= 20.0 or abs(p[key] * 20 - round(p[key] * 20)) > 1e-9:
            raise ValueError('%s must be 5 to 20 V in 50 mV steps' % key)
    v2 = int(round(p['pdo2_voltage'] * 20))
    s[4][0] = (s[4][0] & 0x3F) | ((v2 & 0x03) << 6)
    s[4][1] = (v2 >> 2) & 0xFF
    v3 = int(round(p['pdo3_voltage'] * 20))
    s[4][2] = v3 & 0xFF
    s[4][3] = (s[4][3] & 0xFC) | ((v3 >> 8) & 0x03)
    s[3][2] = (s[3][2] & 0xFE) | (p['usb_comm_capable'] & 1)
    s[4][6] = (s[4][6] & ~0x08 & 0xFF) | ((p['power_only_above_5v'] & 1) << 3)
    s[4][6] = (s[4][6] & ~0x10 & 0xFF) | ((p['req_src_current'] & 1) << 4)
    return s


def show(s, title):
    print(title)
    for i, row in enumerate(s):
        print('  sector %d: %s' % (i, ' '.join('%02X' % b for b in row)))
    d = decode(s)
    amp = lambda a: 'flexible' if a is None else '%.2f A' % a
    print('  PDOs used %d | PDO1 5.00 V %s | PDO2 %.2f V %s | PDO3 %.2f V %s' % (
        d['pdo_count'], amp(d['pdo1_current']), d['pdo2_voltage'], amp(d['pdo2_current']), d['pdo3_voltage'], amp(d['pdo3_current'])))
    print('  USB_COMM_CAPABLE %d | POWER_ONLY_ABOVE_5V %d | REQ_SRC_CURRENT %d | POWER_OK_CFG %d | GPIO_CFG %d | external power %d' % (
        d['usb_comm_capable'], d['power_only_above_5v'], d['req_src_current'], d['power_ok_cfg'], d['gpio_cfg'], d['external_power']))


class Bus:
    def __init__(self, path, addr):
        self.fd = os.open(path, os.O_RDWR)
        fcntl.ioctl(self.fd, I2C_SLAVE, addr)

    def write(self, reg, *data):
        os.write(self.fd, bytes([reg, *data]))

    def read(self, reg, n=1):
        os.write(self.fd, bytes([reg]))
        return list(os.read(self.fd, n))

    def request(self, ctrl0):
        """Start an NVM operation and wait for the controller to clear the request bit."""
        self.write(REG_FTP_CTRL_0, ctrl0 | REQ)
        deadline = time.monotonic() + 2.0
        while self.read(REG_FTP_CTRL_0)[0] & REQ:
            if time.monotonic() > deadline:
                raise TimeoutError('STUSB4500 did not complete the NVM operation')
            time.sleep(0.005)


def nvm_read(bus):
    bus.write(REG_FTP_CUST_PASSWORD, PASSWORD)
    bus.write(REG_FTP_CTRL_0, 0x00)
    bus.write(REG_FTP_CTRL_0, PWR | RST_N)
    sectors = []
    try:
        for n in range(5):
            bus.write(REG_FTP_CTRL_0, PWR | RST_N)
            bus.write(REG_FTP_CTRL_1, OP_READ)
            bus.request((n & SECT) | PWR | RST_N)
            sectors.append(bus.read(REG_RW_BUFFER, 8))
            bus.write(REG_FTP_CTRL_0, 0x00)
    finally:
        nvm_exit(bus)
    return sectors


def nvm_exit(bus):
    bus.write(REG_FTP_CTRL_0, RST_N)
    bus.write(REG_FTP_CTRL_1, 0x00)
    bus.write(REG_FTP_CUST_PASSWORD, 0x00)


def nvm_write(bus, sectors):
    bus.write(REG_FTP_CUST_PASSWORD, PASSWORD)
    bus.write(REG_RW_BUFFER, 0x00)
    bus.write(REG_FTP_CTRL_0, 0x00)
    bus.write(REG_FTP_CTRL_0, PWR | RST_N)
    try:
        # erase all five sectors
        bus.write(REG_FTP_CTRL_1, ((ALL_SECTORS << 3) & 0xF8) | OP_WRITE_SER)
        bus.request(PWR | RST_N)
        bus.write(REG_FTP_CTRL_1, OP_SOFT_PROG_SECTOR)
        bus.request(PWR | RST_N)
        bus.write(REG_FTP_CTRL_1, OP_ERASE_SECTOR)
        bus.request(PWR | RST_N)
        # program each sector
        for n, data in enumerate(sectors):
            bus.write(REG_RW_BUFFER, *data)
            bus.write(REG_FTP_CTRL_0, PWR | RST_N)
            bus.write(REG_FTP_CTRL_1, OP_WRITE_PL)
            bus.request(PWR | RST_N)
            bus.write(REG_FTP_CTRL_1, OP_PROG_SECTOR)
            bus.request((n & SECT) | PWR | RST_N)
    finally:
        nvm_exit(bus)


def selftest():
    d = decode(FACTORY)
    expect = {'pdo_count': 3, 'pdo1_current': 1.5, 'pdo2_voltage': 15.0, 'pdo2_current': 1.5, 'pdo3_voltage': 20.0, 'pdo3_current': 1.0,
              'usb_comm_capable': 0, 'power_only_above_5v': 0, 'req_src_current': 0, 'power_ok_cfg': 2, 'gpio_cfg': 1}
    bad = [k for k, v in expect.items() if d[k] != v]
    assert not bad, 'factory image decodes wrongly: %s' % bad
    assert encode(FACTORY, {k: d[k] for k in PROFILE}) == FACTORY, 'encode(decode(x)) changed the factory image'
    new = encode(FACTORY, PROFILE)
    got = decode(new)
    assert all(got[k] == v for k, v in PROFILE.items()), 'profile does not survive an encode and decode'
    changed = [(i, j) for i in range(5) for j in range(8) if new[i][j] != FACTORY[i][j]]
    assert set(changed) <= {(3, 2), (3, 4), (3, 5), (4, 0), (4, 1), (4, 2), (4, 3), (4, 6)}, 'unexpected bytes changed: %s' % changed
    for amps in (0.5, 1.5, 2.25, 3.0, 3.5, 5.0):
        assert current_amps(current_code(amps)) == amps
    show(FACTORY, 'Factory image')
    show(new, 'Tahanan image, from factory defaults')
    print('selftest passed. Bytes changed from factory: %s' % ', '.join('s%d[%d]' % c for c in changed))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('command', choices=('selftest', 'read', 'write'))
    ap.add_argument('--bus', default='/dev/i2c-1')
    ap.add_argument('--addr', type=lambda v: int(v, 0), default=0x28)
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    if a.command == 'selftest':
        selftest()
        return 0
    bus = Bus(a.bus, a.addr)
    before = nvm_read(bus)
    show(before, 'NVM as read')
    if a.command == 'read':
        return 0
    after = encode(before, PROFILE)
    show(after, 'NVM to write')
    if after == before:
        print('Already programmed with the Tahanan profile. Nothing written.')
        return 0
    if a.dry_run:
        print('Dry run. Nothing written.')
        return 0
    nvm_write(bus, after)
    check = nvm_read(bus)
    if check != after:
        show(check, 'READ-BACK MISMATCH')
        print('FAILED: the NVM does not hold the requested image. Do not ship this board.', file=sys.stderr)
        return 1
    print('Programmed and verified. Reset the controller (replug USB-C or power-cycle) to apply.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
