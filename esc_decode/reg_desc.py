from enum import IntEnum, unique

from termcolor import colored

"""
Section II-Register Descriptions for ESC (EtherCAT Slave Controller), ch2
"""


def decode_run_led_override(value: int) -> str:
    """
    Decodes the RUN LED Override register (0x0138) value into a human-readable string.
    Args:
        value (int): The 8-bit register value.
    Returns:
        str: Human-readable description of the register value.
    """
    assert 0 <= value <= 0xFF, "Value must be a single byte (0-255)"
    led_code = value & 0x0F
    enable_override = (value >> 4) & 0x01

    led_code_desc = {
        0x0: "Off (Init)",
        0x1: "Flash 1x (SafeOp)",
        0xD: "Blinking (PreOp)",
        0xE: "Flickering (Bootstrap)",
        0xF: "On (Operational)",
    }
    if 0x2 <= led_code <= 0xC:
        led_desc = f"Flash {led_code}x"
    else:
        led_desc = led_code_desc.get(led_code, "Unknown")

    return (
        f"RUN LED Override: LED code=0x{led_code:X} ({led_desc}), "
        f"Override={'Enabled' if enable_override else 'Disabled'} "
    )


def decode_err_led_override(value: int) -> str:
    """
    Decodes the ERR LED Override register (0x0139) value into a human-readable string.
    Table 26: Register ERR LED Override (0x0139)
    Bit 3:0  - LED code
    Bit 4    - Enable Override
    Bit 7:5  - Reserved
    """
    assert 0 <= value <= 0xFF, "Value must be a single byte (0-255)"
    led_code = value & 0x0F
    enable_override = (value >> 4) & 0x01

    led_code_desc = {
        0x0: "Off",
        0x1: "Flash 1x",
        0xD: "Blinking (PreOp)",
        0xE: "Flickering (Bootstrap)",
        0xF: "On (Operational)",
    }
    if 0x2 <= led_code <= 0xC:
        led_desc = f"Flash {led_code}x"
    else:
        led_desc = led_code_desc.get(led_code, "Unknown")

    return (
        f"ERR LED Override: LED code=0x{led_code:X} ({led_desc}), "
        f"Override={'Enabled' if enable_override else 'Disabled'} "
    )


def decode_al_status_code(value: int) -> str:
    """
    Decodes the AL Status Code Register (0x0134) value
    ch2.22
    """
    assert 0 <= value <= 0xFF, "Value must be a single byte (0-255)"
    return f"AL status code:{value}"


def decode_pdi_control(value: int) -> str:
    """
    Decodes the PDI Control register (0x0140) value into a human-readable string.
    Args:
        value (int): The 16-bit register value.
    Returns:
        str: Human-readable description of the register value.
    """
    assert 0 <= value <= 0xFFFF, "Value must be a 16-bit value (0-65535)"
    pdi_mode = value & 0x03
    pdi_modes = {
        0x0: "SPI",
        0x1: "I2C",
        0x2: "Reserved",
        0x3: "Digital I/O",
    }
    pdi_mode_desc = pdi_modes.get(pdi_mode, "Unknown")
    return f"PDI Control: Mode={pdi_mode_desc} (0x{pdi_mode:X})"


def decode_al_event_req(value: int) -> str:
    """
    2.32 AL Event Request (0x0220:0x0223)
    """
    assert 0 <= value <= 0xFFFFFFFF, "Value must be a 32-bit value (0-4294967295)"
    out_str = ""
    if value & (0b1):
        out_str += "AL Control Register has been written, "
    if value & (0b1 << 1):
        out_str += "At least one change on DC Latch Inputs, "
    if value & (0b1 << 2):
        out_str += "DC SYNC0, "
    if value & (0b1 << 3):
        out_str += "DC SYNC1, "
    if value & (0b1 << 4):
        out_str += "At least one SyncManager changed, "
    if value & (0b1 << 5):
        out_str += "EEPROM command pending, "
    if value & (0b1 << 6):
        out_str += "Has expired, "
    if value & (0b1 << 7):
        out_str += colored("reserved bit set, ", "red")
    for i in range(8, 24):
        if value & (0b1 << i):
            out_str += f"SyncManager {i - 8} interrupt pending, "
    return out_str


def decode_sync_manager_status(value: int) -> str:
    """
    Decodes the Sync Manager Status register (0x0800) value into a human-readable string.
    Args:
        value (int): The 8-bit register value.
    Returns:
        str: Human-readable description of the register value.
    """
    assert 0 <= value <= 0xFF, "Value must be a single byte (0-255)"
    status_flags = []
    if value & 0x01:
        status_flags.append("SM0 Active")
    if value & 0x02:
        status_flags.append("SM1 Active")
    if value & 0x04:
        status_flags.append("SM2 Active")
    if value & 0x08:
        status_flags.append("SM3 Active")
    if value & 0x10:
        status_flags.append("SM4 Active")
    if value & 0x20:
        status_flags.append("SM5 Active")
    if value & 0x40:
        status_flags.append("SM6 Active")
    if value & 0x80:
        status_flags.append("SM7 Active")

    return f"Sync Manager Status: {', '.join(status_flags) if status_flags else 'No Active SMs'}"


