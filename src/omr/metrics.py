import pandas as pd
import json
import numpy as np


def find_omr_accuracy(omr_output_location, manual_location, form_design_loc):
    omr_df = pd.read_csv(omr_output_location)
    man_df = pd.read_csv(manual_location)
    num_omr_responses = omr_df.filter(regex='[c_|q_][0-9]').isnull().sum(axis=1)
    merged_df = man_df.merge(omr_df, how='inner', on=['file_name', 'box_no'])
    form_designs = json.load(open(form_design_loc))
    circles_per_box = {int(code): len(config['code'] + config['questions']) for code, config in form_designs.items()}
    merged_df['num_circles'] = merged_df['paper_code_x'].map(circles_per_box)
    merged_df['num_circles'] = merged_df['num_circles'] + 1 # plus one for the paper code circle
    print(omr_df.head(100).to_string())
    print(man_df.head(100).to_string())

    num_correct_responses = 0
    num_incorrect_responses = 0
    num_abstentions = 0
    merged_df['row_wrong'] = 0
    merged_df['abstentions'] = 0
    for q_id in omr_df.filter(regex='([c_|q_][0-9])|(paper_code)').columns.values.tolist():
        print('processing question ', q_id)
        for i, row in merged_df.iterrows():
            if pd.isnull(row['{}_x'.format(q_id)]):
                continue
            if int(row['{}_y'.format(q_id)]) == -3:
                num_abstentions += 1
                merged_df.ix[i, 'abstentions'] = merged_df.ix[i, 'abstentions'] + 1
                continue
            if int(row['{}_x'.format(q_id)]) == int(row['{}_y'.format(q_id)]):
                num_correct_responses += 1
            else:
                num_incorrect_responses += 1
                merged_df.ix[i, 'row_wrong'] = merged_df.ix[i, 'row_wrong'] + 1
    assert num_incorrect_responses + num_abstentions + num_correct_responses == merged_df['num_circles'].sum(), \
        'wrong number of answers somehow'
    print('incorrect: {}, abstentions: {},'
          ' correct: {}, total: {}'.format(num_incorrect_responses,
                                           num_abstentions,
                                           num_correct_responses,
                                           num_incorrect_responses + num_abstentions + num_correct_responses))
    print(merged_df.to_string())


if __name__ == '__main__':
    find_omr_accuracy('demo/edge_cases_omr_extraction/data/exam_results/omr_output.csv',
                      'demo/edge_cases_omr_extraction/data/exam_results/human_processed_exam_results.csv',
                      'demo/edge_cases_omr_extraction/data/ext/omr_form_designs.json')
