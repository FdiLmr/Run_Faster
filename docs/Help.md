### Branches
Keep main or master as your stable branch

Create a dev branch:


git checkout -b dev
git push -u origin dev

✔️ When working on features, branch from dev:

git checkout -b feat/strava-auth

Later:

git checkout dev
git merge feat/strava-auth

Keep commit messages clean:

feat: add Strava OAuth flow
fix: handle missing cadence
chore: clean up README

### CI/CD

### Black
black tests/test_sanity.py to reformat

