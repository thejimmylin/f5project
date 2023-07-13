# F5 Project

Finlab Fugle for financial freedom.

# Quickstart

## Pipx (recommended)

Use [pipx](https://github.com/pypa/pipx) to create your F5 project with a template and install all dependencies.

```sh
cd ~/repos
pipx run --no-cache f5project create-project my_f5project
cd my_f5project
pip install -r requirements.txt
```

Then, follow these instructions to make it work:

1. Put all your secrets in `.secrets/index.json` file
2. Run `python main.py` to see if it works
3. Run `scripts/setup_github_secrets.py` to sync your secrets with Github secrets
4. [Optional] Follow the instructions in `scripts/setup_github_secrets.py` to make it a pre-push Git hook
5. `git push` to deploy your code according to `.github/workflows/main.yml`

## Traditional way

If you don't feel like using pipx, you can also run this with traditional pip.

```sh
cd ~/repos
mkdir my_f5project
cd my_f5project
python3 -m venv .venv
source .venv/bin/activate
pip install f5project
f5project f5project create-project .
pip install -r requirements.txt
```

Then, follow these instructions to make it work:

1. Put all your secrets in `.secrets/index.json` file
2. Run `python main.py` to see if it works
3. Run `scripts/setup_github_secrets.py` to sync your secrets with Github secrets
4. [Optional] Follow the instructions in `scripts/setup_github_secrets.py` to make it a pre-push Git hook
5. `git push` to deploy your code according to `.github/workflows/main.yml`

# Why?

This library makes it easier to use Finlab/Fugle with GCF and CD/CD.

When deploying your code on Cloud. Many troubles come up. This library helps you to solve them. Including:

- Read config from a simle JSON file or environment variables, depending on your environment.
- Extract Fugle config and certificate from config, dynamically generate them as needed, by-passing Fugle's restriction that only accepts files as input.
- Provide a decorator to make your function a GCF endpoint, without worrying about the request/response format.
- Simulate GCF request locally.
- Sync Github secrets with local config, make CI/CD easier.

With all of these, you can focus on your trading strategy and iterate faster, letting this library handle the rest.
