from analysis.preprocessing import *
from analysis.processing import *
from analysis.utils import convert_pvalue_to_symbol
import matplotlib.pyplot as plt
import seaborn as sns
import mpld3
import statsmodels as stats
from shutil import copy


def categorical_auto_report(df, target_col):
    # FIXME: This shouldn't be modifying an html string directly, but it's good enough for a basic demo
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
            print('INFO: plotting frequency distribution for {}: {}'.format(col, option))
            option_target_data = df[df[col] == option][target_col]
            try:
                sns.kdeplot(option_target_data, shade=True, label=option, ax=kde_axes, color=colors[i])
            except np.linalg.linalg.LinAlgError:
                print('ERROR: only {} students with {}: {}, and all had the same {}: not plotting'.format(
                    len(options_target_data), col, option, target_col))
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

def make_auto_report(input_file_path,output_folder,ext_folder = None):
    df = pd.read_csv(input_file_path)
    df = df.dropna(how = 'all')  # TODO: more data cleaning here to fill where possible and assert more cleanliness
    for col in df.select_dtypes(include=['object', 'category']).columns:
        df = df[df[col] != '0']
    df = df.drop('file_name', axis=1)

    if not Path(output_folder).exists():
        Path(output_folder).mkdir()
    with open(str(Path(output_folder)/'demo_report.html'), 'w') as out_file:
        out_file.write(categorical_auto_report(df, 'percentage'))
    if ext_folder:
        copy(str(Path(ext_folder)/'report_style.css'),output_folder)
