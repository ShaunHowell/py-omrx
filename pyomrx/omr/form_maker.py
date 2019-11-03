import copy
from pprint import pprint as pp
import numpy as np
import pandas as pd
import re
import openpyxl as pyxl
import matplotlib.pyplot as plt
import atexit

atexit.register(plt.show)

W_THICK = 2
W_DEFAULT = 1
W_THIN = 0.5
COLS = [pyxl.utils.cell.get_column_letter(i) for i in range(1, 99)]


def get_rectangle_from_range(range_cells, row_dims, col_dims):
    range_columns = [
        pyxl.utils.cell.get_column_letter(cell.column)
        for cell in range_cells[0]
    ]
    range_rows = [row[0].row for row in range_cells]
    form_heights = [row_dims[row]['ht'] for row in range_rows]
    form_widths = [col_dims[col]['width'] for col in range_columns]
    form_height = sum(form_heights)
    form_width = sum(form_widths)
    rows_above = []
    for row in range(1, 9999):
        if row in range_rows:
            break
        rows_above.append(row)
    cols_left = []
    height_above = sum([row_dims[row]['ht'] for row in rows_above])
    for col in COLS:
        if col in range_columns:
            break
        cols_left.append(col)
    width_left = sum([col_dims[col]['width'] for col in cols_left])
    return dict(
        top=-height_above,
        bottom=-(height_above + form_height),
        left=width_left,
        right=width_left + form_width)


def main():
    wb = pyxl.load_workbook(filename='temp/Absence register v28 (kc).xlsx')
    if 'template' not in wb:
        raise FileNotFoundError('couldnt find worksheet called "template"')
    form_sheet = wb['template']
    form_ranges = []
    sub_form_ranges = []
    for named_range in wb.get_named_ranges():
        if re.match('form_[0-9]+', named_range.name):
            form_ranges.append(named_range)
        elif re.match('sub_[0-9]+_[0-9]+', named_range.name):
            sub_form_ranges.append(named_range)
        else:
            print(f'named range {named_range.name} didnt match any regex')

    raw_row_dims = [
        form_sheet.row_dimensions[row].__dict__ for row in range(1, 999)
    ]
    row_dims_df = pd.DataFrame(raw_row_dims).dropna()
    row_dims_df = row_dims_df.set_index('index')
    row_dims = row_dims_df.to_dict(orient='index')
    raw_col_dims = [form_sheet.column_dimensions[col].__dict__ for col in COLS]
    col_dims_df = pd.DataFrame(raw_col_dims).sort_values(by='index')
    col_dims_df['width'] = col_dims_df['width'].apply(lambda val: val if val
                                                      else np.NaN).ffill()
    col_dims_df = col_dims_df.set_index('index')
    col_dims = col_dims_df.to_dict(orient='index')
    if not form_ranges:
        raise FileNotFoundError('no form ranges found')
    form_axs = []
    form_top_lefts = []
    for form_range in sorted(
            form_ranges, key=lambda form_range: form_range.name):
        assert re.match(
            'template!',
            form_range.attr_text), 'form range found in non template worksheet'
        range_cells = form_sheet[form_range.attr_text[9:]]
        form_rectangle = get_rectangle_from_range(
            range_cells=range_cells, row_dims=row_dims, col_dims=col_dims)
        form_fig, form_ax = plt.subplots(1, 1)
        form_top_left = dict(
            top=form_rectangle['top'], left=form_rectangle['left'])
        form_rectangle = localise_rectangle_to_form(form_rectangle,
                                                    form_top_left)
        plot_rectangle(form_rectangle, form_ax, thickness=W_THICK)
        form_axs.append(form_ax)
        form_top_lefts.append(form_top_left)

    if not sub_form_ranges:
        raise FileNotFoundError('no sub form ranges found')
    for sub_form_range in sorted(
            sub_form_ranges, key=lambda sub_form_range: sub_form_range.name):
        assert re.match('template!', sub_form_range.attr_text
                        ), 'form range found in non template worksheet'
        range_cells = form_sheet[sub_form_range.attr_text[9:]]
        print(f'processing {sub_form_range.attr_text[9:]}')
        _, parent_form_id, sub_form_id = sub_form_range.name.split('_')
        sub_form_id = int(sub_form_id)
        parent_form_id = int(parent_form_id)
        sub_form_rectangle = get_rectangle_from_range(
            range_cells=range_cells, row_dims=row_dims, col_dims=col_dims)
        parent_form_top_left = form_top_lefts[parent_form_id]
        sub_form_rectangle = localise_rectangle_to_form(
            sub_form_rectangle, parent_form_top_left)
        parent_form_ax = form_axs[parent_form_id]
        plot_rectangle(sub_form_rectangle, parent_form_ax)

    attendance_config = {'code': []}
    output_config = {'1': attendance_config}
    print('done')


def localise_rectangle_to_form(rectangle, parent_top_left, in_place=False):
    rectangle = rectangle if in_place else copy.deepcopy(rectangle)
    rectangle['top'] = rectangle['top'] - parent_top_left['top']
    rectangle['bottom'] = rectangle['bottom'] - parent_top_left['top']
    return rectangle


def plot_rectangle(rectangle, ax, thickness=W_DEFAULT):
    top = rectangle['top']
    left = rectangle['left']
    bottom = rectangle['bottom']
    right = rectangle['right']
    ax.plot([left, right, right, left, left], [top, top, bottom, bottom, top],
            c='black',
            linewidth=thickness)


if __name__ == '__main__':
    main()
