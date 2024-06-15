'''Module for manipulating data types, and creating new data types'''

import os, sys, re, copy, types, itertools, builtins 
import abc
import collections

# Dummy sentinel objects
DEFAULT_ARG = object()
NOT_SET = object()

reIsInt = re.compile('^[\d\-]+$')
reIsFloat = re.compile('^[e\d\-.]+$')
reCamelCaseToUI = re.compile('([A-Z][A-Z][a-z])|([a-z][A-Z])')


class cacheNode(object):
    cache = None
    def __new__(cls, type, key, cache=None, *args, **kwds):
        if cls.cache is None:
            if cache is not None:
                cls.cache = cache
            else:
                cls.cache = {}

        if type not in cls.cache:
            cls.cache[type] = {}

        if key not in cls.cache[type]:
            cls.cache[type][key] = object.__new__(cls)
            cls.cache[type][key].new = True

        else:
            cls.cache[type][key].new = False

        return cls.cache[type][key]

    @classmethod
    def clearCache(cls):
        cls.cache = None

class ReadOnlyError(Exception):
    ''' Read Only Error '''

class Decorator(object):
    __function__ = None

    instance = None
    owner = None

    def __init__(self, function=None, *args, **kwds):

        self.function = function

    def __get__(self, instance, owner):
        self.instance = instance
        self.owner = owner
        return self

    def __call__(self, *args, **kwds):
        if self.function is None:
            self.function = fi(args)
            return self

        else:
            if self.instance is not None:
                results = self.function(self.instance, *args, **kwds)
            else:
                results = self.function(*args, **kwds)

            return results

    def getFunction(self):
        return self.__function__
    def setFunction(self, function):
        if function is not None:
            # Update the attribute that identify the function
            for attr in ('__module__', '__name__', '__doc__'):
                if hasattr(function, attr):
                    setattr(self, attr, getattr(function, attr))
            for attr in ('__dict__',):
                if hasattr(function, attr):
                    getattr(self, attr).update(getattr(function, attr, {}))
        self.__function__ = function
    function = property(getFunction, setFunction)

class ReadOnlyDict(dict):
    '''
        Description:
            A dict where, once locked, is read only

            The locked state is determined by an internal
            varable __locked__ on the dict
    '''

    __locked__ = False

    def __init__(self, *args, **kwds):
        dict.__init__(self, *args, **kwds)
        self.__locked__ = True

    def __deepcopy__(self, *args, **kwds):
        result = {}
        for key, value in self.items():
            result[copy.deepcopy(key, *args, **kwds)] = copy.deepcopy(value, *args, **kwds)
        return result

    def __setitem__(self, key, item):
        if self.__locked__:
            raise ReadOnlyError('Dictionary is Read-Only')
        else:
            return dict.__setitem__(self, key, item)

    def __delitem__(self, key):
        if self.__locked__:
            raise ReadOnlyError('Dictionary is Read-Only')
        else:
            return dict.__delitem__(self, key)

    def __hash__(self):
        return hash(tuple(self.keys() + self.values()))

    def clear(self):
        if self.__locked__:
            raise ReadOnlyError('Dictionary is Read-Only')
        else:
            return dict.clear(self)

    def pop(self, key, *args):
        if self.__locked__:
            raise ReadOnlyError('Dictionary is Read-Only')
        else:
            return dict.pop(self, key, *args)

    def popitem(self):
        if self.__locked__:
            raise ReadOnlyError('Dictionary is Read-Only')
        else:
            return dict.popitem(self)

    def update(self, other):
        if self.__locked__:
            raise ReadOnlyError('Dictionary is Read-Only')
        else:
            return dict.update(self, other)

class OrderedDict(dict):
    '''
    Description:
        Dictionary where the order of keys/values is maintained.
    '''

    # This will hold the order for the dictionary
    __order__ = None

    def __init__(self, *items, **kwds):
        self.__order__ = []

        for item in items:
            if not isinstance(item, (list, tuple)):
                raise RuntimeError('Ordered dict expects a list of tuples: ' + str(items))

            key, value = item

            if not isinstance(key, str):
                raise KeyError('Key should be strings only: ' + str(key))

            # Store in the dict
            self[str(key)] = value

    def __nonzero__(self):
        return bool(self.__order__)

    def __contains__(self, key):
        return key in self.keys()

    def __copy__(self):
        return OrderedDict(*self.items())

    def __deepcopy__(self):
        return OrderedDict(*copy.deepcopy(self.items()))

    def __delitem__(self, key):
        if hasattr(self, key):
            delattr(self, key)
        if key in self:
            dict.__delitem__(self, key)
        if key in self.order:
            self.order.remove(key)

    def __getitem__(self, key):
        return dict.__getitem__(self, self.key(key))

    def __iter__(self):
        return iter(self.order)

    def __repr__(self):
        return str(self)

    def __setattr__(self, attr, value):
        # If attr is order then set it directly
        if attr in ('order', '__order__'):
            dict.__setattr__(self, attr, value)
        else:
            if attr in self:
                self.__setitem__(attr, value)
            else:
                dict.__setattr__(self, attr, value)

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        if isinstance(key, str):
            dict.__setattr__(self, key, value)

        # Add key to end of order if not already in dict
        if key not in self.order:
            self.order.append(key)

    def __str__(self):
        # add a Enum label
        results = '{'

        # Add each key=value
        results += ', '.join([quote(key) + ': ' + quote(self[key]) for key in self])

        # Add the close brakets
        results += '}'

        return results

    def clear(self):
        for key in self:
            del self[key]
        self.__order__ = []

    def copy(self):
        return self.__copy__()

    def index(self, value):
        index = None

        for key in self.keys():
            if value == self[key]:
                index = self.order.index(key)
                break
        else:
            raise ValueError(value)

        return index

    def items(self):
        results = []
        for key in self:
            results.append((key, self[key]))
        return results

    def key(self, key):
        # Get key for index
        if key not in self.order:
            if isinstance(key, int) and key < len(self.order):
                key = self.order[key]
            else:
                value = key
                for key in self.keys():
                    if value == self[key]:
                        break
                else:
                    raise KeyError(key)

        return key

    def keys(self):
        return list(self.order)

    def pop(self, key, default=None):
        value = dict.get(self, key, default)
        del self[key]
        return value

    def popitem(self):
        item = dict.popitem(self)
        del self[fi(item)]
        return item

    def setdefault(self, key, default=None):
        if key not in self:
            self[key] = default

        return self[key]

    def update(self, other):
        for key, value in other.items():
            self[key] = value

    def value(self, key):
        key = self.key(key) # Convert it to a key
        return self[key]

    def values(self):
        results = []
        for key in self:
            results.append(self[key])
        return results

    def getOrder(self):
        if self.__order__ is None:
            self.__order__ = []
        return self.__order__
    order = property(getOrder)

