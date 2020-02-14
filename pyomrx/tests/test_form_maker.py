from pprint import pprint as pp
import openpyxl
from pyomrx.core.form_maker import FormMaker
import pytest
from pathlib import Path


def test_translate_sub_range_to_new_parent(res_folder):
    form_maker = FormMaker(
        str(Path(res_folder) / 'Absence register v31.xlsx'), 'temp')
    # wb = openpyxl.load_workbook('pyomrx\\tests\\res\\Absence register v31.xlsx', data_only=True)
    page_1_range = form_maker.wb.get_named_range('page_1').attr_text
    page_2_range = form_maker.wb.get_named_range('page_2').attr_text
    circles_att_range = form_maker.wb.get_named_range(
        'circles_attendance').attr_text
    translated_circles_range = form_maker.translate_sub_range_to_new_parent(
        circles_att_range, page_1_range, page_2_range)
    assert translated_circles_range == 'template!$D$32:$AH$56'


def test_make_form_doesnt_crash(res_folder):
    form_maker = FormMaker(
        str(Path(res_folder) / 'Absence register v31.xlsx'), 'temp')
    config = form_maker.make_form()


def test_no_prefix_if_none(res_folder):
    form_maker = FormMaker(
        str(Path(res_folder) / 'Absence register v31.xlsx'), 'temp')
    config = form_maker.make_form()
    assert next(
        filter(
            lambda circle_group: circle_group['name'] == 'attendance',
            config['template']['sub_forms']['sub_form_templates'][0]
            ['circles']))['column_prefix'] == None


if __name__ == '__main__':
    pytest.main(['-sk', 'test_no_prefix_if_none'])
