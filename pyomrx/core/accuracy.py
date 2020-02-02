import json

import pandas as pd


def find_omr_accuracy(omr_output_location,
                      manual_location,
                      form_design_loc,
                      omr_mode='exam'):
    omr_df = pd.read_csv(omr_output_location)
    man_df = pd.read_csv(manual_location)
    # num_omr_responses = omr_df.filter(regex='[c_|q_][0-9]').isnull().sum(axis=1)
    form_designs = json.load(open(form_design_loc))
    circles_per_box = {
        int(code): len(config['code'] + config['questions'])
        for code, config in form_designs.items()
    }
    if omr_mode == 'exam':
        merged_df = man_df.merge(
            omr_df, how='inner', on=['file_name', 'box_no'])
        merged_df['num_circles'] = merged_df['paper_code_x'].map(
            circles_per_box)
        merged_df['num_circles'] = merged_df[
            'num_circles'] + 1  # plus one for the paper code circle
    elif omr_mode == 'attendance':
        merged_df = man_df.merge(
            omr_df, how='inner', on=['file_name', 'box_no', 'student_number'])
        merged_df['num_circles'] = 34
    else:
        raise Exception
    print('INFO: omr data:\n{}'.format(omr_df.head(100).to_string()))
    print('INFO: manual data:\n{}'.format(man_df.head(100).to_string()))
    # print('INFO: merged data data:\n{}'.format(
    #     merged_df.head(100).to_string()))

    num_not_marked_manually = len(omr_df) - len(merged_df)
    if num_not_marked_manually != 0:
        print(
            'WARNING: {} not marked manually'.format(num_not_marked_manually))
    num_correct_responses = 0
    num_incorrect_responses = 0
    num_abstentions = 0
    merged_df['row_wrong'] = 0
    merged_df['abstentions'] = 0
    for q_id in omr_df.filter(
            regex=
            '((?:\A|_)[0-9])|(paper_code)|(school_code)|(class_code)|(sheet_number)'
    ).columns.value.tolist():
        print('processing question ', q_id)
        for i, row in merged_df.iterrows():
            if pd.isnull(row['{}_x'.format(q_id)]):
                continue
            if int(row['{}_y'.format(q_id)]) == -3:
                num_abstentions += 1
                merged_df.loc[
                    i, 'abstentions'] = merged_df.loc[i, 'abstentions'] + 1
                continue
            if int(row['{}_x'.format(q_id)]) == int(row['{}_y'.format(q_id)]):
                num_correct_responses += 1
            else:
                num_incorrect_responses += 1
                merged_df.loc[i,
                              'row_wrong'] = merged_df.loc[i, 'row_wrong'] + 1
    total_responses = num_incorrect_responses + num_abstentions + num_correct_responses
    assert total_responses == merged_df['num_circles'].sum(), \
        'wrong number of answers somehow, got {} instead of {}'.format(total_responses, merged_df['num_circles'].sum())
    print('incorrect: {}, abstentions: {},'
          ' correct: {}, total: {}'.format(
              num_incorrect_responses, num_abstentions, num_correct_responses,
              total_responses))
    print(merged_df.to_string())
    return dict(
        incorrect=num_incorrect_responses,
        abstentions=num_abstentions,
        correct=num_correct_responses,
        not_marked_manually=num_not_marked_manually,
        total_responses=total_responses)
