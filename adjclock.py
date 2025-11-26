import pigpio
import time
import threading
import sys
import datetime
from datetime import datetime, timedelta
import math

PWM_GPIO = 18       # BCM pin for PWM output
FREQ_HZ = 60000     # PWM frequency in Hz (60 kHz)
DUTY_CYCLE = 500000 # Duty cycle in range 0..1_000_000 (50%)

pi = pigpio.pi()
if not pi.connected:
    print("Fatal Error: Could not connect to pigpio daemon.")
    sys.exit(1)

class JJYGenerator:
    def __init__(self):
        self.interval_timer = None
        self.stop_flag = False
        
        # list of leap seconds (Japan time)
        self.plus_leapsecond_list = [
            datetime(2017, 1, 1, 9)
        ]
    
    def getleapsecond(self):
        """Leap second +1: inserted within a month -1: removed within a month 0: none"""
        now = datetime.now()
        for leap_date in self.plus_leapsecond_list:
            diff = (leap_date - now).total_seconds()
            if 0 < diff <= 31 * 24 * 60 * 60:
                return 1
        return 0
    
    def generate_mark(self, duration, short=False):
        """Generate mark with specified duration"""
        # Output PWM on GPIO 12
        pi.hardware_PWM(PWM_GPIO, FREQ_HZ, DUTY_CYCLE) # 60KHz 50% dutycycle
        time.sleep(duration) # Play for 'duration' seconds
        pi.hardware_PWM(PWM_GPIO, 0, 0) # stop PWM
        if not short:
            time.sleep(1.0 - duration) # Space to complete 1 second
        return
    
    def schedule(self, date, summer_time):
        """Schedule PWM signals for a minute"""
        print(f"Starting JJY signal for {date.strftime('%Y-%m-%d %H:%M')}")
        minute = date.minute
        hour = date.hour
        fullyear = date.year
        year = fullyear % 100
        week_day = date.weekday()
        if week_day == 6:  # Convert Python's Monday=0 to JavaScript's Sunday=0
            week_day = 0
        else:
            week_day += 1
        
        # Calculate day of year
        year_start = datetime(date.year, 1, 1)
        year_day = (date.replace(hour=0, minute=0, second=0, microsecond=0) - year_start).days + 1
        
        leapsecond = self.getleapsecond()
        
        def marker(short=False):
            """Output a marker at second s of each minute"""
            self.generate_mark(0.2, short)
            return
        
        def bit(value, weight):
            """Output a bit and update the parity bit"""
            nonlocal pa
            b = value >= weight
            value -= weight if b else 0
            pa += 1 if b else 0
            duration = 0.5 if b else 0.8
            self.generate_mark(duration)
            print(f"bit {'1' if b else '0'} (weight {weight})")
            return value
        
        # Marker (M)
        marker()
        print("mark P0")
        
        # Minute
        pa = 0
        minute = bit(minute, 40) # 1
        minute = bit(minute, 20) # 2
        minute = bit(minute, 10) # 3
        minute = bit(minute, 16) # 4
        minute = bit(minute, 8) # 5
        minute = bit(minute, 4) # 6
        minute = bit(minute, 2) # 7
        minute = bit(minute, 1) # 8
        pa2 = pa
        
        marker()  # P1 - 9
        print("mark P1")
        
        # Hour
        pa = 0
        hour = bit(hour, 80) # 10
        hour = bit(hour, 40) # 11
        hour = bit(hour, 20) # 12
        hour = bit(hour, 10) # 13
        hour = bit(hour, 16) # 14
        hour = bit(hour, 8) # 15
        hour = bit(hour, 4) # 16
        hour = bit(hour, 2) # 17
        hour = bit(hour, 1) # 18
        pa1 = pa
        
        marker()  # P2 - 19
        print("mark P2")
        
        # Day of year since January 1
        year_day = bit(year_day, 800) # 20
        year_day = bit(year_day, 400) # 21
        year_day = bit(year_day, 200) # 22
        year_day = bit(year_day, 100) # 23
        year_day = bit(year_day, 160) # 24
        year_day = bit(year_day, 80) # 25
        year_day = bit(year_day, 40) # 26
        year_day = bit(year_day, 20) # 27
        year_day = bit(year_day, 10) # 28
        
        marker()  # P3 - 29
        print("mark P3")
        
        year_day = bit(year_day, 8) # 30
        year_day = bit(year_day, 4) # 31
        year_day = bit(year_day, 2) # 32
        year_day = bit(year_day, 1) # 33
        
        bit(0, 1)  # 0 - 34
        bit(0, 1)  # 0 - 35
        bit(pa1 % 2, 1) # 36
        bit(pa2 % 2, 1) # 37
        bit(0, 1)  # SU1 - 38
        
        marker()  # P4 - 39 
        print("mark P4")
        
        # SU2
        if summer_time:
            bit(1, 1) # 40 Summer time in effect
        else:
            # Summer time in effect (no change from summer to standard time within 6 days)
            bit(0, 1) # 40 Summer time in effect
        
        # Year
        year = bit(year, 80)  # 41
        year = bit(year, 40)  # 42
        year = bit(year, 20)  # 43
        year = bit(year, 10)  # 44
        year = bit(year, 8)  # 45
        year = bit(year, 4)  # 46
        year = bit(year, 2)  # 47
        year = bit(year, 1)  # 48
        
        marker()  # P5 - 49
        print("mark P5")
        
        # Weekday
        week_day = bit(week_day, 4) # 50
        week_day = bit(week_day, 2) # 51
        week_day = bit(week_day, 1) # 52
        
        # Leap second
        if leapsecond == 0:
            # No leap second
            bit(0, 1)  # 0 - 53
            bit(0, 1)  # 0 - 54
        elif leapsecond > 0:
            # Positive leap second
            bit(1, 1)  # 1 - 53
            bit(1, 1)  # 1 - 54
        else:
            # Negative leap second
            bit(0, 1)  # 0 - 53
            bit(0, 1)  # 0 - 54
        
        bit(0, 1)  # 0 - 55
        bit(0, 1)  # 0 - 56
        bit(0, 1)  # 0 - 57
        bit(0, 1)  # 0 - 58
        
        marker(True)  # P6 - 59 // Short marker, so we have 0.9 seconds of silence before the next minute
        print("mark P6")
        return
        
    def start(self):
        """Start generating JJY signals"""
        
        self.stop_flag = False
        now = time.time() * 1000  # milliseconds
        t = math.floor(now / (60 * 1000)) * 60 * 1000
        next_minute = t + 60 * 1000
        delay = (next_minute - now - 1000) / 1000  # Set timer slightly before exactly 0 seconds of each minute
        if delay < 0:
            delay += 60
        print(f"JJY signal will start in {delay:.2f} seconds")
        t = next_minute

        def timer_callback():
            nonlocal t
            if not self.stop_flag:
                timer = threading.Timer(60.0, timer_callback)
                timer.daemon = True
                self.interval_timer = timer
                timer.start()
                self.schedule(datetime.fromtimestamp(t / 1000), False)
                t += 60 * 1000
        
        timer = threading.Timer(delay, timer_callback)
        timer.daemon = False
        self.interval_timer = timer
        timer.start()
    
    def stop(self):
        """Stop generating JJY signals"""
        self.stop_flag = True
        pi.hardware_PWM(PWM_GPIO, 0, 0) # stop PWM
        if self.interval_timer:
            self.interval_timer.cancel()
            self.interval_timer = None

def main():
    try:
        generator = JJYGenerator()
        print("Starting JJY signal generator...")
        generator.start()

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nInterrupted by user. Stopping JJY...")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        generator.stop()
        print("\nThread completed.")

if __name__ == "__main__":
    main()
