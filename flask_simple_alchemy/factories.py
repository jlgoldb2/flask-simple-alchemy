"""
I am a module called 'factories' in a file named 'factories.py' inside the
flask_simple_alchemy folder. I contain the RelationshipFactories class
which is used to generate Relationship Mixins.
"""

import sqlalchemy
from flask.ext.sqlalchemy import SQLAlchemy, _BoundDeclarativeMeta
from sqlalchemy.ext.declarative import declared_attr

from flask_simple_alchemy.factory_helpers import kwarg_corrector


class RelationshipFactories(object):
    """
    I hold the factories that return objects which can be used to\n
    create extremely brief declaration of relationships between\n
    SQLAlchemy.Model (db.Model actually) objects.\n
    """

    def __init__(self, db):
        """
        I initialize the RelationshipFactories's instance.\n
        I expect an instance of the SQLAlchemy object as my first\n
        argument. If I don't get a SQLAlchemy object as my first\n
        argument I will throw an Exception.\n

        Constructor.

            :param db:
                Flask-SQLAlchemy database object. Instance of
                flask.ext.sqlalchemy.SQLAlchemy()
        """
        if not isinstance(db, SQLAlchemy):
            raise Exception('The RelationshipFactories object\
                requires/expects an instance of the SQLAlchemy object.')
        self.db = db

    def foreign_key(self, name, **kwargs):
        """
        I am for generating foreign keys.
        I return a Flask-SQLAlchemy ForeignKey.
        I expect a string (name) as my first arg.
        """
        if not isinstance(name, str):
            e = 'foreign_key must be a string (str). Got a ' + str(type(name))
            raise Exception(e)
        return self.db.ForeignKey(name, **kwargs)

    def relationship(self, class_obj, table_class_name, one_to_one=False,
                     many_to_one=False, uselist=None, lazy=None):
        """
        I return relationship objects.
        """
        kwargs = dict(one_to_one=one_to_one, many_to_one=many_to_one,
                      uselist=uselist, lazy=lazy)

        kwargs = kwarg_corrector(**kwargs)
        return self.db.relationship(table_class_name, uselist=uselist,
                                    backref=self.db.backref(
                                        class_obj.__tablename__,
                                        lazy=lazy))

    def foreign_key_factory(self, tablename, foreign_key='id',
                            fk_type=None, **kwargs):
        """
        I am used to generate ForeignKey mixin objects.
        """
        if fk_type is None:
            fk_type = self.db.Integer
        table_and_fk = [tablename, foreign_key]
        #given 'person' and 'id' => person_id
        local_ref = '_'.join(table_and_fk)
        #given 'person' and 'id' => person.id
        remote_fk = '.'.join(table_and_fk)

        def declare_id():
            @declared_attr
            def func(cls):
                return self.db.Column(fk_type, self.foreign_key(remote_fk))
            return func

        class ForeignKeyMixin(object):
            pass

        setattr(ForeignKeyMixin, 'table_of_fk', tablename)
        #setattr(ForeignKeyRelationship, 'foreign_key', foreign_key)
        setattr(ForeignKeyMixin, local_ref, declare_id())
        return ForeignKeyMixin

    def one_to_one_factory(self, table_class_name_reference,
                           ForeignKeyMixinClass):
        """
        I am used to generate One-to-One relationship mixins.
        """
        def declare_one_to_one(table_class_name):
            """

            """
            @declared_attr
            def func(cls):
                return self.db.relationship(table_class_name,
                      backref=self.db.backref(cls.__tablename__,
                                uselist=False, lazy='select'), )
            return func

        class OneToOneRelationship(ForeignKeyMixinClass):
            """
            I am the Mixin Class for OneToOne Relationships.
            I inherit from ForeignKeyRelClass\n which is generated
            returned by instances RelationshipFactories.foreign_key_factory.\n
            After leaving this factory I will have two '@declared_attr'
            methods: a foreign key and a\n relationship object.
            """
            pass

        setattr(OneToOneRelationship,
                OneToOneRelationship.table_of_fk,
                declare_one_to_one(table_class_name_reference))

        return OneToOneRelationship

    def many_to_one_factory(self, table_class_name_reference,
                            ForeignKeyMixinClass):
        """
        I am used to generate One-to-One relationship mixins.
        """
        def declare_one_to_one(table_class_name):
            """

            """
            @declared_attr
            def func(cls):
                return self.db.relationship(table_class_name,
                    backref=self.db.backref(cls.__tablename__,
                                            lazy='dynamic'), lazy='select'
                                            )
            return func

        class OneToManyRelationship(ForeignKeyMixinClass):
            """
            I am the Mixin Class for OneToOne Relationships.
            I inherit from ForeignKeyRelClass which is generated
            returned by instances RelationshipFactories.foreign_key_factory.
            After leaving this factory I will have two '@declared_attr'
            methods: a foreign key and a relationship object.
            """
            pass

        setattr(OneToManyRelationship,
                OneToManyRelationship.table_of_fk,
                declare_one_to_one(table_class_name_reference))

        return OneToManyRelationship




