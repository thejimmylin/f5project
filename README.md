# F5 Project

Finlab Fugle for financial freedom.

# Quickstart

## With pipx

Use [pipx](https://github.com/pypa/pipx) to create your F5 project with a template and install all dependencies.

```sh
cd ~/repos
pipx run --no-cache f5project create-project my_f5project
cd my_f5project
pip install -r requirements.txt
```

## With traditional way

If you don't feel like using pipx, you can also run this with traditional pip.

```sh
cd ~/repos
mkdir my_f5project
cd my_f5project
python3 -m venv .venv
source .venv/bin/activate
pip install f5project
f5project f5project create-project my_f5project
pip install -r requirements.txt
```

Then, follow the instructions:

1. Put all your secrets in `.secrets/index.json` file
2. Run `python main.py` to see if it works
3. Run `scripts/setup_github_secrets.py` to sync your secrets with Github secrets
4. [Optional] Follow the instructions in `scripts/setup_github_secrets.py` to make it a pre-push Git hook
5. `git push` to deploy your code according to `.github/workflows/main.yml`

The, you can follow the instructions above.

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
