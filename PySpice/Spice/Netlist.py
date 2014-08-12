####################################################################################################
# 
# PySpice - A Spice package for Python
# Copyright (C) 2014 Fabrice Salvaire
# 
####################################################################################################

####################################################################################################
#
# Graph:
#   dipole
#   n-pole: transistor (be, bc) ?
#
# circuit -> element -> node
#   circuit.Q1.b
#   Element -> ElementQ
#   use prefix?
#
####################################################################################################

####################################################################################################

from collections import OrderedDict

# import networkx

####################################################################################################

from ..Tools.StringTools import join_lines, join_list, join_dict
from ..Unit.Units import Unit
from .Simulation import CircuitSimulator

####################################################################################################

class DeviceModel(object):

    """ This class implements a device model.

    Ngspice model types:

    +------+-------------------------------+
    | Code + Model Type                    |
    +------+-------------------------------+
    | R    + Semiconductor resistor model  |
    +------+-------------------------------+
    | C    + Semiconductor capacitor model |
    +------+-------------------------------+
    | L    + Inductor model                |
    +------+-------------------------------+
    | SW   + Voltage controlled switch     |
    +------+-------------------------------+
    | CSW  + Current controlled switch     |
    +------+-------------------------------+
    | URC  + Uniform distributed RC model  |
    +------+-------------------------------+
    | LTRA + Lossy transmission line model |
    +------+-------------------------------+
    | D    + Diode model                   |
    +------+-------------------------------+
    | NPN  + NPN BJT model                 |
    +------+-------------------------------+
    | PNP  + PNP BJT model                 |
    +------+-------------------------------+
    | NJF  + N-channel JFET model          |
    +------+-------------------------------+
    | PJF  + P-channel JFET model          |
    +------+-------------------------------+
    | NMOS + N-channel MOSFET model        |
    +------+-------------------------------+
    | PMOS + P-channel MOSFET model        |
    +------+-------------------------------+
    | NMF  + N-channel MESFET model        |
    +------+-------------------------------+
    | PMF  + P-channel MESFET model        |
    +------+-------------------------------+

    """

    ##############################################

    def __init__(self, name, modele_type, **parameters):

        self._name = str(name)
        self._model_type = str(modele_type)
        self._parameters = dict(**parameters)

    ##############################################

    @property
    def name(self):
        return self._name

    ##############################################

    @property
    def model_type(self):
        return self._model_type

    ##############################################

    def __repr__(self):

        return str(self.__class__) + ' ' + self.name

    ##############################################

    def __str__(self):

        return ".model {} {} ({})".format(self._name, self._model_type, join_dict(self._parameters))

####################################################################################################

class Pin(object):

    """This class implements a pin of an element. It stores a reference to the element, the name of the
    pin and the node."""

    ##############################################

    def __init__(self, element, name, node):

        self._element = element
        self._name = name
        self._node = node

    ##############################################

    @property
    def element(self):
        return self._element

    ##############################################

    @property
    def name(self):
        return self._name

    ##############################################

    @property
    def node(self):
        return self._node

    ##############################################

    def __repr__(self):

        return "Pin {} of {} on node {}".format(self._name, self._element.name, self._node)

    ##############################################

    def add_current_probe(self, circuit):

        """ Add a current probe between the node and the pin. """

        # Fixme: require a reference to circuit

        node = self._node
        self._node = '_'.join((self._element.name, self._name))
        circuit.V(self._node, node, self._node, '0')

####################################################################################################

class ParameterDescriptor(object):

    """ This base class implements a descriptor for element parameters. """

    ##############################################

    def __init__(self, default=None):

        self.default_value = default

        self.attribute_name = None

    ##############################################

    def __get__(self, instance, owner=None):

        try:
            return getattr(instance, '_' + self.attribute_name)
        except AttributeError:
            return self.default_value

    ##############################################

    def validate(self, value):

        return value
        
    ##############################################

    def __set__(self, instance, value):

        setattr(instance, '_' + self.attribute_name, value)

    ##############################################

    def nonzero(self, instance):

        return self.__get__(instance) is not None

    ##############################################

    def to_str(self, instance):

        raise NotImplementedError

####################################################################################################

class PositionalElementParameter(ParameterDescriptor):

    """ This class implements a descriptor for positional element parameters. """

    ##############################################

    def __init__(self, position, default=None, key_parameter=False):

        super(PositionalElementParameter, self).__init__(default)

        self.position = position
        self.key_parameter = key_parameter

    ##############################################

    def __repr__(self):

        return self.__class__.__name__

    ##############################################

    def to_str(self, instance):

        return str(self.__get__(instance))

    ##############################################

    def __cmp__(self, other):

        return cmp(self.key_parameter, other.key_parameter)

