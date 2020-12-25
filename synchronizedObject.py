import types

import types

def _get_method_names(obj):
    """ Get all methods of a class or instance, inherited or otherwise. """
    if type(obj) == types.InstanceType:
        return _get_method_names(obj.__class__)
    elif type(obj) == types.ClassType:
        result = []
        for name, func in obj.__dict__.items(  ):
            if type(func) == types.FunctionType:
                result.append((name, func))
        for base in obj.__bases__:
            result.extend(_get_method_names(base))
        return result


class _SynchronizedMethod:
    """ Wrap lock and release operations around a method call. """

    def __init__(self, method, obj, lock):
        self.__method = method
        self.__obj = obj
        self.__lock = lock

    def __call__(self, *args, **kwargs):
        self.__lock.acquire(  )
        try:
            return self.__method(self.__obj, *args, **kwargs)
        finally:
            self.__lock.release(  )


class SynchronizedObject:
    """ Wrap all methods of an object into _SynchronizedMethod instances. """

    def __init__(self, obj, ignore=[], lock=None):
        import threading

        # You must access __dict__ directly to avoid tickling __setattr__
        self.__dict__['_SynchronizedObject__methods'] = {}
        self.__dict__['_SynchronizedObject__obj'] = obj
        if not lock: lock = threading.RLock(  )
        for name, method in _get_method_names(obj):
            if not name in ignore and not self.__methods.has_key(name):
                self.__methods[name] = _SynchronizedMethod(method, obj, lock)

    def __getattr__(self, name):
        try:
            return self.__methods[name]
        except KeyError:
            return getattr(self.__obj, name)

    def __setattr__(self, name, value):
        setattr(self.__obj, name, value)
        
if __name__ == '__main__':
    import threading
    import time

    class Dummy:

        def foo (self):
            print 'hello from foo'
            time.sleep(5)

        def bar (self):
            print 'hello from bar'

        def baaz (self):
            print 'hello from baaz'

    tw = SynchronizedObject(Dummy(  ), ignore=['baaz'])
    threading.Thread(target=tw.foo).start(  )
    time.sleep(.1)
    threading.Thread(target=tw.bar).start(  )
    time.sleep(.1)
    threading.Thread(target=tw.baaz).start(  )