class Enum(OrderedDict):
    '''
    Description:
        Enumerated data class is a read-only ordered dictionary.

        You can supply a list of values or a list of key/value tuples/lists.
        If you don't give a value its index will be assumed.

        All keys should be strings and values can be anything

        All keys will also have an attribute counter part

        # You can simple supply a list of args
        >>> enum = Enum('one', 'two', 'three')
        >>> print enum
        Enum(one=0, two=1, three=2)

        # Or key/value pairs
        >>> enum = Enum(('one', 'foo'), ('two', 'bar'), ('three', 'baz'))
        >>> print enum
        Enum(one='foo', two='bar', three='baz')

        # Access the values by attributes
        >>> enum.one
        foo

        # Access the values by key
        >>> enum['two']
        bar

        # Access the values by index
        >>> enum[2]
        baz

        @DynamicAttrs
    '''

    __locked__ = False

    def __init__(self, *items, **kwds):

        # Determines if the item keys are auto generated based on the value in upper case format
        upper = kwds.get('upper', False)

        # Determines if the enum is one base
        oneBase = kwds.get('oneBase', False)

        # Auto index non-indexed items
        items = list(items)
        for index, item in enumerate(items):
            if not isinstance(item, (list, tuple)):

                if upper:
                    item = item

                elif oneBase:
                    item = item, index + 1
                else:
                    item = item, index

                items[index] = item
        OrderedDict.__init__(self, *items)

        # Make sure we lock the enum
        self.__locked__ = True

    def __contains__(self, key):
        return key in self.values()

    def __delitem__(self, item):
        if self.__locked__:
            raise RuntimeError('Enum\'s Keys/Values Are Read-Only!')

        OrderedDict.__delitem__(self, item)

    def __setattr__(self, attr, value):
        if self.__locked__:
            raise RuntimeError('Enum\'s Keys/Values Are Read-Only!')

        OrderedDict.__setattr__(self, attr, value)

    def __setitem__(self, item, value):
        if self.__locked__:
            raise RuntimeError('Enum\'s Keys/Values Are Read-Only!')

        OrderedDict.__setitem__(self, item, value)

    def __str__(self):
        # add a Enum label
        results = 'Enum('

        # Add each key=value
        for key in self:
            value = self[key]
            if isinstance(value, str):
                results += str(key) + '=\'' + str(value) + '\', '
            else:
                results += str(key) + '=' + str(value) + ', '

        # Remove the last comma and space
        results = fi(results.rsplit(', ', 1))

        # Add the close brakets
        results += ')'

        return results

    def clear(self, item, value):
        raise RuntimeError('Enum\'s Keys/Values Are Read-Only!')

    def copy(self, item, value):
        raise RuntimeError('Enum\'s Keys/Values Are Read-Only!')

    def pop(self, item, value):
        raise RuntimeError('Enum\'s Keys/Values Are Read-Only!')

    def popitem(self, item, value):
        raise RuntimeError('Enum\'s Keys/Values Are Read-Only!')

    def setdefault(self, item, value):
        raise RuntimeError('Enum\'s Keys/Values Are Read-Only!')

    def update(self, other):
        raise RuntimeError('Enum\'s Keys/Values Are Read-Only!')


class LimitedDict(collections.MutableMapping):
    """
    This dictionary restricts the number of entries to a defined limit

    Args:
        input (dict)
        limit (int)
    """
    def __init__(self, input=None, limit=0):
        if isType(input, [dict, collections.MutableMapping]):
            self._data = dict(input)

        elif input is not None:
            raise TypeError('input must be dict or None')

        else:
            self._data = {}

        self.limit = limit
        self._keys = collections.deque(self._data.keys())

    def __len__(self):
        return self._data.__len__()

    def __iter__(self):
        return self._data.__iter__()

    def __delitem__(self, key):
        if key in self._keys:
            self._keys.remove(key)

        self._data.__delitem__(key)

    def __setitem__(self, key, value):
        self._data.__setitem__(key, value)
        self._keys.append(key)
        self.resize()

    def __getitem__(self, key):
        return self._data.__getitem__(key)

    def __repr__(self):
        return self._data.__repr__()

    def resize(self):
        """
        Remove items until within the preset limit
        """
        keyLength = len(self._keys)
        if keyLength <= self.limit or self.limit <= 0:
            return

        for i in range(keyLength-self.limit):
            key = self._keys.popleft()
            self._data.pop(key, None)


class Command(object):
    '''
    Description:
        Command constructor used to hand back a callable instance with argument prebuilt in.
        This class operates much the same way as the builtin lambda function but added a bit more
        logic to resolve extra arguments pass into the resulting instance. This class will also
        resolve positional arguments on the callable instance such as #1, #2 ...

    Arguments:
        callback = callback to be used when calling the instance
        *args = default arguments to be used when calling the instance
        **kwds = default kwds to be used when calling the instance

    Extra Arguments:
        if the keyword '__extras__' is passed to either the constructor or the caller,
        extra arguments will be passed onto the given callback

        An 'extras' attribute will also be able to be accessable on the instance to change
        this behavior.

    Examples:
        # Test Function
        def testFunction(action, *args, **kwds):
            print action, args, kwds

        # Create a command pointer to testFunction with a default first argument
        cmd = Command(testFunction, 'button_clicked', path = '/var/tmp/default.ma')

        # Now you can execute the cmd
        cmd()

        # Addtional argument/keywords can be pass in if the '__extras__' is given
        # This will work as long ar your function supports the extra arguments
        cmd = Command(testFunction, 'button_clicked', path = '/var/tmp/default.ma', __extras__ = True)
        cmd('reference', path = '/var/tmp/test.ma')

        # --or--

        cmd = Command(testFunction, 'button_clicked', path = '/var/tmp/default.ma')
        cmd.extras = True
        cmd('reference', path = '/var/tmp/test.ma')
    '''

    # Add support for passing a command as a command
    __name__ = 'Command'

    callback = None
    args = None
    kwds = None
    extras = None

    # Compiled regex for searching for positional arguments
    positionalArgs = re.compile(r'^#(\d+)$')

    def __init__(self, callback, *args, **kwds):
        object.__init__(self)

        # First check to see if the callback is valid
        if not callable(callback):
            raise RuntimeError('Invalid callback given:', callback)

        self.callback = callback
        self.args = list(args)
        self.kwds = kwds

        # An 'extras' argument will turn on the combining of extra arguments/keywords
        self.extras = bool(self.kwds.pop('__extras__', False))

    def __build__(self, *extraArgs, **extraKwds):
        args = copy.copy(self.args)
        kwds = copy.copy(self.kwds)
        extras = self.extras or extraKwds.pop('__extras__', False)

        # Search through the arguments looking positional arguments
        # supplied by the calling function, i.e. #1, #2,...
        for index, arg in list(enumerate(args)):
            if isinstance(arg, str):
                positionalArg = fi(self.positionalArgs.findall(str(arg)))
                if positionalArg:
                    positionalArg = int(positionalArg)
                    if positionalArg and len(extraArgs) >= positionalArg:
                        extraArg = extraArgs[positionalArg - 1]

                        # Convert string bools to real python bools
                        if isinstance(extraArg, str) and extraArg.lower() in ('true', 'false'):
                            extraArg = eval(extraArg.title())

                        # Replace the arg with the extra arg
                        args[index] = extraArg

                        # Since a positional argument was found, Assume the user
                        # doesn't want extra arguments tacked on
                        extras = False

        # If the extras argument is true combine the arguments
        if extras:
            args.extend(list(extraArgs))
            kwds.update(extraKwds)

        return args, kwds

    def __call__(self, *extraArgs, **extraKwds):
        # Build the final args and kwds
        args, kwds = self.__build__(*extraArgs, **extraKwds)

        # Now execute the callback with the args and kwds
        results = self.callback(*args, **kwds)

        return results

    def __eq__(self, other):
        '''
        Description:
            Check to make sure other is equal to self
        '''

        if isinstance(other, Command):
            if self.callback == other.callback:
                if self.args == other.args:
                    if self.kwds == other.kwds:
                        if self.extras == other.extras:
                            return True

        return False

    def __repr__(self):
        return '<Command: ' + str(self) + ' >'

    def __str__(self):
        string = str(self.callback.__module__) + '.' + str(self.callback.__name__) + '('

        # Add args
        if self.args:
            for arg in self.args:
                if isinstance(arg, str):
                    string += '\'' + str(arg) + '\''
                else:
                    string += str(arg)
                string += ', '

            # Strip off the last comma and space
            string = string[:-2]

        # Add spacer if needed
        if self.args and self.kwds:
            string += ', '

        # Add kwds
        if self.kwds:
            for key, value in self.kwds.items():
                if isinstance(value, str):
                    string += str(key) + '=\'' + str(value) + '\''
                else:
                    string += str(key) + '=' + str(value)
                string += ', '

            # Strip off the last comma and space
            string = string[:-2]

        string += ')'

        return string

