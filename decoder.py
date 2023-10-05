import os
import re
import yaml
from datetime import datetime, timezone

factors = { 'k':1E3, 'M':1E6, 'G':1E9, 'm':1E-3, 'u':1E-6 }

# load data about registers
with open(os.path.join(os.path.dirname(__file__), 'registers.yaml')) as file:
    registers = yaml.safe_load(file)
for code,reg in registers.items():
    reg['abs'] = isinstance(reg['tolerance'], (int, float))
    if type(reg['tolerance']) is str: 
        if reg['tolerance'][-1]=='%':
            reg['tolerance'] = int(reg['tolerance'][:-1])/100
        else:
            raise Exception(f"Tolerance provided for {code} is neither a number or a percentage.")
    elif not reg['abs']:
        raise Exception(f"Tolerance provided for {code} is neither a number or a percentage.")

class record:

    def __init__(self,measurement="Measurement", raw=None, tag_set={}, field_set={}, timestamp=None, tolerance={}):
        # constructor from explicit data or from raw record
        self.measurement = measurement
        self.tag_set = tag_set
        if raw is None:
            self.field_set = field_set
            self.timestamp = timestamp
            self.tolerance = tolerance
        else:
            self.processRawRecord(raw)

    def valid(self):
        # check that this is a valid measurement
        return (len(self.field_set)>0)

    def __eq__(self, other):
        # the idea here is to use this for the deadband implementation.
        # so we need to check if two records are close enough to be considered equal
        # the criteria will depend on the field and is loaded from yaml.
        if set(self.field_set) != set(other.field_set):
            return False
        for field, value in self.field_set.items():
            if self.tolerance[field]['abs']:
                if abs(value-other.field_set[field])>self.tolerance[field]['tolerance']:
                    return False
            else:
                if abs(value-other.field_set[field])>self.tolerance[field]['tolerance']*value:
                    return False
        if abs((self.timestamp-other.timestamp).total_seconds())>float(self.tolerance["timestamp"]['tolerance']):
            return False
        return True

    def processRawRecord(self,record):
        # read the raw record from the communicating meter and fills in the data members
        def content(foo): return iter(foo.splitlines())
        fields = {}
        tolerance = {}
        timestamp = datetime.now(timezone.utc)
        for n,line in enumerate(content(record)):
            m = re.match('0-0:1.0.0\((\d+)(S|W)\)',line)
            if m :
                timestamp = datetime.strptime(f"{m.group(1)}+0{'2' if m.group(2)=='S' else '1'}:00", "%y%m%d%H%M%S%z")
            m = re.match('(\d-\d):(\d+.\d+.\d+)\((\d+.\d+)\*(.*)\)',line)
            if m and m.group(1)=="1-0":
                register = m.group(2)
                value = float(m.group(3))
                unit = m.group(4)
                if register in registers:
                    factor = factors.get(unit[0],1)
                    fields[registers[register]['label']] = value*factor
                    tolerance[registers[register]['label']] = {k: registers[register][k] for k in ('tolerance','abs')}
        tolerance["timestamp"] = {k: registers['timestamp'][k] for k in ('tolerance','abs')}
        self.field_set = fields
        self.tolerance = tolerance
        self.timestamp = timestamp

    def __str__(self):
        # output as line protocol
        output = f"{self.measurement}"
        for tag,value in self.tag_set.items():
            output += f",{tag}={value}"
        for count,(field, value) in enumerate(self.field_set.items()):
            output += f'{"," if count else " "}{field}={value}'
        if self.timestamp is not None:
            output += f" {int(datetime.timestamp(self.timestamp)*1E9)}"
        return output

def main():
    
    test_string = """
/FLU5\253770234_A

0-0:96.1.4(50216)
0-0:96.1.1(3153414731313035343239303939)
0-0:1.0.0(230819220327S)
1-0:1.8.1(000003.689*kWh)
1-0:1.8.2(000006.940*kWh)
1-0:2.8.1(000022.354*kWh)
1-0:2.8.2(000004.264*kWh)
0-0:96.14.0(0002)
1-0:1.7.0(00.278*kW)
1-0:2.7.0(00.000*kW)
1-0:21.7.0(00.278*kW)
1-0:22.7.0(00.000*kW)
1-0:32.7.0(233.3*V)
1-0:31.7.0(001.51*A)
0-0:96.3.10(1)
0-0:17.0.0(999.9*kW)
1-0:31.4.0(999*A)
0-0:96.13.0()
!EF3C
    """
    
    print(test_string)
    rec = record(raw=test_string,measurement="TEST")
    print(rec)

if __name__ == "__main__":
    main()

