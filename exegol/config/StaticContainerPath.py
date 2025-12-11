from enum import Enum


class StaticContainerPath(Enum):
    # Exegol
    EXEGOL_SPAWN = '/.exegol/spawn.sh'
    EXEGOL_ENTRYPOINT = '/.exegol/entrypoint.sh'

    # Ressources
    EXEGOL_RESOURCES = '/opt/resources'
    MY_RESOURCES = '/opt/my-resources'

    # OpenVPN
    OPENVPN_CREDS_FILE = '/.exegol/vpn/auth/creds.txt'
    OPENVPN_CONFIG_DIR = '/.exegol/vpn/config'
    OPENVPN_CONFIG_FILE = '/.exegol/vpn/config/client.ovpn'
    # Wireguard
    WIREGUARD_CONFIG_FILE = '/etc/wireguard/wg0.conf'

    # JSON Shell logging
    JSON_SHELL_LOGGER = '/.exegol/json_shell_logger.py'
    JSON_SHELL_LOGGING_LOG = '/var/log/exegol/shell_commands.json'
    JSON_SHELL_LOGGING_ZSH = '/etc/zsh.d/shell_logging'
    JSON_SHELL_LOGGING_BASH = '/etc/bash.d/shell_logging'