####################################################################################################

class ElementParameter(ParameterDescriptor):

    """ This class implements a descriptor for element parameters. """

    ##############################################

    def __init__(self, spice_name, default=None):

        super(ElementParameter, self).__init__(default)

        self.spice_name = spice_name

     ##############################################

    def __repr__(self):

        return self.__class__.__name__

####################################################################################################

class FloatPositionalParameter(PositionalElementParameter):

    """ This class implements a float positional element parameter. """

    ##############################################

    def validate(self, value):

        if isinstance(value, Unit):
            return value
        else:
            return Unit(value)

####################################################################################################

class ExpressionPositionalParameter(PositionalElementParameter):

    """ This class implements an expression positional element parameter. """

    ##############################################

    def validate(self, value):

        return str(value)

####################################################################################################

class ElementNamePositionalParameter(PositionalElementParameter):

    """ This class implements an element name positional element parameter. """

    ##############################################

    def validate(self, value):

        return str(value)

####################################################################################################

class ModelPositionalParameter(PositionalElementParameter):

    """ This class implements a model positional element parameter. """

    ##############################################

    def validate(self, value):

        return str(value)

####################################################################################################

class InitialStatePositionalParameter(PositionalElementParameter):

    """ This class implements an initial state positional element parameter. """

    ##############################################

    def validate(self, value):

        return bool(value) # Fixme: check KeyParameter

    ##############################################

    def to__str_(self, instance):

        if self.__get__(instance):
            return 'on'
        else:
            return 'off'

####################################################################################################

class KeyValueParameter(ElementParameter):

    """ This class implements a key value pair element parameter. """

    ##############################################

    def str_value(self, instance):

        return str(self.__get__(instance))

    ##############################################

    def to_str(self, instance):

        if bool(self):
            return '{}={}'.format(self.spice_name, self.str_value(instance))
        else:
            return ''

####################################################################################################

class IntKeyParameter(KeyValueParameter):

    """ This class implements an integer key value element parameter. """

    ##############################################

    def validate(self, value):

        return int(value)

####################################################################################################

class FloatKeyParameter(KeyValueParameter):

    """ This class implements a float key value element parameter. """

    ##############################################

    def validate(self, value):

        return float(value)

####################################################################################################

class FloatPairKeyParameter(KeyValueParameter):

    """ This class implements a float pair key value element parameter. """

    ##############################################

    def validate(self, pair):

        if len(pair) == 2:
            return (float(pair[0]), float(pair[1]))
        else:
            raise ValueError()

    ##############################################

    def str_value(self, instance):

        return ','.join([str(value) for value in self.__get__(instance)])

####################################################################################################

class FlagKeyParameter(ElementParameter):

    """ This class implements a flag key value element parameter. """

    ##############################################

    def __init__(self, spice_name, default=False):

        super(FlagKeyParameter, self).__init__(spice_name, default)

    ##############################################

    def nonzero(self, instance):

        return bool(self.__get__(instance))

    ##############################################

    def to_str(self, instance):

        if self.nonzero(instance):
            return 'off'
        else:
            return ''

####################################################################################################

class BoolKeyParameter(ElementParameter):

    """ This class implements a boolean key value element parameter. """

    ##############################################

    def __init__(self, spice_name, default=False):

        super(BoolKeyParameter, self).__init__(spice_name, default)

    ##############################################

    def nonzero(self, instance):

        return bool(self.__get__(instance))

    ##############################################

    def to_str(self, instance):

        if self.nonzero(instance):
            return '0'
        else:
            return '1'

####################################################################################################

class ExpressionKeyParameter(KeyValueParameter):

    """ This class implements an expression key value element parameter. """

    ##############################################

    def validate(self, value):

        return str(value)

####################################################################################################

class ElementParameterMetaClass(type):

    ##############################################

    def __new__(cls, name, bases, attributes):

        positional_parameters = OrderedDict()
        parameters = OrderedDict() # not required
        for attribute_name, obj in attributes.iteritems():
            if isinstance(obj, PositionalElementParameter):
                obj.attribute_name = attribute_name
                positional_parameters[attribute_name] = obj
            if isinstance(obj, ElementParameter):
                obj.attribute_name = attribute_name
                parameters[attribute_name] = obj
        attributes['positional_parameters'] = positional_parameters
        attributes['optional_parameters'] = parameters

        attributes['parameters_from_args'] = [parameter
                                              for parameter in sorted(positional_parameters.itervalues())
                                              if not parameter.key_parameter]

        return super(ElementParameterMetaClass, cls).__new__(cls, name, bases, attributes)

