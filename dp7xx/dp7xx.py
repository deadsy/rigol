#------------------------------------------------------------------------------
"""

Code to control a DP7xx Power Supply

Tested with model DP712 version 00.01.03

"""
#------------------------------------------------------------------------------

import serial
import time
import random

#------------------------------------------------------------------------------

def clamp(x, lo, hi):
  """clamp a value between limits"""
  if x < lo:
    return lo
  if x > hi:
    return hi
  return x

#------------------------------------------------------------------------------

def minimal_float(x):
  """reduce the string length of a float by stripping trailing 0s"""
  s = '%.2f' % x
  return s.rstrip('0').rstrip('.')

#------------------------------------------------------------------------------

MINIMAL_TIME = 0.05 # 50ms

class dp7xx(object):

  def __init__(self, port, baud=9600, timeout=1):
    """connect to and identify the dp7xx power supply"""
    self.serial = serial.Serial(port, baud, timeout=timeout)
    self.last_time = None
    self.identify()
    self.self_test()
    self.max_v = self.max_voltage()
    self.max_i = self.max_current()
    self.max_over_i = self.max_ocp()
    self.max_over_v = self.max_ovp()

  def command(self, cmd, rsp=True):
    """send a command to the power supply"""
    # wait a minimal amount of time between commands
    if self.last_time is not None:
      delta = MINIMAL_TIME + self.last_time - time.time()
      if delta > 0.0:
        time.sleep(delta)
    self.last_time = time.time()
    # send the command to the serial port
    self.serial.write(cmd)
    # get a response is required
    if rsp:
      return self.serial.readline().strip()
    return None

  def identify(self):
    """query the device identification"""
    rsp = self.command(b'*IDN?\n')
    x = rsp.split(',')
    assert len(x) == 4, 'bad length in identify response'
    self.model = x[1]
    self.sn = x[2]
    self.ver = x[3]

  def self_test(self):
    """query the self test result"""
    rsp = self.command(b'*TST?\n')
    x = rsp.lower()
    self.st_result = ('pass', 'fail')['fail'in x]

  def display(self, ctrl=None):
    """turn the display on or off"""
    if ctrl is None:
      # query state
      return self.command(b':DISP?\n') == 'ON'
    # control state
    state = ('OFF', 'ON')[ctrl]
    self.command(b':DISP %s\n' % state, False)

  def output(self, ctrl=None):
    """turn the channel 1 output on or off"""
    if ctrl is None:
      # query state
      return self.command(b':OUTP:STAT? CH1\n') == 'ON'
    # control state
    state = ('OFF', 'ON')[ctrl]
    self.command(b':OUTP:STAT CH1,%s\n' % state, False)

  def __str__(self):
    s = []
    s.append('model %s' % self.model)
    s.append('serial number %s' % self.sn)
    s.append('version %s' % self.ver)
    s.append('selftest %s' % self.st_result)
    s.append('max voltage %.2fV' % self.max_v)
    s.append('max current %.2fA' % self.max_i)
    return '\n'.join(s)

  # Voltage Functions

  def max_voltage(self):
    """return the maximum voltage"""
    return float(self.command(b':VOLT? MAX\n'))

  def voltage(self, val=None):
    """control the channel 1 voltage"""
    if val is None:
      # query the voltage
      return float(self.command(b':VOLT?\n'))
    # set the voltage
    val = clamp(val, 0.0, self.max_v)
    self.command(b':VOLT %s\n' % minimal_float(val), False)

  def max_ovp(self):
    """return the maximum over voltage protection level"""
    return float(self.command(b':VOLT:PROT? MAX\n'))

  def ovp_level(self, val=None):
    """query/set the over voltage protection level"""
    if val is None:
      # query the voltage
      return float(self.command(b':VOLT:PROT?\n'))
    # set the voltage
    val = clamp(val, 0.0, self.max_over_v)
    self.command(b':VOLT:PROT %.2f\n' % val, False)

  def ovp_ctrl(self, ctrl=None):
    """query/set the over voltage protection state"""
    if ctrl is None:
      return self.command(b':VOLT:PROT:STAT?\n') == 'ON'
    state = ('OFF', 'ON')[ctrl]
    self.command(b':VOLT:PROT:STAT %s\n' % state, False)

  def ovp_tripped(self):
    """has the over voltage protection been tripped?"""
    return self.command(b':VOLT:PROT:TRIP?\n') == 'YES'

  def ovp_clear(self):
    """clear the over voltage protection"""
    self.command(b':VOLT:PROT:CLE\n', False)

  def ovp_str(self):
    """return a string for the ovp state"""
    s = []
    s.append(('off', 'on')[self.ovp_ctrl()])
    s.append('%.2fV' % self.ovp_level())
    s.append(('ok', 'tripped')[self.ovp_tripped()])
    return ' '.join(s)

  def ramp_voltage(self, v0, v1, t, n):
    """ramp voltage from v0 to v1 in t secs, with n steps"""
    assert t > 0.0, 'time must be > 0.0 secs'
    assert n >= 1, 'n steps must be >= 1'
    delta_v = (v1 - v0)/n
    delta_t = t / n
    v = v0
    for i in range(n):
      self.voltage(v)
      time.sleep(delta_t)
      v += delta_v
    self.voltage(v)

  # Current Functions

  def max_current(self):
    """return the maximum current"""
    return float(self.command(b':CURR? MAX\n'))

  def current(self, val=None):
    """control the channel 1 current"""
    if val is None:
      # query the current
      return float(self.command(b':CURR?\n'))
    # set the current
    val = clamp(val, 0.0, self.max_i)
    self.command(b':CURR %s\n' % minimal_float(val), False)

  def max_ocp(self):
    """return the maximum over current protection level"""
    return float(self.command(b':CURR:PROT? MAX\n'))

  def ocp_level(self, val=None):
    """query/set the over current protection level"""
    if val is None:
      # query the current
      return float(self.command(b':CURR:PROT?\n'))
    # set the current
    val = clamp(val, 0.0, self.max_over_i)
    self.command(b':CURR:PROT %.2f\n' % val, False)

  def ocp_ctrl(self, ctrl=None):
    """query/set the over current protection state"""
    if ctrl is None:
      return self.command(b':CURR:PROT:STAT?\n') == 'ON'
    state = ('OFF', 'ON')[ctrl]
    self.command(b':CURR:PROT:STAT %s\n' % state, False)

  def ocp_tripped(self):
    """has the over current protection been tripped?"""
    return self.command(b':CURR:PROT:TRIP?\n') == 'YES'

  def ocp_clear(self):
    """clear the over current protection"""
    self.command(b':CURR:PROT:CLE\n', False)

  def ocp_str(self):
    """return a string for the ocp state"""
    s = []
    s.append(('off', 'on')[self.ocp_ctrl()])
    s.append('%.2fA' % self.ocp_level())
    s.append(('ok', 'tripped')[self.ocp_tripped()])
    return ' '.join(s)

#------------------------------------------------------------------------------
