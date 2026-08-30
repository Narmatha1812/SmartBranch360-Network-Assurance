from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: str) -> dict[str, Any]:
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"Requirements file not found: {path}")

    with file_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    if not isinstance(data, dict):
        raise ValueError("YAML file must contain a dictionary/object.")

    return data


def check_vlan_plan(config: dict[str, Any]) -> None:
    print("\nVLAN / IP CHECK")

    vlans = config.get("vlans", {})
    required_vlans = {10, 20, 30, 99}

    configured_vlans = {int(vlan_id) for vlan_id in vlans}

    missing = required_vlans - configured_vlans

    if missing:
        print(
            f"[FAIL] Missing VLAN(s): "
            f"{', '.join(map(str, sorted(missing)))}"
        )
    else:
        print("[PASS] All required VLANs are present.")

    for vlan_id, vlan_info in vlans.items():
        print(
            f"[PASS] VLAN {vlan_id}: "
            f"{vlan_info['name']} | "
            f"Subnet: {vlan_info['subnet']} | "
            f"Gateway: {vlan_info['gateway']}"
        )

def check_switch_vlans(
    output_file: str,
    switch_name: str,
    required_vlans: set[int],
    ) -> None:
    print(f"\n{switch_name} VLAN CHECK")

    path = Path(output_file)

    if not path.exists():
        print(f"[FAIL] Output file not found: {output_file}")
        return

    output = path.read_text(encoding="utf-8")

    actual_vlans: set[int] = set()

    for line in output.splitlines():
        parts = line.split()

        if len(parts) >= 3 and parts[0].isdigit():
            vlan_id = int(parts[0])

            if vlan_id in required_vlans:
                actual_vlans.add(vlan_id)

    missing = required_vlans - actual_vlans

    if missing:
        print(
            f"[FAIL] {switch_name}: missing VLAN(s): "
            f"{', '.join(map(str, sorted(missing)))}"
        )
        print(
            "Suggested fix: Create the missing VLAN(s) on the switch."
        )
    else:
        print(
            f"[PASS] {switch_name}: all required VLANs are present."
        )


def extract_trunk_vlans(output: str) -> set[int]:
    """
    Extract VLAN numbers from the line:
    'Port        Vlans allowed and active in management domain'

    The following line is expected to contain something like:
    Fa0/24      1,10,20,30,99
    """

    lines = output.splitlines()

    for index, line in enumerate(lines):
        if "Vlans allowed and active in management domain" in line:
            if index + 1 < len(lines):
                next_line = lines[index + 1].strip()

                parts = next_line.split()

                if len(parts) >= 2:
                    vlan_text = parts[-1]

                    try:
                        return {
                            int(vlan.strip())
                            for vlan in vlan_text.split(",")
                        }
                    except ValueError:
                        return set()

    return set()


def check_trunk(
    output_file: str,
    required_vlans: set[int],
) -> None:
    print("\nTRUNK CHECK")

    path = Path(output_file)

    if not path.exists():
        print(f"[FAIL] Output file not found: {output_file}")
        return

    output = path.read_text(encoding="utf-8")

    actual_vlans = extract_trunk_vlans(output)

    if not actual_vlans:
        print("[FAIL] Could not determine active VLANs from trunk output.")
        return

    missing = required_vlans - actual_vlans

    print(f"Actual active VLANs on trunk: {sorted(actual_vlans)}")

    if missing:
        print(
            f"[FAIL] Missing VLAN(s) on trunk: "
            f"{', '.join(map(str, sorted(missing)))}"
        )

        print(
            "Suggested fix: Add the missing VLAN(s) "
            "to the trunk allowed VLAN list."
        )
    else:
        print("[PASS] All required VLANs are present on the trunk.")

def check_r1_interfaces(
    output_file: str,
    config: dict[str, Any],
) -> None:
    print("\nR1 INTERFACE CHECK")

    path = Path(output_file)

    if not path.exists():
        print(f"[FAIL] Output file not found: {output_file}")
        return

    output = path.read_text(encoding="utf-8")

    expected = {
        "GigabitEthernet0/1.10": "10.10.10.1",
        "GigabitEthernet0/1.20": "10.10.20.1",
        "GigabitEthernet0/1.30": "10.10.30.1",
        "GigabitEthernet0/1.99": "10.10.99.1",
    }

    for interface, expected_ip in expected.items():
        found = False

        for line in output.splitlines():
            parts = line.split()

            if len(parts) >= 6 and parts[0] == interface:
                found = True

                actual_ip = parts[1]
                status = parts[4]
                protocol = parts[5]

                if actual_ip != expected_ip:
                    print(
                        f"[FAIL] {interface}: "
                        f"expected IP {expected_ip}, found {actual_ip}"
                    )
                elif status != "up" or protocol != "up":
                    print(
                        f"[FAIL] {interface}: "
                        f"IP {actual_ip}, but status is "
                        f"{status}/{protocol}"
                    )
                else:
                    print(
                        f"[PASS] {interface}: "
                        f"{actual_ip} | {status}/{protocol}"
                    )

                break

        if not found:
            print(
                f"[FAIL] {interface}: interface not found "
                f"in R1 output."
            )