class ClassProperty(property):
    '''
    Description:
        Class which enables you to make properties out of classmethods
    '''

    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()

def quote(value):
    '''
    Description:
        Takes the given value and "qutoes" it to used in concatenation.

        So instead of this:
            cmd = 'myCommand(foo="' + str(foo) + '", bar="' + str(bar) + '")'

        You do this:
            cmd = 'myCommand(foo=' + quote(foo) + ', bar=' + quote(bar) + ')'

        Only values that are strings will be quoted.

        This is extreamly helpful when your argements, foo or bar in this case,
        can be both a string and something else like None, so you don't end up
        with foo="None" when it should actually be foo=None

        You can define a __quote__ method on the given object to define how the
        object should be quoted

    Parameters:
        [in] value: value to be quoted

    Returns:
        Quoted string
    '''
    if hasattr(value, '__quote__') and callable(getattr(value, '__quote__')):
        return str(value.__quote__())
    else:
        if isinstance(value, str):
            return "'" + str(value).encode('string_escape') + "'"
        else:
            return str(value)

def isBool(value):
    '''
    Description:
        Simple function that returns True or False based on if the given value is a bool

    Parameters:
        [in] value: value to check

    Returns:
        boolean
    '''
    return bool(isinstance(value, bool) or str(value).title() in ('True', 'False'))

def isInt(value):
    '''
    Description:
        Simple function that returns True or False based on if the given value is a int

    Parameters:
        [in] value: value to check

    Returns:
        boolean
    '''
    return bool(isinstance(value, int) or reIsInt.match(str(value)))

def isFloat(value):
    '''
    Description:
        Simple function that returns True or False based on if the given value is a int

    Parameters:
        [in] value: value to check

    Returns:
        boolean
    '''
    return bool(isinstance(value, float) or reIsFloat.match(str(value)))

def convertValue(value):
    if isBool(value):
        value = bool(value)
    elif isInt(value):
        value = int(value)
    elif isFloat(value):
        value = float(value)
    return value

def fi(items, default=None):
    '''
    Description:
        Returns the first item in the given list. The function name comes
        from (f)irst (i)tem.

    Parameters:
        [in] items: the list to act upon
        [in] default: the default return value if the list is empty

    Returns:
        The first item in the list

    Examples:
        import mo.wt.utils.type
        print mo.wt.utils.type.fi([1, 2, 3])
        # Result: 1
        print mo.wt.utils.type.fi([])
        # Result: None
    '''

    for attr in ('__len__', '__getitem__'):
        if not hasattr(items, attr):
            items = asList(items)
            break

    if len(items):
        return items[0]
    else:
        return default

def li(items, default=None):
    '''
    Description:
        Returns the last item in the given list. The function name comes
        from (l)ast (i)tem.

    Parameters:
        [in] list: the list to act upon
        [in] default: the default return value if the list is empty

    Returns:
        The last item in the list

    Examples:
        import mo.wt.utils.type
        print mo.wt.utils.type.li([1, 2, 3])
        # Result: 3
        print mo.wt.utils.type.li([])
        # Result: None
    '''

    for attr in ('__len__', '__getitem__'):
        if not hasattr(items, attr):
            items = asList(items)
            break

    if len(items):
        return items[-1]
    else:
        return default

def asList(arg):
    '''
    Description:
        Converts the given argument to a list

    Parameters:
        [in] arg: the argument to convert

    Returns:
        The input argument as a list

    Examples:
        import mo.wt.utils.type
        print mo.wt.utils.type.asList('test')
        # Result: ['test']
        print mo.wt.utils.type.asList([1, 2, 3])
        # Result: [1, 2, 3]
    '''

    if isinstance(arg, list):
        ''' already a list '''
        args = arg
    elif isinstance(arg, tuple):
        args = list(arg)
    elif type(arg) == types.NoneType:
        args = []
    else:
        args = [arg]

    return args

def asListOfLists(arg):
    '''
    Description:
        Converts the given argument to a list of lists.

    Parameters:
        [in] arg: the argument to convert

    Returns:
        The input argument as a list of lists. If the input arg is None, then
        just a list is returned

    Examples:
        import mo.wt.utils.type
        print mo.wt.utils.type.asListOfLists(None)
        # Result: []
        print mo.wt.utils.type.asListOfLists('test')
        # Result: [['test']]
        print mo.wt.utils.type.asListOfLists([255, 255, 255])
        # Result: [[255, 255, 255]]
        print mo.wt.utils.type.asListOfLists([(0, 0, 0), (255, 255, 255)])
        # Result: [(0, 0, 0), (255, 255, 255)]
    '''

    args = asList(arg)

    for arg in args:
        if not isinstance(arg, (list, tuple)):
            args = [args]
            break

    return args

