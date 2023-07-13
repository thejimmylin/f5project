# F5 Project

Finlab Fugle for financial freedom.

This library is not ready for production. It's still under development. The document is not complete, either.

You may need to read the source code sometimes.

# Install

You can install it from PyPI.

```sh
pip install f5project
```

However, if you haven't used it before, you may want to have a quickstart.

You can do that with [pipx](https://github.com/pypa/pipx).

Then, you can create a project with:

```sh
pipx run f5project create-project my_f5project
```

If you don't feel like using pipx, you can also install it in a virtual environment.

```sh
cd ~/repos/my_f5project
python3 -m venv .venv
source .venv/bin/activate
pip install f5project
f5project create-project .
```

# Why?

This library makes it easier to use Finlab/Fugle with other tools together, such as GCF and Github Action.

When deploying your code on GCF. Some troubles come up and you can't just do it like you do on your local machine. This library helps you to solve these problems. It helps you:

- Read config from json file or environment variables.
- Extract Fugle config and certificate from json file or environment variables, dynamically generate them as needed.
- Login Finlab/Fugle with config, which is a little bit annoying because Fugle SDK asks them as files.
- Provide a decorator to make your function a GCF endpoint, without worrying about the request/response format.
- Simulate GCF request locally.
- Sync Github secrets with local config, make CI/CD easier.

Then you can focus on your trading strategy and iterate faster.

# Usages

1. Put all your secrets in `.secrets/index.json` file
2. Run `python main.py` to see if it works
3. Run `scripts/setup_github_secrets.py` to sync your secrets with Github secrets
4. [Optional] Follow the instructions in `scripts/setup_github_secrets.py` to make it a pre-push Git hook
5. `git push` to deploy your code according to `.github/workflows/main.yml`

# TODO

- Use `pipx` to make it easier to have a quickstart template.
- Dynamically generate `CI/CD` pipeline YAML file, so we can focus on the code.
