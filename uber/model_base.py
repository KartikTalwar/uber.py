from StringIO import StringIO
from datetime import datetime
import os
from pprint import pformat
from dateutil.parser import DEFAULTPARSER as dateparser


class Model(object):
    def __init__(self, data=None):
        self._data = data or {}

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, pformat(self._data))

    def __str__(self):
        return ModelPrinter().pprint(self)

    def __eq__(self, other):
        return self._data == other._data

    @property
    def raw(self):
        return self._data


class Field(object):
    """
    Basic json field. Returns as is.
    """
    def __init__(self, name, optional=False, writeable=False):
        """
        Args:
             - name: the key of the json field
             - optional: if not True, __get__ will raise an exception on unavailable keys
             - writeable: makes the field writeable (unsupported on most field types)
        """
        self._name = name
        self._optional = optional
        self._writeable = writeable

    def __get__(self, instance, owner):
        value = instance._data.get(self._name)
        if value is None and not self._optional:
            raise KeyError(self._name)

        return self.to_python(value)

    def __set__(self, instance, value):
        if not self._writeable:
            raise AttributeError("can't set attribute")

        instance._data[self._name] = self.from_python(value)

    def to_python(self, value):
        return value

    def from_python(self, python_value):
        return python_value


class ModelField(Field):
    """
    Translates a field to the given Model type
    """
    def __init__(self, name, model_type, **kwargs):
        super(ModelField, self).__init__(name, **kwargs)
        self._model_type = model_type

    def to_python(self, value):
        if value is None:
            return None

        return self._model_type(value)


class ListField(Field):
    """
    Translates a field to a list, where the individual values are the result of calling value_func
    If the list does not exists and the field is optional, returns []
    """
    def __init__(self, name, item_func, **kwargs):
        super(ListField, self).__init__(name, **kwargs)
        self._item_type = item_func

    def to_python(self, value):
        if value is None:
            return []

        return [self._item_type(x) for x in value]


class DictField(Field):
    """
    Translates a field to a dict, where the individual values are the result of calling value
    If the list does not exists and the field is optional, returns {}
    """
    def __init__(self, name, value, key=None, **kwargs):
        """
        Args:
            - name: the field name
            - value: a type (or a callable) of the value
            - key: a type (or a callable) of the keys
        """
        super(DictField, self).__init__(name, **kwargs)
        self._item_type = value
        self._key_func = key or (lambda x: x)

    def to_python(self, value):
        if value is None:
            return {}

        return {self._key_func(k): self._item_type(v) for k, v in value.items()}


class DateTimeField(Field):
    """
    Parses a datetime string to a string
    """
    def to_python(self, value):
        return dateparser.parse(value)


class EpochField(Field):
    def to_python(self, value):
        return datetime.utcfromtimestamp(value/1000.0)


# provided for readability purposes
BooleanField = Field
FloatField = Field
NumberField = Field
StringField = Field


class ModelPrinter(object):
    """
    a pretty-printer. Inspired by pprint.py
    getting good results out of pprint was way too hacky, mainly due to the different naming convention of the fields in
    __repr__ vs __str__
    """
    def __init__(self):
        self._stream = StringIO()
        self._padding = '    '

    def pprint(self, obj):
        self._pprint_model(obj, 0)
        self._stream.seek(0)
        return self._stream.getvalue()

    def _write(self, data):
        self._stream.write(data)

    def _write_padding(self, data='', depth=0):
        data = self._padding * depth + data
        self._stream.write(data)

    def _pprint_obj(self, obj, depth):
        if isinstance(obj, Model):
            self._pprint_model(obj, depth)
        elif isinstance(obj, list):
            self._write('[\n')
            self._pprint_array(obj, depth + 1)
            self._write_padding(']', depth)
        elif isinstance(obj, dict):
            self._write('{\n')
            self._pprint_dict(obj, depth + 1)
            self._write_padding('}', depth)
        elif isinstance(obj, datetime):
            self._write(str(obj))
        else:
            self._write(pformat(obj, indent=1, depth=depth))

    def _pprint_model(self, obj, depth):
        self._write(type(obj))
        self._write('\n')
        depth += 1
        for name, field in obj.__class__.__dict__.items():
            if not isinstance(field, Field):
                continue

            value = getattr(obj, name)
            if value is None:
                continue

            self._write_padding(name + ': ', depth)
            self._pprint_obj(value, depth)

            self._write('\n')

        self._stream.seek(-1, os.SEEK_CUR)

    def _pprint_dict(self, dict_field, depth):
        for k, v in dict_field.items():
            self._write_padding(depth=depth, data='{}:\t'.format(k))
            self._pprint_obj(depth=depth, obj=v)
            self._write('\n')

    def _pprint_array(self, array, depth):
        for item in array:
            self._write_padding(depth=depth)
            self._pprint_obj(depth=depth, obj=item)
            self._write(',\n')
