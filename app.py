from flask import Flask, render_template, request, redirect, url_for
from pysnmp.hlapi.asyncio.slim import Slim
from pysnmp.smi.rfc1902 import ObjectIdentity, ObjectType
import asyncio
import subprocess

app = Flask(__name__)

port_status = {}
port_oids = {}
target_ip = ''

async def get_operational_status(target_ip, community_string, port_oid):
    slim = Slim(1)
    errorIndication, errorStatus, errorIndex, varBinds = await slim.get(
        community_string,
        target_ip,
        161,
        ObjectType(ObjectIdentity(port_oid))
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

    for port_number in range(10001, 10049):  # Generate OIDs for ports 10001 to 10048
        port_oid = "1.3.6.1.2.1.2.2.1.8." + str(port_number)
        operational_status = await get_operational_status(target_ip, community_string, port_oid)
        
        interface_oid = "1.3.6.1.2.1.2.2.1.2." + str(port_number)
        next_oid = ObjectType(ObjectIdentity(interface_oid))
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
            
            port_status[interface_name] = operational_status
            port_oids[interface_name] = port_oid

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
        global target_ip
        target_ip = request.form['ip_address']
        community_string = 'public'  # You can change this to the appropriate community string
        snmp_data = asyncio.run(get_snmp_data(target_ip, community_string))
        interface_data = asyncio.run(get_interface_data(target_ip, community_string))
        return render_template('index.html', snmp_data=snmp_data, interface_data=interface_data)
    return redirect(url_for('index'))

@app.route('/control_port', methods=['POST'])
def control_port():
    if request.method == 'POST':
        interface_name = request.form['interface_name']
        action = request.form['action']
        global target_ip
        #OID for port FastEthernet0/7: 1.3.6.1.2.1.2.2.1.8.10007
        #snmpset -v1 -c private 10.4.15.31 IF-MIB::ifAdminStatus.1 i 1
        
        print("OID for port {}: {}".format(interface_name, port_oids[interface_name]))
        
        port_status[interface_name] = action
        if action == 'on':
            action = 1
        elif action == 'off':
            action = 2

        
        command = 'snmpset -v1 -c private {} IF-MIB::ifAdminStatus.{} i {}'.format(target_ip, port_oids[interface_name].split('.')[-1], action)
        print(command)
        result = subprocess.run(command, shell=True, capture_output=True)
        print(result)
        print(result.stdout)
        print(result.stderr)
        return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
