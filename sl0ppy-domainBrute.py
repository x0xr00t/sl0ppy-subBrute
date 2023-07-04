#!/env/python
# Team   : Sl0ppyr00t
# AKA    : x0xr00t
# Author : p.hoogeveen
# Tool   : Sl0ppy-DomainBrute


import dns.resolver
import string
import itertools
import argparse
from colorama import Fore, Style, init
import random

def print_banner():
    init(autoreset=True)
    banner = """
       .__  _______                                    .___                    .__      __________                __          
  _____|  | \   _  \ ______ ______ ___.__.           __| _/____   _____ _____  |__| ____\______   \_______ __ ___/  |_  ____  
 /  ___/  | /  /_\  \\____ \\____ <   |  |  ______  / __ |/  _ \ /     \\__  \ |  |/    \|    |  _/\_  __ \  |  \   __\/ __ \ 
 \___ \|  |_\  \_/   \  |_> >  |_> >___  | /_____/ / /_/ (  <_> )  Y Y  \/ __ \|  |   |  \    |   \ |  | \/  |  /|  | \  ___/ 
/____  >____/\_____  /   __/|   __// ____|         \____ |\____/|__|_|  (____  /__|___|  /______  / |__|  |____/ |__|  \___  >
     \/            \/|__|   |__|   \/                   \/            \/     \/        \/       \/                         \/ 
    """
    banner_colors = [Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN]
    colored_banner = ""
    for line in banner.splitlines():
        colored_line = ""
        for char in line:
            if char.isalpha():
                colored_line += random.choice(banner_colors) + char
            else:
                colored_line += char
        colored_banner += colored_line + "\n"
    print(colored_banner)
    print(Style.RESET_ALL)

print_banner()

def brute_force_domains(domain):
    characters = string.ascii_letters + string.digits + string.punctuation

    for length in range(1, 101):  # Set the desired length of the subdomains (1 to 100 characters)
        for combination in itertools.product(characters, repeat=length):
            subdomain = ''.join(combination)
            target = subdomain + '.' + domain
            try:
                answers = 'A' * 100
                for answer in answers:
                    print(Fore.GREEN + target + ' -> ' + str(answer))
            except dns.resolver.NXDOMAIN:
                print(Fore.WHITE + target + ' -> Not Found')
            except dns.resolver.NoAnswer:
                print(Fore.WHITE + target + ' -> No Answer')
            except dns.resolver.NoNameservers:
                print(Fore.WHITE + target + ' -> No Nameservers')
            except dns.exception.Timeout:
                print(Fore.WHITE + target + ' -> DNS Timeout')
            except dns.resolver.NoNameservers:
                print(Fore.WHITE + target + ' -> No Nameservers')

    print(Style.RESET_ALL)
    print("\nFound domains:")
    for domain in found_domains:
        print(domain)

# Parse the command-line arguments
parser = argparse.ArgumentParser(description='Domain brute-forcing script')
parser.add_argument('-d', dest='target_domain', help='Target domain to brute force')

args = parser.parse_args()

# Check if the target domain is provided
if args.target_domain:
    target_domain = args.target_domain
    print_banner()
    brute_force_domains(target_domain)
else:
    parser.print_help()