def listIntersection(list1, list2):
    '''Return the intersection of two lists.'''

    set1 = set(list1)
    set2 = set(list2)
    return list(set1.intersection(set2))

def listDifference(list1, list2):
    '''Return the difference between two lists,
    i.e. subtract the second list from the first.
    Note that list1 - list2 != list2 - list1.'''

    set1 = set(list1)
    set2 = set(list2)
    return list(set1.difference(set2))

def flattenDictOfLists(dictionary, keys=None):
    '''
    Description:
        Takes a dictionary of lists and extracts the values of the given keys
        into a new list

    Parameters:
        [in] dictionary: the dictionary to combine
        [in] keys: a list of keys to use from the dictionary. If not supplied,
                   all keys in the dictionary are used.

    Returns:
        A flat list of all the items in the dictionary.

    Examples:
        import mo.wt.utils.type
        dict = {'a':[1,2,3], 'b':[4,5,6], 'c':[7,8,9]}
        print mo.wt.utils.type.flattenDictOfLists(dict)
        # Result: [1, 2, 3, 4, 5, 6, 7, 8, 9]
        print mo.wt.utils.type.flattenDictOfLists(dict, keys=['a', 'c'])
        # Result: [1, 2, 3, 7, 8, 9]
    '''

    results = []

    keys = asList(keys)
    if not keys:
        keys = sorted(dictionary.keys())

    for key in keys:
        items = dictionary[key]
        if not isinstance(items, (list, tuple)):
            raise RuntimeError(str(items) + ' is a ' + str(type(items)) + '. Expected a list or a tuple. Input dictionary is: ' + str(dictionary))
        for item in items:
            if item not in results:
                results.append(item)

    return sorted(set(results))

def flattenListOfDicts(inputList, keys=None, cleanup=False):
    '''
    Description:
        Takes a list of dictionaries and extracts the values of the given keys
        into a new list

    Parameters:
        [in] dictionary: the dictionary to combine
        [in] keys: a list of keys to use from the dictionary. If not supplied,
                   all keys in the dictionary are used.
        [in] cleanup: if True, exclude values of None from the result

    Returns:
        A flat list of all the items in the dictionary.

    Examples:
        import mo.wt.utils.type
        dict1 = {'one':1, 'two':2}
        dict2 = {'one':11, 'two':22}
        print mo.wt.utils.type.flattenListOfDicts([dict1, dict2], 'two')
        # Result: [2, 22]
        print mo.wt.utils.type.flattenListOfDicts([dict1, dict2], keys=['one', 'two'])
        # Result: [(1, 2), (11, 22)]
    '''

    results = []

    if not keys:
        raise RuntimeError('No keys supplied!')

    keys = asList(keys)

    for dictionary in inputList:

        if not isinstance(dictionary, dict):
            raise RuntimeError(str(dictionary) + ' is not a dictionary, its a ' + str(type(dictionary)) + '. Invalid input list: ' + str(inputList))

        # Get the value for each key in the dictionary
        values = []
        for key in keys:
            value = dictionary.get(key, None)

            # Need to convert these types to something that is hashable in order
            # to use them as keys to a dictionary
            if isinstance(value, (dict, list)):
                value = tuple(value)

            values.append(value)

        # Get a value from the values
        if len(values) == 1:
            value = fi(values)
        else:
            value = tuple(values)

        if cleanup and value is None:
            continue

        # Add the value to the results
        results.append(value)

    return results

def flattenListOfLists(listOfLists):
    '''
    Description:
        Takes a list of lists and returns a flattened list

    Parameters:
        [in] list: the list to flatten

    Returns:
        A flat list

    Examples:
        import mo.wt.utils.type
        print mo.wt.utils.type.flattenListOfLists([[1, 2], [3, 4], [5, 6]])
        # Result: [1, 2, 3, 4, 5, 6]
    '''

    results = []
    for l in listOfLists:
        if l:
            if isinstance(l, (list, tuple)):
                results.extend(l)
            else:
                results.append(l)

    return results


def arrayRemove(list1, list2):
    '''
    Description: remove items in list2 from list1

    Paramters: [in] list1: first list
               [in] list2: subset to remove from first list

    Returns: subset list
    '''
    return [item for item in list1 if not item in list2]


def groupDicts(inputList, keys=None):
    '''
    Description:
        Groups a list of dictionaries by the keys supplied.

    Parameters:
        [in] inputList: a list of dictionaries
        [in] keys: a list of keys to use from the dictionary. If not supplied,
                   all keys in the dictionary are used.

    Returns:
        A dictionary whose keys are the values of the given keys. The values
        are a list of dictionaries whose values of the given keys are equal.

    Examples:
        import mo.wt.utils.type
        dict1 = {'one':1, 'two':2}
        dict2 = {'one':11, 'two':22}
        test = [dict1, dict2]
        print mo.wt.utils.type.groupDicts(test, 'two')
        # Result: {2: [{'two': 2, 'one': 1}], 22: [{'two': 22, 'one': 11}]}
        print mo.wt.utils.type.groupDicts(test, ['one','two'])
        # Result: {(1, 2): [{'two': 2, 'one': 1}], (11, 22): [{'two': 22, 'one': 11}]}
    '''

    results = {}

    if not keys:
        raise RuntimeError('No keys supplied!')

    keys = asList(keys)

    for dictionary in inputList:

        if not isinstance(dictionary, dict):
            raise RuntimeError(str(dictionary) + ' is not a dictionary, its a ' + str(type(dictionary)) + '. Invalid input list: ' + str(inputList))

        # Get the value for each key in the dictionary
        values = []
        for key in keys:
            value = dictionary.get(key, None)

            # Need to convert these types to something that is hashable in order
            # to use them as keys to a dictionary
            if isinstance(value, (dict, list)):
                value = tuple(value)

            values.append(value)

        # Get a key from the values
        if len(values) == 1:
            key = fi(values)
        else:
            key = tuple(values)

        # If the key doesn't exist create it with a list as its value
        if key not in results:
            results[key] = []

        results[key].append(dictionary)

    return results

def invertDict(dict):
    '''
        Description:
            Takes the given dictionary and inverts the keys and values

        Parameters:


        Returns:

    '''

    results = {}
    for key, value in dict.items():
        if value in results:
            print ('WARNING: Multiple values for key while inverting: {value}'.format(value=value))
        results[value] = key
    return results

