from flask import Flask, render_template, request, redirect, url_for
from pysnmp.hlapi.asyncio import setCmd, CommunityData, UdpTransportTarget, ContextData, ObjectIdentity
import asyncio

app = Flask(__name__)

# Your SNMP community string and target IP
community_string = 'private'  # Replace with your SNMP community string
target_ip = '10.4.15.31'  # Replace with your target IP

async def send_snmp_set(port_oid, value):
    errorIndication, errorStatus, errorIndex, varBinds = await setCmd(
        CommunityData(community_string),
        UdpTransportTarget((target_ip, 161)),
        ContextData(),
        ObjectIdentity(port_oid),
        value
    )

    if errorIndication:
        return f"SNMP SET request failed: {errorIndication}"
    elif errorStatus:
        return f"SNMP SET request failed: {errorStatus.prettyPrint()}"
    else:
        return "SNMP SET request successful"

if __name__ == '__main__':
    app.run(debug=True)