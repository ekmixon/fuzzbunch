
import dsz.lp.gui.terminal
import sys, os.path, os
import dsz.ui, dsz
import ops.cmd

def create_and_compile():
    bpfcompiler = f'{dsz.lp.GetResourcesDirectory()}/DSky/Tools/i386-winnt/BpfCompiler.exe'

    filterstring = dsz.ui.GetString('Please enter the filter to wish to use: ')
    netmaskstring = '255.255.255.0'
    try:
        os.makedirs(os.path.join(dsz.lp.GetLogsDirectory(), 'CompiledBpf', 'src'))
    except WindowsError:
        pass
    while 1:
        filtname = dsz.ui.GetString('What would you like to name the filter?')
        infasm = os.path.join(
            dsz.lp.GetLogsDirectory(), 'CompiledBpf', 'src', f'{filtname}.fasm'
        )

        outfilt = os.path.join(
            dsz.lp.GetLogsDirectory(), 'CompiledBpf', f'{filtname}.filt'
        )

        if os.path.exists(outfilt):
            dsz.ui.Echo(f'{outfilt} already exists, please choose another name', dsz.ERROR)
        else:
            break
    with open(infasm, 'w') as f:
        f.write(('filter:%s\n' % filterstring))
        f.write(f'netmask:{netmaskstring}')
    runcmd = ops.cmd.getDszCommand('local run -redirect')
    runcmd.command = ('"%s" -i "%s" -o "%s"' % (bpfcompiler, infasm, outfilt))
    runobject = runcmd.execute()
    output = runobject.processoutput[0].output.strip().replace('\n\n', '\n')
    if (runobject.processstatus.status != 0):
        dsz.ui.Echo('There was an error generating the filter', dsz.ERROR)
        dsz.ui.Echo(output, dsz.ERROR)
        return None
    else:
        dsz.ui.Echo('Compiled filter:', dsz.GOOD)
        for line in output.split('\n'):
            if line.startswith('0'):
                dsz.ui.Echo(line)
        dsz.ui.Echo(f'Compiled filter file: {outfilt}', dsz.GOOD)
    return True
if (__name__ == '__main__') and (create_and_compile() != True):
    sys.exit((-1))