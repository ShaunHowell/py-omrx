import pandas as pd


def assert_correct_result(df, correct_result):
    df = df.sort_index(axis=1)
    correct_result = correct_result.sort_index(axis=1)
    if len(df.columns) != len(correct_result.columns) or not df.columns.equals(
            correct_result.columns):
        raise ValueError(
            f'different columns: {df.columns} != {correct_result.columns}')
    for df_row, correct_row in zip(df.iterrows(), correct_result.iterrows()):
        df_row = df_row[1]
        correct_row = correct_row[1]
        df_cells = df_row.iteritems()
        correct_cells = correct_row.iteritems()
        for df_cell, correct_cell in zip(df_cells, correct_cells):
            if df_cell != correct_cell:
                print(
                    f'df cell type:{type(df_cell)}, correct type:{type(correct_cell)}'
                )
                df_row.name = 'observed'
                correct_row.name = 'correct'
                debug_df = pd.concat([df_row, correct_row], axis=1)
                debug_df['equal'] = debug_df.apply(
                    lambda row: row['observed'] == row['correct'], axis=1)
                raise ValueError(
                    f'{df_cell} != {correct_cell}\n{debug_df.to_string()}')
    return True
