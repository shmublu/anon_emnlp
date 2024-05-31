from flask import Flask, session, request, redirect, url_for, render_template_string, send_file
from flask_session import Session
from io import BytesIO, TextIOWrapper
import csv

app = Flask(__name__)
app.config['SECRET_KEY'] = 'very_secret_key'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)


user_study_intro = """
User Study: Grading Automatically Generated Output to Logic Puzzles

Welcome to our user study on grading automatically generated solutions to logic puzzles. Your task involves evaluating attempted solutions in the SMT-LIB format (a formal standard where each variable is assigned a value) against provided answer keys.

Instructions:

1. Upload the CSV File:
   Please upload the CSV file you were given and enter the grading code in the designated box below.

2. Evaluate Each Solution:
   On each page, you will be prompted with an attempted solution in SMT-LIB format and an answer key.

3. Interpretability Check:
   First, determine if the model's output is interpretable as an answer. Consider the following:
   - Do the values make sense within the context?
   - Are the types of values consistent with those in the answer key?

   For example:
   - If the answer key has prices and the model gives unrelated integers, the solution is likely ungradable.
   - If the answer key has numbers but the model provides boolean values, the solution is also likely ungradable.
   - If the model outputs ages that are wrong but plausible (e.g., non-negative numbers), type "yes" in the box.

4. Gradable Solutions:
   If the solution is gradable:
   - Specify the total number of points possible.
   - Indicate the number of points that are correct.
   - Provide a detailed explanation for your grading decision.

   Note: When calculating assignments:
   - Matching 3 people with an item counts as 3 assignments.
   - Matching 3 people with an item and a price counts as 6 assignments, not 9.

Thank you for participating in this study. Your evaluations will help us improve the accuracy and reliability of automatically generated solutions to logic puzzles.
"""
def parse_ranges(ranges_str):
    """Parse the input string of line ranges into a list of integers."""
    ranges = []
    for part in ranges_str.split(','):
        if '-' in part:
            start, end = map(int, part.split('-'))
            ranges.extend(range(start, end + 1))
        else:
            ranges.append(int(part))
    return ranges

