from flask import Flask, render_template
from pysnmp.hlapi.asyncio.slim import Slim
from pysnmp.smi.rfc1902 import ObjectIdentity, ObjectType
import asyncio

app = Flask(__name__)

async def get_snmp_data():
    slim = Slim(1)

    target_ip = '10.4.15.32'
    community_string = 'public'

    errorIndication, errorStatus, errorIndex, varBinds = await slim.get(
        community_string,
        target_ip,
        161,
        ObjectType(ObjectIdentity("SNMPv2-MIB", "sysUpTime", 0)),
    )

    if errorIndication:
        return errorIndication
    elif errorStatus:
        return "{} at {}".format(
            errorStatus.prettyPrint(),
            errorIndex and varBinds[int(errorIndex) - 1][0] or "?",
        )
    else:
        sys_up_time = int(varBinds[0][1])
        seconds = sys_up_time // 100
        minutes = seconds // 60
        hours = minutes // 60

        result = f"{hours:02}:{minutes % 60:02}:{seconds % 60:02}"
        return result

@app.route('/')
def index():
    snmp_data = asyncio.run(get_snmp_data())
    return render_template('index.html', snmp_data=snmp_data)

if __name__ == '__main__':
    app.run(debug=True)
