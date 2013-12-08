import unittest
from uber.model_base import *

class DummySubModel(Model):
    id = NumberField('id')

class DummyModel(Model):
    some_number = NumberField('someNumber')
    some_boolean = BooleanField('someBoolean')
    some_dict = DictField('someDict', DummySubModel)
    some_array = ListField('someArray', DummySubModel)
    some_model = ModelField('someModel', DummySubModel)

class DummyModelOptional(Model):
    some_number = NumberField('someNumber', optional=True)
    some_dict = DictField('someDict', DummySubModel, optional=True)
    some_array = ListField('someArray', DummySubModel, optional=True)
    some_model = ModelField('someModel', DummySubModel, optional=True)

class TestModelBase(unittest.TestCase):
    def test_model(self):
        d = {
            'someNumber': 1,
            'someBoolean': True,
            'someDict': {
                'xxx': {
                    'id': 1
                },
                'yyy': {
                    'id': 2
                }
            },
            'someArray': [{
                'id': 3
            },{
                'id': 4
            }],
            'someModel': {
                'id': 5
            }
        }

        model = DummyModel(d)
        self.assertEqual(model.raw, d)
        self.assertEqual(model.some_number, 1)
        self.assertEqual(model.some_boolean, True)
        some_dict = model.some_dict
        self.assertEqual(len(some_dict), 2)
        self.assertEqual(some_dict['xxx'], DummySubModel({'id': 1}))
        self.assertEqual(some_dict['xxx'], DummySubModel({'id': 1}))

        self.assertEqual(model.some_array, [DummySubModel({'id': 3}), DummySubModel({'id': 4})])
        self.assertEqual(model.some_model, DummySubModel({'id': 5}))

    def test_optional(self):
        model = DummyModelOptional({})
        self.assertIsNone(model.some_model)
        self.assertIsNone(model.some_number)
        self.assertEqual(model.some_array, [])
        self.assertEqual(model.some_dict, {})

    def test_dict_with_key_func(self):
        d = {
            'dicty':
                {
                    '1': {'id': 'a'},
                    '2': {'id': 'b'},
                }
        }

        class DummyTestModel(Model):
            dicty = DictField('dicty', key=int, value=DummySubModel)


        model = DummyTestModel(d)
        self.assertEqual([1, 2], model.dicty.keys())
        self.assertEqual(DummySubModel({'id': 'a'}), model.dicty[1])
        self.assertEqual(DummySubModel({'id': 'b'}), model.dicty[2])

    def test_readonly(self):
        model = DummySubModel({'id': 1})

        with self.assertRaises(AttributeError):
            model.id = 1

    def test_writeable(self):
        class WriteableModel(Model):
            id = NumberField('id', writeable=True)

        model = WriteableModel({'id': 1})
        self.assertEqual(model.id, 1)
        model.id = 2
        self.assertEqual(model.id, 2)


if __name__ == '__main__':
    unittest.main()
