from unittest import TestCase
from demo.make_simple_report import run_demo
import os
import re


class TestDemoMakeSimpleReport(TestCase):
    def test_make_simple_report(self):
        os.chdir('demo/make_simple_report')
        if os.path.isfile('reports/demo_report.html'):
            os.remove('reports/demo_report.html')
        try:
            run_demo.main()
        except:
            print('simple report demo raised an exception')
            raise
        os.chdir('../..')
        with open('tests/in/demo_make_simple_report_out.html') as correct_file:
            correct_file_contents = correct_file.read()
            correct_file_contents = re.sub('(?:<script>.+</script>)|(?:fig_[^"]+)', '', correct_file_contents,
                                           flags=re.S)
        with open('demo/make_simple_report/reports/demo_report.html') as output_file:
            output_file_contents = output_file.read()
            output_file_contents = re.sub('(?:<script>.+</script>)|(?:fig_[^"]+)', '', output_file_contents, flags=re.S)
        self.maxDiff = None
        self.assertEqual(correct_file_contents, output_file_contents, 'output file incorrect')