def decode_watchdog_status(value: int) -> str:
    """
    Decodes the Watchdog Status register (0x0440) value into a human-readable string.
    Args:
        value (int): The 8-bit register value.
    Returns:
        str: Human-readable description of the register value.
    """
    assert 0 <= value <= 0xFF, "Value must be a single byte (0-255)"
    if value == 0x00:
        return "Watchdog Status: No Error"
    elif value == 0x01:
        return "Watchdog Status: PDI Watchdog Triggered"
    elif value == 0x02:
        return "Watchdog Status: Sync Manager Watchdog Triggered"
    else:
        return f"Watchdog Status: Unknown (0x{value:X})"


def decode_ch2_1(value: int) -> str:
    """ch2.1: Identification Register (0x0000)"""
    return f"Identification Register: 0x{value:08X}"


def decode_ch2_2(value: int) -> str:
    """ch2.2: Revision Register (0x0004)"""
    return f"Revision Register: 0x{value:08X}"


al_state_map = {
    0x01: "Init",
    0x02: "Pre-Operational",
    0x03: "Bootstrap",
    0x04: "Safe-Operational",
    0x08: "Operational",
}


def decode_ch2_20(value: int) -> str:
    """ch2.20: AL Control (0x0120)"""
    state = value & 0x000F

    return (
        f"AL Control: req state={al_state_map.get(state, 'Unknown')} (0x{state:X}), "
        f"Error Ind Ack={value & (0b1 << 4)}, "
        f"Device ID req={value & (0b1 << 5)}"
    )


def decode_ch2_21(value: int) -> str:
    """ch2.21: AL Status (0x0130)"""
    state = value & 0x000F
    return (
        f"State={al_state_map.get(state, 'Unknown')} (0x{state:X}), "
        f"Error Ind ={value & (0b1 << 4)}, "
        f"Device ID loaded={value & (0b1 << 5)}, "
    )


# @unique
# class Esc_reg(IntEnum):
#     RUN_LED_OVERRIDE = 0x0138
#     ERROR_REGISTER = 0x0134
#     PDI_CONTROL = 0x0140
#     SYNC_MANAGER_STATUS = 0x0800
#     WATCHDOG_STATUS = 0x0440

