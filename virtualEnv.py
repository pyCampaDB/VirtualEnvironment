######################################### PACKAGES ##############################################################
from subprocess import (check_call, call, 
                        CalledProcessError, run as runSubprocess)
from os.path import exists
from os import chdir, getenv, getcwd
from sys import executable, modules
from pkg_resources import (require, DistributionNotFound, 
                           VersionConflict)
from signal import signal, SIGINT


######################################### METHODS ##########################################################################

# avoid exiting the script when executing Ctrl+C
def signal_handler(sign, frame):
    print('Ctrl+C pressed')

# Activate the virtual environment
def call_activate():
    try:
        call('activate.bat', shell=True)
        print('Virtual environment activated'
              ' (only affects this subprocess)\n')
    except Exception as e:
        print(f'Error to activate the virtual environment: {e}\n')


# creates and activates the virtual environment venv
def manage_and_activate_env():
    venv = input('Enter the name of your venv: ')
    venv_path = f'{venv}/Scripts'
    if exists(venv_path):
        chdir(venv_path)
        call_activate()
        chdir('../../')
    else:
        print(f"The package {venv_path} "
              "doesn't exist.\nInstalling venv...\n")
        call([executable, '-m', 'venv', f'{venv}'])
        if exists(venv_path):
            chdir(venv_path)
            call_activate()
            chdir('../../')


# Function to install a package
def check_and_install_package(package):
    try:
        require(package)
        print(f'\nPackage already installed.\n')
    except DistributionNotFound:
        print(f"\nThe package {package} doesn't exist."
              "\nInstalling package...\n")
        check_call([executable, '-m', 'pip', 'install', package])
    except VersionConflict as vc:
        installed_version = vc.dist.version
        required_version = vc.req
        print(f"\nA version's conflict detected:\n"
              f"Version installed: {installed_version}"
              f"Version required: {required_version}"
               "Trying to install the package required\n")
        check_call([executable, '-m', 'pip', 'install', 
                    '--upgrade', package])
    except CalledProcessError as cp:
        print(f"\nAn error occurred: {cp.returncode}\n")
        check_call(([executable, '-m', 'pip', 'install', 
                     '--upgrade', package]))
        check_call([executable, '-m', 'pip', 'install', package])



# Function to install all packages written in requirements.txt
def check_and_install_packages(STANDARD_PACKAGE):
    
    if exists('requirements.txt'):
        req = 'requirements.txt'
    else:
        req = input('Enter the file name: ')
    with open(f"{getcwd()}\\{req}", 'r') as packages:
        for package in packages.readlines():
            if package.strip() in STANDARD_PACKAGE:
                print(f"Package {package.strip()} already installed!\n")
            else:
                check_and_install_package(package.strip())
        packages.close()

# Delete directory path of venv
def delete_venv(venv):
    try:
        runSubprocess(f'rmdir {venv}', 
                      shell=True,
                      check=True)
    except CalledProcessError as cp:
        print(f'An error occurred: {cp.returncode}')


def uninstall_package():
    package = input('Enter the package name: ')
    try:
        runSubprocess(
            f'pip uninstall {package}',
            shell=True,
            check=True
        )
    except CalledProcessError as cp:
        print(f'An error occurred: {cp.returncode}')

# Reset your venv
def reset_venv(venv):
    delete_venv(venv)
    manage_and_activate_env()

def run_script(file):
    try:
        runSubprocess(f"python {file}.py", check=True, shell=True)
    except CalledProcessError as e:
        print(f'An error occurred: {e.stderr.decode()}')

def cmd():
    command = input(f'{getcwd()}: ')
    try:
        runSubprocess(
            command,
            shell=True,
            check=True
        )
    except CalledProcessError as cp:
        print(f'An error occurred: {cp.returncode}')

