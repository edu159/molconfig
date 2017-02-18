from multiprocessing import Process, Pipe
import pymol


class InjectedFunc():
    def __init__(self, func_name, func):
        self.func_name = func_name
        self.func = func

    def __call__(self, *args, **kwargs):
        new_args = (self.func_name, ) + args
        return self.func(*new_args, **kwargs)

class CMDPymol:
    
    def __init__(self):
        self._inject_cmd_functions()
        self.conn, self.child_conn = Pipe()
        self.pymol_process = CMDListener(self.child_conn)
        self.pymol_process.start()
         
           
    def _inject_cmd_functions(self):
        for m in dir(pymol.cmd):
            if callable(getattr(pymol.cmd, m)) and not (m.startswith('_') or m[0].isupper()):
                setattr(self, m, InjectedFunc(m, self._func))

    def _func(self, *args, **kwargs):
        self.conn.send((args, kwargs))
        ret = self.conn.recv()
        # If space is present the dictionary is copied back item by item :(.
        if "space" in kwargs.keys():
            for k,v in ret[1].items():
                kwargs["space"][k] = v
            return ret[0]
        return ret

        
class CMDListener(Process):

    def __init__(self, conn):
        Process.__init__(self)
        self.conn = conn

    def run(self):
        import __main__
        __main__.pymol_argv = ['pymol','-qxi'] # Pymol: quiet and no GUI
        reload(pymol)
        pymol.finish_launching()
        while True:
            cmd_info = self.conn.recv()
            func_name = cmd_info[0][0]
            args = cmd_info[0][1:]
            kwargs = cmd_info[1]
            func= getattr(pymol.cmd, func_name) 
            ret = func(*args, **kwargs)
            # Check that it exited gracefully
            if "space" in kwargs.keys():
                ret = (ret, kwargs["space"])

            self.conn.send(ret)
            if (func_name == "quit"):
                break
        return 