@app.route('/examples', methods=['GET'])
def show_examples():
    # Sample data for demonstration with an answer key and explanations
    example_puzzles = [
        [
            "1",
            """(error "line 33 column 34: unexpected character")
(error "line 33 column 53: unexpected character")
(error "line 36 column 23: unexpected character")
(error "line 36 column 42: unexpected character")
(error "line 36 column 68: unexpected character")
(error "line 36 column 87: unexpected character")
(error "line 39 column 20: unexpected character")
(error "line 39 column 39: unexpected character")
(error "line 39 column 64: unexpected character")
(error "line 39 column 83: unexpected character")
(error "line 42 column 39: unexpected character")
(error "line 42 column 58: unexpected character")
(error "line 42 column 101: unexpected character")
(error "line 42 column 120: unexpected character")
sat
(
  (define-fun Eighth_Order () Int
    2)
  (define-fun First_Order () Int
    8)
  (define-fun Melissa_Points () Int
    187)
  (define-fun Second_Order () Int
    7)
  (define-fun Seventh_Order () Int
    1)
  (define-fun Natasha_Points () Int
    190)
  (define-fun Evelyn_Points () Int
    184)
  (define-fun Willie_Points () Int
    181)
)""",
            """ Evelyn, 187 points, eighth
Melissa, 184 points, seventh
Natasha, 190 points, first
Willie, 181 points, second """,
            "Careful! Even with errors, the answer can still be interpretable. However, we cannot interpret this because we don't know what Second_Order = 1 means and which person corresponds to. If we could interpret this, there would be 8 total assignments (matching two categories to four people)"
        ],
        [
            "2",
            """sat
(
  (define-fun Mouse_Pos () Int
    2)
  (define-fun Frog_Pos () Int
    1)
  (define-fun Kiwi_Pos () Int
    1)
  (define-fun Cucumber_Pos () Int
    2)
  (define-fun Cat_Pos () Int
    3)
  (define-fun Grapes_Pos () Int
    3)
)""",
            """|        |  1   |    2     |   3    |
| Food   | kiwi | cucumber | grapes |
| Pet    | frog | cat      | mouse  |""",
            "This one is gradable, even if many assignments are incorrect. Because we are finding the position of every assignment, there are 6 total points to get correctly here. It gets 4 of them correct (all except cat and mouse) and thus the score is 4/6."
        ]
    ]
    return render_template_string('''
    <html>
    <head>
        <title>Example Solutions</title>
        <link href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
    <div class="container mt-5">
        <div class="row">
            <div class="col-md-8 offset-md-2">
                <div class="card card-body">
                    <h3 class="text-center">Example Solutions</h3>
                    {% for puzzle in example_puzzles %}
                        <div class="form-group">
                            <label><b>Example {{ loop.index }} - Puzzle:</b></label>
                            <pre>{{ puzzle[1] }}</pre>
                            <label><b>Example {{ loop.index }} - Answer Key:</b></label>
                            <pre>{{ puzzle[2] }}</pre>
                            <label><b>Example {{ loop.index }} - Explanation:</b></label>
                            <p>{{ puzzle[3] }}</p>
                        </div>
                    {% endfor %}
                    <form action="{{ url_for('grade_puzzle') }}">
                        <button type="submit" class="btn btn-primary">Proceed to Grading</button>
                    </form>
                </div>
            </div>
        </div>
    </div>
    </body>
    </html>
    ''', example_puzzles=example_puzzles)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files.get('file')
        if file:
            lines_input = request.form['lines_to_grade']
            lines_to_grade = parse_ranges(lines_input)
            stream = BytesIO(file.read())
            stream.seek(0)
            reader = csv.reader(TextIOWrapper(stream, encoding='utf-8'))
            puzzles = [(i, row) for i, row in enumerate(reader) if i in lines_to_grade]  # Include line numbers
            session['puzzles'] = puzzles
            session['current_index'] = 0
            return redirect(url_for('show_examples'))
    return render_template_string('''
    <html>
    <head>
        <title>Upload CSV File</title>
        <link href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
        <style>
            .disclaimer { margin-top: 20px; padding: 15px; background-color: #f8f9fa; border: 1px solid #ddd; }
        </style>
    </head>
    <body>
    <div class="container mt-5">
        <div class="row">
            <div class="col-md-6 offset-md-3">
                <div class="card card-body">
                    <h3 class="text-center">Upload CSV File for Auto-Grading</h3>
                    <div class="disclaimer">
                         <h2>Instructions:</h2>

    <ol>
        <li>
            <h3>Upload the CSV File:</h3>
            <p>Please upload the CSV file you were given and enter the grading code in the designated box below.</p>
        </li>
        <li>
            <h3>Evaluate Each Solution:</h3>
            <p>On each page, you will be prompted with an attempted solution in SMT-LIB format and an answer key.</p>
        </li>
        <li>
            <h3>Interpretability Check:</h3>
            <p>First, determine if the model's output is interpretable as an answer. Consider the following:</p>
            <ul>
                <li>Do the values make sense within the context?</li>
                <li>Are the types of values consistent with those in the answer key?</li>
            </ul>
            <p>For example:</p>
            <ul>
                <li>If the answer key has prices and the model gives unrelated integers, the solution is likely ungradable.</li>
                <li>If the answer key has numbers but the model provides boolean values, the solution is also likely ungradable.</li>
                <li>If the model outputs ages that are wrong but plausible (e.g., non-negative numbers), type "yes" in the box.</li>
            </ul>
        </li>
        <li>
            <h3>Gradable Solutions:</h3>
            <p>If the solution is gradable:</p>
            <ul>
                <li>Specify the total number of points possible (based on the number of assignments).</li>
                <li>Indicate the number of points that are correct.</li>
                <li>Provide a detailed explanation for your grading decision.</li>
            </ul>
        </li>
    </ol>

    <p>Thank you for participating in this study. Your evaluations will help us improve the accuracy and reliability of automatically generated solutions to logic puzzles.</p>
</body>
                    </div>
                    <form method="post" enctype="multipart/form-data">
                        <div class="form-group mb-2">
                            <input type="file" class="form-control" name="file" required>
                        </div>
                        <div class="form-group mx-sm-3 mb-2">
                            <input type="text" class="form-control" name="lines_to_grade" placeholder="Lines to autograde (e.g., 1-5,7,10-12)" required>
                        </div>
                        <button type="submit" class="btn btn-primary mb-2">Upload and Grade</button>
                    </form>
                </div>
            </div>
        </div>
    </div>
    </body>
    </html>
    ''')

