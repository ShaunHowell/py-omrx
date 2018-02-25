from pathlib import Path
import pandas as pd
import json
import numpy as np


def join_results_metadata(exam_results, exam_ids, student_metadata, form_designs):
    exam_results['student_id'] = sum(
        [exam_results['c_{}'.format(i)].astype('int').values * 10 ** (4 - i) for i in range(1, 5)])
    form_designs_summary = dict()
    for paper_id, design in form_designs.items():
        circles_per_question = design['questions']
        num_questions = len(circles_per_question)
        max_marks = sum(circles_per_question) - len(circles_per_question)
        form_designs_summary.update({paper_id: {'num_questions': num_questions, 'max_marks': max_marks}})
    form_designs_summary = pd.DataFrame.from_dict(form_designs_summary, orient='index')
    form_designs_summary['exam_id'] = form_designs_summary.index.astype('int')
    joined_df = exam_results.merge(exam_ids, left_on='paper_code', right_on='id')
    joined_df = joined_df.merge(student_metadata, left_on='student_id', right_on='ID').dropna(how='all', axis=1)
    joined_df = joined_df.merge(form_designs_summary, left_on='paper_code', right_on='exam_id')
    return joined_df


def calc_percentage(joined_exam_results):
    df = joined_exam_results.copy()
    df['percentage'] = df.apply(lambda row: sum(
        [row['q_{}'.format(i)] for i in range(1, row['num_questions'])]) * 100 / row['max_marks'], axis=1)
    return df


def preprocess(exam_results_path, metadata_folder, output_folder=None):
    exam_results = pd.read_csv(exam_results_path)
    exam_ids = pd.read_csv(str(Path(metadata_folder) / 'exam_ids.csv'))
    student_metadata = pd.read_csv(str(Path(metadata_folder) / 'student_metadata.csv'))
    form_designs = json.load(open(str(Path(metadata_folder) / 'omr_form_designs.json')))
    joined_df = join_results_metadata(exam_results, exam_ids, student_metadata, form_designs)
    joined_df = calc_percentage(joined_df)
    if output_folder:
        if not Path(output_folder).exists():
            Path(output_folder).mkdir()
        joined_df.to_csv(str(Path(output_folder) / 'full_dataset.csv'), index=False)
    return joined_df


if __name__ == '__main__':
    preprocess('demo/data_extract_and_merge/data/exam_results/demo_output_exam_results.csv',
               'demo/data_extract_and_merge/data/ext', 'demo/data_extract_and_merge/data/exam_results')
