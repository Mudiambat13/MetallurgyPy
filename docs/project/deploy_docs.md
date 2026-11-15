# Deploying the documentation

The site is built with MkDocs Material and published by GitHub Actions to GitHub Pages. Nothing runs on your machine to publish it: you push, and the `docs` workflow does the rest.

Address once deployed: `https://mudiambat13.github.io/MetallurgyPy/`

## One-time setup

1. Push the repository to `github.com/Mudiambat13/MetallurgyPy` (branch `main`).
2. On GitHub, open **Settings → Pages**.
3. Under **Build and deployment → Source**, choose **GitHub Actions**. (Do not choose "Deploy from a branch".)
4. Open the **Actions** tab. The `docs` workflow starts on the push. If it did not, run it with **Run workflow**.
5. When the `deploy` job is green, the site is live at the address above. The first deployment can take a minute or two.

!!! warning "Repository name and address"
    `site_url` and `repo_url` in `mkdocs.yml` assume the account `Mudiambat13` and the repository name `MetallurgyPy`. If you use another name, edit those two lines, otherwise links and the sitemap point to the wrong place.

## What the workflow does

| Step | Purpose |
|---|---|
| Install `docs/requirements.txt` | MkDocs, Material theme, pymdown extensions |
| `gen_model_reference.py --check` | Fails if the equations/assumptions on the scientific pages differ from the code |
| `gen_api_reference.py --check` | Fails if the API pages differ from the docstrings |
| `mkdocs build --strict` | Fails on any broken link, missing page or warning |
| Upload and deploy | Publishes the `site/` folder (only on pushes, not on pull requests) |

## Keeping the documentation in step with the code

The scientific model sections and the API pages are generated from the code. After changing a model or a docstring:

```bash
python tools/gen_model_reference.py
python tools/gen_api_reference.py
```

Commit the regenerated files. The tests and the workflow refuse a stale page.

## Preview locally

```bash
pip install -r docs/requirements.txt
mkdocs serve          # http://127.0.0.1:8000
mkdocs build --strict # same check as CI
```

## If something goes wrong

- **Build fails with a warning**: strict mode turns warnings into errors. Read the first warning in the log; usually a broken link or a page missing from `nav`.
- **404 after a green deployment**: Pages source is not set to *GitHub Actions* (step 3).
- **Formulas not rendered**: MathJax is loaded from `unpkg.com`; a network that blocks it shows the raw LaTeX.
- **Private repository**: GitHub Pages for private repositories needs a paid GitHub plan.
