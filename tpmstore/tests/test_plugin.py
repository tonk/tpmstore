# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from argparse import ArgumentParser

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch

from ansible.errors import AnsibleError
from ansible.module_utils import six
from tpmstore.tpmstore import LookupModule
from tpm import TpmApiv4
from logging import getLogger


log = getLogger(__name__)

class FakeTPM(TpmApiv4):
    def __init__(self, url, **kwargs):
        self.unlock_reason = False
        for key in kwargs:
            if key == 'private_key':
                self.private_key = kwargs[key]
            elif key == 'public_key':
                self.public_key = kwargs[key]
            elif key == 'username':
                self.username = kwargs[key]
            elif key == 'password':
                self.password = kwargs[key]
            elif key == 'unlock_reason':
                self.unlock_reason = kwargs[key]

    def list_passwords_search(self, search):
        if search == 'name:[1result]':
            return [{'id': 42}]
        elif search == 'name:[2result]':
            return [{'id': 42}, {'id': 73}]
        elif search == 'name:[noresult]':
            return []
        else:
            log.debug(search)
            return [{'id': search}]

    def show_password(self, id):
        return {'id': id, 'password': 'foobar'}


class TestTpmstorePlugin(unittest.TestCase):

    def setUp(self):
        self.lookup_plugin = LookupModule()

    def test_least_arguments_exception(self):
        exception_error = 'At least 4 arguments required.'
        with self.assertRaises(AnsibleError) as context:
            self.lookup_plugin.run(['tpmurl', 'tpmuser'])
        log.debug("context exception: {}".format(context.exception))
        self.assertTrue(exception_error in str(context.exception))

    def test_create_argument_exception(self):
        wrong_term = 'Foo'
        exception_error = "create can only be True or False and not: {}".format(wrong_term)
        with self.assertRaises(AnsibleError) as context:
            self.lookup_plugin.run(['tpmurl', 'tpmuser', 'tpmass', 'create={}'.format(wrong_term)])
        log.debug("context exception: {}".format(context.exception))
        self.assertTrue(exception_error in str(context.exception))

    def test_invalid_url_exception(self):
        wrong_url = 'ftp://foo.bar'
        exception_error = "First argument has to be a valid URL to TeamPasswordManager API: {}".format(wrong_url)
        with self.assertRaises(AnsibleError) as context:
            self.lookup_plugin.run(['{}'.format(wrong_url), 'tpmuser', 'tpmass', 'name=dostuff'])
        log.debug("context exception: {}".format(context.exception))
        self.assertTrue(exception_error in str(context.exception))

    def test_other_tpm_exception(self):
        wrong_url = 'https://does.not.exists.com'
        exception_error = "Connection error for "
        with self.assertRaises(AnsibleError) as context:
            self.lookup_plugin.run(['{}'.format(wrong_url), 'tpmuser', 'tpmass', 'name=dostuff'])
        log.debug("context exception: {}".format(context.exception))
        self.assertTrue(exception_error in str(context.exception))

    @patch('tpm.TpmApiv4', new=FakeTPM)
    def test_too_many_results_exception(self):
        search_sring = "2result"
        exception_error = 'Found more then one match for the entry, please be more specific: {}'.format(search_sring)
        with self.assertRaises(AnsibleError) as context:
            self.lookup_plugin.run(['https://foo.bar', 'tpmuser', 'tpmass', 'name={}'.format(search_sring)])
        log.debug("context exception: {}".format(context.exception))
        self.assertTrue(exception_error in str(context.exception))

    @patch('tpm.TpmApiv4', new=FakeTPM)
    def test_create_needs_projectid_exception(self):
        search_sring = "noresult"
        exception_error = 'To create a complete new entry, project_id is mandatory.'
        with self.assertRaises(AnsibleError) as context:
            self.lookup_plugin.run(['https://foo.bar', 'tpmuser', 'tpmass', 'name={}'.format(search_sring), 'create=True'])
        log.debug("context exception: {}".format(context.exception))
        self.assertTrue(exception_error in str(context.exception))