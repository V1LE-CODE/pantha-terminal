# OsirisCLI: The Encrypted Note-Based Terminal

---
![License](https://img.shields.io/badge/license-MIT-orange)
![Python](https://img.shields.io/badge/python-3.11+-blue?logo=python&logoColor=white) 
![Platform](https://img.shields.io/badge/platform-Windows-blue) 
![Commits](https://img.shields.io/github/commit-activity/m/OSI-project/osiris-cli)
![GitHub stars](https://img.shields.io/github/stars/OSI-project/osiris-cli?style=social)
![Downloads](https://img.shields.io/github/downloads/OSI-project/osiris-cli/total)
![Made With Love](https://img.shields.io/badge/made%20with-%E2%9D%A4-red)
---

## 🚀 Overview

**OsirisCLI** is a next-generation, encrypted terminal workspace disguised as a minimalist command shell. It offers a unique blend of hacker-style aesthetics with professional-grade security, designed for private, local-first knowledge storage. Every note created within OsirisCLI is **encrypted** on disk using strong key derivation and authenticated encryption, ensuring your data remains unreadable without your password. Even if files are copied or stolen, their contents stay protected.

Once unlocked, OsirisCLI transforms the terminal into a powerful, command-driven productivity environment where you can create, search, edit, pin, and organize notes instantly—no mouse, no clutter, no distractions. It's built for speed, privacy, and control, never relying on cloud services, background trackers, or external databases. Everything lives locally, encrypted and isolated, providing an immersive workflow that feels like operating your own personal secure system.

## ✨ Key Features

*   **Encrypted Local Storage**: All notes are encrypted on disk using robust cryptographic methods, ensuring maximum privacy and security.
*   **Terminal-style UI**: A sleek, interactive command-line interface with live input and a rich log output.
*   **Orange Aesthetic**: A vibrant and eye-catching orange theme with fun, readable terminal colors.
*   **Rich ASCII Banners**: Dynamic ASCII art, including a magical Osiris awakening animation.
*   **Command-Driven Workflow**: Efficient note management (create, view, edit, delete, pin, unpin, rename) directly from the command line.
*   **Persistent History**: Your command history is saved, allowing for easy recall and navigation.
*   **No Cloud Dependency**: Designed for ultimate privacy, OsirisCLI operates entirely offline, with no external network calls.
*   **Cross-Platform Compatibility**: Built with Python, ensuring broad compatibility across various operating systems.

## 🔒 Security & Encryption

OsirisCLI employs a multi-layered security approach to protect your sensitive information:

*   **Strong Key Derivation**: Utilizes `PBKDF2` with `HMAC-SHA256` to derive strong encryption keys from your password, making brute-force attacks computationally infeasible.
*   **Authenticated Encryption**: Implements `AES-256` in `GCM` mode, providing both confidentiality and integrity for your notes. This ensures that not only is your data unreadable, but it also cannot be tampered with without detection.
*   **Local-First Design**: Your data never leaves your machine. There are no cloud backups, no telemetry, and no third-party integrations that could compromise your privacy.
*   **Password Requirements**: Enforces strong password policies, requiring a minimum length, uppercase and lowercase letters, digits, and special characters to enhance security.

### Cryptographic Implementation Details

| Parameter | Value |
| :--- | :--- |
| Key Derivation Function | `PBKDF2` |
| HMAC | `SHA-256` |
| Iterations | `100,000` |
| Salt Size | `16 bytes` |
| Key Size | `32 bytes (256-bit)` |
| Encryption Algorithm | `AES (Advanced Encryption Standard)` |
| Mode of Operation | `GCM (Galois/Counter Mode)` |
| Nonce Size | `12 bytes` |
| Tag Size | `16 bytes` |

## ⚙️ Architecture

OsirisCLI is built primarily in Python, leveraging the `Textual` framework for its rich terminal user interface. Key architectural components include:

*   **`app/main.py`**: The core application logic, handling UI rendering, command parsing, and interaction with the vault.
*   **`app/encryption.py`**: Contains the cryptographic engine responsible for all encryption and decryption operations.
*   **`app/storage.py`**: Manages the secure storage and retrieval of encrypted notes on the local filesystem.
*   **`vault.py`**: Provides an abstraction layer for note management, interacting with the storage and encryption modules.

## 💻 Installation

### Prerequisites

*   Python 3.11+ installed.
*   `pip` (Python package installer).

### Steps

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/OSI-project/osiris-cli.git
    cd osiris-cli
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the application**:
    ```bash
    python app/main.py
    ```

### Windows Installer

For Windows users, a dedicated installer is available. Download the latest `OsirisSetup-Windows-vX.X.X.exe` from the [releases page](https://github.com/OSI-project/osiris-cli/releases).

## 💡 Comprehensive Command Reference

Upon launching OsirisCLI, you will be greeted by the command prompt. Here are some essential commands:

| Command | Description | Example |
| :------ | :---------- | :------ |
| `unlock <password>` | Unlocks the encrypted vault. | `unlock MySuperSecretPassword123!` |
| `lock` | Locks the vault, encrypting all notes. | `lock` |
| `status` | Displays the current vault status (locked/unlocked). | `status` |
| `note list` | Lists all notes in the vault. | `note list` |
| `note create <title>` | Creates a new note with the specified title. | `note create MyFirstNote` |
| `note view <title>` | Displays the content of a note. | `note view MyFirstNote` |
| `note append <title> <text>` | Appends text to an existing note. | `note append MyFirstNote "This is additional content."` |
| `note delete <title>` | Deletes a note. | `note delete MyFirstNote` |
| `note pin <title>` | Pins a note for quick access. | `note pin ImportantTask` |
| `note unpin <title>` | Unpins a note. | `note unpin ImportantTask` |
| `note pinned` | Lists all pinned notes. | `note pinned` |
| `history` | Shows the command history. | `history` |
| `clear` | Clears the terminal screen. | `clear` |
| `exit` / `quit` | Exits the application. | `exit` |

## 🗺️ Roadmap

We have an exciting roadmap planned for OsirisCLI, with a focus on enhancing functionality and user experience. Here are some of the features we are working on:

*   **Cross-Platform Installers**: Providing dedicated installers for macOS and Linux.
*   **Plugin System**: Allowing users to extend OsirisCLI with custom commands and functionality.
*   **Advanced Search**: Implementing full-text search capabilities within the encrypted vault.
*   **Theming Engine**: Enabling users to create and share their own color themes.
*   **Note Tagging & Categorization**: Adding support for organizing notes with tags and categories.
*   **Export/Import**: Allowing users to securely export and import their notes.

## 🤝 Contributing

We welcome contributions from the community! If you're interested in making OsirisCLI even better, please consider:

*   **Reporting Bugs**: Encountered an issue? Please report it on our [bug report discussions](https://github.com/orgs/OSI-project/discussions/categories/bug-report).
*   **Suggesting Features**: Have an idea for a new feature? Share it on our [feature request discussions](https://github.com/orgs/OSI-project/discussions/categories/feature-request).
*   **Submitting Pull Requests**: Fork the repository, make your changes, and submit a pull request. Please ensure your code adheres to our style guidelines and includes appropriate tests.
*   **Joining the Team**: OsirisCLI is an open-source project aimed to be a free encrypted note-based terminal made by our team OSI. If you have any interest in joining the team, click here to [contact us](https://github.com/orgs/OSI-project/discussions/categories/team-join).

For more details, please refer to our [CONTRIBUTING.md](https://github.com/OSI-project/osiris-cli/blob/main/CONTRIBUTING.md) guide.

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/OSI-project/osiris-cli/blob/main/LICENSE) file for details.

Copyright (c) 2026 OSI. All rights reserved.

## 📞 Contact

For any inquiries or support, please reach out via our [GitHub Discussions](https://github.com/orgs/OSI-project/discussions).

---

**Thank you for using OsirisCLI!**