def upload_docker():
    username = getenv('DOCKER_USERNAME', default='default_username')
    pwd = getenv('DOCKER_PASSWORD', default='default_password')
    requirements = ''
    option1 = ''
    option2 = ''
    while option1 not in ['Y', 'y', 'N', 'n']:
        option1 = input('\nDo you need install dependencies by requirements.txt? [Y/N]: ')
        if option1 not in ['Y', 'y', 'N', 'n']:
            print('\nInvalid option.\n')

    if option1 in ['Y', 'y']:
        requirements = """
# Copy requirements file (if you need)
COPY requirements.txt /app/

# Install dependencies in the virtual environment
RUN pip install --no-cache-dir -r requirements.txt
"""
    while option2 not in ['Y', 'y', 'N', 'n']:
        option2 = input('\nDo you need to install a Jupyter Notebook? [Y/N]: ')
        if option2 not in ['Y', 'y', 'N', 'n']:
            print('\nInvalid option.\n')
    jupyter = ''
    if option2 in ['Y', 'y']:
        jupyter = "RUN pip install jupyter ipykernel"
    try:
        runSubprocess(['docker', 'login', '--username', username, '--password', pwd], check=True)

        dockerfile_contents = f"""
#Use the official image of Python
FROM python:3.11.0-slim

#Establised your work directory
WORKDIR /app

# Install venv and create a virtual environment
RUN python -m venv /app/venv

# Activate the virtual environment
ENV PATH="/app/venv/bin:$PATH"

#Install requirements.txt dependencies (if you need it)
{requirements}

# Install Jupyter (if you need it)
{jupyter}

# Copy all the files
COPY . /app

# Expose the port 8888 for Jupyter
EXPOSE 8888

# Environment variable (optional)
ENV NAME VirtualEnvironment

# Command to run the application, ensure it runs within the virtual environment
CMD ["python", "virtualEnvironment.py"]
"""
    
        image_name = input('Enter the name of your image: ')

        print('\nWriting Dockerfile\n')
        with open('Dockerfile', 'w') as file:
            file.write(dockerfile_contents)
            file.close()
        print('\nBuilding image...\n')
        runSubprocess(f'docker build -t {image_name}:latest .', shell=True, check=True)
        print('\nImage built.\n')
        runSubprocess(f'docker push {image_name}', shell=True, check=True)
        print('\nImage uploaded to DockerHub.\n')


    except CalledProcessError as cp:
        print(f'CalledProcessError: {cp.stderr}')
    except Exception as e:
        print(f'Exception: {e}')


def run_container_docker():
    ports = input('ports: ')
    name_container = input('container: ')
    name_img = input('image: ')
    try:
        runSubprocess('docker run -p'
                      f' {ports} --name {name_container} {name_img}',
                      check=True, shell=True)
    except CalledProcessError as cp:
        print(f'An error occurred: {cp.returncode}')

def docker_start():
    container = input('name container: ')
    try:
        runSubprocess(f'docker start {container}', shell=True, check=True)
    except CalledProcessError as cp:
        print(f'An error occurred: {cp.returncode}')

def docker_stop():
    container = input('name container: ')
    try:
        runSubprocess(f'docker stop {container}', shell=True, check=True)
    except CalledProcessError as cp:
        print(f'An error occurred: {cp.returncode}')

def docker_restart():
    container = input('name container: ')
    try:
        runSubprocess(f'docker restart {container}', shell=True, check=True)
    except CalledProcessError as cp:
        print(f'An error occurred: {cp.returncode}')

def docker_ps():
    try:
        runSubprocess('docker ps', shell=True, check=True)
    except CalledProcessError as cp:
        print(f'An error occurred: {cp.returncode}')

def docker_ps_a():
    try:
        runSubprocess('docker ps -a', shell=True, check=True)
    except CalledProcessError as cp:
        print(f'An error occurred: {cp.returncode}')

def upload_github():
    try:
        email = getenv("GITHUB_EMAIL", default='default_email')
        runSubprocess(f'git config --global user.email "{email}"',
                      shell=True, check=True)
        print('\nname')
        username = getenv("GITHUB_USERNAME", default='default_username')
        runSubprocess(f'git config --global user.name "{username}"',
                      shell=True, check=True)
        runSubprocess('git init', shell=True, check=True)
        print('\nInitializing Github & git status\n')
        #runSubprocess('git status', shell=True, check=True)
        runSubprocess('git add .', shell=True, check=True)
        print('\ngit add .\n')
        commit = input('Enter commit message: ')
        
        runSubprocess(f'git commit -m "{commit}"', shell=True, check=True)
        print('\ncommit\n')          
        
        first_upload = ''
        while first_upload not in ['Y', 'y', 'N', 'n']:
            first_upload = input('Enter if it is your first commit [Y/N]: ')
            if first_upload not in ['Y', 'y', 'N', 'n']:
                print('\nInvalid option\n')
        
        if first_upload in ['Y', 'y']:
            runSubprocess('git branch -M main', shell=True, check=True)
            print('\ngit branch\n')
            my_git = input('Enter repository name: ')
            print('\nremote add origin\n')
            runSubprocess(
                f'git remote add origin https://github.com/pyCampaDB/{my_git}.git',
                shell=True, check=True, capture_output=True
                )
        print('\npush\n')
        runSubprocess(f'git push -u origin main', shell=True, check=True)
        print('\nProject uploaded to GitHub\n')
    except CalledProcessError as cp:
        print(f'\nCalledProcessError: {cp.stderr}\n')
    except Exception as e:
        print(f'Exeption: {e}')

