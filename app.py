from flask import Flask, render_template
from pysnmp.hlapi.asyncio.slim import Slim
from pysnmp.smi.rfc1902 import ObjectIdentity, ObjectType
import asyncio

app = Flask(__name__)

async def get_snmp_data():
    slim = Slim(1)

    target_ip = '10.4.15.32'
    community_string = 'public'

    # Retrieve sysUpTime
    errorIndication1, errorStatus1, errorIndex1, varBinds1 = await slim.get(
        community_string,
        target_ip,
        161,
        ObjectType(ObjectIdentity("SNMPv2-MIB", "sysUpTime", 0)),
    )

    # Retrieve sysDescr
    errorIndication2, errorStatus2, errorIndex2, varBinds2 = await slim.get(
        community_string,
        target_ip,
        161,
        ObjectType(ObjectIdentity("SNMPv2-MIB", "sysDescr", 0)),
    )

    if errorIndication1 or errorIndication2:
        return errorIndication1 or errorIndication2
    elif errorStatus1 or errorStatus2:
        return "{} at {}".format(
            errorStatus1.prettyPrint(),
            errorIndex1 and varBinds1[int(errorIndex1) - 1][0] or "?",
        )
    else:
        sys_up_time = int(varBinds1[0][1])
        sys_descr = varBinds2[0][1].prettyPrint()
        
        seconds = sys_up_time // 100
        minutes = seconds // 60
        hours = minutes // 60

        result = {
            "SysUpTime": f"{hours:02}:{minutes % 60:02}:{seconds % 60:02}",
            "SysDescr": sys_descr
        }
        return result

@app.route('/')
def index():
    snmp_data = asyncio.run(get_snmp_data())
    return render_template('index.html', snmp_data=snmp_data)

if __name__ == '__main__':
    app.run(debug=True)
