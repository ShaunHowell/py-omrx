from analysis.processing import *
import pandas as pd


def main():
    df = pd.read_csv('data/exam_results/demo_exam_results.csv')
    df = df.dropna()  # TODO: more data cleaning here to fill where possible and assert more cleanliness
    df = df[df['Student Level'] != '0']
    df = df[df['Paper Name'] != '0']

    with open('reports/demo_report.html', 'w') as out_file:
        out_file.write(categorical_auto_report(df, 'Percentage'))


if __name__ == '__main__':
    main()
