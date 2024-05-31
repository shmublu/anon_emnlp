import csv
from collections import defaultdict
from scipy.stats import spearmanr

def parse_fraction(fraction):
    """ Helper function to parse a fraction string 'X/Y' into a float X/Y """
    num, denom = map(int, fraction.split('/'))
    return num / denom

def compare_grades(user_csv, llm_csv, stats, overlaps, user_grades, llm_grades):
    with open(user_csv, newline='') as user_file, open(llm_csv, newline='') as llm_file:
        user_reader = csv.reader(user_file)
        llm_reader = csv.reader(llm_file)
        
        next(user_reader)  # Skip headers
        next(llm_reader)
        
        llm_grades_list = list(llm_reader)  # Read LLM grades into a list for easy access

        for user_row in user_reader:
            if user_row[3].strip().lower() == "yes":
                line_number = int(user_row[0]) + 1
                user_grade_string = f"{user_row[5]}/{user_row[4]}"
                user_grade_fraction = parse_fraction(user_grade_string)

                if line_number < len(llm_grades_list):
                    llm_row = llm_grades_list[line_number - 1]
                    llm_grade_fraction = parse_fraction(llm_row[5])
                    
                    user_grades.append(user_grade_fraction)
                    llm_grades.append(llm_grade_fraction)
                    
                    absolute_difference = abs(user_grade_fraction - llm_grade_fraction)
                    stats['total_absolute_difference'] += absolute_difference
                    stats['count_compared'] += 1
                    stats['total_relative_difference'] += user_grade_fraction - llm_grade_fraction

                    if absolute_difference <= 0.01:
                        stats['exact_match_count'] += 1

                    if user_grade_fraction == 1 or llm_grade_fraction == 1:
                        stats['either_perfect'] += 1  # Increment if either user or LLM grades perfectly

                    if user_grade_fraction == 1 and llm_grade_fraction == 1:
                        stats['perfect_agreement_count'] += 1

                    if user_grade_fraction == 1 and llm_grade_fraction != 1:
                        stats['user_perfect_not_llm'] += 1
                    if user_grade_fraction != 1 and llm_grade_fraction == 1:
                        stats['llm_perfect_not_user'] += 1

                    if user_grade_fraction < llm_grade_fraction:
                        stats['llm_over_estimated'] += 1
                    elif user_grade_fraction > llm_grade_fraction:
                        stats['llm_under_estimated'] += 1

                    overlaps[llm_csv].setdefault(line_number, []).append((user_grade_fraction, llm_grade_fraction))

def analyze_overlaps(overlaps):
    overlap_results = {}
    for llm_csv, line_grades in overlaps.items():
        for line, grades in line_grades.items():
            if len(grades) > 1:
                user_grades = [grade[0] for grade in grades]
                llm_grade = grades[0][1]
                min_grade = min(user_grades)
                max_grade = max(user_grades)
                if llm_grade >= min_grade and llm_grade <= max_grade:
                    overlap_results[(llm_csv, line)] = 'LLM grade within the range'
                else:
                    overlap_results[(llm_csv, line)] = 'LLM grade outside the range'
    return overlap_results

# Initialize data structures
stats = defaultdict(int)
overlaps = defaultdict(dict)
user_grades = []
llm_grades = []
csv_pairs = [('shmuel_graded_corrsorli.csv', 'orli.csv'),('graded_results_orli.csv', 'orli.csv'),]

# Process each CSV pair
for user_csv, llm_csv in csv_pairs:
    compare_grades(user_csv, llm_csv, stats, overlaps, user_grades, llm_grades)

# Compute Spearman correlation and aggregate statistics
spearman_corr, _ = spearmanr(user_grades, llm_grades)
average_absolute_difference = stats['total_absolute_difference'] / stats['count_compared']
average_relative_difference = stats['total_relative_difference'] / stats['count_compared']
percent_llm_over_estimated = (stats['llm_over_estimated'] / stats['count_compared'] * 100)
percent_llm_under_estimated = (stats['llm_under_estimated'] / stats['count_compared'] * 100)
percent_exact_match = (stats['exact_match_count'] / stats['count_compared'] * 100)
percent_perfect_agreement = (stats['perfect_agreement_count'] / stats['either_perfect'] * 100) if stats['either_perfect'] > 0 else 0

final_stats = {
    "User perfect, LLM not": stats['user_perfect_not_llm'],
    "LLM perfect, User not": stats['llm_perfect_not_user'],
    "Average absolute difference": average_absolute_difference,
    "Average relative difference": average_relative_difference,
    "Percent LLM overestimated": percent_llm_over_estimated,
    "Percent LLM underestimated": percent_llm_under_estimated,
    "Percent exact match within epsilon": percent_exact_match,
    "Percent perfect agreement (adjusted)": percent_perfect_agreement,
    "Spearman correlation": spearman_corr,
    "Total Compared": stats['count_compared']
}

overlap_analysis = analyze_overlaps(overlaps)

# Output the final statistics and overlap analysis
print("Final Statistics:", final_stats)
print("Overlap Analysis:", overlap_analysis)

