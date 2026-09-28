# Résumé source and editorial notes

Prepared September 7, 2026 as a balanced software engineering and ML résumé.

## Source selection

The conversation referred to three résumés without identifying filenames. These three recent, distinct versions in Downloads were used as the stated working assumption:

- `Kshitiz_Neupane_Resume_Automation_Web_Systems.pdf`: internship, research pipeline, web development, tooling, current university email.
- `Kshitiz_Neupane_Resume_2026_Summer.pdf`: WorkForge AI, research narrative, F1 results.
- `Kshitiz_Neupane_Resume_2026.pdf`: mathematics coursework, ML foundations, data analysis skills, Bayesian/PCA portfolio entries.

The existing portfolio PDF duplicated the Automation/Web Systems résumé's content. Original source PDFs were left unchanged outside the portfolio. The new PDF preserves the common one-page US Letter layout, Computer Modern serif type, centered contact header, section rules, aligned dates, and concise bullet lists.

## Evidence and choices

- [ShiftGuard README](https://github.com/kshitiz-tech/ShiftGuard/blob/main/README.md): 12,000 model-window evaluations, 3 datasets, 5 classifiers, 5 seeds, and overall failure ROC-AUC 0.799 (95% CI 0.760–0.832). These are recorded benchmark results, not a claim of performance in production. The final wording preserves variation across datasets and shifts.
- [F1 README](https://github.com/kshitiz-tech/F1_data_analysis/blob/main/README.md): holdout podium ROC-AUC 0.943 and finish-position MAE 3.554, pre-race feature separation, and saved pipelines.
- [ManageYourHome README](https://github.com/kshitiz-tech/ManageYourHome/blob/main/README.md): React/TypeScript, Django REST, JWT refresh, authenticated endpoints, and per-user calculations. Pagination is stated in the Automation/Web Systems résumé.
- [Money Manager README](https://github.com/kshitiz-tech/MoneyManagers/blob/main/README.md): seven screens, SQLite persistence, password hashing, Docker, and browser access via noVNC. Retained on the website; omitted from the one-page résumé to prioritize breadth.
- [Bayesian regression README](https://github.com/kshitiz-tech/Bayesian-Linear-Regression/blob/main/README.md): MAP, posterior inference, predictive uncertainty, and California Housing. Retained on the website.
- WorkForge AI is supported by the Summer résumé. No public repository was found in the account's public listing, so no repository link or private/public status was invented.
- The research role's 86% recall and over 92% precision come from the Automation/Web Systems résumé. The public research README does not substantiate those numbers, so the résumé says “reported”; no independent experiment was run in this task.
- Omitted SEU results because the source simultaneously claims “sub-millisecond” deletion and 6.7 ms latency. The stronger résumé uses corroborated benchmark work rather than choosing between conflicting figures.
- Mechanistic interpretability is a user-requested research interest. Specific interests in representations, circuits, causal interventions, and reliability are drafted areas of interest, not claims of completed research or publications.
- The “Currently working on” section uses the requested interpretability focus and the most recently updated public project, ShiftGuard. ShiftGuard's ongoing status is an editorial assumption and can be changed in `now` when priorities change.
- Education, GPA, graduation, internship dates, and the ongoing research role follow the source résumés. No employment verification was performed.

## Future edits

Edit `content/profile.json`, then run `python3 scripts/build.py --resume`. The same contact details and selected project records generate both the website and résumé. A project appears in the PDF only when `resume` is `true`; a separate `featured` flag controls its website placement. The build fails if the résumé spills onto a second page or contains overflowing text.

These notes are included in the source package for maintainability. They are excluded from the public website artifact.
