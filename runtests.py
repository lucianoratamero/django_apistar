#!/usr/bin/env python
import os
import sys

import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == "__main__":
    os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.test_settings'
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["tests"])
    sys.exit(bool(failures))
#
#
#
# import os
# import sys
# import django
# from django.test.runner import DiscoverRunner
#
# sys.path.append(os.path.normpath(os.path.join(os.getcwd(), '../..')))
# print(sys.path)
# os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
# django.setup()
#
#
# import ipdb; ipdb.set_trace()
# tr = DiscoverRunner(verbosity=1)
# tr.setup_test_environment()
# failures = tr.run_tests(['django_apistar', ])
# if failures:
#     sys.exit(failures)