def dictCombinations(dict):
    '''
        Description:
            Given a dictionary of values/list of values
            generate all combinations of the dict

        Parameters:
            [in] dict: dict to generate combinations for

        Returns:
            list of dict combinations

        Examples:
            dictCombinations({'one':[1,11,111], 'two':['2','22'], 'three':'3'})
            # Result: [{'three': '3', 'two': '2', 'one': 1},
                       {'three': '3', 'two': '22', 'one': 1},
                       {'three': '3', 'two': '2', 'one': 11},
                       {'three': '3', 'two': '22', 'one': 11},
                       {'three': '3', 'two': '2', 'one': 111},
                       {'three': '3', 'two': '22', 'one': 111}]
    '''

    results = []

    keys = sorted(dict)
    values = [asList(dict[key]) for key in keys]
    for product in itertools.product(*values):
        result = builtins .dict(zip(keys, product))
        if result not in results:
            results.append(result)

    return results



def resolveArgs(*args, **kwds):
    '''
    Description:
        Takes the input arguments and returns the first value that doesn't
        evaluate to None. This is useful for functions that support and long
        and short name parameters.

    Parameters:
        [in] *args:
        [in] **kwds:

    Returns:
        The first valid argument

    Examples:
        import mo.wt.utils.type
        def test(s=None, shortName=None): print mo.wt.utils.type.resolveArgs(s, shortName)
        test(s='foo', shortName='bar')
        # Result: foo
        test(s='')
        # Result:
        test(s=None, shortName=False)
        # Result: False
    '''

    results = None

    for arg in args:
        if arg is not None:
            results = arg
            if results: # Continue if results evaluates to False
                break

    if results is None:
        results = kwds.pop('default', None)

    return results

def dictToFlags(flagDict, quoteString='"'):
    '''
    Description
        Convert a dictionary into a string of flags and values which can be used
        as options in a shell command. The values in the dictionary are processed
        differently depending on their type.

        ***** Strings *****

        String values are processed as-is, but wrapped with the quoteString.
        For example:

            {'frameRange': '1-50'}

        would become:

            -frameRange '1-50'

        ***** Integers *****

        Integer values are processed as-is:

            {'local': 1}

        would become:

            -local 1

        ***** Booleans *****

        Boolean values that are True, will cause the option to appear in the
        return string:

            {'verbose': True}

        would become:

            -verbose

        Boolean flags that are False will be omitted from the return string.

        ***** Lists *****

        Lists are reserved for multi-use options. For example:

            {'need': ['mtd-nover_primary', 'taisukeDev']}

        would become:

            -need mtd-nover_primary -need taisukeDev

        ***** Tuples *****

        Tuples are reserved for single options with multiple values. The last
        element in the tuple can be used to specify a delimiter. Delimiters
        come from a limited set, which are defined in the code below.

            {'colour': (255,255,0,',')}

        would become:

            -colour 255,255,0

    Paramters:
        [in] flagDict: the dictionary to convert
        [in] quoteString: the string to enclose string values in

    Returns
        The option string
    '''

    result = ''
    for key, value in flagDict.iteritems():

        if type(value) == types.BooleanType:
            if not value: # If the option is False, then ignore it
                continue
            result += '-' + key + ' '

        elif type(value) == types.ListType:
            for item in value:
                if type(item) in types.StringTypes:
                    item = quoteString + item + quoteString
                result += '-' + key + ' ' + str(item) + ' '

        elif type(value) == types.TupleType:
            value = list(value)

            delimiter = value[-1]
            if delimiter in [' ', ',', ', ']: # These are valid delimiters
                value.pop()
            else:
                delimiter = ' '

            for i in range(len(value)):
                if type(value[i]) in types.StringTypes:
                    value[i] = quoteString + value[i] + quoteString

            result += '-' + key + ' ' + delimiter.join(value)

        else:

            result += '-' + key + ' '

            if type(value) in types.StringTypes:
                result += quoteString + value + quoteString + ' '
            else:
                result += str(value) + ' '

    return result


#       staticmethods and classmethods aren't callable for some reason
#       until the functions are compiled, so here we are explicitly
#       including them here
def callable(function):
    return __builtins__['callable'](function) or type(function) in (staticmethod, classmethod)

def getDictionaryMaxDepth(d):
    '''
    Description:
        recursive function that, given a dictionary of dictionaries, will return the maximum depth reached
        useful for building data structures around dictionaries

    Parameters:
        [in] d: dictionary to count depth

    Returns:
        the lowest "depth" of nested dictionary, for example
            data = {'apes': {'a category 1': {'asset': {'layoutVariant': {'version1': {'stage': 'True'}, 'version2': {'stage': 'True'} }}}}, \
            'tnn':{'apes category 1': {'asset1': {'layoutVariant': {'version': {'stage': 'True'}}}, \
                                        'asset2': {'layoutVariant 1': {'version': {'stage': 'True'}}, \
                                                    'layoutVariant 2': {'version': {'stage': 'True'}} }} }}

        returns 6
    '''
    depths = []
    for k,v in d.items():
        if isinstance(v, dict):
            depths.append(getDictionaryMaxDepth(v))
    if len(depths) > 0:
        return 1 + max(depths)
    return 1

def getKeyValueLevel(data, level=None, index=1):
    '''
    Description:


    Parameters:
        [in] data:
        [in] level:
        [in] index:

    Returns:
        dict representation of class
    '''
    if type(data) is not dict:
        print ('steppedKeyValue: Error: please pass a dict: ', type(data))

    for k, v in data.items():
        #print 'type: ', k, ' children: ', v
        if type(v) is dict:
            #print 'index: ', index
            #print 'level: ', level
            if level and index < level:
                getKeyValueLevel(data=v, level=level, index=index+1)
    return data

class Ddict(dict):
    ''' Simplified defaultdict, currently it would be better to use collections.defaultdict until this is flushed out'''
    def __init__(self, default=None):
        self.default = default

    def __getitem__(self, key):
        if not self.has_key(key):
            self[key] = self.default()
        return dict.__getitem__(self, key)

def ClassToDict(o):
    '''
    Description:
        Return a dictionary from object that has public variable -> key pairs

    Parameters:
        [in] o: class instance to parse

    Returns:
        dict representation of class
    '''

    dict = {}
    # This is "almost" an unnecessary function; all the attributes in a class are already in __dict__
    for elem in o.__dict__.keys():
        if elem.find("_" + o.__class__.__name__) == 0:
            continue
            # We discard private variables, which are automatically named _ClassName__variablename
            # when we define it in the class as __variablename
        else:
            dict[elem] = o.__dict__[elem]
    return dict

def DictToClass(d):
    '''
    Description:
        Return a class that has same attributes/values and dictionaries key/value

    Parameters:
        [in] d: dict to turn into a class

    Returns:
        class built of attributes past in from key/value pairs
    '''

    # see if it is indeed a dictionary
    if type(d) is not types.DictType:
        print ('Error: Did not pass a dictionary to DictToClass()')
        return None

    # define a dummy class
    class Dummy:
        pass

    c = Dummy
    for elem in d.keys():
        c.__dict__[elem] = d[elem]
    return c


