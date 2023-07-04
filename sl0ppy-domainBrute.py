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
import threading
import psutil


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
    color_index = 0
    for line in banner.splitlines():
        colored_line = ""
        for char in line:
            if char.isalpha():
                colored_line += banner_colors[color_index % len(banner_colors)] + char
                color_index += 1
            else:
                colored_line += char
        colored_banner += colored_line + "\n"
    print(colored_banner)
    print(Style.RESET_ALL)


def brute_force_domains(domain):
    characters = string.ascii_letters + string.digits + string.punctuation
    found_domains = []

    total_combinations = 0
    for length in range(1, 101):  # Set the desired length of the subdomains (1 to 100 characters)
        total_combinations += len(characters) ** length

    current_combination = 0
    for length in range(1, 101):
        for combination in itertools.product(characters, repeat=length):
            current_combination += 1
            subdomain = ''.join(combination)
            target = subdomain + '.' + domain
            try:
                answers = 'A' * 100
                for answer in answers:
                    pass
            except dns.resolver.NXDOMAIN:
                pass
            except dns.resolver.NoAnswer:
                pass
            except dns.resolver.NoNameservers:
                pass
            except dns.exception.Timeout:
                pass
            except dns.resolver.NoNameservers:
                pass
            else:
                found_domains.append(target)

            # Check CPU usage and limit to 80%
            if psutil.cpu_percent() > 80:
                threading.Event().wait(0.1)  # Sleep for 100ms to reduce CPU usage

            # Print progress percentage
            progress = (current_combination / total_combinations) * 100
            print(f"\rProgress: {progress:.2f}%", end='')

    return found_domains


def main():
    # Parse the command-line arguments
    parser = argparse.ArgumentParser(description='Domain brute-forcing script')
    parser.add_argument('-d', dest='target_domain', help='Target domain to brute force')

    args = parser.parse_args()

    # Check if the target domain is provided
    if args.target_domain:
        target_domain = args.target_domain
        print_banner()
        print("Brute forcing in progress...")
        found_domains = brute_force_domains(target_domain)
        print("\nFound subdomains:")
        for domain in found_domains:
            print(domain)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
