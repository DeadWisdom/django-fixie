"""
Operations to manipulate django fixtures.
"""
import sys, os, zipfile, json
from pprint import pprint

from django.db.models import get_apps, get_app, get_models, get_model
from django.utils._os import upath

def get_names():
    app_module_paths = []
    for app in get_apps():
        if hasattr(app, '__path__'):
            # It's a 'models/' subpackage
            for path in app.__path__:
                app_module_paths.append(upath(path))
        else:
            # It's a models.py module
            app_module_paths.append(upath(app.__file__))

    app_fixtures = [os.path.join(os.path.dirname(path), 'fixtures') for path in app_module_paths]
    for path in app_fixtures:
        if 'django/contrib' in path or 'site-packages/' in path:
            continue
        if not os.path.exists(path):
            continue
        for filename in os.listdir(path):
            yield os.path.join(path, filename)

def find_fixture_path(name):
    for path in get_names():
        filename = os.path.basename(path)
        if filename == name:
            return path
        base, ext = os.path.splitext(filename)
        if base == name:
            return path
    if os.path.exists(name):
        return name

def group_types(objects, key):
    types = {}
    for obj in objects:
        types.setdefault(obj[key], []).append(obj)
    return types

def merge_objects(a, b):
    if (not isinstance(a, dict) or not isinstance(b, list)):
        if (a is None and b is not None):
            return b
        if isinstance(a, basestring):
            if (a.strip() == '' and b is not None):
                return b
        return a
    result = {}
    for keys in set(a.keys() + b.keys()):
        result[k] = merge_objects(a.get(k), b.get(k))
    return result

def object_str(obj):
    output = []
    for k in sorted(obj.keys()):
        v = obj[k]
        if isinstance(v, basestring) and len(v) > 80:
            v = v[:76].rstrip(' ') + " ..."
        v = repr(v)
        if v.startswith("u'") or v.startswith('u"'):
            v = v[1:]
        output.append( "%s: %s" % (k.rjust(16), v) )
    output.append("")
    return "\n".join(output)


class Model(object):
    def __init__(self, name, objects):
        self.name = name
        self.objects = objects
        self.collapse()

    def collapse(self):
        self.schema = reduce(merge_objects, [obj['fields'] for obj in self.objects])

    def view(self):
        print "--------------------------------------\nModel:", self.name, "\n--------------------------------------"
        print object_str(self.schema)

    def remove(self, column_name):
        for object in self.objects:
            try:
                del object['fields'][column_name]
            except KeyError:
                pass
        self.collapse()

    def get_django_model(self):
        app_name, model_name = self.name.rsplit('.', 1)
        return get_model(app_name, model_name)

    def validate(self):
        errors = []
        model = self.get_django_model()
        if model is None:
            return ["model is gone"]
        else:
            model_fields = set( model._meta.get_all_field_names() )
            for field, value in self.schema.items():
                if field not in model_fields:
                    errors.append("field not in model: %s" % field)
            for field in model._meta.fields:
                if not field.blank and self.schema.get(field.name) is None:
                    if field.primary_key == True:
                        continue
                    errors.append("missing field is required: %s" % field.name)
        return errors

    def drop_unused(self):
        log = []
        model = self.get_django_model()
        if not model:
            self.objects = []  # Drops all of these objects from the fixtures
            return ["dropping unused model"]
        model_fields = set( model._meta.get_all_field_names() )
        for field, value in self.schema.items():
            if field not in model_fields:
                log.append( "dropping unused field: %s" % field )
                self.remove(field)
        return log

    def set_default(self, column_name, value):
        for object in self.objects:
            if object['fields'].get(column_name, None) is None:
                if callable(value):
                    object['fields'][column_name] = value(object)
                else:
                    object['fields'][column_name] = value

    def set(self, column_name, value):
        for object in self.objects:
            if callable(value):
                object['fields'][column_name] = value(object)
            else:
                object['fields'][column_name] = value


class Fixture(object):
    def __init__(self, name):
        self._types = {}
        self.models = {}

        self.path = find_fixture_path(name)
        if self.path is None:
            raise NameError("Cannot find fixture: %r" % name)
        
        self.load(self.path)

    def load(self, path):
        with open(path) as file:
            data = json.load(file)

        self._types = group_types(data, 'model')
        self.models = {}
        for type, objects in self._types.items():
            self.models[type] = Model(type, objects)

    def names(self):
        return self.models.keys()

    def __iter__(self):
        for model in self.models.values():
            if not model.objects:
                del self.models[model.name]
                continue
            yield model

    def __getitem__(self, k):
        return self.models[k]

    def get_objects(self):
        objects = []
        for model in self:
            objects.extend(model.objects)
        return objects

    def validate(self):
        success = True
        for model in self:
            errors = model.validate()
            if errors:
                success = False
                print model.name + ":"
                for error in errors:
                    print "", error
                print ""
        return success

    def drop_unused(self):
        for model in self:
            log = model.drop_unused()
            if log:
                print model.name + ":"
                for item in log:
                    print "", item
                print ""

    def drop(self, model_name):
        model = self[model_name]
        model.objects = []
        del self.models[model.name]

    def denormalize(self, model_name, keys, fk_model, fk):
        model = self[model_name]
        left, right = keys
        mapping = dict((obj['fields'][left], obj['fields'][right]) for obj in model.objects)

        model = self[fk_model]
        for object in model.objects:
            object['fields'][fk] = mapping.get(object['pk'])

        print "Denormalized %s into %s -> %s\n" % (model_name, fk_model, fk)

    def save(self, path=None):
        path = path or self.path
        with open(path, "w") as file:
            json.dump(self.get_objects(), file)