class DefaultDictBase(dict):
    '''Dictionary with a default value for unknown keys.'''
    def __init__(self, default=None, *args, **kwargs):
        self.default = default
        self.update(dict(*args, **kwargs))
    #def __missing__(self, key):
    #    result = self[key] = DefaultDictBase()
    #    return result

class DefaultDictCopy(DefaultDictBase):
    '''DefaultDict that copies its default value '''
    def __getitem__(self, key):
        if key in self:
            return self.get(key)
        return self.setdefault(key, copy.deepcopy(self.default))

class DefaultDictNoCopy(DefaultDictBase):
    ''' DefaultDict that uses its default value as is. This is about 7 times faster than copying '''
    def __getitem__(self, key):
        return self.setdefault(key, self.default)

def defaultDict(default=None,*args,**kwargs):
    "create a DefaultDict suitable for the given default"
    if id(default)==id(copy.deepcopy(default)):
        return DefaultDictNoCopy(default,*args,**kwargs)
    return DefaultDictCopy(default,*args,**kwargs)

def uniqifyList(l=None, preserveOrder=True, reverseUniqifyOrder=True):
    '''
    Description:
        Returns a list with only unique items

    Parameters:
        [in] l: list to operate on
        [in] preserveOrder: setting this to False makes it run twice as fast, but does not preserve list order
        [in] reverseUniqifyOrder: determines whether to return a list that uniqifies from the back or the front - this only works with preserve order

    Returns:
        uniqified list
    '''
    l = copy.deepcopy(l)

    if reverseUniqifyOrder: l.reverse()

    if l is None: return
    if type(l) is not list:
        raise RuntimeError('Error: First argument must be a list')

    # Preserve List Order
    if preserveOrder:
        # abusing function attrs :D
        def idfun(x): return x
        seen = {}
        result = []
        for item in l:
            marker = idfun(item)
            if marker in seen: continue
            seen[marker] = 1
            result.append(item)
        if reverseUniqifyOrder:
            result.reverse()
            return result
        else:
            return result

    # Twice as fast, does not preserve uniqifyOrder
    else:
        set = {}
        map(set.__setitem__, l, [])
        return set.keys()


def sortListtByNthField(l, n):
    '''
    Description:
        Sorts a list by the nth value of sequences in the list
        for example, in a list of tuples, you wanted to sort a list by the nth value of a tuple

    Parameters:
        [in] l: list to operate on
        [in] n: value to operate on inside sequence in the list

    Returns:
        sorted list
    '''
    nList = [(x[n], x) for x in l]
    nList.sort()
    return [val for (key, val) in nList]

class AttrDict(dict):
    """ A dictionary type which allows direct attribute access to its keys """

    def __getattr__(self, name):

        if name in self.__dict__:
            return self.__dict__[name]
        elif name in self:
            return self.get(name)
        else:
            # Check for wtStringUtils.denormalized name
            name = denormalize(name)
            if name in self:
                return self.get(name)
            else:
                raise AttributeError('no attribute named %s' % name)

    def __setattr__(self, name, value):

        if name in self.__dict__:
            self.__dict__[name] = value
        elif name in self:
            self[name] = value
        else:
            # Check for wtStringUtils.denormalized name
            name2 = denormalize(name)
            if name2 in self:
                self[name2] = value
            else:
                # New attribute
                self[name] = value

class CompositeDict(AttrDict):
    ''' A class which works like a hierarchical dictionary, based on the Composite design pattern '''

    ID = 0

    def __init__(self, name=None):

        if name:
            self._name = name
            print ('self._name: ', self._name)

        else:
            print ('str(self.__class__.ID): ', str(self.__class__.ID))

            self._name = ''.join(('id#',str(self.__class__.ID)))
            self.__class__.ID += 1

        self._children = []
        # Link  back to parent
        self.parent = None
        self[self._name] =  AttrDict()

    def __getattr__(self, name):

        if name in self.__dict__:
            return self.__dict__[name]
        elif name in self:
            return self.get(name)
        else:
            # Check for wtStringUtils.denormalized name
            name = denormalize(name)
            if name in self:
                return self.get(name)
            else:
                # Look in children list
                child = self.findChild(name)
                if child:
                    return child
                else:
                    attr = getattr(self[self._name], name)
                    print ('attr: ', attr)
                    if attr:
                        return attr

                    raise AttributeError('no attribute named %s' % name)

    def isRoot(self):
        """ Return whether I am a root component or not """

        # If I don't have a parent, I am root
        return not self.parent

    def isLeaf(self):
        """ Return whether I am a leaf component or not """

        # I am a leaf if I have no children
        return not self._children

    def getName(self):
        """ Return the name of this ConfigInfo object """

        return self._name

    def getIndex(self, child):
        """ Return the index of the child ConfigInfo object 'child' """

        if child in self._children:
            return self._children.index(child)
        else:
            return -1

    def getDict(self):
        """ Return the contained dictionary """

        return self[self._name]

    def getProperty(self, child, key):
        """ Return the value for the property for child 'child' with key 'key' """

        # First get the child's dictionary
        childDict = self.getInfoDict(child)
        if childDict:
            return childDict.get(key, None)

    def setProperty(self, child, key, value):
        """ Set the value for the property 'key' for
        the child 'child' to 'value' """

        # First get the child's dictionary
        childDict = self.getInfoDict(child)
        if childDict:
            childDict[key] = value

    def getChildren(self):
        """ Return the list of immediate children of this object """

        return self._children

    def getAllChildren(self):
        """ Return the list of all children of this object """

        l = []
        for child in self._children:
            l.append(child)
            l.extend(child.getAllChildren())

        return l

    def getChild(self, name):
        """ Return the immediate child object with the given name """

        for child in self._children:
            if child.getName() == name:
                return child

    def findChild(self, name):
        """ Return the child with the given name from the tree """

        # Note - this returns the first child of the given name
        # any other children with similar names down the tree
        # is not considered.

        for child in self.getAllChildren():
            if child.getName() == name:
                return child

    def findChildren(self, name):
        """ Return a list of children with the given name from the tree """

        # Note: this returns a list of all the children of a given
        # name, irrespective of the depth of look-up.

        children = []

        for child in self.getAllChildren():
            if child.getName() == name:
                children.append(child)

        return children

    def getPropertyDict(self):
        """ Return the property dictionary """

        d = self.getChild('__properties')
        if d:
            return d.getDict()
        else:
            return {}

    def getParent(self):
        """ Return the person who created me """

        return self.parent

    def __setChildDict(self, child):
        """ Private method to set the dictionary of the child
        object 'child' in the internal dictionary """

        d = self[self._name]
        d[child.getName()] = child.getDict()

    def setParent(self, parent):
        """ Set the parent object of myself """

        # This should be ideally called only once
        # by the parent when creating the child :-)
        # though it is possible to change parenthood
        # when a new child is adopted in the place
        # of an existing one - in that case the existing
        # child is orphaned - see addChild and addChild2
        # methods !
        self.parent = parent

    def setName(self, name):
        """ Set the name of this ConfigInfo object to 'name' """

        self._name = name

    def setDict(self, d):
        """ Set the contained dictionary """

        self[self._name] = d.copy()

    def setAttribute(self, name, value):
        """ Set a name value pair in the contained dictionary """

        self[self._name][name] = value

    def getAttribute(self, name):
        """ Return value of an attribute from the contained dictionary """

        return self[self._name][name]

    def addChild(self, name, force=False):
        """ Add a new child 'child' with the name 'name'.
        If the optional flag 'force' is set to True, the
        child object is overwritten if it is already there.

        This function returns the child object, whether
        new or existing """

        if type(name) != str:
            raise ValueError('Argument should be a string!')

        child = self.getChild(name)
        if child:
            # print 'Child %s present!' % name
            # Replace it if force==True
            if force:
                index = self.getIndex(child)
                if index != -1:
                    child = self.__class__(name)
                    self._children[index] = child
                    child.setParent(self)

                    self.__setChildDict(child)
            return child
        else:
            child = self.__class__(name)
            child.setParent(self)

            self._children.append(child)
            self.__setChildDict(child)
            return child