@app.route('/grade', methods=['GET', 'POST'])
def grade_puzzle():
    if 'current_index' not in session:
        return redirect(url_for('upload_file'))

    index = session['current_index']
    puzzles = session['puzzles']

    if request.method == 'POST' and index < len(puzzles):
        line_number, puzzle = puzzles[index]
        gradeable = request.form['gradeable'].lower() == 'yes'
        if gradeable:
            puzzle.extend([
                'yes',
                request.form['total_possible'],
                request.form['points_earned'],
                request.form['explanation']
            ])
        else:
            puzzle.extend([
                'no',
                '0',
                '0',
                'Not applicable'
            ])
        session['current_index'] += 1
        index += 1

    if index >= len(puzzles):
        return redirect(url_for('download_results'))

    line_number, puzzle = puzzles[index]
    return render_template_string('''
    <html>
    <head>
        <title>Grade Puzzle</title>
        <link href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
        <script>
            function toggleFields() {
                var gradeable = document.getElementById('gradeable').value.toLowerCase();
                var display = (gradeable === 'yes') ? "block" : "none";
                document.getElementById('gradingFields').style.display = display;
            }
        </script>
    </head>
    <body>
    <div class="container mt-5">
        <div class="row">
            <div class="col-md-6 offset-md-3">
                <div class="card card-body">
                    <h3>Puzzle {{ index }}</h3>
                    <form method="post">
                        <div class="form-group">
                            <label>Attempted Solution:</label>
                            <pre>{{ puzzle[2] }}</pre>
                        </div>
                        <div class="form-group">
                            <label>Answer Key:</label>
                            <pre>{{ puzzle[-1] }}</pre>
                        </div>
                        <div class="form-group">
                            <label>Is the solution gradeable? (yes/no):</label>
                            <input type="text" class="form-control" name="gradeable" id="gradeable" oninput="toggleFields();" required>
                        </div>
                        <div id="gradingFields" style="display:none;">
                            <div class="form-group">
                                <label>Total Points Possible:</label>
                                <input type="number" class="form-control" name="total_possible" min="0">
                            </div>
                            <div class="form-group">
                                <label>Points Earned:</label>
                                <input type="number" class="form-control" name="points_earned" min="0">
                            </div>
                            <div class="form-group">
                                <label>Explanation for Grading:</label>
                                <textarea class="form-control" name="explanation"></textarea>
                            </div>
                        </div>
                        <button type="submit" class="btn btn-primary">Submit and Next</button>
                    </form>
                </div>
            </div>
        </div>
    </div>
    </body>
    </html>
    ''', puzzle=puzzle, index=line_number)

@app.route('/download', methods=['GET'])
def download_results():
    if 'puzzles' not in session:
        return redirect(url_for('upload_file'))

    output = BytesIO()
    text_output = TextIOWrapper(output, encoding='utf-8', write_through=True)
    writer = csv.writer(text_output)
    writer.writerow(['Line Number', 'Attempted Solution', 'Answer Key', 'Gradeable', 'Total Possible', 'Points Earned', 'Explanation'])

    for line_number, puzzle in session.get('puzzles', []):
        writer.writerow([
            line_number-1,  # puzzle number
            puzzle[2],  # attempted solution
            puzzle[6],  # answer key
            puzzle[7],  # is gradeable as determined by user
            puzzle[8],  # total points possible as determined by user
            puzzle[9],  # points given by user
            puzzle[10]  # explanation
        ])

    text_output.flush()
    text_output.detach()
    output.seek(0)  # Ensure the stream is at the beginning

    return send_file(
        output,
        mimetype="text/csv",
        as_attachment=True,
        download_name="graded_results.csv"
    )

if __name__ == '__main__':
    app.run(debug=True)