def git_remote_v():
    try:
        runSubprocess(
            'git remote -v', shell=True, check=True
        )
    except CalledProcessError as cp:
        print(f'An error occurred: {cp.returncode}')

def git_remove_origin():
    try:
        runSubprocess(
            'git remote remove origin',
            shell=True,
            check=True
        )
    except CalledProcessError as cp:
        print(f'An error occurred: {cp.returncode}')

def run():
    STANDARD_PACKAGE = []
    signal(SIGINT, signal_handler)
    manage_and_activate_env()
    for key in modules.keys():
        STANDARD_PACKAGE.append(key.strip())
    selection = '1'
    while selection in ['1', '2', '3', '4', '5']:
        selection = input('\n'
                          '1. CMD\n'
                          '2. Run Script\n'
                          '3. Virtual Environment Settings\n'
                          '4. Docker\n'
                          '5. GIT\n'
                          '(Other). Exit\n'
                          'Enter the option: ')

        if selection == '1':
            try:
                while True:
                    a = cmd()
                    if a.lower() == 'exit':
                        break
            except EOFError:
                pass

        
                
        elif selection == '3':
            menu = '2'
            while menu in ['1', '2', '3', '4', '5']:
                menu = input('\n*********************************** VIRTUAL ENVIRONMENT SETTINGS ***********************************\n\n'
                            '\n1. Install an only package'
                            '\n2. Install all packages written in requirements.txt'
                            '\n3. Check your packages already installed'
                            '\n4. Uninstall a package'
                            '\n5. Reset your virtual environment'
                            '\n(Other). Exit\n'
                            '\nEnter your choice: ')
                if menu == '1':
                    package = input('Enter the package name: ')
                    if package in STANDARD_PACKAGE:print(f'{package} already installed!\n')
                    else:check_and_install_package(package)
                elif menu == '2':check_and_install_packages(STANDARD_PACKAGE)
                elif menu == '3': [print(pack) for pack in STANDARD_PACKAGE]
                elif menu == '4': uninstall_package()
                elif menu == '5': reset_venv()
            print('\n***************************************** EXIT VIRTUAL ENVIRONMENT SETTINGS *****************************************\n')


        elif selection == '2': 
            file = input('\nEnter file name: ')
            run_script(file)
        elif selection in ['4', '5']:   
            from dotenv import load_dotenv
            load_dotenv()
            
            if selection == '4':
                docker_option = '1'
                while docker_option in ['1', '2', '3', '4', '5', '6', '7']:
                    docker_option = input('\n******************** DOCKER: ********************\n'
                                          '1. Upload an image to Docker Hub\n'
                                          '2. Run a docker container\n'
                                          '3. Start docker container\n'
                                          '4. Stop docker container\n'
                                          '5. Restart docker container\n'
                                          '6. Show the containers executing\n'
                                          '7. Show all containers\n'
                                          '(Other) Exit Docker\n\n'
                                          'Enter your choice: ')
                    if docker_option == '1':upload_docker()
                    elif docker_option == '2': run_container_docker()
                    elif docker_option=='3': docker_start()
                    elif docker_option=='4': docker_stop()
                    elif docker_option=='5': docker_restart()
                    elif docker_option=='6': docker_ps()
                    elif docker_option=='7': docker_ps_a()
                    else: print('\n******************** EXIT DOCKER ********************\n')
          
            else:
                
                git_option = '1'
                while git_option in ['1', '2', '3']:
                    git_option = input(
                        '\n******************** GIT ********************\n\n'
                        '1. Upload your project to GitHub\n'
                        '2. git remote -v\n'
                        '3. git remote remove origin\n\n'
                        '(Other) Enter your choice: '
                    )

                    if git_option == '1':
                        upload_github()
                    elif git_option == '2': git_remote_v()
                    elif git_option == '3': git_remove_origin()
                print('\n******************** EXIT GIT ********************\n\n')


######################################### MAIN ############################################################################
if __name__ == '__main__':
    run()