def simple_table_factory(db, default_primary_key='id',
                         default_pk_type='integer'):
    """
    I am a factory that produces a class Mixin that provides:
    1) default 'id' primary_key columns
        change primary key attribute and type via:
            default_primary_key='some_stringy_key'
            default_pk_type='string'
    2) and table attributes/columns in easy-to-use lists
    """
    def get_sqltypes_from_db():
        """
        I am get_sqltypes. I use an extremely long, nested list comprehension
        to extract all the sqltypes from the db (instance of SQLAlchemy) obj.
        Using the resulting list, I generate a dict of lowercase keys and
        sqltype object values returned.
        """
        types = {}

        sqltypes = [sqltype for sqltype in
            [obj for name, obj in db.__dict__.items()
            if getattr(obj, '__mro__', None) is not None]
            if sqlalchemy.sql.type_api.TypeEngine in sqltype.mro()]

        for obj in sqltypes:
            name = obj.__name__.lower()
            types[name] = obj
        return types

    sqltypes = get_sqltypes_from_db()

    def get_sqltype(typename):
        """
        I am the get_type function.
        I am a function that returns SQLAlchemy column data types given
        a stringy representation of that type.
            i.e. given the arg 'string', I return the db.String function.
            i.e. given the arg 'integer', I return the db.Integer function.
        """
        try:
            return sqltypes[str(typename)]
        except:
            raise Exception(str(typename) + ' was not a valid type')


    def simple_setter(class_object, column_typename):
        """
        I am a function that returns a setter function. The setter function
        that I return iterates a list of strings and sets those attributes
        as the appropriate datatype.
        """
        def set_type(self, value):
            for item in value:
                setattr(class_object,
                        item,
                        db.Column(get_sqltype(column_typename)))
                setattr(self, '_' + column_typename, value)
        return set_type

    def simple_getter(column_typename):
        def get_type(self):
                return getattr(self, '_' + column_typename)
        return get_type

    def metaclass_factory():
        class SomeMetaClass(type):
            pass
        return SomeMetaClass

    SimpleMetaClass = metaclass_factory()


    for k, v in sqltypes.items():
        setattr(SimpleMetaClass, k + 's',
                property(simple_getter(k),
                         simple_setter(SimpleMetaClass, k)))


    class DoubleMetaClass(SimpleMetaClass, _BoundDeclarativeMeta):
        pass

    class SimpleTable(object):
        """
        I am SimpleTable. I am a Mixin that provides:
            1) an integer primary key 'id'
            2) the ability to define SQLAlchemy columns via iterable lists.
        """
        _decl_class_registry = []
        __metaclass__ = DoubleMetaClass
        __abstract__= True


    if default_primary_key:
        setattr(SimpleTable, default_primary_key,
                db.Column(get_sqltype(default_pk_type), primary_key=True))


    return SimpleTable
