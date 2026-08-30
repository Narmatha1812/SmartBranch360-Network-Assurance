 # 🌐 SmartBranch 360 — Network Assurance & Troubleshooting System

> A secure, segmented branch-office network designed in Cisco Packet Tracer with automated configuration validation using Python.

## 📌 Project Overview

**SmartBranch 360** is a branch-office network designed to provide secure connectivity, network segmentation, centralized services, secure device management, and automated configuration assurance.

The network separates users and services into dedicated VLANs and IP subnets while providing inter-VLAN routing, DHCP, DNS, NAT, ACL-based Guest isolation, and SSH-based network-device management.

A Python-based **Network Assurance Checker** is also developed to validate Cisco `show` command outputs against the expected network plan and identify configuration problems with suggested fixes.

The project also demonstrates **intentional fault injection, automated diagnosis, configuration repair, and verification**.

---

## 🎯 Objectives

- Design a segmented branch-office network using VLANs.
- Provide communication between required VLANs using router-on-a-stick.
- Configure DHCP for client networks.
- Provide DNS service through the server.
- Isolate Guest users from Server and Management networks.
- Enable secure SSH-based management from the Management VLAN.
- Configure NAT for external network access.
- Develop a Python tool for configuration assurance.
- Intentionally introduce network faults and diagnose them automatically.

---

## 🏗️ Network Architecture


                         ┌─────────────────┐
                         │       R1        │
                         │  Cisco Router   │
                         └────────┬────────┘
                                  │
                         Trunk 802.1Q
                                  │
                         ┌────────▼────────┐
                         │      SW1        │
                         │   Main Switch   │
                         └───────┬─────────┘
                                 │
                    Trunk         │
                                 │
                         ┌───────▼─────────┐
                         │      SW2        │
                         │  Access Switch  │
                         └───────┬─────────┘
                                 │
               ┌─────────────────┼─────────────────┐
               │                 │                 │
          Management PC       AP1              Other links
                              /  \
                             /    \
                       Laptop0    Laptop1
