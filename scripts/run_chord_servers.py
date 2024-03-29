import click
import csv
from math import ceil, floor, sqrt
import os


@click.command()
@click.argument('server_list_file', default='server-list.csv')
@click.argument('server_join_file', default='server-list-join.csv')
@click.argument('template_file', default='scripts/tmux_template.yaml')
@click.option('--remote', is_flag=True)
@click.option('--pem_file', type=str)
@click.option('--no_exec', is_flag=True)
@click.option('--setup', is_flag=True)
@click.option('--no_sync', is_flag=True)
def gen_run_script(server_list_file, server_join_file, template_file, remote, no_exec, pem_file, setup, no_sync):
    servers = []
    toJoin = []
    addresses = set()

    with open(server_list_file, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            servers.append(dict(row))
    with open(server_join_file, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            toJoin.append(dict(row))
    script = ''
    with open(template_file, 'r') as file:
        script += file.read()
    for idx, s in enumerate(servers):
        if remote is True:
            remote_exec = f'ssh -i {pem_file} ec2-user@{s["address"]}'
            if setup is True:
                if s["address"] not in addresses:
                    script += f'    - shell_command:\n'
                    script += f'      - {remote_exec} \"sudo yum install python3-pip -y && sudo pip3 install grpcio grpcio-tools click\"\n'
            else:
                script += f'    - shell_command:\n'
                if not no_sync and s["address"] not in addresses:
                    script += f'      - rsync -r -v -a --delete -P -e "ssh -i {pem_file}" *.txt *.csv ec2-user@{s["address"]}:/home/ec2-user/chord/\n'
                    script += f'      - rsync -r -v -a --delete -P -e "ssh -i {pem_file}" ./src/  ec2-user@{s["address"]}:/home/ec2-user/chord/src\n'
                    script += f'      - rsync -r -v -a --delete -P -e "ssh -i {pem_file}" ./scripts/  ec2-user@{s["address"]}:/home/ec2-user/chord/scripts\n'
                script += f'      - {remote_exec} \"cd /home/ec2-user/chord && bash ./scripts/aws_start_server.sh ' \
                    f'0.0.0.0:{s["port"]} {s["id"]} {toJoin[idx]["address"]}:{toJoin[idx]["port"]}\"\n'
        else:
            script += f'    - reset && python src/chord.py {s["address"]}:{s["port"]} --id {s["id"]} ' \
                f'--join {toJoin[idx]["address"]}:{toJoin[idx]["port"]} \n'
        addresses.add(s["address"])
    with open('launch_chord.yaml', 'w') as file:
        file.write(script)
    if not no_exec:
        os.system('tmuxp load -y launch_chord.yaml')


if __name__ == "__main__":
    gen_run_script()
