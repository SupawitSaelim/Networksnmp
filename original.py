from pysnmp.hlapi.asyncio.slim import Slim
from pysnmp.smi.rfc1902 import ObjectIdentity, ObjectType
import asyncio

async def run():
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
        print(errorIndication)
    elif errorStatus:
        print(
            "{} at {}".format(
                errorStatus.prettyPrint(),
                errorIndex and varBinds[int(errorIndex) - 1][0] or "?",
            )
        )
    else:
        for varBind in varBinds:
            print(" = ".join([x.prettyPrint() for x in varBind]))

    slim.close()

asyncio.run(run())