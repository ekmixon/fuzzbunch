
from ops.pprint import pprint
import dsz.ui
import ops.cmd, ops.db, ops.project

def main():
    alltargetsallprojects = ops.project.getAllTargets()
    cmd = ops.cmd.getDszCommand('arp')
    cmd.optdict = {'query': True}
    arp = cmd.execute()
    if cmd.success:
        targetsup = []
        for arptgt in arp.entry:
            targetsup.extend(
                {
                    'proj': tgt.project.name,
                    'target': tgt.hostname,
                    'id': tgt.implant_id,
                    'ip': arptgt.ip,
                    'mac': arptgt.mac,
                    'interface': arptgt.adapter,
                }
                for tgt in alltargetsallprojects
                if (arptgt.mac.lower() in tgt.macs)
            )

        if targetsup:
            dsz.ui.Echo('Targets that are up', dsz.GOOD)
            pprint(targetsup, header=['Project', 'Target', 'Target ID', 'IP', 'MAC', 'Interface'], dictorder=['proj', 'target', 'id', 'ip', 'mac', 'interface'])
        else:
            dsz.ui.Echo("Doesn't look like anything is up", dsz.WARNING)
    else:
        dsz.ui.Echo(('arp -query failed. check command id %d ' % arp._cmdid), dsz.ERROR)
if (__name__ == '__main__'):
    main()