def denormalize(val):
    ''' De-normalize a string so we can use it as a python object '''

    if val.find('_') != -1:
        val = val.replace('_', '-')
    return val


def normalize(val):
    ''' normalize, in case it needs to be brought back to original state from denormalize '''

    if val.find('-') != -1:
        val = val.replace('-', '_')
    return val


def camelCaseToUI(camelCase):
    '''
    Description:
        Adds spaces to a camel case string.
        Failure to space out string returns the original string.

    Parameters:
        [in] camelCase: camel case string to convert

    Returns:
        camel case converted to ui compatiable string

    Examples:
        >>> camelCaseToUI('camelCase')
        Camel Case
    '''

    if camelCase is not None:
        return reCamelCaseToUI.sub(lambda match: match.group()[:1] + ' ' + match.group()[1:], camelCase).title()


def Print(*values):
    '''
    Description:
        Simple function used to print stuff. useful for doing delayed print via the
        Command class above

    Parameters:
        [in] *values: any argument passed in will be catured and printed
    '''

    for value in values:
        print (value,print)

def dictSubset(d, keys, dictObject=dict):
    """
    Returns a subset of a dictionary using the supplied keys
    if keys is a dictionary, we look for the key and assign it to the value
    If the value is None, use the key
    eg:
    keys = {"keyToLookFor": "outputKeyName", "defaultKey": None}
    returns {"outputKeyName": value, "defaultKey, value}

    IN:
        [dict] d
        [list] keys
    """
    result = dictObject()
    if issubclass(type(keys), dict):
        for key, value in keys.items():
            if not key in d.keys():
                continue

            if value is None:
                result[key] = d.get(key)

            else:
                result[value] = d.get(key)

    else:
        keys = asList(keys)

        for key in keys:
            if not key in d.keys():
                continue

            result[key] = d.get(key)

    return result

def isType(value, types):
    types = asList(types)

    for t in types:
        if issubclass(type(value), t):
            return True

        if type(value).__module__ == t.__module__ and type(value).__name__ == t.__name__:
            # it has been derived
            return True

    return False

def asStrInput(input):
    if isType(input, str):
        return "'{0}'".format(input)

    return str(input)


def parseArgs(*args, **kwargs):
    for arg in args:
        if arg is None:
            continue

        return arg

    if kwargs and "default" in kwargs.keys():
        return kwargs.get("default")

    return None


def asBool(value):
    value = fi(value)
    if isType(value, str):
        if value.lower() == "true":
            return True

        elif value.lower() == "false":
            return False

    try:
        return bool(value)

    except:
        return False


def asDict(value):
    if isType(value, dict):
        return value

    if isType(value, [list, tuple]):
        # if len(value) == 2:
        #     return {value[0]: value[1]}

        result = {}
        for item in value:
            result[item] = None

        return result

    return {value: None}

def functionToString(function, args=None, kwargs=None):
    if isinstance(function, str):
        name = function

    else:
        name = function.__name__

    if not args and not kwargs:
        result = "{0}()".format(name)
        return (result, result)

    result = "{0}(".format(name)
    typedResult = result
    index = 0
    if args:
        args = asList(args)
        for arg in args:
            if index == 0:
                result += asStrInput(arg)
                typedResult += str(type(arg).__name__)

            else:
                result += ", {0}".format(asStrInput(arg))
                typedResult += ", " + str(type(arg).__name__)

            index += 1

    if kwargs and issubclass(type(kwargs), dict):
        for key, value in kwargs.items():
            if index == 0:
                result += "{0}={1}".format(key, asStrInput(value))
                typedResult += "{0} {1}".format(str(type(value).__name__), key)

            else:
                result += ", {0}={1}".format(key, asStrInput(value))
                typedResult += ", {0} {1}".format(str(type(value).__name__), key)

            index += 1

    result += ")"
    typedResult += ")"

    return (result, typedResult)

def chunks(theList, chunkSize):
    '''
    Yield successive n-sized chunks from list theList.
    Useful for breaking up a large list into chunks of
    '''
    for i in range(0, len(theList), chunkSize):
        yield theList[i:i + chunkSize]


def objListToDict(objList, fn):
    '''
    Take a list of objects and return them as a dictionary
    based on the passed variable name
    if fn is a function, the obj will be passed to the function fn(obj)
    otherwise it will get the attribute. getattr(obj, fn)

    examples:
        objListToDict(objs, 'variable')
        objListToDict(objs, lambda x: x.getCustomKey())

    IN:
        [list]     objList
        [str/func] fn

    OUT:
        [dict]
    '''
    d = dict()
    isCallable = callable(fn)
    for obj in objList:
        if isCallable:
            key = fn(obj)

        else:
            key = getattr(obj, fn)

        if key not in d:
            d[key] = [obj]
            continue

        d[key].append(obj)

    return d


def isWithinTolerance(*args, **kwargs):
    '''
    ..py:function:isWithinTolerance(*args, tolerance=0.01)
    Checks that all args are within the tolerance of each other

    :param list args: list of floats to check
    :param float tolerance: tolerance value, default=0.01
    :returns: within tolerance
    :rtype: float
    :raises TypeError: If args is not numeric
    '''
    tol = kwargs.get('tolerance', 0.01)
    return max(args) - min(args) < tol