# Integer address to register name mapping
REG_ADDR_TO_NAME = {
    0x0000: "Type",
    0x0001: "Revision",
    0x0002: "Build (low)",
    0x0003: "Build (high)",
    0x0004: "FMMUs supported",
    0x0005: "SyncManagers supported",
    0x0006: "RAM Size",
    0x0007: "Port Descriptor",
    0x0008: "ESC Features supported (low)",
    0x0009: "ESC Features supported (high)",
    0x0010: "Configured Station Address (low)",
    0x0011: "Configured Station Address (high)",
    0x0012: "Configured Station Alias (low)",
    0x0013: "Configured Station Alias (high)",
    0x0020: "Register Write Enable",
    0x0021: "Register Write Protection",
    0x0030: "ESC Write Enable",
    0x0031: "ESC Write Protection",
    0x0040: "ESC Reset ECAT",
    0x0041: "ESC Reset PDI",
    0x0100: "ESC DL Control (low)",
    0x0101: "ESC DL Control",
    0x0102: "ESC DL Control",
    0x0103: "ESC DL Control (high)",
    0x0108: "Physical Read/Write Offset (low)",
    0x0109: "Physical Read/Write Offset (high)",
    0x0110: "ESC DL Status (low)",
    0x0111: "ESC DL Status (high)",
    0x0120: "AL Control (low)",
    0x0121: "AL Control (high)",
    0x0130: "AL Status (low)",
    0x0131: "AL Status (high)",
    0x0134: "AL Status Code (low)",
    0x0135: "AL Status Code (high)",
    0x0138: "RUN LED Override",
    0x0139: "ERR LED Override",
    0x0140: "PDI Control",
    0x0141: "ESC Configuration",
    0x014E: "PDI Information (low)",
    0x014F: "PDI Information (high)",
    0x0150: "PDI Configuration (low)",
    0x0151: "PDI Configuration",
    0x0152: "PDI Configuration",
    0x0153: "PDI Configuration (high)",
    0x0200: "ECAT Event Mask (low)",
    0x0201: "ECAT Event Mask (high)",
    0x0204: "PDI AL Event Mask (low)",
    0x0205: "PDI AL Event Mask",
    0x0206: "PDI AL Event Mask",
    0x0207: "PDI AL Event Mask (high)",
    0x0210: "ECAT Event Request (low)",
    0x0211: "ECAT Event Request (high)",
    0x0220: "AL Event Request (low)",
    0x0221: "AL Event Request",
    0x0222: "AL Event Request",
    0x0223: "AL Event Request (high)",
    0x0300: "RX Error Counter (0)",
    0x0301: "RX Error Counter (1)",
    0x0302: "RX Error Counter (2)",
    0x0303: "RX Error Counter (3)",
    0x0304: "RX Error Counter (4)",
    0x0305: "RX Error Counter (5)",
    0x0306: "RX Error Counter (6)",
    0x0307: "RX Error Counter (7)",
    0x0308: "Forwarded RX Error Counter (0)",
    0x0309: "Forwarded RX Error Counter (1)",
    0x030A: "Forwarded RX Error Counter (2)",
    0x030B: "Forwarded RX Error Counter (3)",
    0x030C: "ECAT Processing Unit Error Counter",
    0x030D: "PDI Error Counter",
    0x030E: "PDI Error Code (low)",
    0x030F: "PDI Error Code (high)",
    0x0310: "Lost Link Counter (0)",
    0x0311: "Lost Link Counter (1)",
    0x0312: "Lost Link Counter (2)",
    0x0313: "Lost Link Counter (3)",
    0x0400: "Watchdog Divider (low)",
    0x0401: "Watchdog Divider (high)",
    0x0410: "Watchdog Time PDI (low)",
    0x0411: "Watchdog Time PDI (high)",
    0x0420: "Watchdog Time Process Data (low)",
    0x0421: "Watchdog Time Process Data (high)",
    0x0440: "Watchdog Status Process Data (low)",
    0x0441: "Watchdog Status Process Data (high)",
    0x0442: "Watchdog Counter Process Data",
    0x0443: "Watchdog Counter PDI",
    0x0500: "SII EEPROM Interface (0)",
    0x0501: "SII EEPROM Interface (1)",
    0x0502: "SII EEPROM Interface (2)",
    0x0503: "SII EEPROM Interface (3)",
    0x0504: "SII EEPROM Interface (4)",
    0x0505: "SII EEPROM Interface (5)",
    0x0506: "SII EEPROM Interface (6)",
    0x0507: "SII EEPROM Interface (7)",
    0x0508: "SII EEPROM Interface (8)",
    0x0509: "SII EEPROM Interface (9)",
    0x050A: "SII EEPROM Interface (10)",
    0x050B: "SII EEPROM Interface (11)",
    0x050C: "SII EEPROM Interface (12)",
    0x050D: "SII EEPROM Interface (13)",
    0x050E: "SII EEPROM Interface (14)",
    0x050F: "SII EEPROM Interface (15)",
    0x0510: "MII Management Interface (0)",
    0x0511: "MII Management Interface (1)",
    0x0512: "MII Management Interface (2)",
    0x0513: "MII Management Interface (3)",
    0x0514: "MII Management Interface (4)",
    0x0515: "MII Management Interface (5)",
    0x0516: "MII Management Interface (6)",
    0x0517: "MII Management Interface (7)",
    0x0518: "MII Management Interface (8)",
    0x0519: "MII Management Interface (9)",
    0x051A: "MII Management Interface (10)",
    0x051B: "MII Management Interface (11)",
    0x0600: "FMMU",
    0x0800: "SyncManager",
    0x0900: "Distributed Clocks",
    0x0E00: "ESC-specific registers",
    0x0F00: "Digital I/O Output Data (0)",
    0x0F01: "Digital I/O Output Data (1)",
    0x0F02: "Digital I/O Output Data (2)",
    0x0F03: "Digital I/O Output Data (3)",
    0x0F10: "General Purpose Outputs (0)",
    0x0F11: "General Purpose Outputs (1)",
    0x0F12: "General Purpose Outputs (2)",
    0x0F13: "General Purpose Outputs (3)",
    0x0F14: "General Purpose Outputs (4)",
    0x0F15: "General Purpose Outputs (5)",
    0x0F16: "General Purpose Outputs (6)",
    0x0F17: "General Purpose Outputs (7)",
    0x0F18: "General Purpose Inputs (0)",
    0x0F19: "General Purpose Inputs (1)",
    0x0F1A: "General Purpose Inputs (2)",
    0x0F1B: "General Purpose Inputs (3)",
    0x0F1C: "General Purpose Inputs (4)",
    0x0F1D: "General Purpose Inputs (5)",
    0x0F1E: "General Purpose Inputs (6)",
    0x0F1F: "General Purpose Inputs (7)",
    0x0F80: "User RAM (start)",
    0x0FFF: "User RAM (end)",
}

# Register name to integer address mapping
# REG_NAME_TO_ADDR = {v: k for k, v in REG_ADDR_TO_NAME.items()}


ESC_desc_map = {
    0x0000: decode_ch2_1,
    0x0004: decode_ch2_2,
    0x0120: decode_ch2_20,
    0x0130: decode_ch2_21,
    0x0134: decode_al_status_code,
    0x0138: decode_run_led_override,
    0x0139: decode_err_led_override,
    0x0140: decode_pdi_control,
    0x0220: decode_al_event_req,
    0x0440: decode_watchdog_status,
    0x0800: decode_sync_manager_status,
}
