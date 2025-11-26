# JJY Time Signal Generator (adjclock.py)

A Raspberry Pi-based JJY (Japanese Standard Time) signal generator that broadcasts time-code signals compatible with radio-controlled clocks.

## Overview

This Python script generates JJY time signals using PWM (Pulse Width Modulation) on a Raspberry Pi GPIO pin. The signals emulate the JJY time code standard broadcast by NICT (National Institute of Information and Communications Technology) in Japan at 40 kHz and 60 kHz.

## Hardware Requirements

- **Raspberry Pi** (any model with GPIO support)
- **GPIO Pin 18** (BCM numbering) - used for PWM output
- **pigpio daemon** - must be running on the system
- Optional: Amplifier circuit to boost the 60 kHz carrier signal for radio transmission

## Software Requirements

- Python 3.x
- `pigpio` library
- Running `pigpiod` daemon

### Installation

```bash
sudo apt-get install pigpio python3-pigpio
sudo systemctl enable pigpiod
sudo systemctl start pigpiod
pip install pigpio
```

## Features

### 1. **JJY Time Code Generation**
Generates complete JJY time code frames every minute containing:
- Current minute (0-59)
- Current hour (0-23)
- Day of year (1-366)
- Year (00-99)
- Day of week (0=Sunday through 6=Saturday)
- Leap second indicators
- Parity bits for error checking

### 2. **PWM Signal Output**
- **Carrier Frequency**: 60 kHz
- **Duty Cycle**: 50%
- **Hardware PWM**: Uses Raspberry Pi's hardware PWM for precise timing
- **GPIO**: BCM pin 18

### 3. **JJY Time Code Structure**
Each minute consists of 60 time slots (0-59 seconds):
- **Marker pulses (0.2s)**: Position markers at seconds 0, 9, 19, 29, 39, 49, 59
- **Binary '1' (0.5s)**: Half-second carrier reduction
- **Binary '0' (0.8s)**: 800ms carrier reduction
- **Gaps**: Remaining time in each second has full carrier amplitude

### 4. **Encoded Information**

| Seconds | Information | Encoding |
|---------|-------------|----------|
| 1-8 | Minutes (0-59) | BCD with weights 40, 20, 10, 16, 8, 4, 2, 1 |
| 9 | Position marker P1 | - |
| 10-18 | Hours (0-23) | BCD with weights 80, 40, 20, 10, 16, 8, 4, 2, 1 |
| 19 | Position marker P2 | - |
| 20-33 | Day of year (1-366) | BCD with various weights |
| 29, 39, 49 | Position markers P3, P4, P5 | - |
| 36-37 | Parity bits | Hour and minute parity |
| 40 | Summer time flag | SU2 indicator |
| 41-48 | Year (00-99) | BCD encoding |
| 50-52 | Day of week | 0=Sunday, 6=Saturday |
| 53-54 | Leap second warning | Indicates upcoming leap second |
| 59 | Position marker P6 | Short marker (0.2s) |

### 5. **Leap Second Support**
- Tracks scheduled leap second insertion dates
- Provides advance warning (within one month) via bits 53-54
- Currently configured with January 1, 2017 leap second

### 6. **Automatic Synchronization**
- Automatically synchronizes to system time
- Starts transmission at the beginning of the next minute
- Continuously generates signals every 60 seconds
- Uses threading for precise timing

### 7. **Parity Bit Calculation**
- **PA1**: Parity for hour bits (seconds 12-18)
- **PA2**: Parity for minute bits (seconds 1-8)
- Provides error detection for receivers

## Usage

### Basic Operation

```bash
python3 adjclock.py
```

The script will:
1. Connect to the pigpio daemon
2. Calculate delay until the next minute boundary
3. Start generating JJY signals on GPIO 18
4. Print debug information showing bit values and markers
5. Continue running until interrupted with Ctrl+C

### Output Example

```
Starting JJY signal generator...
JJY signal will start in 23.45 seconds
Starting JJY signal for 2025-11-26 14:30
mark P0
bit 0 (weight 40)
bit 1 (weight 20)
bit 1 (weight 10)
...
mark P1
```

## Class: JJYGenerator

### Methods

#### `__init__()`
Initializes the generator with leap second data and threading controls.

#### `getleapsecond()`
Returns leap second status:
- `1`: Positive leap second within 31 days
- `0`: No leap second scheduled
- `-1`: Negative leap second within 31 days (rare)

#### `generate_mark(duration, short=False)`
Generates a PWM pulse of specified duration:
- Activates 60 kHz PWM at 50% duty cycle
- Sleeps for the specified duration
- Stops PWM
- Pads with silence to complete 1 second (unless `short=True`)

#### `schedule(date, summer_time)`
Generates the complete 60-second JJY time code for a given date:
- Encodes all time information into proper bit positions
- Outputs PWM signals for each bit
- Prints debug information
- Parameters:
  - `date`: datetime object for the minute to encode
  - `summer_time`: Boolean flag for summer time (DST) - currently unused in Japan

#### `start()`
Starts the continuous JJY signal generation:
- Calculates delay to next minute boundary
- Sets up recurring 60-second timer
- Begins signal transmission

#### `stop()`
Stops signal generation:
- Sets stop flag
- Cancels scheduled timers
- Disables PWM output

## Technical Details

### PWM Configuration
```python
PWM_GPIO = 18       # BCM pin 18
FREQ_HZ = 60000     # 60 kHz carrier
DUTY_CYCLE = 500000 # 50% (range 0-1,000,000)
```

### Timing Precision
- Uses hardware PWM for accurate frequency generation
- Threading timers synchronized to system clock
- Sub-second precision for signal alignment

### Signal Encoding
The JJY standard uses amplitude modulation of a carrier wave:
- **Full amplitude**: Normal carrier (binary '1' state in gaps)
- **Reduced amplitude**: During pulse periods (markers and bits)
- This implementation uses PWM on/off to simulate amplitude reduction

## Troubleshooting

### "Could not connect to pigpio daemon"
Ensure pigpiod is running:
```bash
sudo systemctl status pigpiod
sudo systemctl start pigpiod
```

### No signal output
- Verify GPIO 18 is not used by other processes
- Check pigpio permissions
- Confirm PWM is enabled in Raspberry Pi configuration

### Inaccurate time
- Ensure Raspberry Pi system time is accurate
- Consider using NTP for time synchronization:
```bash
sudo timedatectl set-ntp true
```

## Limitations

- Does not include actual RF transmission circuitry
- Requires external amplifier and antenna for wireless transmission
- Summer time flag is hardcoded to `False` (Japan does not use DST)
- Leap second list must be manually updated
- No consideration for timezone
- "second" timing (aka marker) relies on software/timer, so it might be inacurate. We might need more accurate timebase, such as PPS of GPS/RTC

## License

This is an educational implementation of the JJY time signal standard.

## References

- [JJY Time Signal Standard (NICT)](https://www.nict.go.jp/en/sts/jjy.html)
- [Japanese Standard Time Signal Format](https://www.nict.go.jp/en/sts/jjy_signal.html)
- [The pigpio Library](https://abyz.me.uk/rpi/pigpio/)
- [Web JJY](https://github.com/shogo82148/web-jjy)