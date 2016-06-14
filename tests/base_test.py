import sys
import os

google_appengine_home = os.environ.get('GOOGLE_APPENGINE_HOME', '/usr/local/google_appengine')

for path in [google_appengine_home]:
    if path not in sys.path:
        sys.path[0:0] = [path]

import unittest

from google.appengine.ext import testbed
from google.appengine.datastore import datastore_stub_util
from google.appengine.ext import ndb
from google.appengine.ext.cloudstorage import cloudstorage_stub


# noinspection PyProtectedMemberDisneyStoreAvailability
class BaseTest(unittest.TestCase):
    # so that nosetests run
    context = None

    def __init__(self, method_name=''):
        super(BaseTest, self).__init__(method_name)
        self.datastore_probability = 1

    def setUp(self):
        super(BaseTest, self).setUp()

        root_path = '.'
        application_id = 'graphene-gae-test'

        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.setup_env(app_id=application_id, overwrite=True)
        policy = datastore_stub_util.PseudoRandomHRConsistencyPolicy(probability=self.datastore_probability)
        self.testbed.init_datastore_v3_stub(root_path=root_path, consistency_policy=policy, require_indexes=True)
        self.testbed.init_app_identity_stub()
        self.testbed.init_blobstore_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_taskqueue_stub(root_path=root_path)
        self.testbed.init_urlfetch_stub()
        self.storage = cloudstorage_stub.CloudStorageStub(self.testbed.get_stub('blobstore').storage)
        self.testbed.init_mail_stub()
        self.testbed.init_user_stub()
        self.taskqueue_stub = self.testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)

        ndb.get_context().clear_cache()
        ndb.get_context().set_cache_policy(lambda x: True)

    def tearDown(self):
        self.testbed.init_datastore_v3_stub(False)

        self.testbed.deactivate()
        self.testbed = None
        super(BaseTest, self).tearDown()

    def get_filtered_tasks(self, url=None, name=None, queue_names=None):
        return self.taskqueue_stub.get_filtered_tasks(url=url, name=name, queue_names=queue_names)

    # region Extra Assertions
    def assertEmpty(self, l, msg=None):
        self.assertEqual(0, len(list(l)), msg=msg or str(l))

    def assertLength(self, l, expectation, msg=None):
        self.assertEqual(len(l), expectation, msg)

    def assertEndsWith(self, str, expected_suffix):
        cond = str.endswith(expected_suffix)
        self.assertTrue(cond)

    def assertStartsWith(self, str, expected_prefix):
        cond = str.startswith(expected_prefix)
        self.assertTrue(cond)
        # endregion

    def assertPositive(self, n):
        self.assertTrue(n > 0)

    def assertNegative(self, n):
        self.assertTrue(n < 0)