####################################################################################################

class Element(object):

    """ This class implements a base class for an element. """

    __metaclass__ = ElementParameterMetaClass

    prefix = None

    ##############################################

    def __init__(self, name, pins, *args, **kwargs):

        self._name = str(name)
        self._pins = list(pins) # Fixme: pins is not a ordered dict, cf. property

        # self._parameters = list(args)

        for parameter, value in zip(self.parameters_from_args, args):
            setattr(self, parameter.attribute_name, value)

        for key, value in kwargs.iteritems():
            if key in self.positional_parameters or self.optional_parameters:
                setattr(self, key, value)

    ##############################################

    @property
    def name(self):
        return self.prefix + self._name

    ##############################################

    @property
    def pins(self):
        return self._pins

    ##############################################

    @property
    def nodes(self):
        return [pin.node for pin in self._pins]

    ##############################################

    def __repr__(self):

        return self.__class__.__name__ + ' ' + self.name

    ##############################################

    def format_node_names(self):

        return join_list((self.name, join_list(self.nodes)))

    ##############################################

    def parameter_iterator(self):

        for parameter_dict in self.positional_parameters, self.optional_parameters:
            for parameter in parameter_dict.itervalues():
                if parameter.nonzero(self):
                    yield parameter

    ##############################################

    # @property
    # def parameters(self):
    #     return self._parameters

    ##############################################

    def format_spice_parameters(self):

        return join_list([parameter.to_str(self) for parameter in self.parameter_iterator()])

    ##############################################

    def __str__(self):

        return join_list((self.format_node_names(), self.format_spice_parameters()))

####################################################################################################

class TwoPinElement(Element):

    """ This class implements a base class for a two-pin element. """

    ##############################################

    def __init__(self, name, node_plus, node_minus, *args, **kwargs):

        pins = (Pin(self, 'plus', node_plus), Pin(self, 'minus', node_minus))

        super(TwoPinElement, self).__init__(name, pins, *args, **kwargs)

    ##############################################

    @property
    def plus(self):
        return self.pins[0]

    ##############################################

    @property
    def minus(self):
        return self.pins[1]

####################################################################################################

class TwoPortElement(Element):

    """ This class implements a base class for a two-port element.

    .. warning:: As opposite to Spice, the input nodes are specified before the output nodes.
    """

    ##############################################

    def __init__(self, name,
                 input_node_plus, input_node_minus,
                 output_node_plus, output_node_minus,
                 *args, **kwargs):

        pins = (Pin(self, 'output_plus', output_node_plus),
                Pin(self, 'output_minus', output_node_minus),
                Pin(self, 'input_plus', input_node_plus),
                Pin(self, 'input_minus', input_node_minus))

        super(TwoPortElement, self).__init__(name, pins, *args, **kwargs)

    ##############################################

    @property
    def output_plus(self):
        return self.pins[0]

    ##############################################

    @property
    def output_minus(self):
        return self.pins[1]

    ##############################################

    @property
    def input_plus(self):
        return self.pins[2]

    ##############################################

    @property
    def input_minus(self):
        return self.pins[3]

####################################################################################################

class Node(object):

    """This class implements a node in the circuit. It stores a reference to the elements connected to
    the node."""

    # Fixme: but not directly to the pins!

    ##############################################

    def __init__(self, name):

        self._name = name
        self._elements = set()

    ##############################################

    def __repr__(self):
        return 'Node {}'.format(self._name)

    ##############################################

    @property
    def name(self):
        return self._name

    @property
    def elements(self):
        return self._elements

    ##############################################

    def add_element(self, element):
        self._elements.add(element) 

####################################################################################################

