from collections import defaultdict
import io
import os
import os.path as op
import shutil

import nbformat
import nbgrader
import nbgrader.api

class MDExporter(nbgrader.plugins.ExportPlugin):
    """
    Exports the graders into a directory as markdown files, one per student.
    """
    def export(self, gradebook):
        dest = self.to if self.to else 'grades'
        self.log.info('Exporting grades to directory {}'.format(dest))

        students = defaultdict(list)

        for assignment in filter(lambda g: g.num_submissions > 0, gradebook.assignments):
            for student in gradebook.students:
                # Submission data. Assignment name, score, max score
                data = [assignment.name, 0, assignment.max_score]
                try:
                    submission = gradebook.find_submission(assignment.name, student.id)
                    data[1] = submission.score
                except nbgrader.api.MissingEntry:
                    pass
                students[student.id].append(data)

        for student, scores in students.items():
            # Filter students who have not submitted anything
            if not scores:
                continue

            out_dir = op.join(dest, student)
            if op.exists(out_dir):
                shutil.rmtree(out_dir)
            os.makedirs(out_dir)

            ss = io.StringIO()
            print('## Grades\n', file=ss)
            print('### Tests\n', file=ss)
            self.print_type(scores, 'Test', ss)
            self.print_type(scores, 'Homework', ss)

            # Write a notebook with a single Markdown cell
            nb = nbformat.v4.new_notebook()
            cell = nbformat.v4.new_markdown_cell(ss.getvalue())
            nb.cells.append(cell)
            with open(op.join(out_dir, 'grades.ipynb'), 'wt') as outf:
                nbformat.write(nb, outf)

    @staticmethod
    def print_type(scores, ass_type, outf):
        """Prints the results of a certain type of assignments to the .md file."""
        print('| Assignment | Score | Max. score |', file=outf)
        print('| :--------- | ----: | ---------: |', file=outf)
        for stuff in sorted(filter(lambda s: ass_type in s[0], scores)):
            print('| {} | {} | {} |'.format(*stuff), file=outf)
        print(file=outf)
