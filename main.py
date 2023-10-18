# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    def get_cpu_info():
        cpu_info = {}

        try:
            with open('/proc/cpuinfo', 'r') as file:
                lines = file.readlines()

                for line in lines:
                    parts = line.strip().split(':')
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip()
                        cpu_info[key] = value

        except FileNotFoundError:
            print(
                "Error: /proc/cpuinfo not found. Are you sure this is a Raspberry Pi running Debian?")

        return cpu_info
    return get_cpu_info()

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print(print_hi('PyCharm'))

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