class Netlist(object):

    """ This class implements a base class for a netlist. """

    ##############################################

    def __init__(self):

        self._ground = None
        self._elements = {}
        self._models = {}
        self._dirty = True
        # self._nodes = set()
        self._nodes = {}

        # self._graph = networkx.Graph()

    ##############################################

    def element_iterator(self):

        return self._elements.itervalues()

    ##############################################

    def model_iterator(self):

        return self._models.itervalues()

    ##############################################

    def __str__(self):

        netlist = join_lines(self.element_iterator()) + '\n'
        if self._models:
            netlist += join_lines(self.model_iterator()) + '\n'
        return netlist

    ##############################################

    def _add_element(self, element):

        if element.name not in self._elements:
            self._elements[element.name] = element
            self._dirty = True
        else:
            raise NameError("Element name {} is already defined".format(element.name))

    ##############################################

    def model(self, name, modele_type, **parameters):

        model = DeviceModel(name, modele_type, **parameters)
        if model.name not in self._models:
            self._models[model.name] = model

    ##############################################

    @property
    def nodes(self):

        if self._dirty:
            # nodes = set()
            # for element in self.element_iterator():
            #     nodes |= set(element.nodes)
            # if self._ground is not None:
            #     nodes -= set((self._ground,))
            # self._nodes = nodes
            self._nodes.clear()
            for element in self.element_iterator():
                for node_name in element.nodes:
                    if node_name not in self._nodes:
                        node = Node(node_name)
                        self._nodes[node_name] = node
                    else:
                        node = self._nodes[node_name]
                    node.add_element(element)
        return self._nodes.values()

    ##############################################

    def __getitem__(self, attribute_name):

        if attribute_name in self._elements:
            return self._elements[attribute_name]
        elif attribute_name in self._models:
            return self._models[attribute_name]
        elif attribute_name in self._nodes:
            return attribute_name
        else:
            raise IndexError(attribute_name)

    ##############################################

    def __getattr__(self, attribute_name):
        
        try:
            return self.__getitem__(attribute_name)
        except IndexError:
            raise AttributeError(attribute_name)

####################################################################################################

class SubCircuit(Netlist):

    """ This class implements a sub-cicuit netlist. """

    ##############################################

    def __init__(self, name, *nodes, **kwargs):

        super(SubCircuit, self).__init__()

        self.name = str(name)
        self._external_nodes = list(nodes)
        self._ground = kwargs.get('ground', 0)
        
    ##############################################

    @property
    def gnd(self):
        """ Local ground """
        return self._ground

    ##############################################

    def check_nodes(self):

        nodes = set(self._external_nodes)
        connected_nodes = set()
        for element in self.element_iterator():
            connected_nodes.add(nodes & element.nodes)
        not_connected_nodes = nodes - connected_nodes
        if not_connected_nodes:
            raise NameError("SubCircuit Nodes {} are not connected".format(not_connected_nodes))

    ##############################################

    def __str__(self):

        netlist = '.subckt {} {}\n'.format(self.name, join_list(self._external_nodes))
        netlist += super(SubCircuit, self).__str__()
        netlist += '.ends\n'
        return netlist

####################################################################################################

class SubCircuitFactory(SubCircuit):

    # Fixme : versus SubCircuit

    __name__ = None
    __nodes__ = None

    ##############################################

    def __init__(self, **kwargs):

        super(SubCircuitFactory, self).__init__(self.__name__, *self.__nodes__, **kwargs)

####################################################################################################

class Circuit(Netlist):

    """ This class implements a cicuit netlist.

    To get the corresponding Spice source use::

       circuit = Circuit()
       ...
       str(circuit)

    """

    # .lib
    # .func
    # .csparam

    ##############################################

    def __init__(self, title,
                 ground=0,
                 global_nodes=(),
             ):

        super(Circuit, self).__init__()

        self.title = str(title)
        self._ground = ground
        self._global_nodes = set(global_nodes) # .global
        self._includes = set() # .include
        self._parameters = {} # .param
        self._subcircuits = {}

    ##############################################

    @property
    def gnd(self):
        return self._ground

    ##############################################

    def include(self, path):

        """ Include a file. """

        self._includes.add(path)

    ##############################################

    def parameter(self, name, expression):

        """ Set a parameter. """
        
        self._parameters[str(name)] = str(expression)

    ##############################################

    def subcircuit(self, subcircuit):

        """ Add a sub-circuit. """

        self._subcircuits[str(subcircuit.name)] = subcircuit

    ##############################################

    def subcircuit_iterator(self):

        """ Return a sub-circuit iterator. """

        return self._subcircuits.itervalues()

    ##############################################

    def __str__(self):

        netlist = '.title {}\n'.format(self.title)
        if self._includes:
            netlist += join_lines(self._includes, prefix='.include ')  + '\n'
        if self._global_nodes:
            netlist += '.global ' + join_list(self._global_nodes) + '\n'
        if self._parameters:
            netlist += join_lines(self._parameters, prefix='.param ') + '\n'
        if self._subcircuits:
            netlist += join_lines(self.subcircuit_iterator())
        netlist += super(Circuit, self).__str__()
        netlist += '.end\n'
        return netlist

    ##############################################

    def simulator(self, *args, **kwargs):
        return CircuitSimulator(self, *args, **kwargs)

####################################################################################################
# 
# End
# 
####################################################################################################
