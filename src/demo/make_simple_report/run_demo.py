# TODO: make dummy csv input file which is ok to add to repo

import pandas as pd
import matplotlib.pyplot as plt, mpld3
import seaborn as sns
import numpy as np
import scipy.stats as stats


def convert_pvalue_to_symbol(pvalue, legend=None):
    legend = {'*': 0.05, '**': 0.01, '***': 0.001} if legend == None else legend
    for symbol, val in sorted(legend.items(), key=lambda item: item[1]):
        if pvalue < val:
            return symbol
    return ''


def categorical_auto_report(df, target_col):
    # This shouldn't be modifying an html string directly, but it's good enough for this demo
    html_string = ''
    prop_cycle = plt.rcParams['axes.prop_cycle']
    colors = prop_cycle.by_key()['color']
    target_data = df[target_col]
    # Find categorical column labels
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns
    # Compare performance between all options for each category
    for col in categorical_cols:
        html_string += '<h1 id={}>Comparison by {}</h1>\n'.format(col.replace(' ', '_'), col.lower())
        col_fig, (kde_axes, bar_axes) = plt.subplots(2, 1, gridspec_kw={'height_ratios': [3, 1]})
        kde_axes.set_xlim(target_data.min(), target_data.max())
        bar_axes.set_xlim(target_data.min(), target_data.max())
        averages = []
        options_target_data = []
        options = df[col].unique()
        # create kde plot (~smooth frequency distribution) and bar chart of means
        for i, option in enumerate(options):
            option_target_data = df[df[col] == option][target_col]
            sns.kdeplot(option_target_data, shade=True, label=option, ax=kde_axes, color=colors[i])
            averages.append(option_target_data.mean())
            options_target_data.append(option_target_data)
        bar_axes.barh(np.arange(len(options)), averages, color=colors, tick_label=options)
        # t-test for each option: is the difference of its mean to the mean of the other data statistically significant?
        ttest_results = []
        for i, option_target_data in enumerate(options_target_data):
            comparison_data = options_target_data[:i] + options_target_data[i + 1:]
            option_ttest_results = [
                convert_pvalue_to_symbol(
                    stats.ttest_ind(option_target_data, alt, equal_var=False, nan_policy='raise')[1])
                for alt in comparison_data]
            option_ttest_results.insert(i, '-')
            ttest_results.append(option_ttest_results)
        ttest_df = pd.DataFrame(ttest_results, index=options, columns=options)
        html_string += mpld3.fig_to_html(col_fig) + '\n'
        html_string += '<p>Statistical significance:</p>\n' + ttest_df.to_html() + '\n'
        html_string += 'Note: * p &lt .05, ** p &lt .01, *** p &lt .001\n'
    # Add menu to the top of the report for navigation
    dropdown_html = ''.join(
        [' ' * 16 + '<a href="#{}">{}</a>\n'.format(cat.replace(' ', '_'), cat) for cat in categorical_cols])
    html_string_start = ''' 
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" type="text/css" href="report_style.css">
</head>
<body>
    <div class="navbar">
        <a href="#">Top</a>
        <div class="dropdown">
            <button class="dropbtn">Choose comparison 
                <i class="fa fa-caret-down"></i>
            </button>
            <div class="dropdown-content">
{}
            </div>
        </div>
    </div>
'''.format(dropdown_html)
    html_string = html_string_start + html_string + '</body>\n</html>'
    return html_string


def main():
    df = pd.read_csv('data/exam_results/demo_exam_results.csv')
    df = df.dropna()  # TODO: more data cleaning here to fill where possible and assert more cleanliness
    df = df[df['Student Level'] != '0']
    df = df[df['Paper Name'] != '0']

    with open('reports/demo_report.html', 'w') as out_file:
        out_file.write(categorical_auto_report(df, 'Percentage'))


if __name__ == '__main__':
    main()