def check_dhcp_output(
    output_file: str,
    config: dict[str, Any],
) -> None:
    print("\nDHCP CHECK")

    path = Path(output_file)

    if not path.exists():
        print(f"[FAIL] Output file not found: {output_file}")
        return

    output = path.read_text(encoding="utf-8")
    lines = output.splitlines()

    expected_networks = {
        "EMPLOYEE": "10.10.10.0",
        "GUEST": "10.10.20.0",
        "MANAGEMENT": "10.10.99.0",
    }

    for pool_name, expected_network in expected_networks.items():

        pool_found = False
        actual_network = None

        for index, line in enumerate(lines):

            if line.strip().startswith(f"Pool {pool_name}"):

                pool_found = True

                # Search the lines belonging to this DHCP pool
                for next_line in lines[index + 1:index + 20]:

                    parts = next_line.split()

                    # Actual Cisco line looks like:
                    #
                    # 10.10.10.1  10.10.10.1  -  10.10.10.254  7 / 4 / 254
                    #
                    # Therefore:
                    # parts[0] = first IP
                    # parts[1] = first IP again
                    # parts[2] = '-'

                    if len(parts) >= 4 and parts[2] == "-":

                        actual_network = parts[0]

                        break

                break

        if not pool_found:
            print(
                f"[FAIL] DHCP pool {pool_name} was not found."
            )
            continue

        if actual_network is None:
            print(
                f"[FAIL] DHCP pool {pool_name}: "
                "IP address range could not be detected."
            )
            continue

        expected_start = expected_network.rsplit(".", 1)[0] + ".1"

        if actual_network == expected_start:
            print(
                f"[PASS] DHCP pool {pool_name}: "
                f"network {expected_network}/24."
            )
        else:
            print(
                f"[FAIL] DHCP pool {pool_name}: "
                f"expected {expected_network}/24, "
                f"found {actual_network}."
            )

def check_guest_acl(output_file: str) -> None:
    print("\nGUEST ACL CHECK")

    path = Path(output_file)

    if not path.exists():
        print(f"[FAIL] Output file not found: {output_file}")
        return

    output = path.read_text(encoding="utf-8")

    required_rules = [
        "permit udp any eq bootpc any eq bootps",
        "permit udp 10.10.20.0 0.0.0.255 host 10.10.30.10 eq domain",
        "permit tcp 10.10.20.0 0.0.0.255 host 10.10.30.10 eq domain",
        "deny ip 10.10.20.0 0.0.0.255 10.10.30.0 0.0.0.255",
        "deny ip 10.10.20.0 0.0.0.255 10.10.99.0 0.0.0.255",
        "permit ip 10.10.20.0 0.0.0.255 any",
    ]

    missing_rules = []

    for rule in required_rules:
        if rule not in output:
            missing_rules.append(rule)

    if not missing_rules:
        print("[PASS] Guest ACL contains all required security rules.")
    else:
        print("[FAIL] Guest ACL is missing required rule(s):")

        for rule in missing_rules:
            print(f"       - {rule}")

        print(
            "Suggested fix: Restore the missing Guest ACL rule(s)."
        )

def check_nat_output(output_file: str) -> None:
    print("\nNAT CHECK")

    path = Path(output_file)

    if not path.exists():
        print(f"[FAIL] Output file not found: {output_file}")
        return

    output = path.read_text(encoding="utf-8")

    required_nat_rule = (
        "ip nat inside source list 1 "
        "interface GigabitEthernet0/0 overload"
    )

    if required_nat_rule in output:
        print("[PASS] NAT overload rule is configured.")
    else:
        print("[FAIL] NAT overload rule is missing.")
        print(
            "Suggested fix: Configure NAT overload using "
            "ACL 1 and GigabitEthernet0/0."
        )

    inside_count = 0
    outside_count = 0

    for line in output.splitlines():
        stripped = line.strip()

        if stripped == "ip nat inside":
            inside_count += 1

        elif stripped == "ip nat outside":
            outside_count += 1

    if inside_count >= 4:
        print(
            f"[PASS] NAT inside interfaces detected: "
            f"{inside_count}"
        )
    else:
        print(
            f"[FAIL] Expected 4 NAT inside interfaces, "
            f"found {inside_count}."
        )

    if outside_count >= 1:
        print("[PASS] NAT outside interface detected.")
    else:
        print("[FAIL] NAT outside interface is missing.")        

def main() -> None:
    try:
        config = load_yaml("requirements.yaml")

        print("=" * 60)
        print("SMARTBRANCH 360 NETWORK ASSURANCE CHECKER")
        print("=" * 60)

        check_vlan_plan(config)

        required_vlans = {
            int(vlan_id)
            for vlan_id in config["vlans"].keys()
        }

        check_switch_vlans(
            "sample_outputs/sw1_vlan.txt",
            "SW1",
            required_vlans,
        )

        check_switch_vlans(
            "sample_outputs/sw2_vlan.txt",
            "SW2",
            required_vlans,
        )

        check_trunk(
            "sample_outputs/sw2_trunk.txt",
            required_vlans,
        )

        check_r1_interfaces(
            "sample_outputs/r1_interfaces.txt",
            config,
        )

        check_dhcp_output(
            "sample_outputs/r1_dhcp_pool.txt",
             config,
        )

        check_guest_acl(
            "sample_outputs/r1_guest_acl.txt"
        )

        check_nat_output(
            "sample_outputs/r1_nat.txt"
        )

        print("\nCHECK COMPLETE")

    except (FileNotFoundError, ValueError, OSError) as error:
        print(f"[ERROR] {error}")


if __name__ == "__main__":
    main()