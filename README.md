Overview
====================

Django Fixie helps you to manipulate fixtures.

Note: Currently only works with JSON fixtures.  If that's a problem, please tell me.


Examples
=====================

Say you've adjusted your Django models and you want to get rid of the models in your fixtures
that aren't in your models anymore:

 > from fixie import Fixture
 > fixtures = Fixture("data/fixtures.json")
 > fixtures.drop_unused()
 > fixtures.save()


Say you made a bunch of changes to your models and you want to see where your fixtures differ:

 > from fixie import Fixture
 > fixtures = Fixture("data/fixtures.json")
 > fixtures.validate()
    app.blogtag:
     model is gone

    app.page:
     missing field is required: category

    app.page:
     field not in model: blogtag


Say you want to drop the unused fields in 'app.page':
 
 > from fixie import Fixture
 > fixtures = Fixture("data/fixtures.json")
 > fixtures['app.page'].drop_unused()
 > fixtures.save()


Say you want to look at the data in a fixture, in this example a custom user class:

 > from fixie import Fixture
 > fixtures = Fixture("data/fixtures.json")
 > fixtures['app.user'].view()

    --------------------------------------
    Model: app.user 
    --------------------------------------
                 bio: ''
           education: ''
               email: 'admin@example.com'
               image: ''
          last_login: '2013-07-20T23:55:35Z'
                name: 'Admin'
            password: 'pbkdf2_sha256$10000$sdfq234tasdfa43twedsf+jh+a324rdsf/gRqNCiMI/GlZQiKN7OOB1I4bhs='
              status: 'active'
                type: 'admin'
             website: ''

This shows example data for each field.  Some are empty, meaning that no object has any value there.  But say you wanted 
to change all the websites to "example.com"

 > from fixie import Fixture
 > fixtures = Fixture("data/fixtures.json")
 > fixtures['app.user'].set('website', 'example.com')
 > fixtures.save()

Or maybe you want to change all the user's website to 'example.com' only if they don't already have a website.

 > from fixie import Fixture
 > fixtures = Fixture("data/fixtures.json")
 > fixtures['app.user'].set_default('website', 'example.com')
 > fixtures.save()

Or perhaps you want to change it to the end of their email address, for some reason, set() and set_default() allow a callable
as a value:

 > from fixie import Fixture
 > def get_email(entry):
 >    return entry['fields']['email'].split('@')[1]
 >
 > fixtures = Fixture("data/fixtures.json")
 > fixtures['app.user'].set('website', get_email)
 > fixtures.save()
 