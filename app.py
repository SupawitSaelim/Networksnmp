from flask import Flask, render_template, request, redirect, url_for
from pysnmp.hlapi.asyncio.slim import Slim
from pysnmp.smi.rfc1902 import ObjectIdentity, ObjectType
import asyncio

app = Flask(__name__)

async def get_operational_status(target_ip, community_string, operational_status_oid):
    slim = Slim(1)
    errorIndication, errorStatus, errorIndex, varBinds = await slim.get(
        community_string,
        target_ip,
        161,
        ObjectType(ObjectIdentity(operational_status_oid))
    )

    if errorIndication:
        return "Error"
    elif errorStatus:
        return "Error"
    else:
        return varBinds[0][1].prettyPrint()

async def get_interface_data(target_ip, community_string):
    slim = Slim(1)
    interface_data = []

    # Define OIDs for the known 6 ports
    interface_oids = [
        "1.3.6.1.2.1.2.2.1.2.2",
        "1.3.6.1.2.1.2.2.1.2.3",
        "1.3.6.1.2.1.2.2.1.2.4",
        "1.3.6.1.2.1.2.2.1.2.5",
    ]

    operational_status_oid_base = "1.3.6.1.2.1.2.2.1.8."

    for index in range(1, 5):  # Generate OIDs for ports 1 through 6
        port_oid = operational_status_oid_base + str(index)
        operational_status = await get_operational_status(target_ip, community_string, port_oid)
        
        # Fetch the interface name from the results of the get request
        next_oid = ObjectType(ObjectIdentity(interface_oids[index - 1]))
        errorIndication, errorStatus, errorIndex, varBinds = await slim.get(
            community_string,
            target_ip,
            161,
            next_oid
        )
        
        if errorIndication:
            return errorIndication
        elif errorStatus:
            return "{} at {}".format(
                errorStatus.prettyPrint(),
                errorIndex and varBinds[int(errorIndex) - 1][0] or "?",
            )
        else:
            interface_name = varBinds[0][1].prettyPrint()
            interface_data.append((interface_name, operational_status))

    return interface_data

async def get_snmp_data(target_ip, community_string):
    slim = Slim(1)

    errorIndication1, errorStatus1, errorIndex1, varBinds1 = await slim.get(
        community_string,
        target_ip,
        161,
        ObjectType(ObjectIdentity("SNMPv2-MIB", "sysUpTime", 0)),
    )

    errorIndication2, errorStatus2, errorIndex2, varBinds2 = await slim.get(
        community_string,
        target_ip,
        161,
        ObjectType(ObjectIdentity("SNMPv2-MIB", "sysDescr", 0)),
    )
    
    errorIndication3, errorStatus3, errorIndex3, varBinds3 = await slim.get(
        community_string,
        target_ip,
        161,
        ObjectType(ObjectIdentity("SNMPv2-MIB", "sysName", 0)),
    )

    if errorIndication1 or errorIndication2 or errorIndication3:
        return errorIndication1 or errorIndication2 or errorIndication3
    elif errorStatus1 or errorStatus2 or errorStatus3:
        return "{} at {}".format(
            errorStatus1.prettyPrint(),
            errorIndex1 and varBinds1[int(errorIndex1) - 1][0] or "?",
        )
    else:
        sys_up_time = int(varBinds1[0][1])
        sys_descr = varBinds2[0][1].prettyPrint()
        sys_name = varBinds3[0][1].prettyPrint()
        
        seconds = sys_up_time // 100
        minutes = seconds // 60
        hours = minutes // 60

        result = {
            "SysUpTime": f"{hours:02}:{minutes % 60:02}:{seconds % 60:02}",
            "SysDescr": sys_descr,
            "SysName": sys_name
        }
        return result


@app.route('/')
def index():
    return render_template('index.html', snmp_data=None, interface_data=None)

@app.route('/ip_address', methods=['GET', 'POST'])
def get_ip_address():
    if request.method == 'POST':
        target_ip = request.form['ip_address']
        community_string = 'public'  # You can change this to the appropriate community string
        snmp_data = asyncio.run(get_snmp_data(target_ip, community_string))
        interface_data = asyncio.run(get_interface_data(target_ip, community_string))
        return render_template('index.html', snmp_data=snmp_data, interface_data=interface_data)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