class Callable(abc.ABC):
    '''
    This is a callable python class that behaves like a function
    arguments passed are passed to the __init__ and __call__ method
    You must overload the __call__ method, but the __init__ is optional

    These two examples behave the same:
        class add(Callable):
            def __init__(self, a, b):
                self.a = a
                self.b = b

            def __call__(self, *args, **kwargs):
                return (self.a + self.b)

        add(1, 2)
        >> 3

        class add(Callable):
            def __call__(self, a, b):
                return a + b

        add(1, 2)
        >> 3
    '''
    __metaclass__ = abc.ABCMeta

    def __new__(cls, *args, **kwargs):
        instance = super(Callable, cls).__new__(cls)
        instance.__init__()
        try:
            return instance(*args, **kwargs)

        except Exception as e:
            if str(e).startswith('__call__'):
                raise type(e)(cls.__name__ + '()' + str(e)[10:])
            raise e

    @abc.abstractmethod
    def __call__(self):
        pass


def asNamedTuple(*args, **kwargs):
    '''
    Convert a set of args to be used as an ordered namedtuple
    This is useful in returning multiple args from a function
    results still behave like a tuple, but now get more readable attribute access

    Args:
        *args: positional values
        keys (Sequence): List of keys to match to positional values
        name (Optional(str)): Name for the tuple, default='Output'

    Returns:
        tuple: A namedtuple

    Raises:
        TypeError: If keys/args do not match, keys is not specified or unexpected kwargs

    Examples:
        >>> result = asNamedTuple(10, 12, 38, keys=('rows', 'columns', 'children'), name='Test')
        >>> print result
        Test(rows=10, columns=12, children=38)
        >>> print result.rows
        10
        >>> print result[1]
        12
    '''
    keys = kwargs.pop('keys', None)
    if not keys:
        raise TypeError('asNamedTuple missing "keys" arg')

    if not isinstance(keys, collections.Sequence):
        raise TypeError('keys expected a list, got {0}'.format(type(keys)))

    name = kwargs.pop('name', 'Output')
    if kwargs.keys():
        raise TypeError('asNamedTuple got unexpected keywords: {0}'.format(', '.join(kwargs.keys())))

    if not len(keys) == len(args):
        raise TypeError('asNamedTuple got {0} args, expected {1}'.format(len(args), len(keys)))

    obj = collections.namedtuple(name, keys)
    return obj(**{key: args[i] for i, key in enumerate(keys)})


class ExtendedTuple(tuple):
    '''
    This can be subclassed to replace namedtuples that require validation
    initialize the fields property for allowed fields
    super the validateInputs classmethod if you require additional validation
    '''
    __metaclass__ = abc.ABCMeta
    __slots__ = ()

    @abc.abstractproperty
    def fields(self):
        '''
        Return a tuple of allowed inputs
        '''
        return

    def __new__(cls, *args, **kwargs):
        kwargs = cls.validateInputs(args, kwargs)
        values = [kwargs[key] for key in cls.fields]
        if len(values) == 1:
            values = tuple([values])

        return tuple.__new__(cls, values)

    @classmethod
    def validateInputs(cls, args, kwargs):
        '''
        Ensure that we have a valid dictionary of inputs

        Args:
            args (list): args to validate
            kwargs (dict): kwargs to validate

        Returns:
            dict: modified kwargs

        Raises:
            TypeError: If args fail validation
        '''
        className = cls.__name__
        numArgs = len(args)
        numFields = len(cls.fields)
        if numArgs > numFields:
            msg = '{0} got {1} positional args, max {2}'.format(
                className, numArgs, numFields)
            raise TypeError(msg)

        for i, arg in enumerate(args):
            key = cls.fields[i]
            if key in kwargs:
                msg = '{0} got multiple values for {1}'.format(
                    className, key)
                raise TypeError(msg)

            kwargs[key] = arg

        keys = kwargs.keys()
        numKwargs = len(keys)
        if numKwargs < numFields:
            missingFields = (k for k in cls.fields if k not in keys)
            msg = '{0} missing args: {1}'.format(className, ', '.join(missingFields))
            raise TypeError(msg)

        if numKwargs > numFields:
            newFields = (k for k in keys if k not in cls.fields)
            msg = '{0} got unexpected args: {1}'.format(className, ', '.join(newFields))
            raise TypeError(msg)

        return kwargs

    def __repr__(self):
        '''
        Return a string to reconstruct this class

        Returns:
            str
        '''
        def formatField(field):
            value = self[self.fields.index(field)]
            if isinstance(value, types.StringTypes):
                value = "'{0}'".format(value)

            return '{0}={1}'.format(field, value)

        className = self.__class__.__name__
        fields = ', '.join(map(formatField, self.fields))

        return '{0}({1})'.format(className, fields)

    def asdict(self):
        '''
        Return a new OrderedDict which maps field names to their values

        Returns:
            collections.OrderedDict
        '''
        return collections.OrderedDict(zip(self.fields, self))

    __dict__ = property(asdict)

    def __getnewargs__(self):
        ''''
        Return self as a plain tuple.  Used by copy and pickle.

        Returns:
            tuple
        '''
        return tuple(self)

    def __getattr__(self, attr):
        if attr not in self.fields:
            msg = '{0} has no attribute: {1}'.format(self.__class__.__name__, attr)
            raise AttributeError(msg)

        return self[self.fields.index(attr)]


class WmInfo(object):
    """Simple Class to store wmInfo types"""

    UNKNOWN = 0
    MISC = 1
    CREATURE = 2
    FACIAL = 3
    GROVE = 4
    GROVESPECIES = 5
    LIGHT = 6
    PROP = 7
    WATER = 8
    MODEL = 9


class IndexedTuple(tuple):
    """
    This behaves like a tuple but gives index access while stripping whitespace.

    For example:
        HEADERS = IndexedList('Element', 'Scene Node', 'Date', 'User', 'Notes')

        assert HEADERS.Element == 0
        assert HEADERS[0] == 'Element'
        assert HEADERS.SceneNode = 1
        assert HEADERS[1] == 'Scene Node'
        assert len(HEADERS) == 5
        assert list(HEADERS) == ['Element', 'Scene Node', 'Date', 'User', 'Notes']
    """
    __stripped = None

    def __init__(self, *args):
        super(IndexedTuple, self).__init__(*args)
        self.__stripped = tuple(re.sub('[\W_]+', '', a) for a in args)

    def __new__(cls, *args):
        return tuple.__new__(cls, args)

    def __getattr__(self, attr):
        if attr in self:
            return self.index(attr)

        if attr in self.__stripped:
            return self.__stripped.index(attr)

        raise AttributeError('\'{0}\' object has no attribute \'{1}\''.format(
            self.__class__.__name__, attr))
